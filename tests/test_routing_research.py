import json

import numpy as np
import pandas as pd
import pytest

from src.routing_research import haversine_km, run_routing_research, transport_cost_inr
from src.run_full_pipeline import run_full_pipeline


def _write_fixture_inputs(root):
    warehouses = pd.DataFrame([
        {'Warehouse_ID': 'WH_A', 'Latitude': 10.0, 'Longitude': 77.0, 'Capacity_MT': 5.0, 'Storage_Cost_per_MT': 2.0, 'Rice_Supported': 1, 'Onion_Supported': 0, 'Tomato_Supported': 0},
        {'Warehouse_ID': 'WH_B', 'Latitude': 10.2, 'Longitude': 77.2, 'Capacity_MT': 8.0, 'Storage_Cost_per_MT': 3.0, 'Rice_Supported': 1, 'Onion_Supported': 0, 'Tomato_Supported': 0},
    ])
    warehouse_path = root / 'warehouses.csv'
    warehouses.to_csv(warehouse_path, index=False)
    origin = (float(warehouses.Latitude.mean()), float(warehouses.Longitude.mean()))
    distance = haversine_km(*origin, float(warehouses.iloc[0].Latitude), float(warehouses.iloc[0].Longitude))
    quantity = 2.0
    cost = transport_cost_inr(distance, quantity, 5.0)
    scenario_id = 'Rice_sarima_2012-12-31_h1'

    allocations = pd.DataFrame([{
        'crop': 'Rice', 'warehouse_id': 'WH_A', 'available_quantity_quintal': quantity,
        'allocated_quantity_quintal': quantity, 'capacity_quintal': 50.0,
        'storage_cost_inr': 0.4, 'transport_cost_inr': cost,
        'total_cost_inr': 0.4 + cost, 'distance_km': distance,
        'utilization_percentage': quantity / 50.0 * 100.0,
        'optimization_status': 'Optimal', 'scenario_id': scenario_id,
        'model': 'sarima', 'decision_date': '2012-12-31', 'horizon': 1,
        'price_unit': 'INR per quintal',
    }])
    allocation_path = root / 'warehouse_optimization_results.csv'
    allocations.to_csv(allocation_path, index=False)
    warehouse_summary = pd.DataFrame([{
        'crop': 'Rice', 'total_available_quantity_quintal': quantity,
        'total_allocated_quantity_quintal': quantity, 'total_unallocated_quantity_quintal': 0.0,
        'total_storage_cost_inr': 0.4, 'total_transport_cost_inr': cost,
        'total_cost_inr': 0.4 + cost, 'average_cost_per_quintal': (0.4 + cost) / quantity,
        'number_of_warehouses_used': 1, 'constraint_violations': 0,
        'scenario_id': scenario_id, 'model': 'sarima', 'decision_date': '2012-12-31',
        'horizon': 1, 'solver_status': 'Optimal', 'objective_value_inr': 0.4 + cost,
        'unallocated_penalty_inr': 0.0, 'capacity_utilization_percentage': 0.4,
        'average_warehouse_distance_km': distance, 'price_unit': 'INR per quintal',
    }])
    summary_path = root / 'warehouse_summary.csv'
    warehouse_summary.to_csv(summary_path, index=False)

    sell_store = pd.DataFrame([{
        'crop': 'Rice', 'model': 'sarima', 'decision_date': '2012-12-31', 'horizon': 1,
        'quantity_quintal': quantity, 'price_unit': 'INR per quintal',
    }])
    sell_store_path = root / 'sell_store_decisions.csv'
    sell_store.to_csv(sell_store_path, index=False)
    config_path = root / 'experiment_config.json'
    config_path.write_text(json.dumps({'selected_models': {'Rice': 'sarima'}}), encoding='utf-8')
    warehouse_assumptions = {
        'transport_rate_inr_per_km_per_metric_tonne': 5.0,
        'origin_override_latitude': None,
        'origin_override_longitude': None,
    }
    warehouse_assumptions_path = root / 'warehouse_assumptions.json'
    warehouse_assumptions_path.write_text(json.dumps(warehouse_assumptions), encoding='utf-8')
    routing_assumptions_path = root / 'routing_assumptions.json'
    routing_assumptions_path.write_text(json.dumps({
        'transport_rate_inr_per_km_per_metric_tonne': 5.0,
        'sensitivity': {'transport_cost_multipliers': [0.5, 1.0], 'available_quantity_multipliers': [0.5, 1.0]},
    }), encoding='utf-8')

    pd.DataFrame([{'crop':'Rice','model':'sarima','horizon':1,'RMSE':3.0,'MAE':2.0}]).to_csv(root/'forecast_horizon_metrics.csv',index=False)
    pd.DataFrame([{'crop':'Rice','model':'sarima','fold':1,'R2':0.25}]).to_csv(root/'forecast_fold_metrics.csv',index=False)
    pd.DataFrame([{'crop':'Rice','model':'sarima','fold':1,'train_end':'2012-12-31'}]).to_csv(root/'forecast_predictions.csv',index=False)
    pd.DataFrame([{'crop':'Rice','model':'sarima','horizon':1,'decision_agreement_percentage':75.0,'mean_regret_inr':4.0}]).to_csv(root/'sell_store_summary.csv',index=False)

    return {
        'warehouse_dataset': str(warehouse_path),
        'warehouse_results': str(allocation_path),
        'warehouse_summary': str(summary_path),
        'sell_store_results': str(sell_store_path),
        'config_path': str(config_path),
        'warehouse_assumptions_path': str(warehouse_assumptions_path),
        'routing_assumptions_path': str(routing_assumptions_path),
        'origin': origin,
        'distance': distance,
        'transport_cost': cost,
    }


