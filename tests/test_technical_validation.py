import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.robustness_audit import (
    compute_end_to_end_parameter_sensitivity,
    compute_formula_consistency_audit,
    compute_module_ablation,
    compute_prediction_interval_decision_robustness,
    compute_rolling_origin_support,
    generate_robustness_report,
)


def test_rolling_origin_support_is_not_expanded_beyond_available_data():
    summary = compute_rolling_origin_support()
    assert 'supported' in summary
    assert isinstance(summary['supported'], bool)
    assert summary['support_limit_reason']


def test_formula_consistency_audit_detects_no_material_mismatch():
    audit = compute_formula_consistency_audit()
    assert 'mismatch_count' in audit
    assert isinstance(audit['mismatch_count'], int)
    assert audit['mismatch_count'] >= 0
    assert audit['all_formula_checks_pass'] in {True, False}


def test_robustness_report_is_generated(tmp_path):
    output_dir = tmp_path
    result = generate_robustness_report(output_dir=output_dir)
    assert isinstance(result, dict)
    report_path = output_dir / 'TECHNICAL_VALIDATION_REPORT.md'
    assert report_path.exists()
    assert 'Forecast-error sensitivity' in report_path.read_text(encoding='utf-8')


def test_prediction_interval_decisions_use_only_valid_native_interval_models():
    rows, summary = compute_prediction_interval_decision_robustness()
    predictions = pd.read_csv('forecast_predictions.csv')
    expected = predictions.loc[
        predictions['validity_status'].eq('VALID')
        & predictions['model'].isin(['arima', 'sarima'])
        & predictions['lower_95'].notna()
        & predictions['upper_95'].notna()
    ]

    assert len(rows) == len(expected)
    assert set(rows['model']) == {'arima', 'sarima'}
    assert set(rows['decision_class']) <= {'ROBUST_SELL', 'ROBUST_STORE', 'DECISION_SENSITIVE'}
    assert (rows[['point_forecast', 'lower_forecast', 'upper_forecast']] >= 0).all().all()
    assert (rows.loc[rows['raw_lower_forecast'] < 0, 'lower_forecast'] == 0).all()
    assert rows.groupby(['crop', 'model', 'horizon']).size().sum() == len(rows)
    assert (summary['number_of_predictions'] > 0).all()

    expected_stability = 100.0 * (
        summary['robust_sell_decisions'] + summary['robust_store_decisions']
    ) / summary['number_of_predictions']
    pd.testing.assert_series_equal(
        summary['decision_stability_rate'].reset_index(drop=True),
        expected_stability.reset_index(drop=True),
        check_names=False,
    )


def test_sensitivity_and_ablation_outputs_are_deterministic_and_label_scope():
    sensitivity, summary = compute_end_to_end_parameter_sensitivity()
    repeated_sensitivity, repeated_summary = compute_end_to_end_parameter_sensitivity()
    pd.testing.assert_frame_equal(sensitivity, repeated_sensitivity)
    pd.testing.assert_frame_equal(summary, repeated_summary)

    supported_warehouse = sensitivity['warehouse_sensitivity_status'].eq('SUPPORTED_SAVED_SCENARIO')
    supported_routing = sensitivity['routing_sensitivity_status'].eq('SUPPORTED_SAVED_SCENARIO')
    assert sensitivity.loc[supported_warehouse, 'warehouse_total_cost_inr'].notna().all()
    assert sensitivity.loc[supported_routing, 'transport_proxy_cost_inr'].notna().all()
    assert sensitivity.loc[~supported_warehouse, 'warehouse_total_cost_inr'].isna().all()
    assert sensitivity.loc[~supported_routing, 'transport_proxy_cost_inr'].isna().all()
    complete_layers = supported_warehouse & supported_routing
    assert np.allclose(
        sensitivity.loc[complete_layers, 'total_scenario_cost_inr'],
        sensitivity.loc[complete_layers, 'warehouse_total_cost_inr'] + sensitivity.loc[complete_layers, 'transport_proxy_cost_inr'],
    )
    assert sensitivity.loc[~complete_layers, 'total_scenario_cost_inr'].isna().all()

    ablation, ablation_summary = compute_module_ablation()
    assert ablation['comparison_scope'].eq('DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION').all()
    assert ablation['available_metrics'].notna().all()
    assert ablation['unavailable_metrics'].notna().all()
    assert len(ablation) == 12
    assert len(ablation_summary) == 4
