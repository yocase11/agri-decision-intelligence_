import inspect
import json

import numpy as np
import pandas as pd
import pytest

from src.sell_store_research import (
    DECISION_COLUMNS,
    SENSITIVITY_COLUMNS,
    _baseline_records,
    _decision_records,
    _score_actual_decision,
    _sensitivity,
    decide_sell_or_store_economic,
)
from src.run_full_pipeline import run_full_pipeline


def economic(**overrides):
    values = {
        'current_price_inr_per_quintal': 1000.0,
        'forecast_price_inr_per_quintal': 1200.0,
        'quantity_quintal': 2.0,
        'storage_duration_months': 3.0,
        'storage_rate_inr_per_kg_per_month': 0.1,
        'spoilage_rate': 0.05,
        'transport_cost_inr': 0.0,
    }
    values.update(overrides)
    return decide_sell_or_store_economic(**values)


def test_sell_now_value():
    result = economic()
    assert result['sell_now_value_inr'] == 2000.0


def test_store_value():
    result = economic()
    assert result['expected_store_revenue_inr'] == 2280.0
    assert result['storage_cost_inr'] == 60.0
    assert result['store_value_inr'] == 2220.0
    assert result['incremental_store_value_inr'] == 220.0


def test_spoilage_reduces_effective_quantity():
    assert economic()['effective_quantity_quintal'] == pytest.approx(1.9)


def test_storage_cost_increases_with_duration():
    three_months = economic(storage_duration_months=3.0)
    six_months = economic(storage_duration_months=6.0)
    assert six_months['storage_cost_inr'] == 2 * three_months['storage_cost_inr']


def test_store_decision_when_net_store_value_is_higher():
    assert economic()['decision'] == 'store'


def test_sell_decision_when_sell_now_value_is_higher():
    result = economic(forecast_price_inr_per_quintal=900.0, spoilage_rate=0.1)
    assert result['decision'] == 'sell'


def test_zero_spoilage():
    result = economic(spoilage_rate=0.0)
    assert result['effective_quantity_quintal'] == 2.0
    assert result['spoilage_cost_inr'] == 0.0


def test_zero_storage_cost():
    result = economic(storage_rate_inr_per_kg_per_month=0.0)
    assert result['storage_cost_inr'] == 0.0


def test_unit_consistency():
    result = economic(quantity_quintal=1.0, current_price_inr_per_quintal=1000.0, forecast_price_inr_per_quintal=1000.0, spoilage_rate=0.0)
    assert result['quantity_kg_for_storage_cost'] == 100.0
    assert result['sell_now_value_inr'] == 1000.0
    assert result['storage_cost_inr'] == pytest.approx(30.0)


def _fixture_inputs(actual_future=900.0):
    predictions = pd.DataFrame([{
        'crop': 'Rice', 'model': 'seasonal_naive', 'fold': 1, 'horizon': 1,
        'train_end': '2010-12-31', 'forecast_date': '2011-03-31',
        'actual': actual_future, 'predicted': 1200.0,
        'validity_status': 'VALID', 'price_unit': 'INR per quintal',
    }])
    source = {'Rice': pd.Series([1000.0, 1100.0, 1150.0], index=pd.PeriodIndex(['2010Q2', '2010Q3', '2010Q4'], freq='Q'))}
    intervals = pd.DataFrame(columns=['crop', 'model', 'fold', 'horizon', 'lower_95', 'upper_95'])
    assumptions = {
        'scenario_quantity_quintal': 1.0,
        'transport_cost_inr': 0.0,
        'storage_rate_inr_per_kg_per_month': {'Rice': 0.0},
        'spoilage_rate_per_holding_decision': {'Rice': 0.0},
        'storage_duration_months_per_forecast_quarter': 3.0,
    }
    return predictions, intervals, source, assumptions


def test_no_future_information_leakage():
    assert 'actual_future_price' not in inspect.signature(decide_sell_or_store_economic).parameters
    first, intervals, source, assumptions = _fixture_inputs(actual_future=800.0)
    second, _, _, _ = _fixture_inputs(actual_future=1400.0)
    row_a = _decision_records(first, intervals, source, assumptions).iloc[0]
    row_b = _decision_records(second, intervals, source, assumptions).iloc[0]
    assert row_a['decision_date'] < row_a['future_actual_date']
    assert row_b['decision_date'] < row_b['future_actual_date']
    assert row_a['decision'] == row_b['decision']
    assert row_a['actual_optimal_decision'] != row_b['actual_optimal_decision']


def test_decision_regret_calculation():
    actual_sell, actual_store, optimal, best_value = _score_actual_decision(
        actual_future_price=900.0,
        current_price=1000.0,
        quantity=1.0,
        duration=3.0,
        storage_rate=0.0,
        spoilage=0.0,
        transport_cost=0.0,
    )
    realized_store_decision_value = actual_store
    regret = best_value - realized_store_decision_value
    assert optimal == 'sell'
    assert actual_sell == 1000.0
    assert actual_store == 900.0
    assert regret == 100.0


