"""Scenario-based single-leg transport evaluation for saved warehouse allocations.

The available artifacts do not support an empirical farmer-to-market CVRP. This
module evaluates reference-origin-to-assigned-warehouse proxy routes only.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.routing import best_route


ROUTE_COLUMNS = [
    'crop', 'scenario_id', 'decision_date', 'horizon', 'model', 'warehouse_id',
    'origin_id', 'destination_id', 'origin_latitude', 'origin_longitude',
    'destination_latitude', 'destination_longitude', 'allocated_quantity_quintal',
    'allocated_quantity_metric_tonne', 'distance_km', 'distance_source',
    'route_sequence', 'routing_method', 'transport_rate_inr_per_km_per_metric_tonne',
    'transport_cost_inr', 'route_status', 'route_feasible', 'price_unit',
]
SUMMARY_COLUMNS = [
    'crop', 'scenario_id', 'decision_date', 'horizon', 'model', 'allocated_quantity_quintal',
    'unallocated_quantity_quintal', 'total_route_distance_km', 'average_route_distance_km',
    'total_transport_cost_inr', 'average_transport_cost_inr_per_quintal', 'number_of_routes',
    'route_feasibility', 'capacity_violations', 'demand_violations',
    'haversine_route_count', 'osrm_route_count', 'distance_source', 'price_unit',
    'routing_method',
]
BASELINE_COLUMNS = [
    'crop', 'scenario_id', 'model', 'horizon', 'method', 'total_distance_km',
    'average_distance_per_route_km', 'total_transport_cost_inr',
    'average_transport_cost_inr_per_quintal', 'allocated_quantity_quintal',
    'unserved_quantity_quintal', 'number_of_routes', 'route_feasible',
    'distance_source', 'routing_method', 'price_unit',
]
SENSITIVITY_COLUMNS = [
    'crop', 'scenario_id', 'model', 'decision_date', 'horizon', 'scenario_type',
    'scenario_multiplier', 'base_allocated_quantity_quintal',
    'quantity_transported_quintal', 'unserved_quantity_quintal', 'distance_km',
    'distance_source', 'transport_cost_inr', 'route_feasible', 'route_status',
    'price_unit',
]
END_TO_END_COLUMNS = [
    'crop', 'forecast_model', 'forecast_horizon', 'forecast_RMSE', 'forecast_MAE',
    'forecast_R2', 'sell_store_agreement_percentage', 'sell_store_mean_regret_inr',
    'warehouse_method', 'warehouse_storage_cost_inr', 'allocated_quantity_quintal',
    'unallocated_quantity_quintal', 'routing_method', 'distance_km',
    'transport_cost_inr', 'total_cost_inr', 'route_distance_source',
    'scenario_id', 'decision_date', 'metric_provenance', 'price_unit',
]


def haversine_km(origin_lat, origin_lon, destination_lat, destination_lon):
    """Independent spherical straight-line distance calculation in kilometres."""
    from math import atan2, cos, radians, sin, sqrt

    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, (origin_lat, origin_lon, destination_lat, destination_lon))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    haversine_term = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2.0 * earth_radius_km * atan2(sqrt(haversine_term), sqrt(1.0 - haversine_term))


def transport_cost_inr(distance_km, quantity_quintal, rate_inr_per_km_per_metric_tonne):
    """Convert quintals to metric tonnes explicitly and return total INR cost."""
    values = (distance_km, quantity_quintal, rate_inr_per_km_per_metric_tonne)
    if not all(np.isfinite(float(value)) for value in values):
        raise ValueError('Distance, quantity, and transport rate must be finite')
    if distance_km < 0 or quantity_quintal < 0 or rate_inr_per_km_per_metric_tonne < 0:
        raise ValueError('Distance, quantity, and transport rate must be nonnegative')
    quantity_metric_tonne = float(quantity_quintal) / 10.0
    return float(distance_km) * quantity_metric_tonne * float(rate_inr_per_km_per_metric_tonne)


def _load_inputs(warehouse_results_path, warehouse_summary_path, warehouse_dataset_path, warehouse_assumptions_path, routing_assumptions_path):
    allocations = pd.read_csv(warehouse_results_path)
    summaries = pd.read_csv(warehouse_summary_path)
    warehouses = pd.read_csv(warehouse_dataset_path)
    warehouse_assumptions = json.loads(Path(warehouse_assumptions_path).read_text(encoding='utf-8'))
    routing_assumptions = json.loads(Path(routing_assumptions_path).read_text(encoding='utf-8'))

    required_allocations = {
        'crop', 'scenario_id', 'decision_date', 'horizon', 'model', 'warehouse_id',
        'available_quantity_quintal', 'allocated_quantity_quintal', 'capacity_quintal',
        'distance_km', 'transport_cost_inr', 'price_unit',
    }
    missing = required_allocations - set(allocations.columns)
    if missing:
        raise ValueError(f'Warehouse allocation artifact missing fields: {sorted(missing)}')
    required_warehouses = {'Warehouse_ID', 'Latitude', 'Longitude', 'Capacity_MT', 'Rice_Supported', 'Onion_Supported', 'Tomato_Supported'}
    missing = required_warehouses - set(warehouses.columns)
    if missing:
        raise ValueError(f'Warehouse dataset missing fields: {sorted(missing)}')
    if warehouses['Warehouse_ID'].duplicated().any():
        raise ValueError('Warehouse_ID must be unique')
    if not allocations['price_unit'].eq('INR per quintal').all():
        raise ValueError('Warehouse allocation quantity must be labeled in quintals')
    if not np.isfinite(allocations[['allocated_quantity_quintal', 'distance_km', 'transport_cost_inr']].to_numpy(dtype=float)).all():
        raise ValueError('Warehouse allocation contains non-finite route inputs')
    if (allocations['allocated_quantity_quintal'] < 0).any():
        raise ValueError('Warehouse allocation contains negative quantities')
    required_summary = {
        'crop', 'scenario_id', 'model', 'decision_date', 'horizon',
        'total_available_quantity_quintal', 'total_allocated_quantity_quintal',
        'total_unallocated_quantity_quintal', 'constraint_violations',
    }
    missing_summary = required_summary - set(summaries.columns)
    if missing_summary:
        raise ValueError(f'Warehouse summary artifact missing fields: {sorted(missing_summary)}')
    if summaries['scenario_id'].duplicated().any():
        raise ValueError('Warehouse summary must contain one row per scenario')
    if set(allocations['scenario_id'].unique()) != set(summaries['scenario_id'].unique()):
        raise ValueError('Warehouse allocation and summary scenario IDs do not match')
    allocation_totals = allocations.groupby('scenario_id')['allocated_quantity_quintal'].sum().sort_index()
    summary_totals = summaries.set_index('scenario_id')['total_allocated_quantity_quintal'].sort_index()
    if not np.allclose(allocation_totals, summary_totals, rtol=0, atol=1e-6):
        raise ValueError('Warehouse allocation rows do not balance to the saved warehouse summary')
    rate = float(routing_assumptions['transport_rate_inr_per_km_per_metric_tonne'])
    warehouse_rate = float(warehouse_assumptions['transport_rate_inr_per_km_per_metric_tonne'])
    if not np.isclose(rate, warehouse_rate, rtol=0, atol=1e-12):
        raise ValueError('Routing and warehouse transport rate assumptions differ; refusing silent inconsistency')
    origin, origin_note = _resolve_origin(warehouses, warehouse_assumptions)
    return allocations, summaries, warehouses, warehouse_assumptions, routing_assumptions, origin, origin_note


def _resolve_origin(warehouses, assumptions):
    lat = assumptions.get('origin_override_latitude')
    lon = assumptions.get('origin_override_longitude')
    if (lat is None) != (lon is None):
        raise ValueError('Both reference-origin coordinate overrides are required together')
    if lat is not None:
        return (float(lat), float(lon)), 'configured reference origin; not observed farmer coordinates'
    origin = (float(warehouses['Latitude'].mean()), float(warehouses['Longitude'].mean()))
    return origin, 'warehouse coordinate centroid; synthetic reference proxy, not a farmer/customer location'


def _route_record(row, warehouse, origin, rate, distance_source='Haversine'):
    crop = str(row['crop'])
    support_column = f'{crop}_Supported'
    if support_column not in warehouse or int(warehouse[support_column]) != 1:
        raise ValueError(f'Warehouse {row["warehouse_id"]} is not marked compatible with {crop}')
    quantity = float(row['allocated_quantity_quintal'])
    capacity_q = float(warehouse['Capacity_MT']) * 10.0
    distance = haversine_km(origin[0], origin[1], float(warehouse['Latitude']), float(warehouse['Longitude']))
    if not np.isclose(distance, float(row['distance_km']), rtol=0, atol=1e-7):
        raise ValueError(f"Saved warehouse distance does not match independent Haversine check for {row['scenario_id']}")
    cost = transport_cost_inr(distance, quantity, rate)
    if not np.isclose(cost, float(row['transport_cost_inr']), rtol=1e-8, atol=1e-7):
        raise ValueError(f"Saved transport cost does not match routing recomputation for {row['scenario_id']}")
    feasible = quantity <= capacity_q + 1e-7
    return {
        'crop': crop,
        'scenario_id': row['scenario_id'],
        'decision_date': row['decision_date'],
        'horizon': int(row['horizon']),
        'model': row['model'],
        'warehouse_id': str(row['warehouse_id']),
        'origin_id': 'WAREHOUSE_CENTROID_REFERENCE',
        'destination_id': str(row['warehouse_id']),
        'origin_latitude': origin[0],
        'origin_longitude': origin[1],
        'destination_latitude': float(warehouse['Latitude']),
        'destination_longitude': float(warehouse['Longitude']),
        'allocated_quantity_quintal': quantity,
        'allocated_quantity_metric_tonne': quantity / 10.0,
        'distance_km': distance,
        'distance_source': distance_source,
        'route_sequence': 1,
        'routing_method': 'single_leg_reference_origin_to_warehouse',
        'transport_rate_inr_per_km_per_metric_tonne': rate,
        'transport_cost_inr': cost,
        'route_status': 'SCENARIO_PROXY_FEASIBLE' if feasible else 'CAPACITY_VIOLATION',
        'route_feasible': bool(feasible),
        'price_unit': 'INR per quintal',
    }


def _summary_rows(route_frame, warehouse_summaries):
    rows = []
    routes_grouped = {key: group for key, group in route_frame.groupby('scenario_id', sort=False)} if not route_frame.empty else {}
    for _, scenario in warehouse_summaries.iterrows():
        route_group = routes_grouped.get(scenario['scenario_id'], pd.DataFrame(columns=route_frame.columns))
        quantity = float(scenario['total_allocated_quantity_quintal'])
        route_count = len(route_group)
        total_distance = float(route_group['distance_km'].sum()) if route_count else 0.0
        total_cost = float(route_group['transport_cost_inr'].sum()) if route_count else 0.0
        distance_sources = route_group['distance_source'].value_counts().to_dict() if route_count else {}
        demand_violation = abs(
            float(scenario['total_allocated_quantity_quintal'])
            + float(scenario['total_unallocated_quantity_quintal'])
            - float(scenario['total_available_quantity_quintal'])
        ) > 1e-6
        feasible = (
            bool(route_group['route_feasible'].all())
            and float(scenario['total_unallocated_quantity_quintal']) <= 1e-8
            and int(scenario['constraint_violations']) == 0
        )
        rows.append({
            'crop': scenario['crop'],
            'scenario_id': scenario['scenario_id'],
            'decision_date': scenario['decision_date'],
            'horizon': int(scenario['horizon']),
            'model': scenario['model'],
            'allocated_quantity_quintal': quantity,
            'unallocated_quantity_quintal': float(scenario['total_unallocated_quantity_quintal']),
            'total_route_distance_km': total_distance,
            'average_route_distance_km': total_distance / route_count if route_count else 0.0,
            'total_transport_cost_inr': total_cost,
            'average_transport_cost_inr_per_quintal': total_cost / quantity if quantity > 0 else 0.0,
            'number_of_routes': route_count,
            'route_feasibility': feasible,
            'capacity_violations': int(scenario['constraint_violations']),
            'demand_violations': int(demand_violation),
            'haversine_route_count': int(distance_sources.get('Haversine', 0)),
            'osrm_route_count': int(distance_sources.get('OSRM', 0)),
            'distance_source': 'Haversine proxy only' if route_count else 'unavailable_no_positive_allocation',
            'price_unit': 'INR per quintal',
            'routing_method': 'single_leg_reference_origin_to_warehouse' if route_count else 'no_route_no_positive_allocation',
        })
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _nearest_feasible_records(scenario_row, warehouse_frame, origin, rate):
    crop = str(scenario_row['crop'])
    quantity = float(scenario_row['total_allocated_quantity_quintal'])
    support_column = f'{crop}_Supported'
    candidates = warehouse_frame.loc[warehouse_frame[support_column].eq(1)].copy()
    candidates['capacity_quintal'] = candidates['Capacity_MT'].astype(float) * 10.0
    candidates['distance_km'] = candidates.apply(
        lambda row: haversine_km(origin[0], origin[1], float(row['Latitude']), float(row['Longitude'])), axis=1
    )
    remaining = quantity
    assigned = []
    for _, warehouse in candidates.sort_values(['distance_km', 'Warehouse_ID']).iterrows():
        if remaining <= 1e-9:
            break
        amount = min(remaining, float(warehouse['capacity_quintal']))
        if amount <= 0:
            continue
        assigned.append((warehouse, amount))
        remaining -= amount
    distance_sum = 0.0
    cost_sum = 0.0
    for warehouse, amount in assigned:
        distance = float(warehouse['distance_km'])
        distance_sum += distance
        cost_sum += transport_cost_inr(distance, amount, rate)
    return {
        'total_distance_km': distance_sum,
        'total_transport_cost_inr': cost_sum,
        'allocated_quantity_quintal': quantity - max(0.0, remaining),
        'unserved_quantity_quintal': max(0.0, remaining),
        'number_of_routes': len(assigned),
        'route_feasible': remaining <= 1e-8,
        'distance_source': 'Haversine',
        'routing_method': 'nearest_feasible_warehouse_haversine',
    }


def _baseline_comparison(route_frame, warehouse_summaries, warehouse_frame, origin, rate):
    from src.routing import best_route

    routes_by_scenario = {key: group for key, group in route_frame.groupby('scenario_id', sort=False)} if not route_frame.empty else {}
    rows = []
    for _, scenario in warehouse_summaries.iterrows():
        sid = scenario['scenario_id']
        group = routes_by_scenario.get(sid, pd.DataFrame(columns=route_frame.columns))
        quantity = float(scenario['total_allocated_quantity_quintal'])
        # The saved warehouse MILP assignment is the proposed route destination.
        rows.append({
            'crop': scenario['crop'], 'scenario_id': sid, 'model': scenario['model'],
            'horizon': int(scenario['horizon']), 'method': 'Warehouse MILP allocation + Haversine',
            'total_distance_km': float(group.distance_km.sum()) if not group.empty else 0.0,
            'average_distance_per_route_km': float(group.distance_km.mean()) if not group.empty else 0.0,
            'total_transport_cost_inr': float(group.transport_cost_inr.sum()) if not group.empty else 0.0,
            'average_transport_cost_inr_per_quintal': float(group.transport_cost_inr.sum() / quantity) if quantity > 0 else 0.0,
            'allocated_quantity_quintal': quantity, 'unserved_quantity_quintal': float(scenario['total_unallocated_quantity_quintal']),
            'number_of_routes': len(group), 'route_feasible': bool(group.route_feasible.all()) if not group.empty else quantity == 0,
            'distance_source': 'Haversine', 'routing_method': 'saved_warehouse_milp_assignment', 'price_unit': 'INR per quintal',
        })
        nearest = _nearest_feasible_records(scenario, warehouse_frame, origin, rate)
        rows.append({
            'crop': scenario['crop'], 'scenario_id': sid, 'model': scenario['model'],
            'horizon': int(scenario['horizon']), 'method': 'Nearest feasible warehouse',
            'total_distance_km': nearest['total_distance_km'],
            'average_distance_per_route_km': nearest['total_distance_km'] / nearest['number_of_routes'] if nearest['number_of_routes'] else 0.0,
            'total_transport_cost_inr': nearest['total_transport_cost_inr'],
            'average_transport_cost_inr_per_quintal': nearest['total_transport_cost_inr'] / quantity if quantity else 0.0,
            'allocated_quantity_quintal': nearest['allocated_quantity_quintal'],
            'unserved_quantity_quintal': nearest['unserved_quantity_quintal'],
            'number_of_routes': nearest['number_of_routes'], 'route_feasible': nearest['route_feasible'],
            'distance_source': nearest['distance_source'], 'routing_method': nearest['routing_method'],
            'price_unit': 'INR per quintal',
        })
        legacy_cost = 0.0
        legacy_distance = 0.0
        legacy_routes = 0
        for route in group.itertuples(index=False):
            legacy = best_route(
                route.origin_latitude, route.origin_longitude,
                route.destination_latitude, route.destination_longitude,
                route.allocated_quantity_quintal * 100.0,
                offline_mode=True,
                cost_per_km_per_tonne=rate,
            )
            legacy_cost += float(legacy['estimated_cost'])
            legacy_distance += float(legacy['distance_km'])
            legacy_routes += 1
        rows.append({
            'crop': scenario['crop'], 'scenario_id': sid, 'model': scenario['model'],
            'horizon': int(scenario['horizon']), 'method': 'Legacy best_route offline formula',
            'total_distance_km': legacy_distance,
            'average_distance_per_route_km': legacy_distance / legacy_routes if legacy_routes else 0.0,
            'total_transport_cost_inr': legacy_cost,
            'average_transport_cost_inr_per_quintal': legacy_cost / quantity if quantity > 0 else 0.0,
            'allocated_quantity_quintal': quantity,
            'unserved_quantity_quintal': float(scenario['total_unallocated_quantity_quintal']),
            'number_of_routes': legacy_routes,
            'route_feasible': bool(group.route_feasible.all()) if not group.empty else quantity == 0,
            'distance_source': 'Haversine', 'routing_method': 'src.routing.best_route(offline_mode=True)',
            'price_unit': 'INR per quintal',
        })
    return pd.DataFrame(rows, columns=BASELINE_COLUMNS)


def _sensitivity(route_frame, warehouse_frame, assumptions):
    rows = []
    for route in route_frame.itertuples(index=False):
        warehouse = warehouse_frame.loc[warehouse_frame['Warehouse_ID'].astype(str).eq(str(route.warehouse_id))].iloc[0]
        base_quantity = float(route.allocated_quantity_quintal)
        capacity_q = float(warehouse['Capacity_MT']) * 10.0
        for kind, multiplier in (
            [('transport_cost_multiplier', value) for value in assumptions['sensitivity']['transport_cost_multipliers']]
            + [('available_quantity_multiplier', value) for value in assumptions['sensitivity']['available_quantity_multipliers']]
        ):
            requested = base_quantity * (multiplier if kind == 'available_quantity_multiplier' else 1.0)
            transported = min(requested, capacity_q)
            unserved = max(0.0, requested - transported)
            rate_multiplier = multiplier if kind == 'transport_cost_multiplier' else 1.0
            cost = transport_cost_inr(route.distance_km, transported, route.transport_rate_inr_per_km_per_metric_tonne * rate_multiplier)
            feasible = unserved <= 1e-8
            rows.append({
                'crop': route.crop, 'scenario_id': route.scenario_id, 'model': route.model,
                'decision_date': route.decision_date, 'horizon': int(route.horizon),
                'scenario_type': kind, 'scenario_multiplier': float(multiplier),
                'base_allocated_quantity_quintal': base_quantity,
                'quantity_transported_quintal': transported, 'unserved_quantity_quintal': unserved,
                'distance_km': float(route.distance_km), 'distance_source': route.distance_source,
                'transport_cost_inr': cost, 'route_feasible': bool(feasible),
                'route_status': 'SCENARIO_PROXY_FEASIBLE' if feasible else 'CAPACITY_EXCEEDED',
                'price_unit': 'INR per quintal',
            })
    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


def _end_to_end_table(routing_summary, warehouse_summaries, sell_store_summary_path, horizon_metrics_path, fold_metrics_path, predictions_path):
    sell_store_summary = pd.read_csv(sell_store_summary_path)
    horizon_metrics = pd.read_csv(horizon_metrics_path)
    fold_metrics = pd.read_csv(fold_metrics_path)
    forecast_predictions = pd.read_csv(predictions_path)
    forecast_fold_lookup = forecast_predictions[['crop', 'model', 'fold', 'train_end']].drop_duplicates()
    forecast_fold_lookup['decision_date'] = pd.to_datetime(forecast_fold_lookup['train_end']).dt.strftime('%Y-%m-%d')
    horizon_fold = routing_summary.merge(
        forecast_fold_lookup,
        on=['crop', 'model', 'decision_date'],
        how='left',
    )
    horizon_fold = horizon_fold.merge(
        horizon_metrics[['crop', 'model', 'horizon', 'RMSE', 'MAE']],
        on=['crop', 'model', 'horizon'], how='left',
    )
    horizon_fold = horizon_fold.merge(
        fold_metrics[['crop', 'model', 'fold', 'R2']],
        on=['crop', 'model', 'fold'], how='left',
    )
    horizon_fold = horizon_fold.merge(
        sell_store_summary[['crop', 'model', 'horizon', 'decision_agreement_percentage', 'mean_regret_inr']],
        on=['crop', 'model', 'horizon'], how='left',
    )
    horizon_fold = horizon_fold.merge(
        warehouse_summaries[['scenario_id', 'total_storage_cost_inr', 'total_unallocated_quantity_quintal']],
        on='scenario_id', how='left',
    )
    # Forecast RMSE/MAE are horizon-level aggregates; R2 is the matching fold's complete-vector R2.
    horizon_fold['warehouse_method'] = 'MILP'
    horizon_fold['forecast_model'] = horizon_fold['model']
    horizon_fold['warehouse_storage_cost_inr'] = horizon_fold['total_storage_cost_inr']
    horizon_fold['total_cost_inr'] = horizon_fold['warehouse_storage_cost_inr'] + horizon_fold['total_transport_cost_inr']
    horizon_fold['route_distance_source'] = horizon_fold['distance_source']
    horizon_fold['metric_provenance'] = 'forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv'
    table = horizon_fold.rename(columns={
        'horizon': 'forecast_horizon',
        'RMSE': 'forecast_RMSE',
        'MAE': 'forecast_MAE',
        'R2': 'forecast_R2',
        'decision_agreement_percentage': 'sell_store_agreement_percentage',
        'mean_regret_inr': 'sell_store_mean_regret_inr',
        'total_route_distance_km': 'distance_km',
        'total_transport_cost_inr': 'transport_cost_inr',
    })
    return table.reindex(columns=END_TO_END_COLUMNS)


def _write_figures(output, baseline_comparison, route_summary, sensitivity):
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    baseline_comparison.groupby(['crop', 'method'])['total_transport_cost_inr'].mean().unstack().plot(kind='bar', ax=ax)
    ax.set_title('Scenario transport cost by crop and route method')
    ax.set_xlabel('Crop')
    ax.set_ylabel('Mean transport cost (INR per scenario)')
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'routing_cost_by_crop.png', dpi=300)
    plt.close(fig)

    distance = baseline_comparison.groupby(['crop', 'method'])['total_distance_km'].mean().unstack()
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    distance.plot(kind='bar', ax=ax)
    ax.set_title('Straight-line proxy distance by crop and method')
    ax.set_xlabel('Crop')
    ax.set_ylabel('Distance (km; Haversine proxy)')
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'routing_distance_comparison.png', dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
    ax.scatter(route_summary['total_route_distance_km'], route_summary['total_transport_cost_inr'], alpha=0.7)
    ax.set_title('Scenario distance and transport cost')
    ax.set_xlabel('Total single-leg proxy distance (km)')
    ax.set_ylabel('Transport cost (INR)')
    ax.grid(alpha=0.25)
    fig.savefig(output / 'routing_cost_components.png', dpi=300)
    plt.close(fig)

    method_cost = baseline_comparison.groupby('method')['average_transport_cost_inr_per_quintal'].mean().sort_index()
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    method_cost.plot(kind='bar', ax=ax, color='#4e79a7')
    ax.set_title('Mean scenario transport cost per quintal by method')
    ax.set_xlabel('Routing method')
    ax.set_ylabel('INR/quintal')
    ax.tick_params(axis='x', rotation=20)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output / 'routing_method_comparison.png', dpi=300)
    plt.close(fig)

    for scenario_type, title, filename in (
        ('transport_cost_multiplier', 'Transport-rate sensitivity', 'routing_transport_sensitivity.png'),
        ('available_quantity_multiplier', 'Available-quantity sensitivity', 'routing_quantity_sensitivity.png'),
    ):
        data = sensitivity[sensitivity.scenario_type.eq(scenario_type)].groupby(
            ['crop', 'scenario_multiplier'], as_index=False
        ).agg(mean_cost=('transport_cost_inr', 'mean'), mean_unserved=('unserved_quantity_quintal', 'mean'))
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        for crop, group in data.groupby('crop'):
            ax.plot(group['scenario_multiplier'], group['mean_cost'], marker='o', label=crop)
        ax.set_title(title)
        ax.set_xlabel('Scenario multiplier (x)')
        ax.set_ylabel('Mean transport cost (INR per scenario)')
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
        fig.savefig(output / filename, dpi=300)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for ax, scenario_type, title in (
        (axes[0], 'transport_cost_multiplier', 'Transport-rate multiplier'),
        (axes[1], 'available_quantity_multiplier', 'Available-quantity multiplier'),
    ):
        subset = sensitivity[sensitivity.scenario_type.eq(scenario_type)].groupby(
            ['crop', 'scenario_multiplier'], as_index=False
        ).agg(mean_cost=('transport_cost_inr', 'mean'))
        for crop, group in subset.groupby('crop'):
            ax.plot(group['scenario_multiplier'], group['mean_cost'], marker='o', label=crop)
        ax.set_title(title)
        ax.set_xlabel('Scenario multiplier (x)')
        ax.set_ylabel('Mean transport cost (INR per scenario)')
        ax.grid(alpha=0.25)
    axes[1].legend(frameon=False)
    fig.suptitle('Scenario-based transport sensitivity')
    fig.savefig(output / 'routing_sensitivity.png', dpi=300)
    plt.close(fig)


def _render_report(route_summary, baselines, sensitivity, assumptions, origin, origin_note, end_to_end):
    baseline_text = baselines.groupby(['crop', 'method'], as_index=False).agg(
        scenarios=('scenario_id', 'nunique'),
        mean_distance_km=('total_distance_km', 'mean'),
        mean_transport_cost_inr=('total_transport_cost_inr', 'mean'),
        mean_cost_per_quintal=('average_transport_cost_inr_per_quintal', 'mean'),
        feasible_scenarios=('route_feasible', 'sum'),
    ).to_string(index=False)
    transport_sensitivity = sensitivity[sensitivity.scenario_type.eq('transport_cost_multiplier')].groupby(
        ['crop', 'scenario_multiplier'], as_index=False
    ).agg(mean_cost_inr=('transport_cost_inr', 'mean'), mean_unserved_quintal=('unserved_quantity_quintal', 'mean')).to_string(index=False)
    quantity_sensitivity = sensitivity[sensitivity.scenario_type.eq('available_quantity_multiplier')].groupby(
        ['crop', 'scenario_multiplier'], as_index=False
    ).agg(mean_cost_inr=('transport_cost_inr', 'mean'), mean_unserved_quintal=('unserved_quantity_quintal', 'mean')).to_string(index=False)
    return f'''# Routing Research Validation Report

## OBJECTIVE
Quantify single-leg transport distance and cost from saved warehouse allocations under a stated reference-origin scenario. This is a scenario-based transport routing evaluation, not a farmer route study or a CVRP.

## DATA SOURCES
- Warehouse destination coordinates and compatibility: supplied warehouse dataset; provenance is not independently verified.
- Scenario allocation and quantity: protected `warehouse_optimization_results.csv` and `warehouse_summary.csv`.
- Upstream validated selected model and decision metadata: `sell_store_decisions.csv` and `experiment_config.json`.
- Routing origin: {origin_note}, coordinate ({origin[0]:.6f}, {origin[1]:.6f}).

## OBSERVED / SUPPLIED DATA
Available per route scenario are crop, scenario ID, decision date, horizon, selected model, allocated quantity, warehouse ID, warehouse coordinates, and the warehouse evaluator's Haversine distance. No actual farmer origin, market/customer destination, customer demand, vehicle fleet/capacity, time windows, or observed route logs are supplied. These are not inferred.

## ASSUMPTIONS
```json
{json.dumps(assumptions, indent=2)}
```
The transport rate is a configurable INR/km/MT scenario assumption, not a carrier quote. 1 quintal is converted to 0.1 metric tonne. The route source is Haversine straight-line distance in km, not road distance. OSRM was not queried because the origin is a synthetic centroid rather than an observed traveler origin.

## SIMULATED VALUES
Each saved warehouse allocation is evaluated as one independent single-leg reference-origin-to-warehouse scenario. Scenario quantities and distances are not observed farmer trips. No vehicle count, travel time, route sequence, or time-window metric is reported because the required data is absent.

## OPTIMIZED VALUES
The warehouse destination is the already selected MILP allocation. The routing evaluator does not change warehouse assignments and does not rewrite warehouse outputs. It independently recomputes the Haversine length and quantity-based transport cost for each allocated warehouse line.

## ROUTING / VRP FORMULATION
This is not a CVRP or multi-vehicle VRP. It is a single-leg cost calculation:
`transport_cost_inr = distance_km * (quantity_quintal / 10) * assumed_transport_rate_inr_per_km_per_metric_tonne`
Each selected warehouse has one direct proxy leg from `WAREHOUSE_CENTROID_REFERENCE` to the supplied warehouse coordinates. There are no intermediate nodes, routing decisions, vehicle capacities, multiple vehicles, customer demands, or time windows in the data.

## BASELINES
- `Warehouse MILP allocation + Haversine`: saved assigned warehouse and saved allocation quantity, with independent distance/cost recomputation.
- `Nearest feasible warehouse`: nearest crop-compatible facility with enough capacity; split to further feasible facilities only if needed.
- `Legacy best_route offline formula`: existing single-leg `best_route` with offline mode, which uses Haversine and the same configured base transport rate.

```text
{baseline_text}
```
No OSRM comparison is reported because actual origin coordinates are unavailable and OSRM results on a synthetic centroid would not be empirical road-route evidence.

## RESULTS
```text
{route_summary.to_string(index=False)}
```
The end-to-end table links existing forecast, sell/store, warehouse, and routing summaries by crop/model/horizon/scenario without retraining or rewriting upstream artifacts.

## SENSITIVITY ANALYSIS
These are configured scenarios, not probability distributions or observed rates.

### Transport rate multipliers
```text
{transport_sensitivity}
```

### Allocated quantity multipliers
```text
{quantity_sensitivity}
```

## VALIDATION
- Saved warehouse allocation IDs and crop compatibility are checked.
- Haversine distances are independently recomputed from source coordinates and compared with the protected warehouse distances.
- Transport costs are independently recomputed and compared with the protected warehouse cost values.
- Route quantities are nonnegative and cannot exceed the selected warehouse capacity.
- Deterministic sensitivity outputs are independently recomputed in the verification script.
- Upstream forecasting, sell/store, and warehouse outputs are read-only inputs to this run.

## LIMITATIONS
- No genuine CVRP can be supported: origins, multiple demand nodes, vehicles, vehicle capacities, time windows, and observed routes are absent.
- The origin is synthetic, so Haversine distances are only reference proxies; no actual farmer route or road-distance claim is made.
- Supplied warehouse coordinates and capacities are not independently verified operational data.
- Transport rates are assumed and no carrier quotes, tolls, fuel surcharges, or driver costs are available.
- The evaluation only covers existing positive warehouse allocations and does not optimize route sequences or alter the allocation.

## REPRODUCIBILITY
Run the existing pipeline in isolated research mode with `--routing-research`, providing the saved warehouse-results CSV, warehouse dataset, and routing assumptions. Forecast, sell/store, and warehouse optimization artifacts remain unchanged.

## NO-OVERCLAIM STATEMENT
Results quantify transport costs under configured scenario assumptions only. They do not demonstrate real-world route optimality, farmer savings, warehouse efficiency, or causal income effects.
'''


def run_routing_research(
    warehouse_results_path,
    warehouse_summary_path,
    warehouse_dataset_path,
    sell_store_results_path='sell_store_decisions.csv',
    warehouse_assumptions_path='warehouse_research_assumptions.json',
    routing_assumptions_path='routing_research_assumptions.json',
    forecast_horizon_metrics_path='forecast_horizon_metrics.csv',
    forecast_fold_metrics_path='forecast_fold_metrics.csv',
    forecast_predictions_path='forecast_predictions.csv',
    sell_store_summary_path='sell_store_summary.csv',
    output_dir='.',
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    allocations, warehouse_summaries, warehouses, warehouse_assumptions, routing_assumptions, origin, origin_note = _load_inputs(
        warehouse_results_path, warehouse_summary_path, warehouse_dataset_path,
        warehouse_assumptions_path, routing_assumptions_path,
    )
    warehouse_lookup = warehouses.set_index(warehouses['Warehouse_ID'].astype(str), drop=False).to_dict('index')
    positive_allocations = allocations.loc[allocations['allocated_quantity_quintal'] > 1e-9].copy()
    route_rows = []
    for _, row in positive_allocations.iterrows():
        warehouse_id = str(row['warehouse_id'])
        if warehouse_id not in warehouse_lookup:
            raise ValueError(f'Allocated warehouse {warehouse_id} is missing from warehouse source data')
        route_rows.append(_route_record(
            row, warehouse_lookup[warehouse_id], origin,
            float(routing_assumptions['transport_rate_inr_per_km_per_metric_tonne']),
        ))
    routes_df = pd.DataFrame(route_rows, columns=ROUTE_COLUMNS)
    route_summary = _summary_rows(routes_df, warehouse_summaries)
    baselines_df = _baseline_comparison(routes_df, warehouse_summaries, warehouses, origin, float(routing_assumptions['transport_rate_inr_per_km_per_metric_tonne']))
    sensitivity_df = _sensitivity(routes_df, warehouses, routing_assumptions)
    end_to_end = _end_to_end_table(
        route_summary, warehouse_summaries, sell_store_summary_path,
        forecast_horizon_metrics_path,
        forecast_fold_metrics_path, forecast_predictions_path,
    )

    routes_df.to_csv(output / 'routing_routes.csv', index=False)
    routes_df.to_csv(output / 'routing_results.csv', index=False)
    route_summary.to_csv(output / 'routing_summary.csv', index=False)
    baselines_df.to_csv(output / 'routing_baseline_comparison.csv', index=False)
    sensitivity_df.to_csv(output / 'routing_sensitivity.csv', index=False)
    table_r = baselines_df.groupby(['crop', 'method'], as_index=False, sort=True).agg(
        total_routes=('number_of_routes', 'sum'),
        total_distance_km=('total_distance_km', 'sum'),
        total_transport_cost_inr=('total_transport_cost_inr', 'sum'),
        mean_cost_per_quintal=('average_transport_cost_inr_per_quintal', 'mean'),
        feasible_scenarios=('route_feasible', 'sum'),
    )
    table_s = baselines_df.groupby(['crop', 'method'], as_index=False, sort=True).agg(
        allocated_quantity_quintal=('allocated_quantity_quintal', 'sum'),
        total_distance_km=('total_distance_km', 'sum'),
        total_transport_cost_inr=('total_transport_cost_inr', 'sum'),
        average_transport_cost_inr_per_quintal=('average_transport_cost_inr_per_quintal', 'mean'),
        distance_source=('distance_source', 'first'),
    )
    table_r.to_csv(output / 'table_r_routing_performance.csv', index=False)
    table_s.to_csv(output / 'table_s_transport_comparison.csv', index=False)
    end_to_end.to_csv(output / 'table_end_to_end_pipeline.csv', index=False)
    report = _render_report(route_summary, baselines_df, sensitivity_df, routing_assumptions, origin, origin_note, end_to_end)
    (output / 'routing_validation_report.md').write_text(report, encoding='utf-8')
    _write_figures(output, baselines_df, route_summary, sensitivity_df)

    phase_reports = []
    for report_path in (
        'forecast_final_validation_report.md',
        'sell_store_validation_report.md',
        'warehouse_validation_report.md',
    ):
        path = Path(report_path)
        if path.exists():
            phase_reports.append(f'## {path.name}\n\n{path.read_text(encoding="utf-8")}')
    end_report = f'''# ADIS End-to-End Research Report

This report consolidates existing forecasting, retrospective sell/store, warehouse allocation, and scenario-based routing evaluations. It does not retrain models or regenerate upstream research calculations.

## Routing classification
The available data supports scenario-based single-leg reference-origin-to-warehouse transport evaluation only. It does not support a genuine CVRP or actual farmer-route analysis.

## Consolidated scenario table
```text
{end_to_end.to_string(index=False)}
```

## Routing evidence
{report}

## Phase reports
{chr(10).join(phase_reports)}

## Limitations and no-overclaim statement
Forecast, sell/store, and warehouse outputs are treated as supplied research artifacts and are not rewritten. Warehouse and origin provenance, cost assumptions, and transport rate limitations remain as stated in those phase reports. No real-world farmer savings, actual road-route optimality, or causal income claims are made.
'''
    (output / 'END_TO_END_RESEARCH_REPORT.md').write_text(end_report, encoding='utf-8')

    return {
        'routes': routes_df,
        'summary': route_summary,
        'baselines': baselines_df,
        'sensitivity': sensitivity_df,
        'end_to_end': end_to_end,
        'selected_route_count': len(routes_df),
        'origin': origin,
        'origin_note': origin_note,
    }
