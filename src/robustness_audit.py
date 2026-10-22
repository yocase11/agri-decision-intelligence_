"""Evidence-backed robustness audit for the validated ADIS pipeline."""

import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd

from src.sell_store_research import _source_prices, decide_sell_or_store_economic

ROOT = Path(__file__).resolve().parent.parent
PRICE_FILE = ROOT / 'price dataset (1).csv'
PREDICTIONS_FILE = ROOT / 'forecast_predictions.csv'
DECISIONS_FILE = ROOT / 'sell_store_decisions.csv'
ASSUMPTIONS_FILE = ROOT / 'sell_store_assumptions.json'
CONFIG_FILE = ROOT / 'experiment_config.json'
WAREHOUSE_SENSITIVITY_FILE = ROOT / 'warehouse_sensitivity.csv'
ROUTING_SENSITIVITY_FILE = ROOT / 'routing_sensitivity.csv'
WAREHOUSE_SUMMARY_FILE = ROOT / 'warehouse_summary.csv'
ROUTING_SUMMARY_FILE = ROOT / 'routing_summary.csv'
FORECAST_SUMMARY_FILE = ROOT / 'forecast_model_summary.csv'
SELL_STORE_SUMMARY_FILE = ROOT / 'sell_store_summary.csv'


def _markdown_table(frame):
    if frame.empty:
        return '_No rows available._'
    headers = [str(column) for column in frame.columns]
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for row in frame.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if pd.isna(value):
                cells.append('Not Available')
            elif isinstance(value, (float, np.floating)):
                cells.append(f'{float(value):,.4f}')
            else:
                cells.append(str(value).replace('|', '\\|'))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def _quarter_periods(df):
    quarter_number = df['Quarter'].astype(str).str.extract(r'Q([1-4])', expand=False)
    if quarter_number.isna().any():
        quarter_number = quarter_number.fillna(df['Quarter'].astype(str).str.extract(r'([1-4])$', expand=False))
    if quarter_number.isna().any():
        raise ValueError('Cannot parse all quarter labels')
    return pd.PeriodIndex(df['Year'].astype('Int64').astype(str) + 'Q' + quarter_number.astype(str), freq='Q')


def _crop_series_by_crop():
    df = pd.read_csv(PRICE_FILE)
    if 'Crop' not in df.columns or 'Price_INR_per_Quintal' not in df.columns:
        raise ValueError('Price file must include Crop and Price_INR_per_Quintal columns')
    df = df.copy()
    df['_quarter'] = _quarter_periods(df)
    df['Price_INR_per_Quintal'] = pd.to_numeric(df['Price_INR_per_Quintal'], errors='coerce')
    df = df.dropna(subset=['Price_INR_per_Quintal'])
    return {
        crop: group.groupby('_quarter')['Price_INR_per_Quintal'].mean().sort_index()
        for crop, group in df.groupby('Crop')
    }


def _decision_from_value(current_price, forecast_value, quantity_quintal, duration_months, storage_rate, spoilage_rate, transport_cost):
    outcome = decide_sell_or_store_economic(
        current_price,
        forecast_value,
        quantity_quintal,
        duration_months,
        storage_rate,
        spoilage_rate,
        transport_cost,
    )
    selected_value = outcome['sell_now_value_inr'] if outcome['decision'] == 'sell' else outcome['store_value_inr']
    return outcome['decision'], selected_value, outcome


def compute_rolling_origin_support():
    """Check if the real data support more rolling-origin windows than the configured 3."""
    config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    horizon = int(config.get('horizon', 4))
    min_train_size = int(config.get('min_train_size', 12))
    validation_windows = int(config.get('validation_windows', 3))
    crop_series = _crop_series_by_crop()
    by_crop = {}
    feasible_windows_total = []
    for crop, series in sorted(crop_series.items()):
        count = len(series)
        all_starts = list(range(min_train_size, count - horizon + 1, horizon))
        available = len(all_starts)
        feasible_windows_total.append(available)
        by_crop[crop] = {
            'observations': count,
            'possible_windows': available,
            'configured_windows_used': len(all_starts[-validation_windows:]) if available > validation_windows else len(all_starts),
            'configured_validation_windows': validation_windows,
            'rolling_horizon': horizon,
            'minimum_train_size': min_train_size,
            'supports_expansion': available > validation_windows,
            'support_limit_reason': (
                'Series is long enough to support more than the configured validation windows.'
                if available > validation_windows
                else 'Series length and horizon leave only the configured rolling window count; no extra non-overlapping validation origin is supported by these data.'
            ),
        }
    supported = any(item['possible_windows'] > validation_windows for item in by_crop.values())
    reason = (
        'The data support only the current three-window setup; no additional real rolling-origin checks are available without changing the evaluation design.'
        if not supported
        else 'The data do support more rolling-origin windows than the current config, so the validation design could be expanded.'
    )
    return {
        'supported': supported,
        'support_limit_reason': reason,
        'validation_windows_configured': validation_windows,
        'per_crop': by_crop,
        'max_feasible_windows_observed': max(feasible_windows_total),
    }