def _baseline_fixture():
    row = {
        'crop': 'Rice', 'model': 'seasonal_naive', 'horizon': 1,
        'decision': 'store', 'actual_optimal_decision': 'sell',
        'sell_now_value_inr': 1000.0, 'store_value_inr': 1100.0,
        'quantity_quintal': 1.0, 'spoilage_rate': 0.0,
        'actual_future_price_inr_per_quintal': 900.0, 'storage_cost_inr': 0.0,
        '_fold': 1,
    }
    second_model = {**row, 'model': 'arima', 'decision': 'sell'}
    return pd.DataFrame([row, second_model])


def test_always_sell_baseline():
    baselines = _baseline_records(_baseline_fixture())
    row = baselines.loc[baselines.model.eq('always_sell')].iloc[0]
    assert row['action'] == 'sell'
    assert row['realized_net_value_inr'] == 1000.0
    assert len(baselines.loc[baselines.model.eq('always_sell')]) == 1


def test_always_store_baseline():
    baselines = _baseline_records(_baseline_fixture())
    row = baselines.loc[baselines.model.eq('always_store')].iloc[0]
    assert row['action'] == 'store'
    assert row['realized_net_value_inr'] == 900.0
    assert len(baselines.loc[baselines.model.eq('always_store')]) == 1


def test_seasonal_naive_baseline():
    baselines = _baseline_records(_baseline_fixture())
    assert set(baselines['model']) == {'always_sell', 'always_store', 'seasonal_naive_forecast'}
    row = baselines.loc[baselines.model.eq('seasonal_naive_forecast')].iloc[0]
    assert row['action'] == 'store'


def test_sensitivity_analysis_schema():
    predictions, intervals, source, assumptions = _fixture_inputs()
    decisions = _decision_records(predictions, intervals, source, assumptions)
    assumptions['sensitivity'] = {
        'storage_cost_multipliers': [0.5, 1.0, 1.5, 2.0],
        'spoilage_rates': [0.0, 0.02, 0.05, 0.1],
        'future_price_multipliers': [0.9, 1.0, 1.1],
        'storage_duration_months': [3, 6, 9, 12],
    }
    result = _sensitivity(decisions, assumptions)
    assert result.columns.tolist() == SENSITIVITY_COLUMNS
    assert set(result.scenario_type) == {
        'storage_cost_multiplier', 'spoilage_rate', 'future_price_multiplier', 'storage_duration_months'
    }
    assert len(result) == 15


def test_missing_prediction_interval_does_not_create_fake_interval():
    predictions, intervals, source, assumptions = _fixture_inputs()
    result = _decision_records(predictions, intervals, source, assumptions).iloc[0]
    assert not result['forecast_interval_available']
    assert result['uncertainty_status'] == 'interval unavailable; point forecast used'
    assert np.isfinite(result['forecast_price_inr_per_quintal'])


def test_zero_quantity_and_invalid_rates_are_handled_explicitly():
    result = economic(quantity_quintal=0.0)
    assert result['sell_now_value_inr'] == 0.0
    with pytest.raises(ValueError):
        economic(spoilage_rate=1.1)


def test_decision_output_schema_contains_required_fields():
    predictions, intervals, source, assumptions = _fixture_inputs()
    result = _decision_records(predictions, intervals, source, assumptions)
    assert set(DECISION_COLUMNS).issubset(result.columns)
    assert result.loc[0, 'price_unit'] == 'INR per quintal'


def test_full_pipeline_research_mode_uses_validated_artifacts_without_legacy_training(monkeypatch, tmp_path):
    import src.sell_store_research as research_module

    observed = {}

    def fake_research(**kwargs):
        observed.update(kwargs)
        return {'selected_models': {'Rice': 'sarima'}}

    monkeypatch.setattr(research_module, 'run_sell_store_research', fake_research)
    result = run_full_pipeline(
        dataset_path='source.csv',
        model_dir=str(tmp_path / 'models'),
        sell_store_research=True,
        validated_predictions_path='validated_predictions.csv',
        validated_intervals_path='validated_intervals.csv',
        validation_config_path='validation_config.json',
        sell_store_assumptions_path='assumptions.json',
        sell_store_output_dir=str(tmp_path / 'research'),
    )

    assert result['mode'] == 'validated_sell_store_research'
    assert observed['predictions_path'] == 'validated_predictions.csv'
    assert observed['intervals_path'] == 'validated_intervals.csv'
    assert observed['config_path'] == 'validation_config.json'
    assert observed['assumptions_path'] == 'assumptions.json'
    assert observed['output_dir'] == str(tmp_path / 'research')
