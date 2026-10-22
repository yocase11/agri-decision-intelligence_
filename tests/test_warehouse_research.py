import numpy as np
import pandas as pd

from src.warehouse_research import (
    BASELINE_COLUMNS,
    SENSITIVITY_COLUMNS,
    _baseline_rows,
    _constraint_violations,
    _cost_components,
    _options_for_crop,
    _sensitivity_rows,
    solve_cost_minimization,
)
from src.run_full_pipeline import run_full_pipeline


ASSUMPTIONS = {
    'transport_rate_inr_per_km_per_metric_tonne': 5.0,
    'unallocated_penalty_inr_per_quintal': 1_000_000.0,
    'sensitivity': {
        'storage_cost_multipliers': [0.5, 1.0, 1.5, 2.0],
        'transport_cost_multipliers': [0.5, 1.0, 1.5, 2.0],
        'available_quantity_multipliers': [0.5, 1.0, 1.5],
    },
}


def options_fixture():
    return [
        {
            'warehouse_id': 'W_LOW', 'capacity_quintal': 8.0, 'distance_km': 10.0,
            'storage_rate_inr_per_quintal_month': 1.0, 'storage_cost_per_quintal': 3.0,
            'transport_cost_per_quintal': 0.5,
        },
        {
            'warehouse_id': 'W_HIGH', 'capacity_quintal': 20.0, 'distance_km': 20.0,
            'storage_rate_inr_per_quintal_month': 4.0, 'storage_cost_per_quintal': 12.0,
            'transport_cost_per_quintal': 1.0,
        },
    ]


def scenario_fixture():
    return pd.Series({
        'crop': 'Rice', 'scenario_id': 'Rice_sarima_2012-12-31_h1',
        'model': 'sarima', 'decision_date': '2012-12-31', 'horizon': 1,
        'quantity_quintal': 5.0, 'storage_duration': 3.0,
    })


def warehouse_frame():
    return pd.DataFrame([
        {
            'Warehouse_ID': 'W_RICE', 'Capacity_MT': 2.0, 'Storage_Cost_per_MT': 20.0,
            'Latitude': 10.0, 'Longitude': 77.0,
            'Rice_Supported': 1, 'Onion_Supported': 0, 'Tomato_Supported': 0,
        },
        {
            'Warehouse_ID': 'W_ONION', 'Capacity_MT': 3.0, 'Storage_Cost_per_MT': 10.0,
            'Latitude': 10.1, 'Longitude': 77.1,
            'Rice_Supported': 0, 'Onion_Supported': 1, 'Tomato_Supported': 0,
        },
    ])


def test_capacity_constraint():
    options = options_fixture()
    allocations, unallocated, _, _ = solve_cost_minimization(options, 10.0, 3.0)
    by_id = {option['warehouse_id']: option for option in options}
    assert all(allocations[key] <= by_id[key]['capacity_quintal'] + 1e-8 for key in allocations)
    assert unallocated == 0.0


def test_quantity_balance():
    options = options_fixture()
    allocations, unallocated, _, _ = solve_cost_minimization(options, 10.0, 3.0)
    assert np.isclose(sum(allocations.values()) + unallocated, 10.0)


def test_crop_compatibility():
    frame = warehouse_frame()
    options = _options_for_crop(frame, 'Rice', (10.0, 77.0), ASSUMPTIONS, 3.0)
    assert [option['warehouse_id'] for option in options] == ['W_RICE']
    assert options[0]['capacity_quintal'] == 20.0


def test_nonnegative_allocation():
    allocations, unallocated, _, _ = solve_cost_minimization(options_fixture(), 10.0, 3.0)
    assert all(value >= 0 for value in allocations.values())
    assert unallocated >= 0


def test_zero_constraint_violations():
    options = options_fixture()
    allocations, unallocated, _, _ = solve_cost_minimization(options, 10.0, 3.0)
    compatible = {option['warehouse_id'] for option in options}
    assert _constraint_violations(allocations, unallocated, 10.0, options, compatible) == 0


def test_objective_matches_reported_cost():
    options = options_fixture()
    allocations, unallocated, status, objective = solve_cost_minimization(options, 5.0, 3.0)
    storage, transport, _, _, _ = _cost_components(allocations, options)
    assert status == 'Optimal'
    assert unallocated == 0
    assert np.isclose(objective, storage + transport)