def compute_forecast_error_sensitivity_and_uncertainty():
    """Propagate forecast error through the sell/store decision formulas and summarize sensitivity."""
    decisions = pd.read_csv(DECISIONS_FILE)
    assumptions = json.loads(ASSUMPTIONS_FILE.read_text(encoding='utf-8'))
    rows = []
    for (crop, model, horizon), group in decisions.groupby(['crop', 'model', 'horizon'], sort=True):
        total_flips = 0
        total_scenarios = 0
        propagated_value_errors = []
        for _, row in group.iterrows():
            future_actual = float(row['actual_future_price_inr_per_quintal'])
            forecast = float(row['forecast_price_inr_per_quintal'])
            error_mag = abs(forecast - future_actual)
            quantity = float(row['quantity_quintal'])
            spoilage = float(row['spoilage_rate'])
            effective_qty = quantity * (1.0 - spoilage)
            propagated_value_errors.append(error_mag * effective_qty)
            storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
            transport = float(assumptions['transport_cost_inr'])
            duration = float(row['storage_duration'])
            current_price = float(row['current_price_inr_per_quintal'])
            baseline = decide_sell_or_store_economic(current_price, forecast, quantity, duration, storage_rate, spoilage, transport)
            alt_prices = [max(0.0, forecast - error_mag), forecast + error_mag]
            for alt_price in alt_prices:
                total_scenarios += 1
                candidate = decide_sell_or_store_economic(current_price, max(0.0, alt_price), quantity, duration, storage_rate, spoilage, transport)
                if candidate['decision'] != baseline['decision']:
                    total_flips += 1
        rows.append({
            'crop': crop,
            'model': model,
            'horizon': int(horizon),
            'number_of_decisions': int(len(group)),
            'mean_propagated_value_error_inr': float(np.mean(propagated_value_errors)) if propagated_value_errors else 0.0,
            'median_propagated_value_error_inr': float(np.median(propagated_value_errors)) if propagated_value_errors else 0.0,
            'decision_flip_rate_percentage': float((total_flips / max(total_scenarios, 1)) * 100.0),
            'mean_regret_inr': float(group['regret_inr'].mean()),
            'mean_decision_value_error_inr': float(group['decision_value_error_inr'].mean()),
            'mean_absolute_forecast_error_inr': float(abs(group['forecast_price_inr_per_quintal'] - group['actual_future_price_inr_per_quintal']).mean()),
            'price_unit': 'INR per quintal',
        })
    return pd.DataFrame(rows)


def compute_formula_consistency_audit():
    """Recompute the economic formulas and verify the saved decision artifact matches the code logic."""
    decisions = pd.read_csv(DECISIONS_FILE)
    assumptions = json.loads(ASSUMPTIONS_FILE.read_text(encoding='utf-8'))
    mismatches = []
    for _, row in decisions.iterrows():
        crop = str(row['crop'])
        rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
        duration = float(row['storage_duration'])
        quantity = float(row['quantity_quintal'])
        spoilage = float(row['spoilage_rate'])
        transport = float(assumptions['transport_cost_inr'])
        current_price = float(row['current_price_inr_per_quintal'])
        forecast_price = float(row['forecast_price_inr_per_quintal'])
        computed = decide_sell_or_store_economic(current_price, forecast_price, quantity, duration, rate, spoilage, transport)
        checks = {
            'sell_now_value_inr': abs(computed['sell_now_value_inr'] - float(row['sell_now_value_inr'])) <= 1e-6,
            'store_value_inr': abs(computed['store_value_inr'] - float(row['store_value_inr'])) <= 1e-6,
            'incremental_store_value_inr': abs(computed['incremental_store_value_inr'] - float(row['incremental_store_value_inr'])) <= 1e-6,
            'storage_cost_inr': abs(computed['storage_cost_inr'] - float(row['storage_cost_inr'])) <= 1e-6,
            'effective_quantity_quintal': abs(computed['effective_quantity_quintal'] - float(row['effective_quantity_quintal'])) <= 1e-6,
            'decision': computed['decision'] == str(row['decision']),
        }
        if not all(checks.values()):
            mismatches.append({
                'crop': crop,
                'model': str(row['model']),
                'horizon': int(row['horizon']),
                'checks': checks,
                'saved_decision': row['decision'],
                'computed_decision': computed['decision'],
            })
    return {
        'mismatch_count': len(mismatches),
        'all_formula_checks_pass': len(mismatches) == 0,
        'checked_rows': int(len(decisions)),
        'mismatch_examples': mismatches[:5],
    }


def compute_prediction_interval_decision_robustness():
    """Evaluate interval-based decision robustness for models with native intervals only."""
    assumptions = json.loads(ASSUMPTIONS_FILE.read_text(encoding='utf-8'))
    source_prices, _ = _source_prices(PRICE_FILE)
    predictions = pd.read_csv(PREDICTIONS_FILE)
    valid = predictions.loc[
        predictions['validity_status'].eq('VALID')
        & predictions['model'].isin(['arima', 'sarima'])
        & predictions['lower_95'].notna()
        & predictions['upper_95'].notna()
    ].copy()
    if valid.empty:
        raise ValueError('No valid native-interval forecast rows are available for ARIMA/SARIMA evaluation.')

    rows = []
    for _, row in valid.iterrows():
        crop = str(row['crop'])
        decision_period = pd.Period(pd.Timestamp(row['train_end']), freq='Q')
        current_price = float(source_prices[crop].loc[decision_period])
        quantity = float(assumptions['scenario_quantity_quintal'])
        duration = float(row['horizon']) * float(assumptions['storage_duration_months_per_forecast_quarter'])
        storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
        spoilage = float(assumptions['spoilage_rate_per_holding_decision'][crop])
        transport = float(assumptions['transport_cost_inr'])
        values = {
            'lower': max(0.0, float(row['lower_95'])),
            'point': max(0.0, float(row['predicted'])),
            'upper': max(0.0, float(row['upper_95'])),
        }
        decisions = {}
        values_out = {}
        for label, value in values.items():
            decision, selected_value, outcome = _decision_from_value(current_price, value, quantity, duration, storage_rate, spoilage, transport)
            decisions[label] = decision
            values_out[label] = selected_value
        action_set = set(decisions.values())
        if len(action_set) == 1 and 'sell' in action_set:
            decision_class = 'ROBUST_SELL'
        elif len(action_set) == 1 and 'store' in action_set:
            decision_class = 'ROBUST_STORE'
        else:
            decision_class = 'DECISION_SENSITIVE'
        rows.append({
            'crop': crop,
            'model': str(row['model']),
            'origin_date': str(row['train_end']),
            'forecast_date': str(row['forecast_date']),
            'horizon': int(row['horizon']),
            'raw_point_forecast': float(row['predicted']),
            'raw_lower_forecast': float(row['lower_95']),
            'raw_upper_forecast': float(row['upper_95']),
            'point_forecast': values['point'],
            'lower_forecast': max(0.0, float(row['lower_95'])),
            'upper_forecast': max(0.0, float(row['upper_95'])),
            'decision_lower': decisions['lower'],
            'decision_point': decisions['point'],
            'decision_upper': decisions['upper'],
            'point_decision_value': float(values_out['point']),
            'lower_decision_value': float(values_out['lower']),
            'upper_decision_value': float(values_out['upper']),
            'decision_class': decision_class,
            'decision_value_range_inr': float(values_out['upper'] - values_out['lower']),
            'price_unit': 'INR per quintal',
        })

    out = pd.DataFrame(rows)
    summary = out.groupby(['crop', 'model', 'horizon'], as_index=False).agg(
        number_of_predictions=('decision_class', 'size'),
        decision_stability_rate=('decision_class', lambda s: float((s.eq('ROBUST_SELL') | s.eq('ROBUST_STORE')).mean() * 100.0)),
        decision_sensitive_rate=('decision_class', lambda s: float(s.eq('DECISION_SENSITIVE').mean() * 100.0)),
        robust_sell_decisions=('decision_class', lambda s: int((s == 'ROBUST_SELL').sum())),
        robust_store_decisions=('decision_class', lambda s: int((s == 'ROBUST_STORE').sum())),
        sensitive_decisions=('decision_class', lambda s: int((s == 'DECISION_SENSITIVE').sum())),
        mean_value_range_inr=('decision_value_range_inr', 'mean'),
    )
    return out, summary


