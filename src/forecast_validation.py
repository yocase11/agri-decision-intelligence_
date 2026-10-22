"""Leakage-safe forecasting validation and diagnostic artifact generation."""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from tensorflow.keras.layers import Dense, Input, LSTM
from tensorflow.keras.models import Sequential


CROPS = ('Rice', 'Onion', 'Tomato')
MODELS = ('seasonal_naive', 'arima', 'sarima', 'lstm')
PRICE_COLUMN = 'Price_INR_per_Quintal'
PRICE_UNIT = 'INR per quintal'
SEASONAL_PERIOD = 4
FORECAST_BOUND_MULTIPLIER = 10.0
INTERVAL_CONFIDENCE_LEVEL = 0.95
DM_MIN_PAIRED_ORIGINS = 5


def _compute_metrics(actual, predicted):
    """Compute metrics across a complete, aligned prediction vector."""
    actual = np.asarray(actual, dtype=float).reshape(-1)
    predicted = np.asarray(predicted, dtype=float).reshape(-1)
    invalid = {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan}
    if actual.size == 0 or actual.size != predicted.size:
        return invalid
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        return invalid

    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        error = predicted - actual
        squared_error = np.square(error)
        mae = float(np.mean(np.abs(error)))
        rmse = float(np.sqrt(np.mean(squared_error)))
        mape = np.nan if np.any(actual == 0) else float(np.mean(np.abs(error / actual)) * 100.0)
        sse = float(np.sum(squared_error))
        sst = float(np.sum(np.square(actual - np.mean(actual))))
    if not np.isfinite(mae) or not np.isfinite(rmse):
        return invalid
    r2 = float(1.0 - sse / sst) if sst > 0 else np.nan
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2}


def _quarter_periods(df):
    if 'Year' not in df.columns or 'Quarter' not in df.columns:
        raise ValueError("Dataset must include 'Year' and 'Quarter' columns")
    quarter_number = df['Quarter'].astype(str).str.extract(r'Q([1-4])', expand=False)
    if quarter_number.isna().any():
        quarter_number = quarter_number.fillna(df['Quarter'].astype(str).str.extract(r'([1-4])$', expand=False))
    labels = df['Year'].astype('Int64').astype(str) + 'Q' + quarter_number.astype(str)
    return pd.PeriodIndex(labels, freq='Q')


def _load_crop_series(data_path, crop, price_column=PRICE_COLUMN):
    df = pd.read_csv(data_path)
    if price_column not in df.columns:
        raise ValueError(f"Source price column '{price_column}' is missing; refusing to infer or convert units")
    if 'Crop' not in df.columns:
        raise ValueError("Dataset must include a 'Crop' column")

    df = df.copy()
    df['_quarter'] = _quarter_periods(df)
    crop_rows = df.loc[df['Crop'].astype(str).str.casefold() == crop.casefold()].copy()
    if crop_rows.empty:
        raise ValueError(f'No rows found for crop {crop}')
    raw_crop_rows = len(crop_rows)
    crop_rows[price_column] = pd.to_numeric(crop_rows[price_column], errors='coerce')
    missing_price_rows = int(crop_rows[price_column].isna().sum())
    crop_rows = crop_rows.dropna(subset=[price_column])
    if crop_rows.empty:
        raise ValueError(f'No observed {price_column} values found for crop {crop}')

    duplicate_count = int(len(crop_rows) - crop_rows['_quarter'].nunique())
    grouped = crop_rows.groupby('_quarter', sort=True)[price_column].mean()
    segments = []
    segment_start = 0
    ordinals = grouped.index.asi8
    for position in range(1, len(grouped)):
        if ordinals[position] != ordinals[position - 1] + 1:
            segments.append((segment_start, position))
            segment_start = position
    segments.append((segment_start, len(grouped)))
    longest_segment = max(segments, key=lambda bounds: bounds[1] - bounds[0])
    evaluated = grouped.iloc[longest_segment[0]:longest_segment[1]]
    series = pd.Series(
        evaluated.to_numpy(dtype=float),
        index=evaluated.index.to_timestamp(how='end').normalize(),
        name=crop,
        dtype=float,
    ).sort_index()
    expected_quarters = pd.period_range(grouped.index.min(), grouped.index.max(), freq='Q')
    missing_quarters = expected_quarters.difference(grouped.index)
    metadata = {
        'crop': crop,
        'raw_crop_rows': raw_crop_rows,
        'missing_source_price_rows': missing_price_rows,
        'duplicate_rows_aggregated': duplicate_count,
        'source_price_observations': len(grouped),
        'excluded_due_to_quarter_gaps': len(grouped) - len(evaluated),
        'observations': len(series),
        'start': str(evaluated.index.min()),
        'end': str(evaluated.index.max()),
        'missing_quarters': [str(period) for period in missing_quarters],
        'price_min': float(series.min()),
        'price_max': float(series.max()),
    }
    return series, metadata, df


def _seasonal_naive_forecast(train, horizon):
    if len(train) < SEASONAL_PERIOD:
        raise ValueError(f'Seasonal naive requires at least {SEASONAL_PERIOD} training observations')
    return np.resize(np.asarray(train.iloc[-SEASONAL_PERIOD:], dtype=float), horizon)


def _fit_arima(train):
    return SARIMAX(
        train,
        order=(1, 1, 1),
        seasonal_order=(0, 0, 0, 0),
        enforce_stationarity=True,
        enforce_invertibility=True,
    ).fit(disp=False, maxiter=500, method='lbfgs')


def _fit_sarima(train):
    return SARIMAX(
        train,
        order=(0, 1, 1),
        seasonal_order=(0, 1, 1, SEASONAL_PERIOD),
        enforce_stationarity=True,
        enforce_invertibility=True,
    ).fit(disp=False, maxiter=500, method='lbfgs')