def test_transport_cost_units():
    options = _options_for_crop(warehouse_frame(), 'Rice', (10.0, 77.0), ASSUMPTIONS, 3.0)
    option = options[0]
    assert option['distance_km'] == 0.0
    assert option['transport_cost_per_quintal'] == 0.0

    frame = warehouse_frame()
    frame.loc[0, 'Longitude'] = 77.1
    options = _options_for_crop(frame, 'Rice', (10.0, 77.0), ASSUMPTIONS, 3.0)
    assert np.isclose(options[0]['transport_cost_per_quintal'], options[0]['distance_km'] * 5.0 / 10.0)


def test_storage_cost_units():
    options = _options_for_crop(warehouse_frame(), 'Rice', (10.0, 77.0), ASSUMPTIONS, 3.0)
    assert options[0]['storage_rate_inr_per_quintal_month'] == 2.0
    assert options[0]['storage_cost_per_quintal'] == 6.0
    allocation, unallocated, _, _ = solve_cost_minimization(options, 5.0, 3.0)
    storage, _, _, _, _ = _cost_components(allocation, options)
    assert unallocated == 0
    assert storage == 30.0


def test_unallocated_quantity():
    allocations, unallocated, status, objective = solve_cost_minimization([], 4.0, 3.0, 1000.0)
    assert allocations == {}
    assert unallocated == 4.0
    assert status == 'Optimal'
    assert objective == 4000.0


def test_baseline_schema():
    rows = _baseline_rows('Rice', scenario_fixture(), options_fixture(), 5.0, 3.0, ASSUMPTIONS)
    frame = pd.DataFrame(rows, columns=BASELINE_COLUMNS)
    assert frame.columns.tolist() == BASELINE_COLUMNS
    assert set(frame.method) == {'MILP', 'Nearest Feasible', 'Lowest Storage Cost', 'Existing Method'}
    assert len(frame) == 4


def test_sensitivity_schema():
    rows = _sensitivity_rows('Rice', scenario_fixture(), warehouse_frame(), (10.2, 77.0), ASSUMPTIONS)
    frame = pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)
    assert frame.columns.tolist() == SENSITIVITY_COLUMNS
    assert len(frame) == 11
    assert set(frame.scenario_type) == {
        'storage_cost_multiplier', 'transport_cost_multiplier', 'available_quantity_multiplier'
    }
    storage = frame.loc[frame.scenario_type.eq('storage_cost_multiplier')].set_index('scenario_multiplier')
    assert storage.loc[0.5, 'total_cost_inr'] < storage.loc[1.0, 'total_cost_inr']
    assert storage.loc[1.0, 'total_cost_inr'] < storage.loc[2.0, 'total_cost_inr']
    transport = frame.loc[frame.scenario_type.eq('transport_cost_multiplier')].set_index('scenario_multiplier')
    assert transport.loc[0.5, 'total_cost_inr'] < transport.loc[1.0, 'total_cost_inr']


def test_tiny_hand_calculated_milp_allocation():
    options = [
        {'warehouse_id': 'A', 'capacity_quintal': 10.0, 'storage_cost_per_quintal': 2.0, 'transport_cost_per_quintal': 1.0},
        {'warehouse_id': 'B', 'capacity_quintal': 10.0, 'storage_cost_per_quintal': 5.0, 'transport_cost_per_quintal': 1.0},
    ]
    allocations, unallocated, status, objective = solve_cost_minimization(options, 8.0, 1.0)
    assert allocations == {'A': 8.0, 'B': 0.0}
    assert unallocated == 0.0
    assert status == 'Optimal'
    assert objective == 24.0


def test_full_pipeline_warehouse_research_mode_consumes_upstream_artifacts(monkeypatch, tmp_path):
    import src.warehouse_research as research_module

    observed = {}

    def fake_research(**kwargs):
        observed.update(kwargs)
        return {'summary': pd.DataFrame([{'solver_status': 'Optimal', 'constraint_violations': 0}])}

    monkeypatch.setattr(research_module, 'run_warehouse_research', fake_research)
    result = run_full_pipeline(
        dataset_path='unused-price.csv',
        model_dir=str(tmp_path / 'models'),
        warehouse_dataset='warehouses.csv',
        warehouse_research=True,
        sell_store_results_path='sell_store_decisions.csv',
        warehouse_research_output_dir=str(tmp_path / 'warehouse-results'),
        validation_config_path='experiment_config.json',
        warehouse_research_assumptions_path='warehouse_assumptions.json',
    )

    assert result['mode'] == 'warehouse_research'
    assert observed['sell_store_results'] == 'sell_store_decisions.csv'
    assert observed['warehouse_dataset'] == 'warehouses.csv'
    assert observed['config_path'] == 'experiment_config.json'
    assert observed['assumptions_path'] == 'warehouse_assumptions.json'
    assert observed['output_dir'] == str(tmp_path / 'warehouse-results')