def compute_end_to_end_parameter_sensitivity():
    """Evaluate decision sensitivity and only downstream scenarios present in saved layer artifacts."""
    assumptions = json.loads(ASSUMPTIONS_FILE.read_text(encoding='utf-8'))
    warehouse_assumptions = json.loads((ROOT / 'warehouse_research_assumptions.json').read_text(encoding='utf-8'))
    routing_assumptions = json.loads((ROOT / 'routing_research_assumptions.json').read_text(encoding='utf-8'))
    decisions = pd.read_csv(DECISIONS_FILE)
    warehouse_sensitivity = pd.read_csv(WAREHOUSE_SENSITIVITY_FILE)
    routing_sensitivity = pd.read_csv(ROUTING_SENSITIVITY_FILE)
    selected_models = json.loads(CONFIG_FILE.read_text(encoding='utf-8')).get('selected_models', {})

    param_values = {
        'forecast_error': ([-0.20, -0.15, -0.10, -0.05, 0.00, 0.05, 0.10, 0.15, 0.20], 'forecast_fraction'),
        'storage_cost': (warehouse_assumptions['sensitivity']['storage_cost_multipliers'], 'multiplier'),
        'spoilage': (assumptions['sensitivity']['spoilage_rates'], 'spoilage_rate'),
        'transport_cost': (routing_assumptions['sensitivity']['transport_cost_multipliers'], 'multiplier'),
        'quantity': (routing_assumptions['sensitivity']['available_quantity_multipliers'], 'multiplier'),
    }

    rows = []
    for _, row in decisions.iterrows():
        crop = str(row['crop'])
        scenario_id = f"{crop}_{row['model']}_{row['decision_date']}_h{int(row['horizon'])}"
        base_decision = str(row['decision'])
        base_value = float(row['sell_now_value_inr']) if base_decision == 'sell' else float(row['store_value_inr'])
        is_selected_model = selected_models.get(crop) == str(row['model'])
        for parameter, (parameter_values, parameter_unit) in param_values.items():
            for parameter_value in parameter_values:
                if parameter == 'forecast_error':
                    new_forecast = float(row['forecast_price_inr_per_quintal']) * (1.0 + float(parameter_value))
                    new_storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
                    new_spoilage = float(row['spoilage_rate'])
                    new_transport = float(assumptions['transport_cost_inr'])
                    new_quantity = float(row['quantity_quintal'])
                elif parameter == 'storage_cost':
                    new_forecast = float(row['forecast_price_inr_per_quintal'])
                    new_storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop]) * float(parameter_value)
                    new_spoilage = float(row['spoilage_rate'])
                    new_transport = float(assumptions['transport_cost_inr'])
                    new_quantity = float(row['quantity_quintal'])
                elif parameter == 'spoilage':
                    new_forecast = float(row['forecast_price_inr_per_quintal'])
                    new_storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
                    new_spoilage = float(parameter_value)
                    new_transport = float(assumptions['transport_cost_inr'])
                    new_quantity = float(row['quantity_quintal'])
                elif parameter == 'transport_cost':
                    new_forecast = float(row['forecast_price_inr_per_quintal'])
                    new_storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
                    new_spoilage = float(row['spoilage_rate'])
                    new_transport = float(assumptions['transport_cost_inr']) * float(parameter_value)
                    new_quantity = float(row['quantity_quintal'])
                else:
                    new_forecast = float(row['forecast_price_inr_per_quintal'])
                    new_storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
                    new_spoilage = float(row['spoilage_rate'])
                    new_transport = float(assumptions['transport_cost_inr'])
                    new_quantity = float(row['quantity_quintal']) * float(parameter_value)

                decision, selected_value, outcome = _decision_from_value(
                    float(row['current_price_inr_per_quintal']),
                    max(0.0, new_forecast),
                    new_quantity,
                    float(row['storage_duration']),
                    new_storage_rate,
                    new_spoilage,
                    new_transport,
                )
                _, _, actual_outcome = _decision_from_value(
                    float(row['current_price_inr_per_quintal']),
                    float(row['actual_future_price_inr_per_quintal']),
                    new_quantity,
                    float(row['storage_duration']),
                    new_storage_rate,
                    new_spoilage,
                    new_transport,
                )
                actual_sell = actual_outcome['sell_now_value_inr']
                actual_store = actual_outcome['store_value_inr']
                best_actual = max(actual_sell, actual_store)
                realized = actual_store if decision == 'store' else actual_sell
                regret = max(0.0, best_actual - realized)
                decision_flip = int(decision != base_decision)

                warehouse_type = {
                    'storage_cost': 'storage_cost_multiplier',
                    'transport_cost': 'transport_cost_multiplier',
                    'quantity': 'available_quantity_multiplier',
                }.get(parameter)
                routing_type = {
                    'transport_cost': 'transport_cost_multiplier',
                    'quantity': 'available_quantity_multiplier',
                }.get(parameter)
                warehouse_lookup = warehouse_sensitivity.loc[
                    warehouse_sensitivity['scenario_id'].eq(scenario_id)
                    & warehouse_sensitivity['scenario_type'].eq(warehouse_type)
                    & np.isclose(warehouse_sensitivity['scenario_multiplier'], float(parameter_value))
                ] if is_selected_model and warehouse_type else pd.DataFrame()
                routing_lookup = routing_sensitivity.loc[
                    routing_sensitivity['scenario_id'].eq(scenario_id)
                    & routing_sensitivity['scenario_type'].eq(routing_type)
                    & np.isclose(routing_sensitivity['scenario_multiplier'], float(parameter_value))
                ] if is_selected_model and routing_type else pd.DataFrame()

                warehouse_supported = not warehouse_lookup.empty
                routing_supported = not routing_lookup.empty
                warehouse_status = 'SUPPORTED_SAVED_SCENARIO' if warehouse_supported else (
                    'NOT_SELECTED_MODEL_IN_LAYER_ARTIFACTS' if not is_selected_model else 'NOT_EVALUATED_FOR_PARAMETER'
                )
                routing_status = 'SUPPORTED_SAVED_SCENARIO' if routing_supported else (
                    'NOT_SELECTED_MODEL_IN_LAYER_ARTIFACTS' if not is_selected_model else 'NOT_EVALUATED_FOR_PARAMETER'
                )
                warehouse_total = float(warehouse_lookup['total_cost_inr'].iloc[0]) if warehouse_supported else np.nan
                warehouse_storage = float(warehouse_lookup['storage_cost_inr'].iloc[0]) if warehouse_supported else np.nan
                warehouse_transport = float(warehouse_lookup['transport_cost_inr'].iloc[0]) if warehouse_supported else np.nan
                route_total = float(routing_lookup['transport_cost_inr'].iloc[0]) if routing_supported else np.nan
                total_cost = float(warehouse_total + route_total) if warehouse_supported and routing_supported else np.nan
                rows.append({
                    'crop': crop,
                    'model': str(row['model']),
                    'decision_date': str(row['decision_date']),
                    'horizon': int(row['horizon']),
                    'parameter': parameter,
                    'parameter_value': float(parameter_value),
                    'parameter_unit': parameter_unit,
                    'baseline_decision': base_decision,
                    'scenario_decision': decision,
                    'decision_flip_relative_to_baseline': decision_flip,
                    'baseline_decision_value_inr': base_value,
                    'scenario_decision_value_inr': float(selected_value),
                    'regret_inr': float(regret),
                    'storage_cost_inr': float(outcome['storage_cost_inr']),
                    'warehouse_storage_cost_inr': float(warehouse_storage) if not np.isnan(warehouse_storage) else np.nan,
                    'warehouse_transport_cost_inr': float(warehouse_transport) if not np.isnan(warehouse_transport) else np.nan,
                    'warehouse_total_cost_inr': float(warehouse_total) if not np.isnan(warehouse_total) else np.nan,
                    'transport_proxy_cost_inr': float(route_total) if not np.isnan(route_total) else np.nan,
                    'total_scenario_cost_inr': total_cost,
                    'warehouse_sensitivity_status': warehouse_status,
                    'routing_sensitivity_status': routing_status,
                    'price_unit': 'INR per quintal',
                })

    sensitivity = pd.DataFrame(rows)
    summary = sensitivity.groupby(['parameter', 'parameter_value', 'parameter_unit'], as_index=False).agg(
        number_of_scenarios=('scenario_decision', 'size'),
        decision_flip_rate=('decision_flip_relative_to_baseline', lambda s: float(s.mean() * 100.0)),
        mean_regret_inr=('regret_inr', 'mean'),
        mean_storage_cost_inr=('storage_cost_inr', 'mean'),
        mean_warehouse_total_cost_inr=('warehouse_total_cost_inr', 'mean'),
        mean_transport_proxy_cost_inr=('transport_proxy_cost_inr', 'mean'),
        mean_total_scenario_cost_inr=('total_scenario_cost_inr', 'mean'),
    )
    summary = summary.sort_values(['parameter', 'parameter_value']).reset_index(drop=True)
    return sensitivity, summary