def test_haversine_distance_units_and_known_result():
    assert haversine_km(0.0, 0.0, 0.0, 1.0) == pytest.approx(111.195, rel=1e-4)


def test_transport_cost_quintal_to_metric_tonne_conversion():
    assert transport_cost_inr(100.0, 2.0, 5.0) == 100.0


def test_transport_cost_rejects_negative_and_nonfinite_inputs():
    with pytest.raises(ValueError):
        transport_cost_inr(10.0, -1.0, 5.0)
    with pytest.raises(ValueError):
        transport_cost_inr(np.inf, 1.0, 5.0)


def test_routing_outputs_link_to_warehouse_allocation_and_end_to_end(tmp_path, monkeypatch):
    import src.routing as legacy_routing

    inputs = _write_fixture_inputs(tmp_path)
    monkeypatch.setattr(legacy_routing, 'get_road_distance_and_time', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('OSRM must not be called in proxy mode')))
    monkeypatch.setattr(legacy_routing, 'get_distance_matrix', lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('OSRM table must not be called in proxy mode')))
    result = run_routing_research(
        warehouse_results_path=inputs['warehouse_results'],
        warehouse_summary_path=inputs['warehouse_summary'],
        warehouse_dataset_path=inputs['warehouse_dataset'],
        sell_store_results_path=inputs['sell_store_results'],
        warehouse_assumptions_path=inputs['warehouse_assumptions_path'],
        routing_assumptions_path=inputs['routing_assumptions_path'],
        forecast_horizon_metrics_path=str(tmp_path/'forecast_horizon_metrics.csv'),
        forecast_fold_metrics_path=str(tmp_path/'forecast_fold_metrics.csv'),
        forecast_predictions_path=str(tmp_path/'forecast_predictions.csv'),
        sell_store_summary_path=str(tmp_path/'sell_store_summary.csv'),
        output_dir=str(tmp_path/'output'),
    )
    route = result['routes'].iloc[0]
    assert route['scenario_id'] == 'Rice_sarima_2012-12-31_h1'
    assert route['warehouse_id'] == 'WH_A'
    assert route['distance_source'] == 'Haversine'
    assert route['distance_km'] == pytest.approx(inputs['distance'])
    assert route['transport_cost_inr'] == pytest.approx(inputs['transport_cost'])
    assert route['route_feasible']
    assert set(result['baselines'].method) == {
        'Warehouse MILP allocation + Haversine',
        'Nearest feasible warehouse',
        'Legacy best_route offline formula',
    }
    assert set(result['sensitivity'].scenario_type) == {'transport_cost_multiplier', 'available_quantity_multiplier'}
    assert len(result['end_to_end']) == 1
    assert result['end_to_end'].forecast_model.iloc[0] == 'sarima'
    assert result['end_to_end'].iloc[0]['forecast_RMSE'] == 3.0
    assert result['end_to_end'].iloc[0]['sell_store_agreement_percentage'] == 75.0
    assert result['end_to_end'].route_distance_source.iloc[0] == 'Haversine proxy only'
    assert result['end_to_end'].notna().all().all()
    assert (tmp_path/'output'/'END_TO_END_RESEARCH_REPORT.md').exists()
    assert 'not a CVRP' in (tmp_path/'output'/'routing_validation_report.md').read_text(encoding='utf-8')


def test_missing_warehouse_coordinate_fails_explicitly(tmp_path):
    inputs = _write_fixture_inputs(tmp_path)
    broken = pd.read_csv(inputs['warehouse_dataset']).drop(columns=['Latitude'])
    broken_path = tmp_path/'broken_warehouses.csv'
    broken.to_csv(broken_path,index=False)
    with pytest.raises(ValueError, match='missing fields'):
        run_routing_research(
            warehouse_results_path=inputs['warehouse_results'],
            warehouse_summary_path=inputs['warehouse_summary'],
            warehouse_dataset_path=str(broken_path),
            sell_store_results_path=inputs['sell_store_results'],
            warehouse_assumptions_path=inputs['warehouse_assumptions_path'],
            routing_assumptions_path=inputs['routing_assumptions_path'],
            forecast_horizon_metrics_path=str(tmp_path/'forecast_horizon_metrics.csv'),
            forecast_fold_metrics_path=str(tmp_path/'forecast_fold_metrics.csv'),
            forecast_predictions_path=str(tmp_path/'forecast_predictions.csv'),
            sell_store_summary_path=str(tmp_path/'sell_store_summary.csv'),
            output_dir=str(tmp_path/'out'),
        )


