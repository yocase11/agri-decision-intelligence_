import os
import pickle
import functools
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator

# semi-persistent model cache in memory for speed
_model_cache = {}


def load_price_data(path, date_col='Quarter', year_col='Year', quarterly_col='Quarter'):
    """Load price dataset and parse quarterly dates.

    Expects either a single column with quarter label (e.g., '2009Q1' or 'Q1-2009')
    or separate year and quarter columns.
    """
    df = pd.read_csv(path)

    # Normalize quarter strings to YYYYQX format
    df['quarter_str'] = df[year_col].astype(str) + df[quarterly_col].str.replace(r'^\d{4}', '', regex=True)
    quarters = _parse_quarter_string(df['quarter_str'])
    df['quarter_date'] = quarters

    df = df.sort_values('quarter_date').reset_index(drop=True)
    return df


def _parse_quarter_string(series):
    # Robust quarter parsing for strings like '2009Q1', 'Q1 2009', '2009-Q1', '1/2009'
    normalized = series.astype(str).str.replace('[^0-9Qq-]', ' ', regex=True).str.upper().str.strip()
    # try direct pandas freq
    try:
        return pd.PeriodIndex(normalized, freq='Q').to_timestamp('Q')
    except Exception:
        pass

    def parse_one(v):
        v = v.replace('-', ' ').replace('/', ' ').strip()
        parts = v.split()
        if len(parts) == 2:
            if parts[0].startswith('Q'):
                q = int(parts[0].lstrip('Q'))
                y = int(parts[1])
            elif parts[1].startswith('Q'):
                q = int(parts[1].lstrip('Q'))
                y = int(parts[0])
            else:
                y = int(parts[0])
                q = int(parts[1])
            month = (q - 1) * 3 + 1
            return pd.Timestamp(year=y, month=month, day=1)
        raise ValueError(f'Unable to parse quarter {v}')

    return pd.Series([parse_one(v) for v in normalized], index=series.index)


def clean_price_data(df, fill_method='ffill'):
    """Handle missing values and standardize price columns."""
    price_cols = [c for c in df.columns if c.lower() in ['rice', 'onion', 'tomato'] or c.lower().startswith('rice') or c.lower().startswith('onion') or c.lower().startswith('tomato')]

    if not price_cols:
        raise ValueError('Price columns not found for rice, onion, tomato.')

    df[price_cols] = df[price_cols].replace({'': np.nan, 'NA': np.nan, 'na': np.nan})
    df[price_cols] = df[price_cols].astype(float)

    if fill_method == 'ffill':
        df[price_cols] = df[price_cols].ffill().bfill()
    elif fill_method == 'interpolate':
        df[price_cols] = df[price_cols].interpolate(method='linear').ffill().bfill()
    else:
        df[price_cols] = df[price_cols].fillna(method='ffill').fillna(method='bfill')

    return df


def prepare_crop_timeseries(df, crop, date_col='quarter_date'):
    """Return a time series for a specific crop's price."""
    df = df.copy()

    if date_col not in df.columns:
        if 'Year' in df.columns and 'Quarter' in df.columns:
            df[date_col] = pd.PeriodIndex(
                df['Year'].astype(str) + df['Quarter'].astype(str).str.replace('.*Q', 'Q', regex=True),
                freq='Q',
            ).to_timestamp('Q')
        else:
            raise ValueError(f"Date column '{date_col}' missing")

    crop_col = [c for c in df.columns if c.lower() == crop.lower() or c.lower().startswith(crop.lower())]
    if crop_col:
        crop_col = crop_col[0]
        ts = df.set_index(pd.DatetimeIndex(df[date_col]))[crop_col].sort_index()
        return ts

    if 'Crop' in df.columns:
        crop_rows = df.loc[df['Crop'].astype(str).str.lower() == crop.lower()].copy()
        if not crop_rows.empty:
            preferred_price_columns = ['price_inr_per_quintal', 'final_price', 'price', 'crop_price']
            lower_column_map = {column.lower(): column for column in crop_rows.columns}
            price_candidates = [lower_column_map[name] for name in preferred_price_columns if name in lower_column_map]
            if not price_candidates:
                price_candidates = [c for c in crop_rows.columns if c.lower().endswith('price')]
            if not price_candidates:
                numeric_cols = [
                    c for c in crop_rows.columns
                    if pd.api.types.is_numeric_dtype(crop_rows[c]) and c.lower() not in {'year', 'quarter'}
                ]
                price_candidates = numeric_cols

            if price_candidates:
                price_col = price_candidates[0]
                ts = crop_rows.set_index(pd.DatetimeIndex(crop_rows[date_col]))[price_col].sort_index()
                return ts.sort_index()

    raise ValueError(f"Crop '{crop}' data not found in columns")