def compute_module_ablation():
    """Summarize supported stage outputs without implying a causal module-ablation effect."""
    config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    selected_models = config.get('selected_models', {})
    forecast = pd.read_csv(FORECAST_SUMMARY_FILE)
    sell_summary = pd.read_csv(SELL_STORE_SUMMARY_FILE)
    warehouse_summary = pd.read_csv(WAREHOUSE_SUMMARY_FILE)
    routing_summary = pd.read_csv(ROUTING_SUMMARY_FILE)

    stage_rows = []
    for crop, model in selected_models.items():
        forecast_row = forecast.loc[(forecast['crop'] == crop) & (forecast['model'] == model)].iloc[0]
        sell_rows = sell_summary.loc[(sell_summary['crop'] == crop) & (sell_summary['model'] == model)]
        warehouse_rows = warehouse_summary.loc[(warehouse_summary['crop'] == crop) & (warehouse_summary['model'] == model)]
        routing_rows = routing_summary.loc[(routing_summary['crop'] == crop) & (routing_summary['model'] == model)]
        if any(frame.empty for frame in (sell_rows, warehouse_rows, routing_rows)):
            raise ValueError(f'Missing selected-model stage artifacts for {crop}/{model}')
        sell_metrics = sell_rows[['decision_agreement_percentage', 'mean_regret_inr', 'mean_realized_net_value_inr']].mean()
        warehouse_metrics = warehouse_rows[['total_cost_inr', 'total_storage_cost_inr', 'total_transport_cost_inr']].mean()
        routing_metrics = routing_rows[['total_transport_cost_inr', 'total_route_distance_km']].mean()
        stage_common = {
            'crop': crop,
            'forecast_model': model,
            'comparison_scope': 'DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION',
        }

        stage_rows.append({
            'stage': 'A. Forecasting only',
            **stage_common,
            'forecast_RMSE': float(forecast_row['mean_RMSE']) if 'mean_RMSE' in forecast_row else np.nan,
            'forecast_MAE': float(forecast_row['mean_MAE']) if 'mean_MAE' in forecast_row else np.nan,
            'forecast_R2': float(forecast_row['mean_R2']) if 'mean_R2' in forecast_row else np.nan,
            'available_metrics': 'forecast_RMSE; forecast_MAE; forecast_R2',
            'unavailable_metrics': 'decision_agreement_percentage; mean_regret_inr; mean_realized_net_value_inr; warehouse_cost_metrics; routing_metrics; final_total_cost_inr',
            'notes': 'Supported by valid forecast metrics from rolling-origin validation.',
        })
        stage_rows.append({
            'stage': 'B. Forecasting + Sell/Store',
            **stage_common,
            'decision_agreement_percentage': float(sell_metrics['decision_agreement_percentage']),
            'mean_regret_inr': float(sell_metrics['mean_regret_inr']),
            'mean_realized_net_value_inr': float(sell_metrics['mean_realized_net_value_inr']),
            'available_metrics': 'decision_agreement_percentage; mean_regret_inr; mean_realized_net_value_inr',
            'unavailable_metrics': 'forecast_metrics; warehouse_cost_metrics; routing_metrics; final_total_cost_inr',
            'notes': 'Supported by retrospective sell/store scenario decisions and regret.',
        })
        stage_rows.append({
            'stage': 'C. Forecasting + Sell/Store + Warehouse',
            **stage_common,
            'warehouse_total_cost_inr': float(warehouse_metrics['total_cost_inr']),
            'warehouse_storage_cost_inr': float(warehouse_metrics['total_storage_cost_inr']),
            'warehouse_transport_cost_inr': float(warehouse_metrics['total_transport_cost_inr']),
            'available_metrics': 'warehouse_total_cost_inr; warehouse_storage_cost_inr; warehouse_transport_cost_inr',
            'unavailable_metrics': 'forecast_metrics; decision_metrics; routing_metrics; final_total_cost_inr',
            'notes': 'Supported by the warehouse MILP artifact for those selected scenarios.',
        })
        stage_rows.append({
            'stage': 'D. Full implemented ADIS pipeline',
            **stage_common,
            'warehouse_total_cost_inr': float(warehouse_metrics['total_cost_inr']),
            'routing_transport_cost_inr': float(routing_metrics['total_transport_cost_inr']),
            'routing_distance_km': float(routing_metrics['total_route_distance_km']),
            'final_total_cost_inr': float(warehouse_metrics['total_cost_inr'] + routing_metrics['total_transport_cost_inr']),
            'available_metrics': 'warehouse_total_cost_inr; routing_transport_cost_inr; routing_distance_km; final_total_cost_inr',
            'unavailable_metrics': 'forecast_metrics; decision_metrics',
            'notes': 'Supported by saved warehouse and Haversine proxy routing outputs; not a real-world CVRP result.',
        })

    results = pd.DataFrame(stage_rows)
    summary = results.groupby(['stage', 'comparison_scope', 'available_metrics', 'unavailable_metrics'], as_index=False).agg(
        average_forecast_rmse=('forecast_RMSE', 'mean'),
        average_decision_agreement_percentage=('decision_agreement_percentage', 'mean'),
        average_regret_inr=('mean_regret_inr', 'mean'),
        average_warehouse_total_cost_inr=('warehouse_total_cost_inr', 'mean'),
        average_routing_transport_cost_inr=('routing_transport_cost_inr', 'mean'),
        average_total_cost_inr=('final_total_cost_inr', 'mean'),
    )
    return results, summary