def test_mismatched_allocation_and_summary_are_rejected(tmp_path):
    inputs = _write_fixture_inputs(tmp_path)
    results = pd.read_csv(inputs['warehouse_results'])
    results['allocated_quantity_quintal'] = 0.0
    results.to_csv(inputs['warehouse_results'],index=False)
    with pytest.raises(ValueError, match='do not balance'):
        run_routing_research(
            warehouse_results_path=inputs['warehouse_results'],
            warehouse_summary_path=inputs['warehouse_summary'],
            warehouse_dataset_path=inputs['warehouse_dataset'],
            sell_store_results_path=inputs['sell_store_results'],
            warehouse_assumptions_path=inputs['warehouse_assumptions_path'],
            routing_assumptions_path=inputs['routing_assumptions_path'],
            forecast_horizon_metrics_path=str(tmp_path/'forecast_horizon_metrics.csv'),
            forecast_fold_metrics_path=str(tmp_path/'forecast_fold_metrics.csv'),
            forecast_predictions_path=str(tmp_path/'forecast_predictions.csv'),
            sell_store_summary_path=str(tmp_path/'sell_store_summary.csv'),
            output_dir=str(tmp_path/'out'),
        )


def test_empty_route_input_is_rejected_explicitly(tmp_path):
    inputs = _write_fixture_inputs(tmp_path)
    empty = pd.read_csv(inputs['warehouse_results']).iloc[0:0]
    empty.to_csv(inputs['warehouse_results'], index=False)
    with pytest.raises(ValueError, match='scenario IDs do not match'):
        run_routing_research(
            warehouse_results_path=inputs['warehouse_results'],
            warehouse_summary_path=inputs['warehouse_summary'],
            warehouse_dataset_path=inputs['warehouse_dataset'],
            sell_store_results_path=inputs['sell_store_results'],
            warehouse_assumptions_path=inputs['warehouse_assumptions_path'],
            routing_assumptions_path=inputs['routing_assumptions_path'],
            forecast_horizon_metrics_path=str(tmp_path/'forecast_horizon_metrics.csv'),
            forecast_fold_metrics_path=str(tmp_path/'forecast_fold_metrics.csv'),
            forecast_predictions_path=str(tmp_path/'forecast_predictions.csv'),
            sell_store_summary_path=str(tmp_path/'sell_store_summary.csv'),
            output_dir=str(tmp_path/'out'),
        )


def test_routing_research_runner_uses_saved_warehouse_outputs(monkeypatch, tmp_path):
    import src.routing_research as research_module

    observed = {}

    def fake_research(**kwargs):
        observed.update(kwargs)
        return {'routes': pd.DataFrame([{'distance_source':'Haversine'}]), 'summary': pd.DataFrame([{'route_feasibility':True}]), 'baselines':pd.DataFrame(), 'sensitivity':pd.DataFrame()}

    monkeypatch.setattr(research_module,'run_routing_research',fake_research)
    result=run_full_pipeline(
        dataset_path='unused.csv',model_dir=str(tmp_path/'models'),warehouse_dataset='warehouse.csv',
        routing_research=True,warehouse_results_path='saved_allocations.csv',
        routing_research_output_dir=str(tmp_path/'route_outputs'),routing_research_assumptions_path='route_config.json',
    )
    assert result['mode']=='routing_research'
    assert observed['warehouse_results_path']=='saved_allocations.csv'
    assert observed['warehouse_dataset_path']=='warehouse.csv'
    assert observed['routing_assumptions_path']=='route_config.json'
    assert observed['output_dir']==str(tmp_path/'route_outputs')


def test_routing_sensitivity_recomputes_deterministically(tmp_path):
    inputs = _write_fixture_inputs(tmp_path)
    kwargs = {
        'warehouse_results_path': inputs['warehouse_results'],
        'warehouse_summary_path': inputs['warehouse_summary'],
        'warehouse_dataset_path': inputs['warehouse_dataset'],
        'sell_store_results_path': inputs['sell_store_results'],
        'warehouse_assumptions_path': inputs['warehouse_assumptions_path'],
        'routing_assumptions_path': inputs['routing_assumptions_path'],
        'forecast_horizon_metrics_path': str(tmp_path/'forecast_horizon_metrics.csv'),
        'forecast_fold_metrics_path': str(tmp_path/'forecast_fold_metrics.csv'),
        'forecast_predictions_path': str(tmp_path/'forecast_predictions.csv'),
        'sell_store_summary_path': str(tmp_path/'sell_store_summary.csv'),
    }
    first = run_routing_research(**kwargs, output_dir=str(tmp_path/'first'))['sensitivity']
    second = run_routing_research(**kwargs, output_dir=str(tmp_path/'second'))['sensitivity']
    pd.testing.assert_frame_equal(first, second, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
