"""Cost-minimizing warehouse allocation research evaluator."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from pulp import LpMinimize, LpProblem, LpStatus, LpVariable, PULP_CBC_CMD, lpSum, value

from src.mcdm import haversine
from src.storage_opt import allocate_storage


WAREHOUSE_RESULT_COLUMNS = [
    'crop', 'warehouse_id', 'available_quantity_quintal', 'allocated_quantity_quintal',
    'capacity_quintal', 'storage_cost_inr', 'transport_cost_inr', 'total_cost_inr',
    'distance_km', 'utilization_percentage', 'optimization_status',
    'scenario_id', 'model', 'decision_date', 'horizon', 'price_unit',
]
SUMMARY_COLUMNS = [
    'crop', 'total_available_quantity_quintal', 'total_allocated_quantity_quintal',
    'total_unallocated_quantity_quintal', 'total_storage_cost_inr',
    'total_transport_cost_inr', 'total_cost_inr', 'average_cost_per_quintal',
    'number_of_warehouses_used', 'constraint_violations', 'scenario_id', 'model',
    'decision_date', 'horizon', 'solver_status', 'objective_value_inr',
    'unallocated_penalty_inr', 'capacity_utilization_percentage',
    'average_warehouse_distance_km', 'price_unit',
]
BASELINE_COLUMNS = [
    'crop', 'method', 'total_cost_inr', 'storage_cost_inr', 'transport_cost_inr',
    'average_cost_per_quintal', 'allocated_quantity_quintal',
    'unallocated_quantity_quintal', 'number_of_warehouses_used',
    'capacity_violation_count', 'scenario_id', 'price_unit',
]
UTILIZATION_COLUMNS = [
    'warehouse_id', 'capacity_quintal', 'allocated_quintal',
    'remaining_capacity_quintal', 'utilization_percentage',
    'storage_cost_inr', 'transport_cost_inr', 'total_cost_inr',
    'crop', 'scenario_id', 'optimization_status',
]
SENSITIVITY_COLUMNS = [
    'crop', 'scenario_id', 'model', 'decision_date', 'horizon',
    'scenario_type', 'scenario_multiplier', 'available_quantity_quintal',
    'total_cost_inr', 'storage_cost_inr', 'transport_cost_inr',
    'warehouse_usage', 'capacity_utilization_percentage',
    'unallocated_quantity_quintal', 'solver_status', 'constraint_violations',
    'price_unit',
]


def _load_warehouse_data(path):
    frame = pd.read_csv(path)
    required = {
        'Warehouse_ID', 'Capacity_MT', 'Storage_Cost_per_MT', 'Latitude', 'Longitude',
        'Rice_Supported', 'Onion_Supported', 'Tomato_Supported',
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Warehouse dataset missing required fields: {sorted(missing)}')
    if frame['Warehouse_ID'].duplicated().any():
        raise ValueError('Warehouse_ID must be unique')
    numeric_columns = ['Capacity_MT', 'Storage_Cost_per_MT', 'Latitude', 'Longitude']
    if not np.isfinite(frame[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError('Capacity, storage rate, and warehouse coordinates must be finite')
    if (frame['Capacity_MT'] < 0).any() or (frame['Storage_Cost_per_MT'] < 0).any():
        raise ValueError('Capacity and storage rates cannot be negative')
    for col in ('Rice_Supported', 'Onion_Supported', 'Tomato_Supported'):
        if not frame[col].isin([0, 1]).all():
            raise ValueError(f'{col} must contain binary 0/1 values')
    frame = frame.copy()
    frame['capacity_quintal'] = frame['Capacity_MT'].astype(float) * 10.0
    frame['storage_rate_inr_per_quintal_month_assumed'] = frame['Storage_Cost_per_MT'].astype(float) / 10.0
    return frame


def _reference_origin(warehouses, assumptions):
    lat_override = assumptions.get('origin_override_latitude')
    lon_override = assumptions.get('origin_override_longitude')
    if (lat_override is None) != (lon_override is None):
        raise ValueError('Both origin coordinate overrides must be supplied together')
    if lat_override is not None:
        return float(lat_override), float(lon_override), 'configured reference coordinate; not an observed farmer origin'
    return (
        float(warehouses['Latitude'].mean()),
        float(warehouses['Longitude'].mean()),
        'arithmetic centroid of warehouse coordinates; synthetic reference origin, not a farmer location',
    )


def _options_for_crop(warehouses, crop, origin, assumptions, duration_months, storage_multiplier=1.0, transport_multiplier=1.0):
    support_column = f'{crop}_Supported'
    eligible = warehouses.loc[warehouses[support_column].eq(1)]
    transport_rate = float(assumptions['transport_rate_inr_per_km_per_metric_tonne']) * transport_multiplier
    options = []
    for row in eligible.to_dict('records'):
        distance = haversine(origin[0], origin[1], float(row['Latitude']), float(row['Longitude']))
        storage_rate_q_month = float(row['Storage_Cost_per_MT']) / 10.0 * storage_multiplier
        transport_rate_q = distance * transport_rate / 10.0
        options.append({
            'warehouse_id': str(row['Warehouse_ID']),
            'capacity_quintal': float(row['Capacity_MT']) * 10.0,
            'distance_km': float(distance),
            'storage_rate_inr_per_quintal_month': storage_rate_q_month,
            'storage_cost_per_quintal': storage_rate_q_month * duration_months,
            'transport_cost_per_quintal': transport_rate_q,
            'source_storage_rate_per_mt': float(row['Storage_Cost_per_MT']),
        })
    return options


def solve_cost_minimization(warehouse_options, available_quantity_quintal, duration_months, unallocated_penalty_inr_per_quintal=1_000_000.0):
    """Solve continuous divisible crop allocation with capacity and balance constraints."""
    quantity = float(available_quantity_quintal)
    if not np.isfinite(quantity) or quantity < 0:
        raise ValueError('available_quantity_quintal must be finite and nonnegative')
    if not np.isfinite(duration_months) or duration_months < 0:
        raise ValueError('duration_months must be finite and nonnegative')
    if unallocated_penalty_inr_per_quintal < 0:
        raise ValueError('unallocated penalty must be nonnegative')
    ids = [option['warehouse_id'] for option in warehouse_options]
    if len(ids) != len(set(ids)):
        raise ValueError('warehouse options must have unique warehouse_id values')

    problem = LpProblem('warehouse_cost_minimization', LpMinimize)
    allocation = {
        option['warehouse_id']: LpVariable(f"x_{index}", lowBound=0)
        for index, option in enumerate(warehouse_options)
    }
    unallocated = LpVariable('unallocated_quintal', lowBound=0, upBound=quantity)
    by_id = {option['warehouse_id']: option for option in warehouse_options}
    problem += lpSum(
        allocation[wid] * (by_id[wid]['storage_cost_per_quintal'] + by_id[wid]['transport_cost_per_quintal'])
        for wid in ids
    ) + unallocated * float(unallocated_penalty_inr_per_quintal)
    problem += lpSum(allocation.values()) + unallocated == quantity, 'quantity_balance'
    for option in warehouse_options:
        problem += allocation[option['warehouse_id']] <= option['capacity_quintal'], f"capacity_{option['warehouse_id']}"

    solver = PULP_CBC_CMD(msg=False, gapRel=1e-9)
    problem.solve(solver)
    solver_status = LpStatus.get(problem.status, str(problem.status))
    if solver_status != 'Optimal':
        raise RuntimeError(f'Warehouse MILP did not solve to optimality: {solver_status}')
    allocations = {wid: max(0.0, float(allocation[wid].value() or 0.0)) for wid in ids}
    unallocated_value = max(0.0, float(unallocated.value() or 0.0))
    objective = float(value(problem.objective) or 0.0)
    return allocations, unallocated_value, solver_status, objective


def _cost_components(allocations, options):
    by_id = {option['warehouse_id']: option for option in options}
    storage = sum(allocations.get(wid, 0.0) * option['storage_cost_per_quintal'] for wid, option in by_id.items())
    transport = sum(allocations.get(wid, 0.0) * option['transport_cost_per_quintal'] for wid, option in by_id.items())
    allocated = sum(allocations.values())
    weighted_distance = (
        sum(allocations.get(wid, 0.0) * option['distance_km'] for wid, option in by_id.items()) / allocated
        if allocated > 0 else 0.0
    )
    used = sum(allocations.get(wid, 0.0) > 1e-8 for wid in by_id)
    return float(storage), float(transport), float(allocated), float(weighted_distance), int(used)


def _constraint_violations(allocations, unallocated, quantity, options, compatible_ids):
    violations = 0
    if any(value < -1e-7 for value in allocations.values()) or unallocated < -1e-7:
        violations += 1
    for option in options:
        if allocations.get(option['warehouse_id'], 0.0) > option['capacity_quintal'] + 1e-7:
            violations += 1
    for warehouse_id, amount in allocations.items():
        if warehouse_id not in compatible_ids and amount > 1e-7:
            violations += 1
    if abs(sum(allocations.values()) + unallocated - quantity) > 1e-6:
        violations += 1
    return int(violations)


def _greedy_allocation(options, quantity, sort_key):
    remaining = float(quantity)
    allocations = {option['warehouse_id']: 0.0 for option in options}
    for option in sorted(options, key=sort_key):
        if remaining <= 1e-9:
            break
        amount = min(remaining, float(option['capacity_quintal']))
        allocations[option['warehouse_id']] = amount
        remaining -= amount
    return allocations, max(0.0, remaining)


def _existing_method_allocation(options, crop, quantity):
    if not options:
        return {}, float(quantity)
    capacities = {option['warehouse_id']: option['capacity_quintal'] for option in options}
    raw = allocate_storage(capacities, {crop: float(quantity)})
    allocations = {
        warehouse_id: max(0.0, float(amount or 0.0))
        for (warehouse_id, _), amount in raw.items()
    }
    return allocations, max(0.0, float(quantity) - sum(allocations.values()))


def _method_metrics(method, allocations, unallocated, quantity, options, compatible_ids, duration):
    storage, transport, allocated, avg_distance, used = _cost_components(allocations, options)
    violations = _constraint_violations(allocations, unallocated, quantity, options, compatible_ids)
    capacity_violations = sum(
        allocations.get(option['warehouse_id'], 0.0) > option['capacity_quintal'] + 1e-7
        for option in options
    )
    return {
        'method': method,
        'storage_cost_inr': storage,
        'transport_cost_inr': transport,
        'total_cost_inr': storage + transport,
        'average_cost_per_quintal': (storage + transport) / allocated if allocated > 1e-9 else 0.0,
        'allocated_quantity_quintal': allocated,
        'unallocated_quantity_quintal': unallocated,
        'number_of_warehouses_used': used,
        'capacity_violation_count': int(capacity_violations),
        'constraint_violations': violations,
        'average_warehouse_distance_km': avg_distance,
    }


def _load_scenarios(sell_store_results, config_path):
    decisions = pd.read_csv(sell_store_results)
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    required = {'crop', 'model', 'decision_date', 'horizon', 'quantity_quintal', 'storage_duration', 'price_unit'}
    missing = required - set(decisions.columns)
    if missing:
        raise ValueError(f'Sell/store artifact missing required fields: {sorted(missing)}')
    if not decisions['price_unit'].eq('INR per quintal').all():
        raise ValueError('Sell/store quantities/prices must come from the INR per quintal research artifact')
    selected = config.get('selected_models', {})
    scenarios = decisions.loc[
        decisions.apply(lambda row: selected.get(row['crop']) == row['model'], axis=1)
    ].copy()
    if scenarios.empty:
        raise ValueError('No decision rows matched selected validated models')
    scenarios['scenario_id'] = scenarios.apply(
        lambda row: f"{row['crop']}_{row['model']}_{row['decision_date']}_h{int(row['horizon'])}", axis=1
    )
    if scenarios['scenario_id'].duplicated().any():
        raise ValueError('Selected-model sell/store rows do not uniquely identify scenarios')
    return scenarios, selected


def _scenario_result(crop, scenario, warehouse_data, origin, assumptions, storage_multiplier=1.0, transport_multiplier=1.0, quantity_multiplier=1.0):
    duration = float(scenario['storage_duration'])
    quantity = float(scenario['quantity_quintal']) * quantity_multiplier
    options = _options_for_crop(
        warehouse_data, crop, origin, assumptions, duration,
        storage_multiplier=storage_multiplier, transport_multiplier=transport_multiplier,
    )
    penalty = float(assumptions['unallocated_penalty_inr_per_quintal'])
    allocations, unallocated, status, objective = solve_cost_minimization(options, quantity, duration, penalty)
    compatible_ids = {option['warehouse_id'] for option in options}
    violations = _constraint_violations(allocations, unallocated, quantity, options, compatible_ids)
    storage, transport, allocated, avg_distance, used = _cost_components(allocations, options)
    compatible_capacity = sum(option['capacity_quintal'] for option in options)
    capacity_utilization = allocated / compatible_capacity * 100.0 if compatible_capacity > 0 else 0.0
    penalty_cost = unallocated * penalty
    if abs(objective - (storage + transport + penalty_cost)) > 1e-5:
        raise AssertionError('MILP objective does not equal independently recomputed allocation cost plus shortage penalty')

    allocation_rows = []
    options_by_id = {option['warehouse_id']: option for option in options}
    for warehouse in warehouse_data.to_dict('records'):
        wid = str(warehouse['Warehouse_ID'])
        capacity = float(warehouse['Capacity_MT']) * 10.0
        amount = allocations.get(wid, 0.0)
        if wid in options_by_id:
            option = options_by_id[wid]
            storage_cost = amount * option['storage_cost_per_quintal']
            transport_cost = amount * option['transport_cost_per_quintal']
            distance = option['distance_km']
            row_status = status
        else:
            storage_cost = 0.0
            transport_cost = 0.0
            distance = float(haversine(origin[0], origin[1], float(warehouse['Latitude']), float(warehouse['Longitude'])))
            row_status = 'INCOMPATIBLE'
        allocation_rows.append({
            'crop': crop,
            'warehouse_id': wid,
            'available_quantity_quintal': quantity,
            'allocated_quantity_quintal': amount,
            'capacity_quintal': capacity,
            'storage_cost_inr': storage_cost,
            'transport_cost_inr': transport_cost,
            'total_cost_inr': storage_cost + transport_cost,
            'distance_km': distance,
            'utilization_percentage': amount / capacity * 100.0 if capacity > 0 else 0.0,
            'optimization_status': row_status,
            'scenario_id': scenario['scenario_id'],
            'model': scenario['model'],
            'decision_date': scenario['decision_date'],
            'horizon': int(scenario['horizon']),
            'price_unit': 'INR per quintal',
        })
    summary = {
        'crop': crop,
        'total_available_quantity_quintal': quantity,
        'total_allocated_quantity_quintal': allocated,
        'total_unallocated_quantity_quintal': unallocated,
        'total_storage_cost_inr': storage,
        'total_transport_cost_inr': transport,
        'total_cost_inr': storage + transport,
        'average_cost_per_quintal': (storage + transport) / allocated if allocated > 1e-9 else 0.0,
        'number_of_warehouses_used': used,
        'constraint_violations': violations,
        'scenario_id': scenario['scenario_id'],
        'model': scenario['model'],
        'decision_date': scenario['decision_date'],
        'horizon': int(scenario['horizon']),
        'solver_status': status,
        'objective_value_inr': objective,
        'unallocated_penalty_inr': penalty_cost,
        'capacity_utilization_percentage': capacity_utilization,
        'average_warehouse_distance_km': avg_distance,
        'price_unit': 'INR per quintal',
    }
    utilization_rows = [
        {
            'warehouse_id': row['warehouse_id'],
            'capacity_quintal': row['capacity_quintal'],
            'allocated_quintal': row['allocated_quantity_quintal'],
            'remaining_capacity_quintal': row['capacity_quintal'] - row['allocated_quantity_quintal'],
            'utilization_percentage': row['utilization_percentage'],
            'storage_cost_inr': row['storage_cost_inr'],
            'transport_cost_inr': row['transport_cost_inr'],
            'total_cost_inr': row['total_cost_inr'],
            'crop': crop,
            'scenario_id': scenario['scenario_id'],
            'optimization_status': row['optimization_status'],
        }
        for row in allocation_rows
    ]
    return summary, allocation_rows, utilization_rows, options


def _baseline_rows(crop, scenario, options, quantity, duration, assumptions):
    compatible = {option['warehouse_id'] for option in options}
    methods = []
    methods.append(('Nearest Feasible', *_greedy_allocation(options, quantity, lambda item: (item['distance_km'], item['warehouse_id']))))
    methods.append(('Lowest Storage Cost', *_greedy_allocation(options, quantity, lambda item: (item['storage_cost_per_quintal'], item['warehouse_id']))))
    existing_alloc, existing_unallocated = _existing_method_allocation(options, crop, quantity)
    methods.append(('Existing Method', existing_alloc, existing_unallocated))
    milp_alloc, milp_unallocated, _, _ = solve_cost_minimization(
        options, quantity, duration, assumptions['unallocated_penalty_inr_per_quintal']
    )
    methods.append(('MILP', milp_alloc, milp_unallocated))

    rows = []
    for method, allocations, unallocated in methods:
        metric = _method_metrics(method, allocations, unallocated, quantity, options, compatible, duration)
        rows.append({
            'crop': crop,
            **{key: metric[key] for key in (
                'method', 'total_cost_inr', 'storage_cost_inr', 'transport_cost_inr',
                'average_cost_per_quintal', 'allocated_quantity_quintal',
                'unallocated_quantity_quintal', 'number_of_warehouses_used',
                'capacity_violation_count',
            )},
            'scenario_id': scenario['scenario_id'],
            'price_unit': 'INR per quintal',
        })
    return rows


def _sensitivity_rows(crop, scenario, warehouse_data, origin, assumptions):
    rows = []
    cases = [
        ('storage_cost_multiplier', value, value, 1.0)
        for value in assumptions['sensitivity']['storage_cost_multipliers']
    ] + [
        ('transport_cost_multiplier', value, 1.0, 1.0)
        for value in assumptions['sensitivity']['transport_cost_multipliers']
    ] + [
        ('available_quantity_multiplier', value, 1.0, value)
        for value in assumptions['sensitivity']['available_quantity_multipliers']
    ]
    for scenario_type, multiplier, storage_multiplier, quantity_multiplier in cases:
        transport_multiplier = multiplier if scenario_type == 'transport_cost_multiplier' else 1.0
        summary, _, _, _ = _scenario_result(
            crop, scenario, warehouse_data, origin, assumptions,
            storage_multiplier=storage_multiplier,
            transport_multiplier=transport_multiplier,
            quantity_multiplier=quantity_multiplier,
        )
        rows.append({
            'crop': crop,
            'scenario_id': scenario['scenario_id'],
            'model': scenario['model'],
            'decision_date': scenario['decision_date'],
            'horizon': int(scenario['horizon']),
            'scenario_type': scenario_type,
            'scenario_multiplier': float(multiplier),
            'available_quantity_quintal': summary['total_available_quantity_quintal'],
            'total_cost_inr': summary['total_cost_inr'],
            'storage_cost_inr': summary['total_storage_cost_inr'],
            'transport_cost_inr': summary['total_transport_cost_inr'],
            'warehouse_usage': summary['number_of_warehouses_used'],
            'capacity_utilization_percentage': summary['capacity_utilization_percentage'],
            'unallocated_quantity_quintal': summary['total_unallocated_quantity_quintal'],
            'solver_status': summary['solver_status'],
            'constraint_violations': summary['constraint_violations'],
            'price_unit': 'INR per quintal',
        })
    return rows


def _paper_tables(baselines, utilization):
    table_z = baselines.groupby(['crop', 'method'], as_index=False, sort=True).agg(
        allocated=('allocated_quantity_quintal', 'mean'),
        unallocated=('unallocated_quantity_quintal', 'mean'),
        storage=('storage_cost_inr', 'mean'),
        transport=('transport_cost_inr', 'mean'),
        total=('total_cost_inr', 'mean'),
        average=('average_cost_per_quintal', 'mean'),
        warehouses=('number_of_warehouses_used', 'mean'),
    )
    table_z = table_z.rename(columns={
        'crop': 'Crop', 'method': 'Method', 'allocated': 'Allocated Quantity (quintal)',
        'unallocated': 'Unallocated Quantity (quintal)', 'storage': 'Storage Cost (INR)',
        'transport': 'Transport Cost (INR)', 'total': 'Total Cost (INR)',
        'average': 'Average Cost (INR/quintal)', 'warehouses': 'Warehouses Used',
    })
    table_w = utilization.groupby('warehouse_id', as_index=False, sort=True).agg(
        capacity=('capacity_quintal', 'first'),
        allocated=('allocated_quintal', 'mean'),
        utilization=('utilization_percentage', 'mean'),
        storage=('storage_cost_inr', 'mean'),
        transport=('transport_cost_inr', 'mean'),
    ).rename(columns={
        'warehouse_id': 'Warehouse', 'capacity': 'Capacity (quintal)',
        'allocated': 'Allocated (quintal)', 'utilization': 'Utilization (%)',
        'storage': 'Storage Cost (INR)', 'transport': 'Transport Cost (INR)',
    })
    return table_z, table_w


def _write_figures(output, baselines, utilization, results, sensitivity):
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    method_order = ['MILP', 'Nearest Feasible', 'Lowest Storage Cost', 'Existing Method']
    cost = baselines.groupby(['crop', 'method'], as_index=False)['total_cost_inr'].mean()
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    cost.pivot(index='crop', columns='method', values='total_cost_inr').reindex(columns=method_order).plot(kind='bar', ax=ax)
    ax.set_title('Mean scenario warehouse cost by crop and method')
    ax.set_xlabel('Crop')
    ax.set_ylabel('Mean storage + transport cost (INR per scenario)')
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'warehouse_cost_by_crop_method.png', dpi=300)
    plt.close(fig)

    components = baselines.groupby('method')[['storage_cost_inr', 'transport_cost_inr']].mean().reindex(method_order)
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    components.plot(kind='bar', stacked=True, ax=ax, color=['#4e79a7', '#f28e2b'])
    ax.set_title('Mean storage and transport cost components')
    ax.set_xlabel('Allocation method')
    ax.set_ylabel('Mean cost (INR per scenario)')
    ax.legend(['Storage', 'Transport'], frameon=False)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'warehouse_cost_components.png', dpi=300)
    plt.close(fig)

    avg_util = utilization.groupby('warehouse_id', as_index=False)['utilization_percentage'].mean().sort_values('utilization_percentage', ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax.bar(avg_util['warehouse_id'], avg_util['utilization_percentage'], color='#59a14f')
    ax.set_title('Mean per-scenario utilization by warehouse (top 20 by utilization)')
    ax.set_xlabel('Warehouse')
    ax.set_ylabel('Mean allocated capacity (%)')
    ax.tick_params(axis='x', rotation=70)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'warehouse_utilization.png', dpi=300)
    plt.close(fig)

    allocated = results.groupby('warehouse_id', as_index=False)['allocated_quantity_quintal'].mean().sort_values('allocated_quantity_quintal', ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    ax.bar(allocated['warehouse_id'], allocated['allocated_quantity_quintal'], color='#e15759')
    ax.set_title('Mean MILP allocation by warehouse (top 20 by allocation)')
    ax.set_xlabel('Warehouse')
    ax.set_ylabel('Mean allocated quantity (quintal per scenario)')
    ax.tick_params(axis='x', rotation=70)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'warehouse_allocation_by_warehouse.png', dpi=300)
    plt.close(fig)

    for scenario_type, title, filename in (
        ('storage_cost_multiplier', 'Storage-cost multiplier sensitivity', 'warehouse_storage_sensitivity.png'),
        ('transport_cost_multiplier', 'Transport-cost multiplier sensitivity', 'warehouse_transport_sensitivity.png'),
    ):
        subset = sensitivity[sensitivity['scenario_type'].eq(scenario_type)].groupby(
            ['crop', 'scenario_multiplier'], as_index=False
        ).agg(mean_cost=('total_cost_inr', 'mean'), mean_allocated=('available_quantity_quintal', 'mean'), mean_unallocated=('unallocated_quantity_quintal', 'mean'))
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        for crop, group in subset.groupby('crop'):
            ax.plot(group['scenario_multiplier'], group['mean_cost'], marker='o', label=crop)
        ax.set_title(title)
        ax.set_xlabel('Configured scenario multiplier (x)')
        ax.set_ylabel('Mean storage + transport cost (INR per scenario)')
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
        fig.savefig(output / filename, dpi=300)
        plt.close(fig)


def _render_report(warehouse_path, sell_store_path, assumptions, origin, origin_note, scenarios, summaries, baselines, sensitivity, table_z, table_w):
    data = pd.read_csv(warehouse_path)
    status_counts = summaries['solver_status'].value_counts().to_dict()
    violation_total = int(summaries['constraint_violations'].sum())
    baseline_aggregate = baselines.groupby(['crop', 'method'], as_index=False).agg(
        mean_cost_inr=('total_cost_inr', 'mean'),
        mean_storage_cost_inr=('storage_cost_inr', 'mean'),
        mean_transport_cost_inr=('transport_cost_inr', 'mean'),
        mean_allocated_quintal=('allocated_quantity_quintal', 'mean'),
        mean_unallocated_quintal=('unallocated_quantity_quintal', 'mean'),
        mean_warehouses_used=('number_of_warehouses_used', 'mean'),
    )
    optimized_aggregate = summaries.groupby('crop', as_index=False, sort=True).agg(
        scenarios=('scenario_id', 'nunique'),
        mean_allocated_quintal=('total_allocated_quantity_quintal', 'mean'),
        mean_unallocated_quintal=('total_unallocated_quantity_quintal', 'mean'),
        mean_storage_cost_inr=('total_storage_cost_inr', 'mean'),
        mean_transport_cost_inr=('total_transport_cost_inr', 'mean'),
        mean_total_cost_inr=('total_cost_inr', 'mean'),
        max_constraint_violations=('constraint_violations', 'max'),
    )
    storage_sensitivity = sensitivity[sensitivity.scenario_type.eq('storage_cost_multiplier')].groupby(
        ['crop', 'scenario_multiplier'], as_index=False
    ).agg(mean_cost_inr=('total_cost_inr', 'mean'), mean_unallocated_quintal=('unallocated_quantity_quintal', 'mean')).to_string(index=False)
    transport_sensitivity = sensitivity[sensitivity.scenario_type.eq('transport_cost_multiplier')].groupby(
        ['crop', 'scenario_multiplier'], as_index=False
    ).agg(mean_cost_inr=('total_cost_inr', 'mean'), mean_unallocated_quintal=('unallocated_quantity_quintal', 'mean')).to_string(index=False)
    quantity_sensitivity = sensitivity[sensitivity.scenario_type.eq('available_quantity_multiplier')].groupby(
        ['crop', 'scenario_multiplier'], as_index=False
    ).agg(mean_cost_inr=('total_cost_inr', 'mean'), mean_unallocated_quintal=('unallocated_quantity_quintal', 'mean')).to_string(index=False)
    return f'''# Warehouse Allocation Validation Report

## OBSERVED DATA
- Warehouse file: `{Path(warehouse_path).name}` with {len(data)} unique facilities.
- These are values present in the supplied CSV; repository documentation does not establish whether facilities, capacities, rates, or support flags are verified operational observations. They are not represented here as independently validated real-world warehouse facts.
- Capacity is supplied as `Capacity_MT`; source values range {data.Capacity_MT.min():.1f} to {data.Capacity_MT.max():.1f} metric tonnes.
- Storage rate column: `Storage_Cost_per_MT`, values {data.Storage_Cost_per_MT.min():.2f} to {data.Storage_Cost_per_MT.max():.2f}. The source does not declare currency or billing period.
- Crop-support flags and facility coordinates are present. Support counts: {json.dumps({crop: int(data[f'{crop}_Supported'].sum()) for crop in ('Rice','Onion','Tomato')})}.
- Sell/store input: `{Path(sell_store_path).name}`. The evaluator takes one scenario per row matching the RMSE-selected model. These are simulated one-quintal quantities and not observed concurrent farmer demand.
- No farmer origin coordinates or acreage are available in this input.

## ASSUMPTIONS
```json
{json.dumps(assumptions, indent=2)}
```
- Explicit conversion: 1 metric tonne = 10 quintals; therefore capacity_quintal = Capacity_MT x 10 and rate INR/quintal/month = Storage_Cost_per_MT / 10.
- Storage rate is assumed to mean INR/metric-tonne/month for calculation, although the source column does not specify currency/time. Sell/store `storage_duration` supplies months.
- Transport rate uses the existing routing default 5.0 per km per metric tonne, interpreted as INR/km/MT as a configurable scenario assumption.
- Origin is {origin_note}; reference coordinate = ({origin[0]:.6f}, {origin[1]:.6f}). Distances are haversine straight-line proxies and are not road distances or farmer routes.
- A 1,000,000 INR/quintal shortage penalty is used only to keep the optimization feasible when supply cannot be assigned. It is not included in reported storage-plus-transport cost and is not an observed economic cost.

## SIMULATED VALUES
Each sell/store row is an independent what-if allocation case. A row's quantity is treated as available to store for warehouse analysis regardless of its sell/store action; this isolates warehouse allocation from the upstream economic decision. Aggregated tables average across independent historical cases and do not represent simultaneous network occupancy.

## MILP Formulation
For crop c and compatible warehouse j, continuous decision variable x[c,j] >= 0 is allocated quintals; u[c] >= 0 is unallocated quantity.

Minimize:
`sum_j x[c,j] * (storage_rate[c,j] * duration + distance[c,j] * transport_rate / 10) + shortage_penalty * u[c]`

Subject to:
- `sum_j x[c,j] + u[c] = available_quantity[c]`
- `x[c,j] <= capacity_quintal[j]`
- `x[c,j] = 0` for unsupported crop/warehouse pairs (implemented by omitting those variables)
- `x[c,j] >= 0`, `u[c] >= 0`

Transport rate is divided by 10 because the rate is per metric tonne and quantities are quintals. Solver: PuLP CBC. All {len(summaries)} base scenario solves returned statuses {json.dumps(status_counts)}. CBC reported `Optimal`; a separate numeric optimality gap is not exposed by this PuLP command. Independently recomputed cost/objective checks pass for zero-unallocated cases; the reported objective additionally includes the explicit shortage penalty when unallocated quantity is positive. Total cost columns report storage plus transport only.

## Metrics and Results
- Base selected-model allocation scenarios: {len(scenarios)}; crop/scenario summaries: {len(summaries)}.
- MILP constraint violation count across base scenarios: {violation_total}.
- Metrics include allocation, unallocated quantity, capacity utilization, storage and transport cost, total cost, average cost per allocated quintal, weighted straight-line distance, and warehouses used.
- Warehouse capacity constraints use per-scenario allocation, not sums across independent scenarios.

## OPTIMIZED VALUES
The following are solver-produced scenario means under the assumptions above, not observed costs or operational outcomes:

```text
{optimized_aggregate.to_string(index=False)}
```

### Baseline comparison (mean per scenario)
```text
{baseline_aggregate.to_string(index=False)}
```

## Baselines
- `Nearest Feasible`: greedily fill compatible warehouses in ascending straight-line distance.
- `Lowest Storage Cost`: greedily fill compatible warehouses by source storage rate; transport remains in reported cost but is not used to order this baseline.
- `Existing Method`: existing max-fill `allocate_storage` objective with crop-compatible warehouses prefiltered; it does not minimize economic cost.
- `MILP`: explicit storage-plus-transport cost minimization with the same scenario assumptions.

Methods are reported numerically without rank or winner labels.

## Sensitivity Analysis
These are scenario multipliers, not real-world probabilities.

### Storage cost multiplier
```text
{storage_sensitivity}
```

### Transport cost multiplier
```text
{transport_sensitivity}
```

### Available quantity multiplier
```text
{quantity_sensitivity}
```

## Paper Tables
### Table Z. Warehouse allocation outcomes (mean per independent scenario)
```text
{table_z.to_string(index=False)}
```

### Table W. Warehouse utilization (mean per independent scenario)
```text
{table_w.to_string(index=False)}
```

## Limitations
- Warehouse costs, units, and billing periods are incompletely documented. The assumed INR/MT/month interpretation must be validated before operational use.
- The upstream sell/store quantity is a synthetic 1-quintal scenario, not observed farmer demand; scenario totals are not concurrent loads.
- Farmer origins are unavailable. Centroid-origin haversine distances are reference proxies only; no road-routing optimization is claimed.
- Transport rate is a configurable assumed value, not a carrier quote. Permits, fuel surcharges, spoilage, and route fixed costs are not included.
- Compatible capacity is much larger than the simulated lots, so utilization values are very small and should not be interpreted as observed warehouse fill rates.
- The result is a feasible mathematical allocation under the stated assumptions, not evidence of real-world cost savings or warehouse efficiency improvement.
'''


def run_warehouse_research(
    sell_store_results,
    warehouse_dataset,
    output_dir='.',
    config_path='experiment_config.json',
    assumptions_path='warehouse_research_assumptions.json',
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    assumptions = json.loads(Path(assumptions_path).read_text(encoding='utf-8'))
    warehouse_data = _load_warehouse_data(warehouse_dataset)
    scenarios, selected = _load_scenarios(sell_store_results, config_path)
    origin_lat, origin_lon, origin_note = _reference_origin(warehouse_data, assumptions)
    origin = (origin_lat, origin_lon)

    result_rows = []
    summary_rows = []
    baseline_rows = []
    utilization_rows = []
    sensitivity = []
    for _, scenario in scenarios.iterrows():
        crop = str(scenario['crop'])
        duration = float(scenario['storage_duration'])
        quantity = float(scenario['quantity_quintal'])
        options = _options_for_crop(warehouse_data, crop, origin, assumptions, duration)
        summary, allocations, utilization, _ = _scenario_result(crop, scenario, warehouse_data, origin, assumptions)
        result_rows.extend(allocations)
        summary_rows.append(summary)
        utilization_rows.extend(utilization)
        baseline_rows.extend(_baseline_rows(crop, scenario, options, quantity, duration, assumptions))
        sensitivity.extend(_sensitivity_rows(crop, scenario, warehouse_data, origin, assumptions))

    results_df = pd.DataFrame(result_rows, columns=WAREHOUSE_RESULT_COLUMNS)
    summaries_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    baselines_df = pd.DataFrame(baseline_rows, columns=BASELINE_COLUMNS)
    utilization_df = pd.DataFrame(utilization_rows, columns=UTILIZATION_COLUMNS)
    sensitivity_df = pd.DataFrame(sensitivity, columns=SENSITIVITY_COLUMNS)
    table_z, table_w = _paper_tables(baselines_df, utilization_df)

    results_df.to_csv(output / 'warehouse_optimization_results.csv', index=False)
    summaries_df.to_csv(output / 'warehouse_summary.csv', index=False)
    baselines_df.to_csv(output / 'warehouse_baseline_comparison.csv', index=False)
    utilization_df.to_csv(output / 'warehouse_utilization.csv', index=False)
    sensitivity_df.to_csv(output / 'warehouse_sensitivity.csv', index=False)
    table_z.to_csv(output / 'table_z_warehouse_optimization.csv', index=False)
    table_w.to_csv(output / 'table_w_warehouse_utilization.csv', index=False)
    report = _render_report(
        warehouse_dataset, sell_store_results, assumptions, origin, origin_note,
        scenarios, summaries_df, baselines_df, sensitivity_df, table_z, table_w,
    )
    (output / 'warehouse_validation_report.md').write_text(report, encoding='utf-8')
    _write_figures(output, baselines_df, utilization_df, results_df, sensitivity_df)

    return {
        'results': results_df,
        'summary': summaries_df,
        'baselines': baselines_df,
        'utilization': utilization_df,
        'sensitivity': sensitivity_df,
        'table_z': table_z,
        'table_w': table_w,
        'selected_models': selected,
    }
