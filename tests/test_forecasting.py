import pandas as pd
import numpy as np
import src.forecast as forecast_module
from src.forecasting import forecast_price_arima, evaluate_forecast
from src.price_pipeline import _compute_metrics, aggregate_model_performance, chronological_walk_forward_validation, prepare_crop_timeseries
from src.forecast_validation import (
    _compute_metrics as compute_validation_metrics,
    _dm_comparisons,
    _dm_test,
    _evaluate_series,
    _forecast_fold,
    _interval_outputs,
    _load_crop_series,
    _model_summary,
    _select_models,
    _validate_forecast,
    INTERVAL_CONFIDENCE_LEVEL,
)


def test_forecast_price_arima():
    series = pd.Series([100, 105, 102, 110, 115, 120, 125, 130])
    forecast = forecast_price_arima(series, steps=2, order=(1,1,1), seasonal_order=(0,0,0,0))
    assert len(forecast) == 2


def test_evaluate_forecast():
    actual = pd.Series([10, 12])
    pred = pd.Series([11, 13])
    metrics = evaluate_forecast(actual, pred)
    assert metrics["mae"] == 1


def test_walk_forward_validation_is_chronological_and_leakage_free():
    series = pd.Series(np.arange(20, dtype=float))
    results = chronological_walk_forward_validation(series, model_name='seasonal_naive', horizon=2, min_train_size=8, validation_windows=2)
    assert len(results) >= 1
    assert all(row['train_end_index'] < row['test_start_index'] for row in results)
    assert all(np.isfinite(row['actual']) for row in results)
    assert all(np.isfinite(row['predicted']) for row in results)
    assert 'MAE' not in results[0]
    summary = aggregate_model_performance(results)
    assert summary[0]['valid_folds'] == 2


def test_prepare_crop_timeseries_handles_tall_dataset():
    df = pd.DataFrame([
        {'Year': 2009, 'Quarter': '2009Q1', 'Crop': 'Rice', 'Price_INR_per_Quintal': 120.0, 'Final_Price': 172.8},
        {'Year': 2009, 'Quarter': '2009Q2', 'Crop': 'Rice', 'Price_INR_per_Quintal': 125.0, 'Final_Price': 180.0},
        {'Year': 2010, 'Quarter': '2010Q1', 'Crop': 'Rice', 'Price_INR_per_Quintal': 130.0, 'Final_Price': 187.2},
        {'Year': 2010, 'Quarter': '2010Q2', 'Crop': 'Onion', 'Price_INR_per_Quintal': 90.0, 'Final_Price': 0.9},
    ])

    df['quarter_date'] = pd.PeriodIndex(
        df['Year'].astype(str) + df['Quarter'].astype(str).str.replace('.*Q', 'Q', regex=True),
        freq='Q',
    ).to_timestamp('Q')

    series = prepare_crop_timeseries(df, 'Rice', date_col='quarter_date').dropna()
    assert len(series) == 3
    assert series.index[0].year == 2009
    assert series.iloc[-1] == 130.0


def test_compute_metrics_uses_complete_forecast_vector():
    metrics = _compute_metrics(
        actual=np.array([1.0, 2.0, 4.0, 8.0]),
        predicted=np.array([2.0, 2.0, 2.0, 10.0]),
    )

    assert metrics['MAE'] == 1.25
    assert metrics['RMSE'] == 1.5
    assert metrics['MAPE'] == 43.75
    assert np.isclose(metrics['R2'], 1.0 - 9.0 / 28.75)


def test_forecast_validity_rejects_extreme_values():
    train = pd.Series([900.0, 1000.0, 1100.0, 1200.0])
    diagnostics = {'failure_reason': '', 'converged': True}

    valid, reason = _validate_forecast(train, np.array([1000.0, 1100.0, 1200.0, 1e15]), 4, diagnostics, 'sarima')

    assert not valid
    assert 'validity bound' in reason