def _fit_lstm(train, seed):
    import tensorflow as tf

    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(seed)
    values = np.asarray(train, dtype=float).reshape(-1, 1)
    window = min(SEASONAL_PERIOD, len(values) - 1)
    if window < 1:
        raise ValueError('LSTM requires at least two training observations')

    scaler = MinMaxScaler(feature_range=(0.0, 1.0))
    scaled = scaler.fit_transform(values)
    inputs = np.asarray([scaled[i - window:i, 0] for i in range(window, len(scaled))], dtype=float)
    targets = np.asarray([scaled[i, 0] for i in range(window, len(scaled))], dtype=float)
    sequence_count = len(inputs)
    if sequence_count == 0:
        raise ValueError('LSTM generated no training sequences')

    model = Sequential([
        Input(shape=(window, 1)),
        LSTM(32, activation='relu'),
        Dense(1),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mse')
    model.fit(inputs.reshape(sequence_count, window, 1), targets, epochs=20, batch_size=8, verbose=0, shuffle=False)
    return model, scaler, window, sequence_count


def _forecast_lstm(train, horizon, seed):
    model, scaler, window, sequence_count = _fit_lstm(train, seed)
    last_window = scaler.transform(np.asarray(train, dtype=float).reshape(-1, 1))[-window:, 0]
    predictions = []
    for _ in range(horizon):
        value = float(model.predict(last_window.reshape(1, window, 1), verbose=0)[0, 0])
        predictions.append(value)
        last_window = np.append(last_window[1:], value)
    forecast = scaler.inverse_transform(np.asarray(predictions).reshape(-1, 1)).ravel()
    return forecast, sequence_count


def _forecast_fold(train, model_name, horizon, seed):
    diagnostics = {
        'converged': None, 'aic': np.nan, 'bic': np.nan,
        'forecast_min': np.nan, 'forecast_max': np.nan,
        'warning': '', 'failure_reason': '', 'lstm_training_sequences': 0,
        'parameter_count': np.nan, 'residual_mean': np.nan, 'residual_std': np.nan,
        'ljung_box_p_value': np.nan, 'ljung_box_lag': np.nan,
        'residual_acf_lag1': np.nan, 'interval_generated': False,
        'interval_failure_reason': '', 'small_sample_warning': '',
    }
    lower = np.full(horizon, np.nan, dtype=float)
    upper = np.full(horizon, np.nan, dtype=float)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            if model_name == 'seasonal_naive':
                forecast = _seasonal_naive_forecast(train, horizon)
            elif model_name == 'arima':
                fitted = _fit_arima(train)
                diagnostics['converged'] = bool(fitted.mle_retvals.get('converged', False))
                diagnostics['aic'] = float(fitted.aic)
                diagnostics['bic'] = float(fitted.bic)
                forecast_result = fitted.get_forecast(steps=horizon)
                forecast = np.asarray(forecast_result.predicted_mean, dtype=float)
                try:
                    interval = np.asarray(forecast_result.conf_int(alpha=1.0 - INTERVAL_CONFIDENCE_LEVEL), dtype=float)
                    if interval.shape == (horizon, 2) and np.isfinite(interval).all() and np.all(interval[:, 0] <= interval[:, 1]):
                        lower, upper = interval[:, 0], interval[:, 1]
                        diagnostics['interval_generated'] = True
                    else:
                        diagnostics['interval_failure_reason'] = 'Native confidence interval returned invalid shape, values, or bounds'
                except Exception as exc:
                    diagnostics['interval_failure_reason'] = f'{type(exc).__name__}: {exc}'
                diagnostics['parameter_count'] = int(np.asarray(fitted.params).size)
                residuals = np.asarray(fitted.resid, dtype=float)
                residuals = residuals[np.isfinite(residuals)]
                if residuals.size:
                    diagnostics['residual_mean'] = float(np.mean(residuals))
                    diagnostics['residual_std'] = float(np.std(residuals, ddof=1)) if residuals.size > 1 else np.nan
                    if residuals.size > 1 and np.std(residuals) > 0:
                        diagnostics['residual_acf_lag1'] = float(pd.Series(residuals).autocorr(lag=1))
                    model_df = 2 if model_name == 'arima' else 2
                    lag = min(4, max(1, residuals.size // 5))
                    if residuals.size > lag + model_df:
                        diagnostics['ljung_box_lag'] = lag
                        diagnostics['ljung_box_p_value'] = float(
                            acorr_ljungbox(residuals, lags=[lag], model_df=model_df, return_df=True)['lb_pvalue'].iloc[0]
                        )
                if model_name == 'sarima' and len(train) < max(20, 5 * SEASONAL_PERIOD):
                    diagnostics['small_sample_warning'] = (
                        f'SARIMA training size {len(train)} is small for seasonal period {SEASONAL_PERIOD} '
                        f'with {diagnostics["parameter_count"]} estimated parameters'
                    )
            elif model_name == 'sarima':
                fitted = _fit_sarima(train)
                diagnostics['converged'] = bool(fitted.mle_retvals.get('converged', False))
                diagnostics['aic'] = float(fitted.aic)
                diagnostics['bic'] = float(fitted.bic)
                forecast_result = fitted.get_forecast(steps=horizon)
                forecast = np.asarray(forecast_result.predicted_mean, dtype=float)
                try:
                    interval = np.asarray(forecast_result.conf_int(alpha=1.0 - INTERVAL_CONFIDENCE_LEVEL), dtype=float)
                    if interval.shape == (horizon, 2) and np.isfinite(interval).all() and np.all(interval[:, 0] <= interval[:, 1]):
                        lower, upper = interval[:, 0], interval[:, 1]
                        diagnostics['interval_generated'] = True
                    else:
                        diagnostics['interval_failure_reason'] = 'Native confidence interval returned invalid shape, values, or bounds'
                except Exception as exc:
                    diagnostics['interval_failure_reason'] = f'{type(exc).__name__}: {exc}'
                diagnostics['parameter_count'] = int(np.asarray(fitted.params).size)
                residuals = np.asarray(fitted.resid, dtype=float)
                residuals = residuals[np.isfinite(residuals)]
                if residuals.size:
                    diagnostics['residual_mean'] = float(np.mean(residuals))
                    diagnostics['residual_std'] = float(np.std(residuals, ddof=1)) if residuals.size > 1 else np.nan
                    if residuals.size > 1 and np.std(residuals) > 0:
                        diagnostics['residual_acf_lag1'] = float(pd.Series(residuals).autocorr(lag=1))
                    model_df = 2
                    lag = min(4, max(1, residuals.size // 5))
                    if residuals.size > lag + model_df:
                        diagnostics['ljung_box_lag'] = lag
                        diagnostics['ljung_box_p_value'] = float(
                            acorr_ljungbox(residuals, lags=[lag], model_df=model_df, return_df=True)['lb_pvalue'].iloc[0]
                        )
                if len(train) < max(20, 5 * SEASONAL_PERIOD):
                    diagnostics['small_sample_warning'] = (
                        f'SARIMA training size {len(train)} is small for seasonal period {SEASONAL_PERIOD} '
                        f'with {diagnostics["parameter_count"]} estimated parameters'
                    )
            elif model_name == 'lstm':
                forecast, diagnostics['lstm_training_sequences'] = _forecast_lstm(train, horizon, seed)
            else:
                raise ValueError(f'Unknown model name: {model_name}')
            forecast = np.asarray(forecast, dtype=float).reshape(-1)
            finite = forecast[np.isfinite(forecast)]
            if finite.size:
                diagnostics['forecast_min'] = float(np.min(finite))
                diagnostics['forecast_max'] = float(np.max(finite))
        except Exception as exc:
            forecast = np.asarray([], dtype=float)
            diagnostics['failure_reason'] = f'{type(exc).__name__}: {exc}'
        diagnostics['warning'] = ' | '.join(dict.fromkeys(str(item.message) for item in caught))
    return forecast, lower, upper, diagnostics


def _validate_forecast(train, forecast, horizon, diagnostics, model_name):
    failures = []
    if diagnostics['failure_reason']:
        failures.append(diagnostics['failure_reason'])
    if len(forecast) != horizon:
        failures.append(f'Expected {horizon} predictions; model returned {len(forecast)}')
    if len(forecast) == horizon and not np.isfinite(forecast).all():
        failures.append('Forecast contains NaN or infinity')
    if model_name in {'arima', 'sarima'} and diagnostics['converged'] is not True:
        failures.append('Model optimizer did not converge')
    if len(forecast) == horizon and np.isfinite(forecast).all():
        if np.any(forecast <= 0):
            failures.append('Forecast contains non-positive prices')
        bound = max(float(np.max(np.abs(np.asarray(train, dtype=float)))) * FORECAST_BOUND_MULTIPLIER, 1.0)
        if np.any(np.abs(forecast) > bound):
            failures.append(f'Forecast exceeds validity bound of {bound:.6g} ({FORECAST_BOUND_MULTIPLIER}x max absolute training price)')
    return not failures, '; '.join(dict.fromkeys(failures))


def _fold_starts(observation_count, min_train_size, horizon, validation_windows):
    last_start = observation_count - horizon
    starts = list(range(min_train_size, last_start + 1, horizon))
    if validation_windows and len(starts) > validation_windows:
        starts = starts[-validation_windows:]
    return starts


def _format_index_value(value):
    if hasattr(value, 'date'):
        return value.date().isoformat()
    return str(value)


def _evaluate_series(series, crop, model_name, horizon, min_train_size, validation_windows, seed):
    prediction_rows = []
    fold_rows = []
    for fold_number, train_end in enumerate(_fold_starts(len(series), min_train_size, horizon, validation_windows), start=1):
        train = series.iloc[:train_end]
        test = series.iloc[train_end:train_end + horizon]
        forecast, lower, upper, diagnostics = _forecast_fold(train, model_name, len(test), seed)
        is_valid, failure_reason = _validate_forecast(train, forecast, len(test), diagnostics, model_name)
        if len(forecast) < len(test):
            forecast = np.pad(forecast, (0, len(test) - len(forecast)), constant_values=np.nan)
        else:
            forecast = forecast[:len(test)]
        if len(lower) < len(test):
            lower = np.pad(lower, (0, len(test) - len(lower)), constant_values=np.nan)
            upper = np.pad(upper, (0, len(test) - len(upper)), constant_values=np.nan)
        else:
            lower, upper = lower[:len(test)], upper[:len(test)]

        actual = np.asarray(test, dtype=float)
        metrics = _compute_metrics(actual, forecast) if is_valid else {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan}
        for horizon_step, (date, actual_value, predicted_value) in enumerate(zip(test.index, actual, forecast), start=1):
            finite_prediction = bool(np.isfinite(predicted_value))
            error = float(predicted_value - actual_value) if finite_prediction else np.nan
            prediction_rows.append({
                'crop': crop, 'model': model_name, 'fold': fold_number, 'horizon': horizon_step,
                'train_start': _format_index_value(train.index[0]), 'train_end': _format_index_value(train.index[-1]),
                'test_start': _format_index_value(test.index[0]), 'test_end': _format_index_value(test.index[-1]),
                'forecast_date': _format_index_value(date),
                'actual': float(actual_value), 'predicted': float(predicted_value) if finite_prediction else np.nan,
                'error': error, 'absolute_error': abs(error) if finite_prediction else np.nan,
                'absolute_percentage_error': abs(error / actual_value) * 100.0 if finite_prediction and actual_value != 0 else np.nan,
                'validity_status': 'VALID' if is_valid else 'FAILED', 'failure_reason': failure_reason,
                'price_unit': PRICE_UNIT, 'train_end_index': train_end - 1, 'test_start_index': train_end,
                'lower_95': float(lower[horizon_step - 1]) if np.isfinite(lower[horizon_step - 1]) else np.nan,
                'upper_95': float(upper[horizon_step - 1]) if np.isfinite(upper[horizon_step - 1]) else np.nan,
            })

        fold_rows.append({
            'crop': crop, 'model': model_name, 'fold': fold_number, **metrics,
            'status': 'VALID' if is_valid else 'FAILED',
            'train_observations': len(train), 'validation_observations': len(test),
            'lstm_training_sequences': diagnostics['lstm_training_sequences'],
            'converged': diagnostics['converged'], 'aic': diagnostics['aic'], 'bic': diagnostics['bic'],
            'parameter_count': diagnostics['parameter_count'],
            'residual_mean': diagnostics['residual_mean'], 'residual_std': diagnostics['residual_std'],
            'ljung_box_p_value': diagnostics['ljung_box_p_value'], 'ljung_box_lag': diagnostics['ljung_box_lag'],
            'residual_acf_lag1': diagnostics['residual_acf_lag1'],
            'forecast_min': diagnostics['forecast_min'], 'forecast_max': diagnostics['forecast_max'],
            'warning': diagnostics['warning'], 'failure_reason': failure_reason,
            'small_sample_warning': diagnostics['small_sample_warning'],
            'interval_generated': diagnostics['interval_generated'],
            'interval_failure_reason': diagnostics['interval_failure_reason'],
            'price_unit': PRICE_UNIT,
        })
    return prediction_rows, fold_rows


def _model_summary(fold_metrics):
    columns = ['crop', 'model', 'valid_folds', 'failed_folds', 'mean_MAE', 'mean_RMSE', 'mean_MAPE', 'mean_R2', 'std_MAE', 'std_RMSE', 'std_MAPE', 'std_R2', 'price_unit']
    rows = []
    for (crop, model), group in fold_metrics.groupby(['crop', 'model'], sort=True):
        valid = group.loc[group['status'] == 'VALID']
        row = {'crop': crop, 'model': model, 'valid_folds': len(valid), 'failed_folds': int((group['status'] == 'FAILED').sum()), 'price_unit': PRICE_UNIT}
        for metric in ('MAE', 'RMSE', 'MAPE', 'R2'):
            values = valid[metric].dropna().to_numpy(dtype=float)
            row[f'mean_{metric}'] = float(np.mean(values)) if len(values) else np.nan
            row[f'std_{metric}'] = float(np.std(values, ddof=0)) if len(values) else np.nan
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def _horizon_summary(predictions):
    columns = ['crop', 'model', 'horizon', 'MAE', 'RMSE', 'MAPE', 'number_of_predictions', 'price_unit']
    valid = predictions.loc[predictions['validity_status'] == 'VALID']
    rows = []
    for (crop, model, horizon), group in valid.groupby(['crop', 'model', 'horizon'], sort=True):
        metrics = _compute_metrics(group['actual'], group['predicted'])
        rows.append({
            'crop': crop, 'model': model, 'horizon': int(horizon), 'MAE': metrics['MAE'],
            'RMSE': metrics['RMSE'], 'MAPE': metrics['MAPE'],
            'number_of_predictions': len(group), 'price_unit': PRICE_UNIT,
        })
    return pd.DataFrame(rows, columns=columns)


def _interval_outputs(predictions):
    columns = [
        'crop', 'model', 'fold', 'horizon', 'actual', 'predicted', 'lower_95', 'upper_95',
        'interval_width', 'price_unit',
    ]
    intervals = predictions[[
        'crop', 'model', 'fold', 'horizon', 'actual', 'predicted', 'lower_95', 'upper_95',
        'price_unit', 'validity_status',
    ]].copy()
    bounds_available = np.isfinite(intervals['lower_95']) & np.isfinite(intervals['upper_95'])
    ordered = intervals['lower_95'] <= intervals['upper_95']
    intervals.loc[bounds_available & ~ordered, ['lower_95', 'upper_95']] = np.nan
    bounds_available &= ordered
    intervals['interval_width'] = np.where(
        bounds_available,
        intervals['upper_95'] - intervals['lower_95'],
        np.nan,
    )
    usable = intervals.loc[
        intervals['validity_status'].eq('VALID')
        & intervals['lower_95'].notna()
        & intervals['upper_95'].notna()
    ].copy()
    rows = []
    for (crop, model, horizon), group in usable.groupby(['crop', 'model', 'horizon'], sort=True):
        covered = group['actual'].between(group['lower_95'], group['upper_95'], inclusive='both')
        rows.append({
            'crop': crop,
            'model': model,
                'horizon': str(int(horizon)),
            'empirical_coverage_percentage': float(covered.mean() * 100.0),
            'mean_interval_width': float(group['interval_width'].mean()),
            'number_of_intervals': len(group),
            'confidence_level': INTERVAL_CONFIDENCE_LEVEL,
            'price_unit': PRICE_UNIT,
        })
    coverage = pd.DataFrame(rows)
    if not coverage.empty:
        overall_rows = []
        for (crop, model), group in usable.groupby(['crop', 'model'], sort=True):
            covered = group['actual'].between(group['lower_95'], group['upper_95'], inclusive='both')
            overall_rows.append({
                'crop': crop,
                'model': model,
                'horizon': 'all',
                'empirical_coverage_percentage': float(covered.mean() * 100.0),
                'mean_interval_width': float(group['interval_width'].mean()),
                'number_of_intervals': len(group),
                'confidence_level': INTERVAL_CONFIDENCE_LEVEL,
                'price_unit': PRICE_UNIT,
            })
        coverage = pd.concat([coverage, pd.DataFrame(overall_rows)], ignore_index=True)
    return intervals[columns], coverage


def _dm_test(error_a, error_b, horizon, min_origins=DM_MIN_PAIRED_ORIGINS):
    """Two-sided squared-error DM test with Bartlett HAC and HLN correction."""
    error_a = np.asarray(error_a, dtype=float).reshape(-1)
    error_b = np.asarray(error_b, dtype=float).reshape(-1)
    finite = np.isfinite(error_a) & np.isfinite(error_b)
    error_a, error_b = error_a[finite], error_b[finite]
    n = len(error_a)
    required = max(min_origins, int(horizon) + 2)
    result = {
        'horizon': int(horizon),
        'loss_function': 'squared_error',
        'DM_statistic': np.nan,
        'p_value': np.nan,
        'paired_origins': n,
        'interpretation': '',
    }
    if n < required:
        result['interpretation'] = f'Insufficient paired origins ({n}; requires at least {required}); no significance conclusion.'
        return result

    differential = np.square(error_a) - np.square(error_b)
    centered = differential - np.mean(differential)
    long_run_variance = float(np.dot(centered, centered) / n)
    for lag in range(1, min(int(horizon), n - 1)):
        autocovariance = float(np.dot(centered[lag:], centered[:-lag]) / n)
        bartlett_weight = 1.0 - lag / int(horizon)
        long_run_variance += 2.0 * bartlett_weight * autocovariance
    if not np.isfinite(long_run_variance) or long_run_variance <= 0:
        result['interpretation'] = 'Loss-differential variance is non-positive or non-finite; test not estimable.'
        return result

    raw_statistic = float(np.mean(differential) / np.sqrt(long_run_variance / n))
    hln_term = (n + 1.0 - 2.0 * horizon + horizon * (horizon - 1.0) / n) / n
    if hln_term <= 0:
        result['interpretation'] = 'Harvey-Leybourne-Newbold correction is not defined for this sample.'
        return result
    statistic = raw_statistic * np.sqrt(hln_term)
    p_value = float(2.0 * student_t.sf(abs(statistic), df=n - 1))
    if p_value < 0.05:
        direction = 'model_a has lower squared error' if np.mean(differential) < 0 else 'model_b has lower squared error'
        interpretation = f'Error difference statistically distinguishable at alpha=0.05; {direction}.'
    else:
        interpretation = 'Error difference not statistically distinguishable at alpha=0.05.'
    result.update({'DM_statistic': statistic, 'p_value': p_value, 'interpretation': interpretation})
    return result


def _dm_comparisons(predictions, selected):
    columns = ['crop', 'model_a', 'model_b', 'horizon', 'loss_function', 'DM_statistic', 'p_value', 'paired_origins', 'interpretation']
    rows = []
    valid = predictions.loc[predictions['validity_status'].eq('VALID')].copy()
    for crop, selected_model in selected.items():
        if selected_model is None:
            continue
        crop_data = valid.loc[valid['crop'].eq(crop)]
        for comparator in MODELS:
            if comparator == selected_model:
                continue
            for horizon in sorted(crop_data['horizon'].unique()):
                a = crop_data.loc[(crop_data['model'] == selected_model) & (crop_data['horizon'] == horizon), ['fold', 'actual', 'predicted']]
                b = crop_data.loc[(crop_data['model'] == comparator) & (crop_data['horizon'] == horizon), ['fold', 'actual', 'predicted']]
                paired = a.merge(b, on='fold', suffixes=('_a', '_b'))
                test = _dm_test(
                    paired['predicted_a'].to_numpy() - paired['actual_a'].to_numpy(),
                    paired['predicted_b'].to_numpy() - paired['actual_b'].to_numpy(),
                    int(horizon),
                )
                rows.append({
                    'crop': crop, 'model_a': selected_model, 'model_b': comparator,
                    **test,
                })
    return pd.DataFrame(rows, columns=columns)


def _final_forecast_table(summary, horizon_metrics, selected, interval_metrics, folds):
    columns = [
        'crop', 'model', 'valid_folds', 'failed_folds', 'mean_MAE', 'std_MAE',
        'mean_RMSE', 'std_RMSE', 'mean_MAPE', 'std_MAPE', 'mean_R2', 'std_R2',
        'h1_RMSE', 'h2_RMSE', 'h3_RMSE', 'h4_RMSE', 'price_unit',
    ]
    result = summary.copy()
    pivot = horizon_metrics.pivot_table(index=['crop', 'model'], columns='horizon', values='RMSE', aggfunc='first')
    for step in range(1, 5):
        result[f'h{step}_RMSE'] = [pivot.loc[(r.crop, r.model), step] if (r.crop, r.model) in pivot.index and step in pivot.columns else np.nan for r in result.itertuples()]
    coverage = interval_metrics.loc[interval_metrics['horizon'].eq('all')].set_index(['crop', 'model']) if not interval_metrics.empty else pd.DataFrame()
    result['interval_coverage_percentage'] = [coverage.loc[(r.crop, r.model), 'empirical_coverage_percentage'] if not coverage.empty and (r.crop, r.model) in coverage.index else np.nan for r in result.itertuples()]
    result['selected'] = [selected.get(r.crop) == r.model for r in result.itertuples()]
    baseline_rmse = result.loc[result['model'].eq('seasonal_naive')].set_index('crop')['mean_RMSE'].to_dict()
    result['beats_seasonal_naive_rmse'] = [bool(r.mean_RMSE < baseline_rmse.get(r.crop, np.inf)) if np.isfinite(r.mean_RMSE) else False for r in result.itertuples()]

    diagnostic_rows = []
    for (crop, model), group in folds.groupby(['crop', 'model'], sort=False):
        convergence_values = group['converged'].dropna().astype(bool).unique()
        if len(convergence_values) == 0:
            convergence = 'not applicable'
        elif len(convergence_values) == 1:
            convergence = 'all converged' if convergence_values[0] else 'not all converged'
        else:
            convergence = 'mixed'
        warnings_list = sorted(set(value for value in group['warning'].fillna('').astype(str) if value))
        small_warnings = sorted(set(value for value in group['small_sample_warning'].fillna('').astype(str) if value))
        diagnostic_rows.append((crop, model, convergence, ' | '.join(warnings_list + small_warnings)))
    diagnostic_df = pd.DataFrame(diagnostic_rows, columns=['crop', 'model', 'convergence_status', 'warning_messages'])
    result = result.merge(diagnostic_df, on=['crop', 'model'], how='left')
    result.attrs['selection_diagnostics'] = result[[
        'crop', 'model', 'selected', 'beats_seasonal_naive_rmse',
        'interval_coverage_percentage', 'convergence_status', 'warning_messages',
    ]].copy()
    return result.reindex(columns=columns)


def _write_actual_vs_forecast_figures(root, data_path, predictions, selected):
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    for crop in CROPS:
        series, _, _ = _load_crop_series(data_path, crop)
        crop_predictions = predictions.loc[
            (predictions['crop'] == crop) & predictions['validity_status'].eq('VALID')
        ]
        fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
        ax.plot(series.index, series.to_numpy(), color='#34495e', linewidth=1.8, marker='o', markersize=3, label='Historical actual')
        for model in MODELS:
            rows = crop_predictions.loc[crop_predictions['model'] == model].sort_values(['test_start', 'horizon'])
            if rows.empty:
                continue
            label = f'{model} validation forecast'
            forecast_dates = pd.to_datetime(rows['forecast_date'])
            ax.plot(forecast_dates, rows['predicted'], marker='.', linewidth=1.2, label=label)
            has_interval = rows['lower_95'].notna() & rows['upper_95'].notna()
            if has_interval.any():
                dates = pd.to_datetime(rows.loc[has_interval, 'forecast_date'])
                ax.fill_between(dates, rows.loc[has_interval, 'lower_95'], rows.loc[has_interval, 'upper_95'], alpha=0.15, label=f'{model} native 95% prediction interval')
        selected_model = selected.get(crop)
        selected_rows = crop_predictions.loc[crop_predictions['model'] == selected_model]
        if not selected_rows.empty:
            actual_by_date = selected_rows.drop_duplicates('forecast_date').sort_values('forecast_date')
            ax.scatter(pd.to_datetime(actual_by_date['forecast_date']), actual_by_date['actual'], color='#c0392b', marker='x', s=34, label='Validation actual')
        ax.set_title(f'{crop}: historical and rolling-origin validation forecasts')
        ax.set_xlabel('Quarter')
        ax.set_ylabel(f'Price ({PRICE_UNIT})')
        ax.grid(True, alpha=0.25)
        ax.legend(frameon=False, fontsize=8, ncol=2)
        fig.savefig(root / f'forecast_validation_{crop.lower()}.png', dpi=300)
        plt.close(fig)


def _render_final_report(base_report, interval_metrics, dm_results, final_table, folds):
    interval_text = interval_metrics.to_string(index=False) if not interval_metrics.empty else 'No valid native forecast intervals were generated.'
    dm_text = dm_results.to_string(index=False) if not dm_results.empty else 'No comparisons were estimable.'
    final_text = final_table.to_string(index=False)
    selection_diagnostics = final_table.attrs.get('selection_diagnostics', pd.DataFrame())
    if not selection_diagnostics.empty:
        diagnostic_lines = []
        for crop, selected_model in _select_models(_model_summary(folds)).items():
            selected_row = selection_diagnostics.loc[
                selection_diagnostics['crop'].eq(crop) & selection_diagnostics['model'].eq(selected_model)
            ]
            if selected_row.empty:
                diagnostic_lines.append(f'- {crop}: no eligible selected model.')
                continue
            selected_row = selected_row.iloc[0]
            selected_dm = dm_results.loc[
                dm_results['crop'].eq(crop)
                & dm_results['model_a'].eq(selected_model)
                & dm_results['model_b'].eq('seasonal_naive')
            ]
            dm_interpretation = '; '.join(selected_dm['interpretation'].astype(str).unique()) if not selected_dm.empty else 'No seasonal-naive comparison available.'
            coverage = selected_row['interval_coverage_percentage']
            coverage_text = f'{coverage:.2f}%' if pd.notna(coverage) else 'unavailable'
            diagnostic_lines.append(
                f"- {crop}: {selected_model}; lower mean RMSE than seasonal naive = "
                f"{bool(selected_row['beats_seasonal_naive_rmse'])}; interval coverage = {coverage_text}; "
                f"convergence = {selected_row['convergence_status']}; warnings = "
                f"{selected_row['warning_messages'] if pd.notna(selected_row['warning_messages']) else 'none captured'}; "
                f"DM vs seasonal naive: {dm_interpretation}"
            )
        selection_assessment = '\n'.join(diagnostic_lines)
    else:
        selection_assessment = 'Selection diagnostics unavailable.'
    diagnostic_columns = [
        'crop', 'model', 'fold', 'status', 'train_observations', 'parameter_count',
        'converged', 'aic', 'bic', 'residual_mean', 'residual_std',
        'ljung_box_lag', 'ljung_box_p_value', 'residual_acf_lag1',
        'interval_generated', 'small_sample_warning', 'warning',
    ]
    diagnostic_text = folds[diagnostic_columns].to_string(index=False)
    dm_notes = (
        'The DM test uses paired rolling-origin squared forecast errors, Bartlett HAC variance, '
        'and the Harvey-Leybourne-Newbold finite-sample correction. A test is reported only when '
        f'the number of paired origins is at least max({DM_MIN_PAIRED_ORIGINS}, horizon + 2). '
        'Current comparisons have only three paired origins per horizon, so they are explicitly '
        'marked insufficient and no statistical superiority is claimed.'
    )
    added = f'''# Phase 2 Final Forecast Validation

{base_report}

## Prediction Intervals and Coverage
- ARIMA and SARIMA intervals use each fitted statsmodels result's native `get_forecast().conf_int(alpha=0.05)` output; confidence level is 95%.
- Bounds are not clipped or modified. Interval coverage and width use only valid folds with finite ordered native bounds.
- Seasonal naive and LSTM intervals are unavailable; no heuristic or fabricated interval is supplied.
- Empirical coverage is the percentage of actual validation prices inside the corresponding bounds. Width and coverage are in {PRICE_UNIT}; coverage is also reported separately by horizon.

```text
{interval_text}
```

## ARIMA/SARIMA Diagnostics
Residual mean and sample standard deviation are calculated from fitted residuals. Lag-1 residual autocorrelation is reported. Ljung-Box is reported only when the residual sample size exceeds the chosen lag plus estimated model degrees of freedom; it is diagnostic, not a model acceptance rule. Seasonal small-sample flags remain explicit.

```text
{diagnostic_text}
```

## Diebold-Mariano Comparisons
{dm_notes}

```text
{dm_text}
```

`model_a` is the RMSE-selected model and `model_b` is each comparator, including seasonal naive, ARIMA, SARIMA, and LSTM when distinct. `Insufficient paired origins` means no alpha=0.05 inference is made.

## Paper-Reporting Forecast Table
The table contains the requested paper-reporting metrics. Selection uses only mean validation RMSE among valid folds.

```text
{final_text}
```

### Selected-model assessment
`beats seasonal naive RMSE` is descriptive, not a significance claim. Interval coverage is unavailable for models without native intervals.

{selection_assessment}

## Figures
Generated `forecast_validation_rice.png`, `forecast_validation_onion.png`, and `forecast_validation_tomato.png`. Each chart uses INR per quintal throughout and shows historical actuals, rolling-origin validation predictions, validation actuals, and native 95% ARIMA/SARIMA bounds where available.
'''
    return added


def _select_models(summary):
    selected = {}
    for crop in CROPS:
        candidates = summary.loc[(summary['crop'] == crop) & (summary['valid_folds'] > 0) & summary['mean_RMSE'].notna()]
        selected[crop] = None if candidates.empty else str(candidates.sort_values(['mean_RMSE', 'model']).iloc[0]['model'])
    return selected


def _render_diagnostic_report(data_path, metadata, predictions, fold_metrics, horizon_metrics, summary, selected, config, full_df):
    data_table = pd.DataFrame(metadata).to_string(index=False)
    fold_columns = ['crop', 'model', 'fold', 'status', 'train_observations', 'validation_observations', 'MAE', 'RMSE', 'MAPE', 'R2', 'lstm_training_sequences']
    fold_table = fold_metrics[fold_columns].to_string(index=False)
    horizon_table = horizon_metrics.to_string(index=False)
    summary_table = summary.to_string(index=False)
    sarima_columns = ['crop', 'fold', 'status', 'converged', 'aic', 'bic', 'forecast_min', 'forecast_max', 'warning', 'failure_reason']
    sarima_table = fold_metrics.loc[fold_metrics['model'] == 'sarima', sarima_columns].to_string(index=False)
    failures = fold_metrics.loc[fold_metrics['status'] == 'FAILED']
    failed_table = failures[['crop', 'model', 'fold', 'failure_reason']].to_string(index=False) if not failures.empty else 'None.'

    scale_lines = []
    if 'Final_Price' in full_df.columns and PRICE_COLUMN in full_df.columns:
        for crop, group in full_df.groupby('Crop'):
            pair = group[[PRICE_COLUMN, 'Final_Price']].apply(pd.to_numeric, errors='coerce').dropna()
            if not pair.empty:
                ratio = float((pair['Final_Price'] / pair[PRICE_COLUMN]).median())
                scale_lines.append(f'- {crop}: median Final_Price / {PRICE_COLUMN} ratio = {ratio:.6g}; Final_Price excluded from evaluation.')
    scale_description = '\n'.join(scale_lines) if scale_lines else '- No comparable alternate price field was available.'

    fold_definitions = []
    for (crop, model), group in fold_metrics.groupby(['crop', 'model'], sort=True):
        for _, row in group.iterrows():
            fold_predictions = predictions.loc[(predictions['crop'] == crop) & (predictions['model'] == model) & (predictions['fold'] == row['fold'])]
            if fold_predictions.empty:
                continue
            first = fold_predictions.iloc[0]
            fold_definitions.append(
                f"- {crop} / {model} / fold {int(row['fold'])}: train {first['train_start']} to {first['train_end']} ({int(row['train_observations'])} observations); "
                f"validation {first['test_start']} to {first['test_end']} ({int(row['validation_observations'])} observations)."
            )

    lstm_counts = fold_metrics.loc[fold_metrics['model'] == 'lstm', ['crop', 'fold', 'train_observations', 'lstm_training_sequences']].to_string(index=False)
    selected_text = '\n'.join(f'- {crop}: {model if model else "No model has valid folds"}' for crop, model in selected.items())
    return f'''# Forecasting Diagnostic Report

## Dataset and Units
- Input: `{Path(data_path).name}` ({len(full_df)} raw rows).
- Evaluated source field: `{PRICE_COLUMN}`, whose column name explicitly identifies INR per quintal.
- No price conversion was applied; every metric in this report and the CSV outputs is in {PRICE_UNIT}.
- `{PRICE_COLUMN}` is missing for later rows; those rows were excluded instead of substituting the ambiguously scaled `Final_Price` field.
- `Final_Price` scale evidence from overlapping rows:
{scale_description}
- Duplicate crop-quarter source rows, if present, are aggregated by arithmetic mean. Missing quarters are left missing, never filled or interpolated.

| Crop | Raw crop rows | Missing source-price rows | Source-price observations | Duplicate rows aggregated | Excluded across quarter gaps | Evaluated observations | Start quarter | End quarter | Missing quarters | Minimum price | Maximum price |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|
{data_table}

Each crop uses its longest contiguous sequence of actual quarterly observations. Observations outside that sequence are excluded where a calendar-quarter gap would otherwise distort seasonal period 4. No prices are imputed or interpolated, and the excluded gaps are listed above.

## Frequency and Fold Protocol
- Nominal frequency: quarterly.
- Forecast horizon: {config['horizon']} consecutive calendar quarters per fold.
- Minimum training size: {config['min_train_size']} observed records.
- Validation folds: the latest {config['validation_windows']} non-overlapping rolling-origin windows available after the minimum training window.
- Training is expanding from the first available observation and ends strictly before each validation window.
- Number of fold records: {len(fold_metrics)}; valid: {int((fold_metrics['status'] == 'VALID').sum())}; failed: {int((fold_metrics['status'] == 'FAILED').sum())}.

### Fold definitions and sample sizes
{chr(10).join(fold_definitions) if fold_definitions else 'No eligible folds were available.'}

## Model Configurations
- Seasonal naive baseline: seasonal period = {SEASONAL_PERIOD} quarters; repeat the most recent four observed values.
- ARIMA: order (1, 1, 1), seasonal order (0, 0, 0, 0), stationarity and invertibility enforced.
- SARIMA: order (0, 1, 1), seasonal order (0, 1, 1, 4), stationarity and invertibility enforced; L-BFGS optimizer, maximum 500 iterations.
- LSTM: input shape `(window, 1)`; Input layer, LSTM with 32 units and ReLU, Dense(1) output; no dropout; Adam optimizer, learning rate 0.001; MSE loss; 20 epochs; batch size 8; MinMaxScaler fitted on training data only; window = min(4, training observations - 1); random seed = {config['seed']}; shuffle disabled.

### LSTM effective training sequences per fold
{lstm_counts}

The LSTM sample is small: each fold has only the listed training observations minus its lookback window as supervised sequences. This small effective sample makes its scores sensitive to initialization and should not support a claim of general superiority.

## SARIMA Diagnostics
For every SARIMA fold, `converged`, AIC, BIC, finite forecast minimum/maximum, captured warning text, and failure reason are recorded below and in `forecast_fold_metrics.csv`.

```text
{sarima_table}
```

## Failed Folds
```text
{failed_table}
```

Invalid predictions remain explicitly marked `FAILED` in the prediction-level output when a numeric forecast was produced. Failed folds have NaN fold metrics and are excluded from horizon/model summaries and model selection. No fallback or fabricated prediction is substituted.

## Metric Formulas
For the complete forecast vector in each fold, with error defined as predicted minus actual:
- MAE = mean(abs(actual - predicted))
- RMSE = sqrt(mean((actual - predicted)^2))
- MAPE = mean(abs((actual - predicted) / actual)) * 100
- R2 = 1 - SSE/SST, with SSE = sum((actual - predicted)^2), SST = sum((actual - mean(actual))^2)
- Metrics are expressed in {PRICE_UNIT}, except MAPE (percent) and R2 (unitless). MAPE is undefined if any actual value is zero; R2 is undefined when the validation vector has zero variance.

## Fold-Level Metrics
Each MAE, RMSE, MAPE, and R2 value below is computed once across all forecast steps in that fold, not attached as a per-step fold score.

```text
{fold_table}
```

## Horizon-Level Metrics
Metrics below pool valid predictions across folds for each crop/model/horizon.

```text
{horizon_table}
```

## Model-Level Summary
Means and population standard deviations are across valid fold metrics. Failed folds are separately counted and excluded from these summaries.

```text
{summary_table}
```

## Model Selection
For each crop, select the model with the lowest mean validation RMSE across valid folds. No final test set is used. A model with no valid folds is not selectable.

{selected_text}

## Limitations
- The explicitly labeled source price series is incomplete after the historical block; the differently scaled `Final_Price` field is not substituted.
- To keep seasonal period 4 calendar-correct, observations outside the longest contiguous quarterly segment are excluded rather than bridging missing quarters.
- Small fold counts limit precision of mean and standard-deviation estimates.
- LSTM has few effective sequences per fold and is reported as a comparison model, not presumed superior.
- SARIMA and ARIMA fits may fail convergence or numerical validity checks; such folds remain visible but contribute no metrics or selection scores.
'''


def run_forecasting_validation(data_path, crops=None, random_seed=42, horizon=4, min_train_size=12, validation_windows=3, output_dir='.'):
    """Run validation and write prediction-, fold-, horizon-, and model-level artifacts."""
    crops = tuple(crops or CROPS)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    full_df = pd.read_csv(data_path)
    all_predictions = []
    all_folds = []
    metadata = []

    for crop in crops:
        series, crop_metadata, _ = _load_crop_series(data_path, crop)
        metadata.append(crop_metadata)
        for model_name in MODELS:
            predictions, folds = _evaluate_series(series, crop, model_name, horizon, min_train_size, validation_windows, random_seed)
            all_predictions.extend(predictions)
            all_folds.extend(folds)

    prediction_columns = [
        'crop', 'model', 'fold', 'horizon', 'train_start', 'train_end', 'test_start', 'test_end',
        'forecast_date', 'actual', 'predicted', 'error', 'absolute_error', 'absolute_percentage_error',
        'validity_status', 'failure_reason', 'price_unit',
        'train_end_index', 'test_start_index', 'lower_95', 'upper_95',
    ]
    fold_columns = [
        'crop', 'model', 'fold', 'MAE', 'RMSE', 'MAPE', 'R2', 'status', 'train_observations',
        'validation_observations', 'lstm_training_sequences', 'converged', 'aic', 'bic',
        'parameter_count', 'residual_mean', 'residual_std', 'ljung_box_p_value', 'ljung_box_lag',
        'residual_acf_lag1', 'forecast_min', 'forecast_max', 'warning', 'failure_reason',
        'small_sample_warning', 'interval_generated', 'interval_failure_reason', 'price_unit',
    ]
    predictions_df = pd.DataFrame(all_predictions, columns=prediction_columns)
    folds_df = pd.DataFrame(all_folds, columns=fold_columns)
    summary_df = _model_summary(folds_df)
    horizon_df = _horizon_summary(predictions_df)
    interval_df, interval_metrics_df = _interval_outputs(predictions_df)
    selected = _select_models(summary_df)
    dm_df = _dm_comparisons(predictions_df, selected)
    final_table_df = _final_forecast_table(summary_df, horizon_df, selected, interval_metrics_df, folds_df)
    config = {
        'source_price_column': PRICE_COLUMN, 'price_unit': PRICE_UNIT, 'conversions': [],
        'models': list(MODELS), 'horizon': horizon, 'min_train_size': min_train_size,
        'validation_windows': validation_windows, 'seed': random_seed, 'seasonal_period': SEASONAL_PERIOD,
        'forecast_validity_bound_multiplier': FORECAST_BOUND_MULTIPLIER,
        'prediction_intervals': {'method': 'native statsmodels get_forecast().conf_int()', 'confidence_level': INTERVAL_CONFIDENCE_LEVEL, 'models': ['arima', 'sarima'], 'other_models': 'unavailable'},
        'dm_test': {'loss_function': 'squared_error', 'variance_estimator': 'Bartlett HAC', 'small_sample_correction': 'Harvey-Leybourne-Newbold', 'minimum_origins': f'max({DM_MIN_PAIRED_ORIGINS}, horizon + 2)'},
        'sarima': {'order': [0, 1, 1], 'seasonal_order': [0, 1, 1, SEASONAL_PERIOD], 'enforce_stationarity': True, 'enforce_invertibility': True, 'optimizer': 'lbfgs', 'maxiter': 500},
        'lstm': {'input': '(window, 1)', 'layers': ['Input', 'LSTM(32, activation=relu)', 'Dense(1)'], 'dropout': 0, 'optimizer': 'Adam', 'learning_rate': 0.001, 'loss': 'mse', 'epochs': 20, 'batch_size': 8, 'scaler': 'MinMaxScaler fitted per training fold', 'window': 'min(4, train_size - 1)', 'shuffle': False},
        'selected_models': selected,
    }

    predictions_df.to_csv(root / 'forecast_predictions.csv', index=False)
    folds_df.to_csv(root / 'forecast_fold_metrics.csv', index=False)
    horizon_df.to_csv(root / 'forecast_horizon_metrics.csv', index=False)
    summary_df.to_csv(root / 'forecast_model_summary.csv', index=False)
    interval_df.to_csv(root / 'forecast_intervals.csv', index=False)
    interval_metrics_df.to_csv(root / 'forecast_interval_metrics.csv', index=False)
    dm_df.to_csv(root / 'forecast_dm_tests.csv', index=False)
    final_table_df.to_csv(root / 'forecast_final_table.csv', index=False)
    with (root / 'experiment_config.json').open('w', encoding='utf-8') as output:
        json.dump(config, output, indent=2, allow_nan=False)

    diagnostic_report = _render_diagnostic_report(data_path, metadata, predictions_df, folds_df, horizon_df, summary_df, selected, config, full_df)
    (root / 'FORECASTING_DIAGNOSTIC_REPORT.md').write_text(diagnostic_report, encoding='utf-8')
    final_report = _render_final_report(diagnostic_report, interval_metrics_df, dm_df, final_table_df, folds_df)
    (root / 'forecast_final_validation_report.md').write_text(final_report, encoding='utf-8')
    (root / 'FORECASTING_VALIDATION_REPORT.md').write_text(final_report, encoding='utf-8')
    predictions_df.to_csv(root / 'forecast_validation_results.csv', index=False)
    summary_df.to_csv(root / 'model_comparison.csv', index=False)
    _write_actual_vs_forecast_figures(root, data_path, predictions_df, selected)

    return {
        'prediction_rows': len(predictions_df), 'folds': folds_df, 'horizon_metrics': horizon_df,
        'model_summary': summary_df, 'intervals': interval_df, 'interval_metrics': interval_metrics_df,
        'dm_tests': dm_df, 'final_table': final_table_df, 'selected_models': selected,
        'failed_folds': folds_df.loc[folds_df['status'] == 'FAILED'],
    }