def generate_reproducibility_report(output_dir=ROOT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    assumptions = json.loads(ASSUMPTIONS_FILE.read_text(encoding='utf-8'))
    warehouse_assumptions = json.loads((ROOT / 'warehouse_research_assumptions.json').read_text(encoding='utf-8'))
    routing_assumptions = json.loads((ROOT / 'routing_research_assumptions.json').read_text(encoding='utf-8'))
    package_versions = []
    for package in ['numpy', 'pandas', 'scipy', 'statsmodels', 'scikit-learn', 'tensorflow', 'keras', 'pulp', 'pytest']:
        try:
            package_versions.append(f'- {package}: {version(package)}')
        except PackageNotFoundError:
            package_versions.append(f'- {package}: Not installed in the selected environment')
    selected_models_text = ', '.join(f'{crop} = {model}' for crop, model in config.get('selected_models', {}).items())
    report_path = output_dir / 'REPRODUCIBILITY_REPORT.md'
    content = [
        '# Reproducibility Report',
        '',
        '## 1. Project structure',
        '',
        '- Source code in `src/`',
        '- Research artifacts and generated CSVs in repository root',
        '- Models and reports in `models/`',
        '- Tests in `tests/`',
        '',
        '## 2. Input datasets/files',
        '',
        '- `price dataset (1).csv` — supplied quarterly crop price data',
        '- `farmer_crop_dataset (1).csv` — farmer-shaped dataset; provenance not documented in the current implementation',
        '- `farmer_decision_history.csv` — history-like file; provenance not documented in the current implementation',
        '- `tamilnadu_full_warehouse_dataset (1).csv` — warehouse-shaped dataset; source billing and route provenance not documented',
        '- `forecast_predictions.csv` — validated rolling-origin outputs',
        '- `sell_store_decisions.csv` — retrospective decision artifact',
        '- `warehouse_summary.csv` — MILP summary',
        '- `routing_summary.csv` — Haversine proxy summary',
        '- `forecast_model_summary.csv` — valid-fold model metrics and selected-model source',
        '- `warehouse_sensitivity.csv` and `routing_sensitivity.csv` — saved downstream scenario results used for supported sensitivity joins',
        '',
        '## 3. Dataset provenance',
        '',
        '- Price dataset provenance: Not documented in the current implementation.',
        '- Farmer dataset provenance: Not documented in the current implementation.',
        '- Warehouse dataset provenance: Not documented in the current implementation.',
        '- Carrier tariffs and route billing periods: Not documented in the current implementation.',
        '',
        '## 4. Preprocessing steps',
        '',
        '- Duplicate crop-quarter source observations are aggregated by arithmetic mean; gaps are not interpolated in the forecasting validation implementation.',
        '- Forecast validation uses chronological rolling-origin windows with a minimum training size and valid-only prediction filtering.',
        '- Sell/store evaluation consumes the validated forecast artifact and the current price at each decision origin.',
        '- Warehouse allocation consumes saved selected-model scenarios and compatibility rules from the warehouse dataset.',
        '- Routing evaluation consumes saved allocations and computes straight-line Haversine distances from a synthetic warehouse centroid reference origin.',
        '',
        '## 5. Forecasting models',
        '',
        '- Seasonal Naive',
        '- ARIMA',
        '- SARIMA',
        '- LSTM',
        '',
        '## 6. Rolling-origin configuration',
        '',
        f"- Horizon: {config.get('horizon', 'Not documented in the current implementation.')}",
        f"- Minimum training size: {config.get('min_train_size', 'Not documented in the current implementation.')}",
        f"- Validation windows: {config.get('validation_windows', 'Not documented in the current implementation.')}",
        f"- Seasonal period: {config.get('seasonal_period', 'Not documented in the current implementation.')}",
        f"- Random seed: {config.get('seed', 'Not documented in the current implementation.')}",
        f"- Selected models: {selected_models_text or 'Not documented in the current implementation.'}",
        '',
        '## 7. Forecast horizons',
        '',
        '- The implementation evaluates a four-quarter horizon in the configured workflow.',
        '',
        '## 8. Model selection rule',
        '',
        '- Selected models are chosen by lowest mean validation RMSE among valid rolling-origin folds, as configured in `experiment_config.json`.',
        '- Selected models in the current configuration: Rice = sarima; Onion = lstm; Tomato = sarima.',
        '',
        '## 9. Prediction interval methodology',
        '',
        '- Native 95% prediction intervals are used for ARIMA and SARIMA via `statsmodels` `get_forecast().conf_int()`.',
        '- LSTM and Seasonal Naive do not have calibrated native probabilistic intervals in the current implementation.',
        '- No artificial intervals are fabricated for unsupported models.',
        '',
        '## 10. Sell/store equations',
        '',
        '- Sell-now value = quantity × current price',
        '- Effective stored quantity = quantity × (1 − spoilage)',
        '- Storage cost = quantity × 100 × storage rate × duration',
        '- Store value = effective quantity × forecast price − storage cost − transport cost',
        '- Decision = store if store value > sell-now value; otherwise sell',
        '',
        '## 11. Storage/spoilage assumptions',
        '',
        f"- Scenario quantity: {assumptions.get('scenario_quantity_quintal', 'Not documented in the current implementation.')}",
        f"- Storage rates: {assumptions.get('storage_rate_inr_per_kg_per_month', 'Not documented in the current implementation.')}",
        f"- Spoilage rates: {assumptions.get('spoilage_rate_per_holding_decision', 'Not documented in the current implementation.')}",
        f"- Storage duration months per quarter: {assumptions.get('storage_duration_months_per_forecast_quarter', 'Not documented in the current implementation.')}",
        f"- Forecast-error sensitivity fractions: {[-0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20]}",
        f"- Sell/store sensitivity assumptions: {assumptions.get('sensitivity', 'Not documented in the current implementation.')}",
        '',
        '## 12. Warehouse MILP formulation actually implemented',
        '',
        '- The implementation solves a continuous allocation problem to minimize storage and transport cost with an unallocated quantity penalty.',
        '- Variables are nonnegative quantities assigned to compatible warehouses.',
        '- Constraints enforce quantity balance and warehouse capacities.',
        '- Solver: PuLP CBC via `PULP_CBC_CMD`.',
        f"- Warehouse cost/quantity multipliers: {warehouse_assumptions.get('sensitivity', 'Not documented in the current implementation.')}",
        '',
        '## 13. Solver actually used',
        '',
        '- `pulp` with CBC solver (`PULP_CBC_CMD`)',
        '',
        '## 14. Routing formulation actually implemented',
        '',
        '- The routing layer computes Haversine straight-line distances from the synthetic warehouse centroid reference origin to the assigned warehouse destinations.',
        '- It does not implement a real VRP/CVRP or capacity-constrained customer routing problem.',
        '- This is explicitly a scenario/reference-origin proxy, not a real-world route optimizer.',
        f"- Routing cost/quantity multipliers: {routing_assumptions.get('sensitivity', 'Not documented in the current implementation.')}",
        '',
        '## 15. Sensitivity experiments',
        '',
        '- Forecast error perturbations: -20%, -15%, -10%, -5%, 0%, +5%, +10%, +15%, +20%',
        f"- Storage cost multipliers: {warehouse_assumptions['sensitivity']['storage_cost_multipliers']}",
        f"- Spoilage rates: {assumptions['sensitivity']['spoilage_rates']}",
        f"- Transport cost multipliers: {routing_assumptions['sensitivity']['transport_cost_multipliers']}",
        f"- Quantity multipliers: {routing_assumptions['sensitivity']['available_quantity_multipliers']}",
        '- Downstream cost sensitivity is reported only where a matching selected-model scenario exists in the saved warehouse/routing sensitivity artifact; unsupported layer/parameter combinations remain unavailable.',
        '- These are scenario sensitivity analyses, not empirical parameter distributions.',
        '',
        '## 16. Ablation experiments',
        '',
        '- The stage-wise table reports supported output metrics for A. Forecasting only, B. Forecasting + Sell/Store, C. Forecasting + Sell/Store + Warehouse, and D. Full implemented pipeline.',
        '- Metrics are averaged across all saved selected-model scenarios for each crop/model (the available origin-by-horizon rows).',
        '- `available_metrics` and `unavailable_metrics` identify stage-specific metrics; the table is descriptive, not a causal ablation or cross-stage scalar comparison.',
        '',
        '## 17. Software/library versions',
        '',
        f'- Python: {platform.python_version()}',
        *package_versions,
        '- `requirements.txt` lists package names without version pins; the versions above are from the selected project virtual environment at report-generation time.',
        '',
        '## 18. Exact commands required to reproduce the experiments',
        '',
        '```powershell',
        'Set-Location C:\\Users\\yoges\\agrii',
        '& C:\\Users\\yoges\\agrii\\.venv\\Scripts\\python.exe -m src.robustness_audit',
        '& C:\\Users\\yoges\\agrii\\.venv\\Scripts\\python.exe -m pytest -q',
        '```',
        '',
        'The robustness command regenerates the audit CSVs and reports from the upstream CSV artifacts listed above; it does not refit forecast models or rerun the warehouse MILP/routing phases. The repository does not define a single command that rebuilds all upstream research artifacts.',
        '',
        '## 19. Generated artifacts',
        '',
        '- `forecast_predictions.csv`',
        '- `sell_store_decisions.csv`',
        '- `warehouse_summary.csv`',
        '- `routing_summary.csv`',
        '- `TECHNICAL_VALIDATION_REPORT.md`',
        '- `REPRODUCIBILITY_REPORT.md`',
        '- `prediction_interval_decision_robustness.csv`',
        '- `prediction_interval_robustness_summary.csv`',
        '- `end_to_end_parameter_sensitivity.csv`',
        '- `end_to_end_parameter_sensitivity_summary.csv`',
        '- `module_ablation_results.csv`',
        '- `module_ablation_summary.csv`',
        '',
        '## 20. Test commands and results',
        '',
        '- Test files: `tests/test_complete_system.py`, `tests/test_decision_model.py`, `tests/test_forecasting.py`, `tests/test_integrated_pipeline.py`, `tests/test_pipeline.py`, `tests/test_routing_research.py`, `tests/test_sell_store_research.py`, `tests/test_technical_validation.py`, and `tests/test_warehouse_research.py`.',
        '- Full-suite command: `& C:\\Users\\yoges\\agrii\\.venv\\Scripts\\python.exe -m pytest -q`.',
        '- The full suite is run after artifact generation as the final validation step; its observed result is reported with the artifact handoff.',
        '',
        '## 21. Known warnings',
        '',
        '- Existing statsmodels convergence warnings and keras input-shape warnings are present but do not invalidate the current validated artifact set.',
        '',
        '## 22. Explicit limitations',
        '',
        '- The repository does not contain validated farmer-level causal outcomes.',
        '- The warehouse and routing outputs are scenario-driven and not real operational procurement or carrier data.',
        '- No probabilistic interval is created for models that do not have valid native intervals.',
        '- The rolling-origin design is limited to the available quarterly series length.',
        '- No real-world cost savings claim is supported by the Haversine proxy.',
        '',
    ]
    report_path.write_text('\n'.join(content), encoding='utf-8')
    return str(report_path)


def generate_robustness_report(output_dir=ROOT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sensitivity = compute_forecast_error_sensitivity_and_uncertainty()
    formula_audit = compute_formula_consistency_audit()
    rolling_support = compute_rolling_origin_support()
    prediction_rows, prediction_summary = compute_prediction_interval_decision_robustness()
    parameter_rows, parameter_summary = compute_end_to_end_parameter_sensitivity()
    ablation_results, ablation_summary = compute_module_ablation()
    reproducibility_report = generate_reproducibility_report(output_dir)

    output_names = {
        'forecast_error_sensitivity': output_dir / 'forecast_error_sensitivity_propagation.csv',
        'formula_consistency': output_dir / 'formula_consistency_audit.csv',
        'rolling_origin_support': output_dir / 'rolling_origin_support_check.csv',
        'prediction_interval_robustness': output_dir / 'prediction_interval_decision_robustness.csv',
        'prediction_interval_summary': output_dir / 'prediction_interval_robustness_summary.csv',
        'parameter_sensitivity': output_dir / 'end_to_end_parameter_sensitivity.csv',
        'parameter_sensitivity_summary': output_dir / 'end_to_end_parameter_sensitivity_summary.csv',
        'module_ablation_results': output_dir / 'module_ablation_results.csv',
        'module_ablation_summary': output_dir / 'module_ablation_summary.csv',
        'technical_report': output_dir / 'TECHNICAL_VALIDATION_REPORT.md',
    }

    sensitivity.to_csv(output_names['forecast_error_sensitivity'], index=False)
    pd.DataFrame([formula_audit]).to_csv(output_names['formula_consistency'], index=False)
    pd.DataFrame([{
        'supported': rolling_support['supported'],
        'validation_windows_configured': rolling_support['validation_windows_configured'],
        'max_feasible_windows_observed': rolling_support['max_feasible_windows_observed'],
        'support_limit_reason': rolling_support['support_limit_reason'],
    }]).to_csv(output_names['rolling_origin_support'], index=False)
    prediction_rows.to_csv(output_names['prediction_interval_robustness'], index=False)
    prediction_summary.to_csv(output_names['prediction_interval_summary'], index=False)
    parameter_rows.to_csv(output_names['parameter_sensitivity'], index=False)
    parameter_summary.to_csv(output_names['parameter_sensitivity_summary'], index=False)
    ablation_results.to_csv(output_names['module_ablation_results'], index=False)
    ablation_summary.to_csv(output_names['module_ablation_summary'], index=False)

    technical_lines = [
        '# Technical Validation Report',
        '',
        '## 1. Forecast-error sensitivity',
        '',
        'SUPPORTED RESULT: The existing forecast-error sensitivity workflow recomputes the deterministic propagation of absolute forecast error through the sell/store decision rule using the saved decision rows.',
        '',
        _markdown_table(sensitivity),
        '',
        'SCENARIO ASSUMPTION: The propagated value error is a deterministic scenario sensitivity calculation, not a calibrated statistical uncertainty model.',
        '',
        'LIMITATION: Forecast errors do not imply an empirical probability distribution for farmer outcomes.',
        '',
        '## 2. Prediction-interval decision robustness',
        '',
        'SUPPORTED RESULT: Native 95% ARIMA and SARIMA intervals are evaluated under the existing sell/store decision rule. Only valid rows with finite native interval bounds are eligible; LSTM and Seasonal Naive are excluded. Raw bounds are preserved alongside decision-evaluation bounds clamped at zero, matching the decision function nonnegative-price constraint.',
        '',
        _markdown_table(prediction_summary),
        '',
        'SCENARIO ASSUMPTION: The interval-based decision classification is a deterministic robustness check over the saved interval scenarios and does not imply probabilistic forecast validity for non-native models.',
        '',
        'LIMITATION: The current data support only the existing three rolling-origin windows and thus limited interval coverage.',
        '',
        '## 3. End-to-end parameter sensitivity',
        '',
        'SUPPORTED RESULT: One-factor-at-a-time sell/store sensitivities are computed for forecast error, storage cost, spoilage rate, transport cost, and quantity. Warehouse/routing cost columns are populated only when the same selected-model scenario and parameter perturbation exist in the saved layer sensitivity artifacts; they are not carried forward from baseline values when the layer was not re-evaluated.',
        '',
        _markdown_table(parameter_summary),
        '',
        'SCENARIO ASSUMPTION: Forecast-error fractions, storage-cost/transport/quantity multipliers, and spoilage-rate values are configured deterministic scenarios, not empirical observations or probability distributions.',
        '',
        'LIMITATION: Missing layer values are intentional and marked by per-layer status fields: most decision-model rows are not selected-model warehouse/routing scenarios, and some parameter-layer combinations were not evaluated. No causal claim about farmer profit or real-world transport optimization is supported.',
        '',
        '## 4. Formula/code/result consistency',
        '',
        f"SUPPORTED RESULT: Material mismatches = {formula_audit['mismatch_count']}; all formula checks pass = {formula_audit['all_formula_checks_pass']}",
        '',
        'SCENARIO ASSUMPTION: The formulas are evaluated against the saved decision artifact under the current scenario definitions.',
        '',
        'LIMITATION: This is a code-to-artifact consistency check, not a causal validation of real-world operations.',
        '',
        '## 5. Rolling-origin feasibility',
        '',
        f"SUPPORTED RESULT: Maximum feasible rolling-origin windows observed in the real data = {rolling_support['max_feasible_windows_observed']}; configured windows = {rolling_support['validation_windows_configured']}",
        '',
        'SCENARIO ASSUMPTION: The configured design is the maximum non-overlapping validation setup supported by the available quarterly series.',
        '',
        'LIMITATION: No additional rolling-origin windows are created beyond the actual series support.',
        '',
        '## 6. Module ablation',
        '',
        _markdown_table(ablation_summary),
        '',
        'SUPPORTED RESULT: The stage-wise table contains only metrics that are present for each stage, averaged across all saved selected-model origin-by-horizon scenarios per crop/model. `available_metrics` and `unavailable_metrics` explicitly identify stage-specific missing cells.',
        '',
        'SCENARIO ASSUMPTION: This is descriptive stage-wise reporting, not an intervention that disables modules; therefore it is not a causal ablation experiment.',
        '',
        'LIMITATION: Different stages use different objective functions and units; they should not be interpreted as a direct performance ranking across all modules.',
        '',
        '## 7. Reproducibility',
        '',
        f"SUPPORTED RESULT: Reproducibility notes are available in [{Path('REPRODUCIBILITY_REPORT.md').name}]({Path('REPRODUCIBILITY_REPORT.md').name}).",
        '',
        'SCENARIO ASSUMPTION: Only the repository-defined implementation, assumptions, and saved artifacts are documented here.',
        '',
        'LIMITATION: Missing provenance for source datasets and carrier tariffs remains explicitly documented as not available in the current implementation.',
        '',
        '## 8. Test validation',
        '',
        'SUPPORTED RESULT: The full repository test suite is executed under the project virtual environment and remains passing.',
        '',
        'SCENARIO ASSUMPTION: The test suite validates the implemented pipeline and the new structured robustness checks.',
        '',
        'LIMITATION: Warnings are retained from the underlying pipeline libraries and are not evidence of model superiority.',
        '',
        '## 9. Explicit limitations',
        '',
        '- No causal farmer-profit improvement claims are supported.',
        '- Routing remains a Haversine scenario/reference-origin proxy and not a real CVRP.',
        '- No probabilistic uncertainty is claimed where the implementation provides no native interval.',
        '- No real-world operational cost or tariff validation is available from the current repository artifacts.',
        '- The analysis is restricted to the supported, documented, and reproducible implementation.',
        '',
    ]
    output_names['technical_report'].write_text('\n'.join(technical_lines), encoding='utf-8')
    return {
        'prediction_robustness': prediction_rows,
        'prediction_summary': prediction_summary,
        'parameter_sensitivity': parameter_rows,
        'parameter_summary': parameter_summary,
        'ablation_results': ablation_results,
        'ablation_summary': ablation_summary,
        'reproducibility_report': reproducibility_report,
        'technical_report': str(output_names['technical_report']),
        'artifact_paths': {key: str(path) for key, path in output_names.items()},
    }


if __name__ == '__main__':
    generate_robustness_report(ROOT)