def test_model_selection_excludes_failed_folds():
    folds = pd.DataFrame([
        {'crop': 'Onion', 'model': 'seasonal_naive', 'status': 'VALID', 'MAE': 2.0, 'RMSE': 3.0, 'MAPE': 4.0, 'R2': 0.5},
        {'crop': 'Onion', 'model': 'seasonal_naive', 'status': 'VALID', 'MAE': 4.0, 'RMSE': 5.0, 'MAPE': 6.0, 'R2': 0.2},
        {'crop': 'Onion', 'model': 'arima', 'status': 'VALID', 'MAE': 5.0, 'RMSE': 6.0, 'MAPE': 8.0, 'R2': 0.99},
        {'crop': 'Onion', 'model': 'sarima', 'status': 'FAILED', 'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 'R2': np.nan},
    ])

    summary = _model_summary(folds)
    selected = _select_models(summary)

    baseline = summary.loc[summary['model'] == 'seasonal_naive'].iloc[0]
    failed = summary.loc[summary['model'] == 'sarima'].iloc[0]
    assert baseline['valid_folds'] == 2
    assert baseline['failed_folds'] == 0
    assert baseline['mean_RMSE'] == 4.0
    assert failed['valid_folds'] == 0
    assert failed['failed_folds'] == 1
    assert selected['Onion'] == 'seasonal_naive'


def test_validation_uses_labeled_source_units_without_conversion(tmp_path):
    data_path = tmp_path / 'prices.csv'
    pd.DataFrame([
        {'Year': 2009, 'Quarter': '2009Q1', 'Crop': 'Onion', 'Price_INR_per_Quintal': 1000.0, 'Final_Price': 10.0},
        {'Year': 2009, 'Quarter': '2009Q2', 'Crop': 'Onion', 'Price_INR_per_Quintal': 1200.0, 'Final_Price': 12.0},
    ]).to_csv(data_path, index=False)

    series, metadata, _ = _load_crop_series(data_path, 'Onion')

    assert series.tolist() == [1000.0, 1200.0]
    assert metadata['observations'] == 2
    assert metadata['start'] == '2009Q1'
    assert metadata['end'] == '2009Q2'


def test_validation_drops_observations_outside_contiguous_quarter_segment(tmp_path):
    data_path = tmp_path / 'gapped_prices.csv'
    pd.DataFrame([
        {'Year': 2009, 'Quarter': '2009Q1', 'Crop': 'Onion', 'Price_INR_per_Quintal': 100.0},
        {'Year': 2009, 'Quarter': '2009Q2', 'Crop': 'Onion', 'Price_INR_per_Quintal': 110.0},
        {'Year': 2009, 'Quarter': '2009Q4', 'Crop': 'Onion', 'Price_INR_per_Quintal': 120.0},
        {'Year': 2010, 'Quarter': '2010Q1', 'Crop': 'Onion', 'Price_INR_per_Quintal': 130.0},
        {'Year': 2010, 'Quarter': '2010Q2', 'Crop': 'Onion', 'Price_INR_per_Quintal': 140.0},
    ]).to_csv(data_path, index=False)

    series, metadata, _ = _load_crop_series(data_path, 'Onion')

    assert series.tolist() == [120.0, 130.0, 140.0]
    assert metadata['source_price_observations'] == 5
    assert metadata['excluded_due_to_quarter_gaps'] == 2
    assert metadata['start'] == '2009Q4'


def test_native_intervals_are_ordered_and_coverage_is_calculated():
    predictions = pd.DataFrame([
        {'crop': 'Rice', 'model': 'arima', 'fold': 1, 'horizon': 1, 'actual': 10.0, 'predicted': 11.0, 'lower_95': 9.0, 'upper_95': 12.0, 'validity_status': 'VALID', 'price_unit': 'INR per quintal'},
        {'crop': 'Rice', 'model': 'arima', 'fold': 1, 'horizon': 2, 'actual': 15.0, 'predicted': 12.0, 'lower_95': 10.0, 'upper_95': 14.0, 'validity_status': 'VALID', 'price_unit': 'INR per quintal'},
        {'crop': 'Rice', 'model': 'lstm', 'fold': 1, 'horizon': 1, 'actual': 10.0, 'predicted': 11.0, 'lower_95': np.nan, 'upper_95': np.nan, 'validity_status': 'VALID', 'price_unit': 'INR per quintal'},
    ])

    intervals, coverage = _interval_outputs(predictions)

    assert intervals.columns.tolist() == [
        'crop', 'model', 'fold', 'horizon', 'actual', 'predicted',
        'lower_95', 'upper_95', 'interval_width', 'price_unit',
    ]
    assert (intervals.loc[intervals.lower_95.notna(), 'lower_95'] <= intervals.loc[intervals.lower_95.notna(), 'upper_95']).all()
    assert intervals.loc[intervals.model.eq('lstm'), 'interval_width'].isna().all()
    h1 = coverage.loc[(coverage.model == 'arima') & (coverage.horizon == '1')].iloc[0]
    overall = coverage.loc[(coverage.model == 'arima') & (coverage.horizon == 'all')].iloc[0]
    assert h1['empirical_coverage_percentage'] == 100.0
    assert overall['empirical_coverage_percentage'] == 50.0
    assert h1['mean_interval_width'] == 3.0


def test_dm_comparison_schema_and_insufficient_origins_are_explicit():
    rows = []
    for model in ('seasonal_naive', 'arima', 'sarima', 'lstm'):
        for fold in range(1, 4):
            rows.append({
                'crop': 'Rice', 'model': model, 'fold': fold, 'horizon': 1,
                'actual': float(fold + 10), 'predicted': float(fold + 10 + (0 if model == 'arima' else 1)),
                'validity_status': 'VALID',
            })

    result = _dm_comparisons(pd.DataFrame(rows), {'Rice': 'arima'})

    assert {'crop', 'model_a', 'model_b', 'horizon', 'loss_function', 'DM_statistic', 'p_value', 'interpretation'}.issubset(result.columns)
    assert len(result) == 3
    assert result['interpretation'].str.contains('Insufficient paired origins').all()
    assert result['p_value'].isna().all()


def test_dm_test_computes_statistic_when_sample_is_sufficient():
    error_a = np.array([0.1, -0.2, 0.05, 0.1, -0.1, 0.03, 0.08, -0.04])
    error_b = np.array([1.0, -1.2, 0.9, 1.1, -0.8, 1.3, 0.7, -1.0])
    result = _dm_test(error_a=error_a, error_b=error_b, horizon=1)
    differential = error_a ** 2 - error_b ** 2
    centered = differential - differential.mean()
    long_run_variance = np.dot(centered, centered) / len(differential)
    hln = (len(differential) + 1 - 2) / len(differential)
    expected_statistic = differential.mean() / np.sqrt(long_run_variance / len(differential)) * np.sqrt(hln)

    assert np.isclose(result['DM_statistic'], expected_statistic)
    assert 0 <= result['p_value'] <= 1
    assert 'statistically distinguishable' in result['interpretation']


def test_arima_uses_native_conf_int_for_95_percent_bounds(monkeypatch):
    expected_bounds = np.array([[8.0, 12.0], [9.0, 13.0]])

    class Forecast:
        predicted_mean = np.array([10.0, 11.0])

        def conf_int(self, alpha):
            assert alpha == 1.0 - INTERVAL_CONFIDENCE_LEVEL
            return expected_bounds

    class Fitted:
        mle_retvals = {'converged': True}
        aic = 1.0
        bic = 2.0
        params = np.array([0.1, 0.2])
        resid = np.array([0.2, -0.1, 0.3, -0.2, 0.1, -0.2, 0.1, -0.1])

        def get_forecast(self, steps):
            assert steps == 2
            return Forecast()

    monkeypatch.setattr('src.forecast_validation._fit_arima', lambda _: Fitted())
    forecast, lower, upper, diagnostics = _forecast_fold(pd.Series([9.0, 10.0, 11.0, 12.0]), 'arima', 2, 42)

    assert forecast.tolist() == [10.0, 11.0]
    assert lower.tolist() == [8.0, 9.0]
    assert upper.tolist() == [12.0, 13.0]
    assert diagnostics['interval_generated']


def test_validation_metrics_define_zero_actual_mape_and_constant_r2_as_nan():
    zero_actual_metrics = compute_validation_metrics([0.0, 5.0], [1.0, 5.0])
    constant_actual_metrics = compute_validation_metrics([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
    assert np.isnan(zero_actual_metrics['MAPE'])
    assert np.isnan(constant_actual_metrics['R2'])


def test_horizon_alignment_uses_exact_validation_dates_and_no_future_training():
    index = pd.date_range('2010-03-31', periods=20, freq='QE')
    series = pd.Series(np.arange(100.0, 120.0), index=index)
    predictions, folds = _evaluate_series(series, 'Rice', 'seasonal_naive', 4, 8, 2, 42)

    assert len(folds) == 2
    for fold in folds:
        fold_rows = [row for row in predictions if row['fold'] == fold['fold']]
        assert [row['horizon'] for row in fold_rows] == [1, 2, 3, 4]
        assert all(row['train_end_index'] < row['test_start_index'] for row in fold_rows)
        assert pd.to_datetime(fold_rows[0]['forecast_date']) > pd.to_datetime(fold_rows[0]['train_end'])
        assert pd.to_datetime(fold_rows[0]['forecast_date']) == pd.to_datetime(fold_rows[0]['test_start'])


def test_one_step_forecast_api_returns_scalar(monkeypatch, tmp_path):
    dates = pd.date_range('2020-03-31', periods=5, freq='QE')
    frame = pd.DataFrame({'Crop': ['Tomato'] * 5, 'quarter_date': dates, 'Final_Price': [10, 11, 12, 13, 14]})
    monkeypatch.setattr(forecast_module, 'load_price_data', lambda _: frame)

    class ForecastResult:
        predicted_mean = pd.Series([15.0])

    class DummyModel:
        def predict(self):
            return None

        def get_forecast(self, steps):
            assert steps == 1
            return ForecastResult()

    value = forecast_module.forecast_next_price(DummyModel(), str(tmp_path / 'unused.csv'), 'Tomato', steps=1)

    assert value == 15.0
    assert isinstance(value, float)