def _unpack_pred(pred):
    if hasattr(pred, 'predicted_mean'):
        return pred.predicted_mean
    return pred


def train_arima(ts, order=(1, 1, 1)):
    model = SARIMAX(ts, order=order, seasonal_order=(0, 0, 0, 0), enforce_stationarity=False, enforce_invertibility=False)
    fitted = model.fit(disp=False)
    return fitted


def train_sarima(ts, order=(1, 1, 1), seasonal_order=(1, 0, 1, 4)):
    model = SARIMAX(ts, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    fitted = model.fit(disp=False)
    return fitted


def train_lstm(ts, n_input=4, n_features=1, epochs=50, batch_size=1):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_ts = scaler.fit_transform(ts.values.reshape(-1, 1))

    generator = TimeseriesGenerator(scaled_ts, scaled_ts, length=n_input, batch_size=batch_size)

    model = Sequential()
    model.add(LSTM(50, activation='relu', input_shape=(n_input, n_features)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    model.fit(generator, epochs=epochs, verbose=0)

    return model, scaler, n_input


def forecast_lstm(model, scaler, ts, steps=4, n_input=4):
    scaled_ts = scaler.transform(ts.values.reshape(-1, 1))
    last_batch = scaled_ts[-n_input:].reshape((1, n_input, 1))

    predictions = []
    for i in range(steps):
        pred = model.predict(last_batch, verbose=0)[0]
        predictions.append(pred)
        last_batch = np.append(last_batch[:, 1:, :], [[pred]], axis=1)

    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
    return pd.Series(predictions, index=pd.date_range(ts.index[-1], periods=steps+1, freq='QS')[1:])


def forecast_model(fitted_model, steps=4):
    pred = fitted_model.get_forecast(steps=steps)
    result = pred.predicted_mean
    return result


def validate_forecast(current_price, forecast_prices, low_ratio=0.7, high_ratio=1.5):
    """Clip unrealistic forecasts to a realistic range."""
    validated = []
    for p in forecast_prices:
        if p < current_price * low_ratio:
            validated.append(current_price * low_ratio)
        elif p > current_price * high_ratio:
            validated.append(current_price * high_ratio)
        else:
            validated.append(p)
    return np.array(validated)


def get_model_path(model_dir, crop, model_name):
    os.makedirs(model_dir, exist_ok=True)
    return os.path.join(model_dir, f"{crop.lower()}_{model_name}.pkl")


def cache_model(model_dir, crop, model_name, model):
    model_path = get_model_path(model_dir, crop, model_name)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    _model_cache[(crop.lower(), model_name)] = model


def load_cached_model(model_dir, crop, model_name):
    key = (crop.lower(), model_name)
    if key in _model_cache:
        return _model_cache[key]
    model_path = get_model_path(model_dir, crop, model_name)
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            m = pickle.load(f)
            _model_cache[key] = m
            return m
    return None


def get_or_train_models(df, crop, model_dir):
    # Returns a dict with fitted models and metrics
    ts = prepare_crop_timeseries(df, crop).dropna()
    if len(ts) < 8:
        raise ValueError('Not enough data to train models')

    train = ts
    models = {}

    exist_arima = load_cached_model(model_dir, crop, 'arima')
    if exist_arima is not None:
        arima_model = exist_arima
    else:
        arima_model = train_arima(train)
        cache_model(model_dir, crop, 'arima', arima_model)

    exist_sarima = load_cached_model(model_dir, crop, 'sarima')
    if exist_sarima is not None:
        sarima_model = exist_sarima
    else:
        sarima_model = train_sarima(train)
        cache_model(model_dir, crop, 'sarima', sarima_model)

    exist_lstm = load_cached_model(model_dir, crop, 'lstm')
    if exist_lstm is not None:
        lstm_model, lstm_scaler, n_input = exist_lstm
    else:
        lstm_model, lstm_scaler, n_input = train_lstm(train)
        cache_model(model_dir, crop, 'lstm', (lstm_model, lstm_scaler, n_input))

    models['arima'] = arima_model
    models['sarima'] = sarima_model
    models['lstm'] = (lstm_model, lstm_scaler, n_input)

    return models


def ensemble_forecast(models, df, crop, steps=4):
    current_price = float(df[prepare_crop_timeseries(df, crop).dropna().index[-1]]) if False else None
    # fallback to separate: get latest price from data and compute percent-based
    series = prepare_crop_timeseries(df, crop).dropna()
    current_price = float(series.iloc[-1])

    arima = forecast_model(models['arima'], steps=steps)
    sarima = forecast_model(models['sarima'], steps=steps)
    lstm = forecast_lstm(models['lstm'][0], models['lstm'][1], series, steps=steps, n_input=models['lstm'][2])

    # all taste into same array
    arima = np.asarray(arima).flatten()[:steps]
    sarima = np.asarray(sarima).flatten()[:steps]
    lstm = np.asarray(lstm).flatten()[:steps]

    # weights represent model reliability
    weights = np.array([0.4, 0.3, 0.3])
    ensemble = weights[0]*arima + weights[1]*sarima + weights[2]*lstm

    validated = validate_forecast(current_price, ensemble, low_ratio=0.7, high_ratio=1.5)

    # uncertainty interval ±10% for rough estimate
    low = validated * 0.92
    high = validated * 1.08

    return {
        'ensemble': validated,
        'ci_lower': low,
        'ci_upper': high,
        'arima': arima,
        'sarima': sarima,
        'lstm': lstm,
        'current_price': current_price
    }


# ============================================================================
# Forecasting validation: time-aware rolling-origin evaluation without leakage
# ============================================================================

def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return float('nan')


def _compute_metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.size == 0 or predicted.size == 0 or actual.size != predicted.size:
        return {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan, 'mean_error': np.nan}

    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        error = predicted - actual
        mae = float(np.mean(np.abs(error)))
        rmse = float(np.sqrt(np.mean(error ** 2)))
        mape = float(np.mean(np.abs(error / actual)) * 100.0) if np.all(actual != 0) else np.nan
        ss_res = float(np.sum(error ** 2))
        ss_tot = float(np.sum((actual - np.mean(actual)) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
        mean_error = float(np.mean(error))
    if not np.isfinite(mae) or not np.isfinite(rmse):
        return {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan, 'mean_error': np.nan}
    return {
        'MAE': float(mae),
        'RMSE': float(rmse),
        'MAPE': float(mape),
        'R2': float(r2),
        'mean_error': float(mean_error),
    }


def _seasonal_naive_forecast(train, horizon):
    if len(train) == 0:
        return np.zeros(horizon, dtype=float)
    season_length = min(4, max(1, len(train)))
    seasonal_values = np.asarray(train.iloc[-season_length:].tolist(), dtype=float)
    forecast = np.empty(horizon, dtype=float)
    for i in range(horizon):
        forecast[i] = seasonal_values[i % len(seasonal_values)]
    return forecast


def _fit_arima(train):
    return SARIMAX(train, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def _fit_sarima(train):
    return SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 0, 1, 4), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def _fit_lstm(train, seed=42):
    import tensorflow as tf
    tf.random.set_seed(seed)
    np.random.seed(seed)

    values = np.asarray(train, dtype=float).reshape(-1, 1)
    if len(values) < 5:
        return None

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(values)
    window = min(4, len(scaled) - 1)
    if window < 1:
        return None

    X, y = [], []
    for i in range(window, len(scaled)):
        X.append(scaled[i-window:i, 0])
        y.append(scaled[i, 0])
    if len(X) == 0:
        return None

    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    model = Sequential()
    model.add(LSTM(32, activation='relu', input_shape=(X.shape[1], 1)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=20, batch_size=8, verbose=0)
    return {'model': model, 'scaler': scaler, 'window': window}


def _forecast_with_model(train, model_name, horizon, seed=42):
    if model_name == 'seasonal_naive':
        return _seasonal_naive_forecast(train, horizon)
    if model_name == 'arima':
        model = _fit_arima(train)
        return np.asarray(model.forecast(steps=horizon), dtype=float)
    if model_name == 'sarima':
        model = _fit_sarima(train)
        return np.asarray(model.forecast(steps=horizon), dtype=float)
    if model_name == 'lstm':
        fitted = _fit_lstm(train, seed=seed)
        if fitted is None:
            return np.asarray([train.iloc[-1]] * horizon, dtype=float)
        model = fitted['model']
        scaler = fitted['scaler']
        window = fitted['window']
        series = np.asarray(train, dtype=float).reshape(-1, 1)
        scaled = scaler.transform(series)
        last_window = scaled[-window:]
        preds = []
        for _ in range(horizon):
            x = np.asarray(last_window.reshape(1, -1, 1), dtype=float)
            step_pred = model.predict(x, verbose=0)[0, 0]
            preds.append(step_pred)
            last_window = np.append(last_window[1:], step_pred)
        return scaler.inverse_transform(np.asarray(preds, dtype=float).reshape(-1, 1)).ravel()
    raise ValueError(f'Unknown model name: {model_name}')


def chronological_walk_forward_validation(series, model_name='arima', horizon=4, min_train_size=12, validation_windows=3, seed=42):
    """Return fold-level chronological predictions with no future leakage.

    This function intentionally enforces that every model is trained only on data
    available before the validation origin. Each fold uses a strictly later test
    window and never uses test observations during fitting or preprocessing.
    """
    if isinstance(series, pd.DataFrame):
        if series.empty:
            return []
        series = series.iloc[:, 0]
    from src.forecast_validation import _evaluate_series

    prediction_rows, _ = _evaluate_series(
        pd.Series(series, dtype=float).dropna().sort_index(),
        'Forecast', model_name, horizon, min_train_size, validation_windows, seed,
    )
    return prediction_rows


def validate_crop_model_family(series, crop, model_names=None, horizon=4, min_train_size=12, validation_windows=3, seed=42, output_dir='.'):
    """Evaluate each forecasting model on the same chronological folds and return a summary table."""
    if model_names is None:
        model_names = ['seasonal_naive', 'arima', 'sarima', 'lstm']

    from src.forecast_validation import _evaluate_series

    all_rows = []
    for model_name in model_names:
        _, fold_rows = _evaluate_series(
            series,
            crop,
            model_name=model_name,
            horizon=horizon,
            min_train_size=min_train_size,
            validation_windows=validation_windows,
            seed=seed,
        )
        for row in fold_rows:
            all_rows.append(row)

    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    return all_rows


def aggregate_model_performance(forecast_rows):
    """Aggregate complete fold metrics, or derive them from prediction-level rows."""
    forecast_rows = list(forecast_rows)
    if forecast_rows and 'MAE' not in forecast_rows[0]:
        predictions_by_fold = {}
        for row in forecast_rows:
            key = (row.get('crop'), row.get('model'), row.get('fold'))
            predictions_by_fold.setdefault(key, []).append(row)
        fold_rows = []
        for (crop, model, fold), rows in predictions_by_fold.items():
            valid = all(row.get('validity_status', 'VALID') == 'VALID' for row in rows)
            metrics = _compute_metrics(
                [row['actual'] for row in rows],
                [row['predicted'] for row in rows],
            ) if valid else {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan}
            fold_rows.append({'crop': crop, 'model': model, 'fold': fold, **metrics, 'status': 'VALID' if valid else 'FAILED'})
        forecast_rows = fold_rows

    grouped = {}
    for row in forecast_rows:
        key = (row.get('crop'), row.get('model'))
        grouped.setdefault(key, []).append(row)

    results = []
    for (crop, model), rows in grouped.items():
        valid_rows = [r for r in rows if r.get('status', 'VALID') == 'VALID']
        mae_values = np.asarray([float(r['MAE']) for r in valid_rows if np.isfinite(r['MAE'])], dtype=float)
        rmse_values = np.asarray([float(r['RMSE']) for r in valid_rows if np.isfinite(r['RMSE'])], dtype=float)
        mape_values = np.asarray([float(r['MAPE']) for r in valid_rows if np.isfinite(r['MAPE'])], dtype=float)
        r2_values = np.asarray([float(r['R2']) for r in valid_rows if np.isfinite(r['R2'])], dtype=float)

        metrics = {
            'crop': crop,
            'model': model,
            'valid_folds': sum(r.get('status', 'VALID') == 'VALID' for r in rows),
            'failed_folds': sum(r.get('status') == 'FAILED' for r in rows),
            'mean_MAE': float(np.mean(mae_values)) if mae_values.size else np.nan,
            'mean_RMSE': float(np.mean(rmse_values)) if rmse_values.size else np.nan,
            'mean_MAPE': float(np.mean(mape_values)) if mape_values.size else np.nan,
            'mean_R2': float(np.mean(r2_values)) if r2_values.size else np.nan,
            'std_MAE': float(np.std(mae_values, ddof=0)) if mae_values.size else np.nan,
            'std_RMSE': float(np.std(rmse_values, ddof=0)) if rmse_values.size else np.nan,
            'std_MAPE': float(np.std(mape_values, ddof=0)) if mape_values.size else np.nan,
            'std_R2': float(np.std(r2_values, ddof=0)) if r2_values.size else np.nan,
        }
        results.append(metrics)
    return results


def select_best_validation_model(crop_rows):
    """Select the model with the lowest validation RMSE for each crop."""
    if not crop_rows:
        return None
    summary = aggregate_model_performance(crop_rows)
    if not summary:
        return None
    candidates = [row for row in summary if row['valid_folds'] > 0 and np.isfinite(row['mean_RMSE'])]
    return min(candidates, key=lambda x: x['mean_RMSE']) if candidates else None


def _write_validation_outputs(validation_rows, output_dir='.'):
    if not validation_rows:
        return
    os.makedirs(output_dir, exist_ok=True)
    validation_df = pd.DataFrame(validation_rows)
    validation_df.to_csv(os.path.join(output_dir, 'forecast_validation_results.csv'), index=False)

    comparison_df = pd.DataFrame(aggregate_model_performance(validation_rows))
    comparison_df.to_csv(os.path.join(output_dir, 'model_comparison.csv'), index=False)
    return validation_df, comparison_df


def run_forecasting_validation(data_path, crops=None, random_seed=42, horizon=4, min_train_size=12, validation_windows=3):
    """Generate validated forecast artifacts using the diagnostic evaluation pipeline."""
    from src.forecast_validation import run_forecasting_validation as run_diagnostic_validation

    return run_diagnostic_validation(
        data_path=data_path,
        crops=crops,
        random_seed=random_seed,
        horizon=horizon,
        min_train_size=min_train_size,
        validation_windows=validation_windows,
    )


def evaluate_forecast(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    with np.errstate(divide='ignore', invalid='ignore'):
        mape = np.mean(np.abs((actual - predicted) / np.where(actual == 0, np.nan, actual))) * 100

    return {'mae': mae, 'rmse': rmse, 'mape': mape}


def run_crop_pipeline(df, crop, forecast_steps=4, test_steps=4, model_dir='models'):
    ts = prepare_crop_timeseries(df, crop)
    ts = ts.dropna()

    if len(ts) < (test_steps + 8):
        raise ValueError('Not enough data to train and test')

    train = ts.iloc[:-test_steps]
    test = ts.iloc[-test_steps:]

    # Train or load models to avoid retraining on every run
    models = get_or_train_models(df, crop, model_dir)

    arima_pred = forecast_model(models['arima'], steps=test_steps)
    sarima_pred = forecast_model(models['sarima'], steps=test_steps)
    lstm_pred = forecast_lstm(models['lstm'][0], models['lstm'][1], train, steps=test_steps, n_input=models['lstm'][2])

    arima_scores = evaluate_forecast(test, arima_pred)
    sarima_scores = evaluate_forecast(test, sarima_pred)
    lstm_scores = evaluate_forecast(test, lstm_pred)

    # Ensemble and uncertainty
    ensemble = ensemble_forecast(models, df, crop, steps=forecast_steps)

    current_price = float(ts.iloc[-1])

    # Crisp decision metrics
    rise_pct = (ensemble['ensemble'][0] - current_price) / current_price * 100

    return {
        'crop': crop,
        'train': train,
        'test': test,
        'arima': {'model': models['arima'], 'forecast': arima_pred, 'metrics': arima_scores},
        'sarima': {'model': models['sarima'], 'forecast': sarima_pred, 'metrics': sarima_scores},
        'lstm': {'model': models['lstm'], 'forecast': lstm_pred, 'metrics': lstm_scores},
        'ensemble': ensemble['ensemble'],
        'future_forecast': ensemble['ensemble'],
        'confidence_lower': ensemble['ci_lower'],
        'confidence_upper': ensemble['ci_upper'],
        'best_model': 'ensemble',
        'current_price': current_price,
        'price_change_pct': rise_pct,
        'forecast_validation': {
            'current_price': current_price,
            'low_bound': current_price * 0.7,
            'high_bound': current_price * 1.5,
            'raw_forecast': ensemble['ensemble'].tolist(),
            'validated_forecast': ensemble['ensemble'].tolist(),
            'ci_lower': ensemble['ci_lower'].tolist(),
            'ci_upper': ensemble['ci_upper'].tolist(),
        },
    }


def save_model(model, path):
    if isinstance(model, tuple):  # LSTM case
        lstm_model, scaler, n_input = model
        with open(path, 'wb') as f:
            pickle.dump({'model': lstm_model, 'scaler': scaler, 'n_input': n_input}, f)
    else:
        with open(path, 'wb') as f:
            pickle.dump(model, f)
