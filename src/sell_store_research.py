"""Retrospective sell/store evaluation using validated rolling-origin forecasts."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.forecast_validation import PRICE_COLUMN, PRICE_UNIT


DECISION_COLUMNS = [
    'crop', 'decision_date', 'horizon', 'quantity_quintal',
    'current_price_inr_per_quintal', 'forecast_price_inr_per_quintal',
    'actual_future_price_inr_per_quintal', 'storage_duration', 'storage_cost_inr',
    'spoilage_rate', 'effective_quantity_quintal', 'sell_now_value_inr',
    'store_value_inr', 'incremental_store_value_inr', 'decision',
    'actual_optimal_decision', 'decision_correct', 'regret_inr', 'model', 'price_unit',
    'spoilage_cost_inr', 'expected_store_revenue_inr', 'forecast_interval_available',
    'uncertainty_status', 'future_actual_date', 'decision_value_error_inr',
]
SUMMARY_COLUMNS = [
    'crop', 'model', 'horizon', 'number_of_decisions', 'sell_count', 'store_count',
    'decision_agreement_percentage', 'false_store_percentage', 'false_sell_percentage',
    'mean_sell_now_value_inr', 'mean_store_value_inr', 'mean_regret_inr',
    'median_regret_inr', 'price_unit', 'mean_realized_net_value_inr',
]
BASELINE_COLUMNS = [
    'crop', 'model', 'horizon', 'number_of_decisions', 'sell_count', 'store_count',
    'decision_agreement_percentage', 'false_store_percentage', 'false_sell_percentage',
    'mean_realized_net_value_inr', 'mean_regret_inr', 'median_regret_inr', 'price_unit',
]
SENSITIVITY_COLUMNS = [
    'crop', 'model', 'fold', 'horizon', 'scenario_type', 'scenario_value',
    'storage_duration_months', 'storage_cost_inr', 'spoilage_rate',
    'future_price_inr_per_quintal', 'net_sell_now_value_inr', 'net_store_value_inr',
    'incremental_store_value_inr', 'decision', 'quantity_quintal', 'price_unit',
]
ERROR_SENSITIVITY_COLUMNS = [
    'crop', 'model', 'horizon', 'number_of_decisions', 'decision_agreement_percentage',
    'decision_disagreement_percentage', 'false_store_rate_percentage',
    'false_sell_rate_percentage', 'average_economic_regret_inr',
    'mean_absolute_decision_value_error_inr', 'mean_absolute_forecast_error_inr', 'price_unit',
]


def decide_sell_or_store_economic(
    current_price_inr_per_quintal,
    forecast_price_inr_per_quintal,
    quantity_quintal,
    storage_duration_months,
    storage_rate_inr_per_kg_per_month,
    spoilage_rate,
    transport_cost_inr=0.0,
):
    """Choose the larger point-estimate net value using explicit units and assumptions.

    This function intentionally has no actual-future-price argument. All prices are
    INR/quintal, quantity is quintals, storage rates are INR/kg/month, and duration
    is months. Transport is total INR for the scenario.
    """
    values = {
        'current price': current_price_inr_per_quintal,
        'forecast price': forecast_price_inr_per_quintal,
        'quantity': quantity_quintal,
        'storage duration': storage_duration_months,
        'storage rate': storage_rate_inr_per_kg_per_month,
        'spoilage rate': spoilage_rate,
        'transport cost': transport_cost_inr,
    }
    for name, value in values.items():
        if not np.isfinite(float(value)):
            raise ValueError(f'{name} must be finite')
    if current_price_inr_per_quintal < 0 or forecast_price_inr_per_quintal < 0:
        raise ValueError('Prices cannot be negative')
    if quantity_quintal < 0 or storage_duration_months < 0 or storage_rate_inr_per_kg_per_month < 0 or transport_cost_inr < 0:
        raise ValueError('Quantity, duration, rates, and costs cannot be negative')
    if not 0.0 <= spoilage_rate <= 1.0:
        raise ValueError('spoilage_rate must be between 0 and 1')

    quantity_kg = float(quantity_quintal) * 100.0
    effective_quantity = float(quantity_quintal) * (1.0 - float(spoilage_rate))
    storage_cost = quantity_kg * float(storage_rate_inr_per_kg_per_month) * float(storage_duration_months)
    expected_revenue = effective_quantity * float(forecast_price_inr_per_quintal)
    spoilage_cost = (float(quantity_quintal) - effective_quantity) * float(forecast_price_inr_per_quintal)
    sell_now_value = float(quantity_quintal) * float(current_price_inr_per_quintal)
    store_value = expected_revenue - storage_cost - float(transport_cost_inr)
    incremental_value = store_value - sell_now_value
    return {
        'current_price_inr_per_quintal': float(current_price_inr_per_quintal),
        'forecast_price_inr_per_quintal': float(forecast_price_inr_per_quintal),
        'quantity_quintal': float(quantity_quintal),
        'storage_duration_months': float(storage_duration_months),
        'quantity_kg_for_storage_cost': quantity_kg,
        'storage_rate_inr_per_kg_per_month': float(storage_rate_inr_per_kg_per_month),
        'storage_cost_inr': storage_cost,
        'spoilage_rate': float(spoilage_rate),
        'expected_spoilage_quantity_quintal': float(quantity_quintal) - effective_quantity,
        'effective_quantity_quintal': effective_quantity,
        'expected_store_revenue_inr': expected_revenue,
        'spoilage_cost_inr': spoilage_cost,
        'transport_cost_inr': float(transport_cost_inr),
        'sell_now_value_inr': sell_now_value,
        'store_value_inr': store_value,
        'incremental_store_value_inr': incremental_value,
        'decision': 'store' if store_value > sell_now_value else 'sell',
    }


def _quarter_periods(df):
    quarter_number = df['Quarter'].astype(str).str.extract(r'Q([1-4])', expand=False)
    if quarter_number.isna().any():
        quarter_number = quarter_number.fillna(df['Quarter'].astype(str).str.extract(r'([1-4])$', expand=False))
    if quarter_number.isna().any():
        raise ValueError('Cannot parse all quarter labels')
    return pd.PeriodIndex(df['Year'].astype('Int64').astype(str) + 'Q' + quarter_number.astype(str), freq='Q')


def _source_prices(data_path):
    raw = pd.read_csv(data_path)
    if PRICE_COLUMN not in raw or 'Crop' not in raw:
        raise ValueError(f'Dataset must contain Crop and {PRICE_COLUMN}; no unit inference is performed')
    raw = raw.copy()
    raw['_quarter'] = _quarter_periods(raw)
    raw[PRICE_COLUMN] = pd.to_numeric(raw[PRICE_COLUMN], errors='coerce')
    raw = raw.dropna(subset=[PRICE_COLUMN])
    result = {}
    for crop, group in raw.groupby('Crop'):
        means = group.groupby('_quarter')[PRICE_COLUMN].mean().sort_index()
        result[str(crop)] = means
    return result, raw


def _score_actual_decision(actual_future_price, current_price, quantity, duration, storage_rate, spoilage, transport_cost):
    """Post-decision scoring only; never called to choose the forecast-based action."""
    actual_sell = quantity * current_price
    effective_qty = quantity * (1.0 - spoilage)
    storage_cost_total = quantity * 100.0 * storage_rate * duration
    actual_store = effective_qty * actual_future_price - storage_cost_total - transport_cost
    actual_optimal = 'store' if actual_store > actual_sell else 'sell'
    return actual_sell, actual_store, actual_optimal, max(actual_sell, actual_store)


def _decision_records(predictions, interval_rows, source_prices, assumptions):
    interval_lookup = interval_rows.set_index(['crop', 'model', 'fold', 'horizon']) if not interval_rows.empty else None
    records = []
    for row in predictions.itertuples(index=False):
        if row.validity_status != 'VALID':
            continue
        crop = str(row.crop)
        series = source_prices.get(crop)
        if series is None:
            raise ValueError(f'No source price series for crop {crop}')
        decision_period = pd.Period(pd.Timestamp(row.train_end), freq='Q')
        future_period = pd.Period(pd.Timestamp(row.forecast_date), freq='Q')
        if not decision_period < future_period:
            raise ValueError(f'Leakage guard failed for {crop} {row.model} fold {row.fold} horizon {row.horizon}')
        if decision_period not in series.index:
            raise ValueError(f'No labeled source price at decision date {row.train_end} for {crop}')
        current_price = float(series.loc[decision_period])
        actual_future = float(row.actual)
        quantity = float(assumptions['scenario_quantity_quintal'])
        duration = float(row.horizon) * float(assumptions['storage_duration_months_per_forecast_quarter'])
        storage_rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
        spoilage = float(assumptions['spoilage_rate_per_holding_decision'][crop])
        transport = float(assumptions['transport_cost_inr'])

        # The chooser receives forecast/current information only; the actual is used below for retrospective scoring.
        expected = decide_sell_or_store_economic(
            current_price, float(row.predicted), quantity, duration, storage_rate, spoilage, transport
        )
        actual_sell, actual_store, actual_optimal, best_actual_value = _score_actual_decision(
            actual_future, current_price, quantity, duration, storage_rate, spoilage, transport
        )
        realized_selected_value = actual_store if expected['decision'] == 'store' else actual_sell
        regret = max(0.0, best_actual_value - realized_selected_value)
        actual_value_for_selected_action = actual_store if expected['decision'] == 'store' else actual_sell
        absolute_decision_value_error = abs(
            (expected['store_value_inr'] if expected['decision'] == 'store' else expected['sell_now_value_inr'])
            - actual_value_for_selected_action
        )
        interval_available = False
        if interval_lookup is not None:
            key = (crop, str(row.model), int(row.fold), int(row.horizon))
            if key in interval_lookup.index:
                bounds = interval_lookup.loc[key]
                interval_available = pd.notna(bounds['lower_95']) and pd.notna(bounds['upper_95'])

        records.append({
            'crop': crop,
            'decision_date': pd.Timestamp(row.train_end).date().isoformat(),
            'horizon': int(row.horizon),
            'quantity_quintal': quantity,
            'current_price_inr_per_quintal': current_price,
            'forecast_price_inr_per_quintal': float(row.predicted),
            'actual_future_price_inr_per_quintal': actual_future,
            'storage_duration': duration,
            'storage_cost_inr': expected['storage_cost_inr'],
            'spoilage_rate': spoilage,
            'effective_quantity_quintal': expected['effective_quantity_quintal'],
            'sell_now_value_inr': expected['sell_now_value_inr'],
            'store_value_inr': expected['store_value_inr'],
            'incremental_store_value_inr': expected['incremental_store_value_inr'],
            'decision': expected['decision'],
            'actual_optimal_decision': actual_optimal,
            'decision_correct': expected['decision'] == actual_optimal,
            'regret_inr': regret,
            'model': str(row.model),
            'price_unit': PRICE_UNIT,
            'spoilage_cost_inr': expected['spoilage_cost_inr'],
            'expected_store_revenue_inr': expected['expected_store_revenue_inr'],
            'forecast_interval_available': bool(interval_available),
            'uncertainty_status': 'native 95% interval available' if interval_available else 'interval unavailable; point forecast used',
            'future_actual_date': pd.Timestamp(row.forecast_date).date().isoformat(),
            'decision_value_error_inr': absolute_decision_value_error,
            '_fold': int(row.fold),
            '_forecast_error_inr_per_quintal': abs(float(row.predicted) - actual_future),
        })
    decisions = pd.DataFrame(records)
    if decisions.empty:
        raise ValueError('No valid forecast predictions were available for sell/store evaluation')
    return decisions


def _summary(decisions):
    rows = []
    for (crop, model, horizon), group in decisions.groupby(['crop', 'model', 'horizon'], sort=True):
        n = len(group)
        false_store = ((group['decision'] == 'store') & (group['actual_optimal_decision'] == 'sell')).sum()
        false_sell = ((group['decision'] == 'sell') & (group['actual_optimal_decision'] == 'store')).sum()
        rows.append({
            'crop': crop, 'model': model, 'horizon': int(horizon), 'number_of_decisions': n,
            'sell_count': int(group['decision'].eq('sell').sum()),
            'store_count': int(group['decision'].eq('store').sum()),
            'decision_agreement_percentage': float(group['decision_correct'].mean() * 100.0),
            'false_store_percentage': float(false_store / n * 100.0),
            'false_sell_percentage': float(false_sell / n * 100.0),
            'mean_sell_now_value_inr': float(group['sell_now_value_inr'].mean()),
            'mean_store_value_inr': float(group['store_value_inr'].mean()),
            'mean_regret_inr': float(group['regret_inr'].mean()),
            'median_regret_inr': float(group['regret_inr'].median()),
            'price_unit': PRICE_UNIT,
            'mean_realized_net_value_inr': float(_realized_values(group).mean()),
        })
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _realized_values(group):
    effective = group['quantity_quintal'] * (1.0 - group['spoilage_rate'])
    actual_store = effective * group['actual_future_price_inr_per_quintal'] - group['storage_cost_inr']
    actual_sell = group['sell_now_value_inr']
    return np.where(group['decision'].eq('store'), actual_store, actual_sell)


def _baseline_records(decisions):
    rows = []
    policy_inputs = [
        ('always_sell', decisions.drop_duplicates(['crop', '_fold', 'horizon'])),
        ('always_store', decisions.drop_duplicates(['crop', '_fold', 'horizon'])),
        ('seasonal_naive_forecast', decisions.loc[decisions['model'].eq('seasonal_naive')]),
    ]
    for policy, policy_decisions in policy_inputs:
        for _, row in policy_decisions.iterrows():
            action = 'sell' if policy == 'always_sell' else 'store' if policy == 'always_store' else row['decision']
            actual_sell = float(row['sell_now_value_inr'])
            actual_store = (
                float(row['quantity_quintal']) * (1.0 - float(row['spoilage_rate']))
                * float(row['actual_future_price_inr_per_quintal']) - float(row['storage_cost_inr'])
            )
            optimal = str(row['actual_optimal_decision'])
            best_value = max(actual_sell, actual_store)
            realized = actual_store if action == 'store' else actual_sell
            rows.append({
                'crop': row['crop'], 'model': policy, 'horizon': int(row['horizon']),
                'action': action, 'actual_optimal_decision': optimal,
                'agreement': action == optimal,
                'false_store': action == 'store' and optimal == 'sell',
                'false_sell': action == 'sell' and optimal == 'store',
                'realized_net_value_inr': realized,
                'regret_inr': max(0.0, best_value - realized),
                'sell_now_value_inr': actual_sell,
                'store_value_inr': actual_store,
                'price_unit': PRICE_UNIT,
            })
    return pd.DataFrame(rows)


def _baseline_summary(baselines):
    rows = []
    for (crop, model, horizon), group in baselines.groupby(['crop', 'model', 'horizon'], sort=True):
        n = len(group)
        rows.append({
            'crop': crop, 'model': model, 'horizon': int(horizon), 'number_of_decisions': n,
            'sell_count': int(group['action'].eq('sell').sum()), 'store_count': int(group['action'].eq('store').sum()),
            'decision_agreement_percentage': float(group['agreement'].mean() * 100.0),
            'false_store_percentage': float(group['false_store'].mean() * 100.0),
            'false_sell_percentage': float(group['false_sell'].mean() * 100.0),
            'mean_realized_net_value_inr': float(group['realized_net_value_inr'].mean()),
            'mean_regret_inr': float(group['regret_inr'].mean()),
            'median_regret_inr': float(group['regret_inr'].median()), 'price_unit': PRICE_UNIT,
        })
    return pd.DataFrame(rows, columns=BASELINE_COLUMNS)


def _forecast_error_sensitivity(decisions):
    rows = []
    for (crop, model, horizon), group in decisions.groupby(['crop', 'model', 'horizon'], sort=True):
        n = len(group)
        false_store = ((group['decision'] == 'store') & (group['actual_optimal_decision'] == 'sell')).sum()
        false_sell = ((group['decision'] == 'sell') & (group['actual_optimal_decision'] == 'store')).sum()
        rows.append({
            'crop': crop, 'model': model, 'horizon': int(horizon), 'number_of_decisions': n,
            'decision_agreement_percentage': float(group['decision_correct'].mean() * 100.0),
            'decision_disagreement_percentage': float((~group['decision_correct']).mean() * 100.0),
            'false_store_rate_percentage': float(false_store / n * 100.0),
            'false_sell_rate_percentage': float(false_sell / n * 100.0),
            'average_economic_regret_inr': float(group['regret_inr'].mean()),
            'mean_absolute_decision_value_error_inr': float(group['decision_value_error_inr'].mean()),
            'mean_absolute_forecast_error_inr': float(group['_forecast_error_inr_per_quintal'].mean()),
            'price_unit': PRICE_UNIT,
        })
    return pd.DataFrame(rows, columns=ERROR_SENSITIVITY_COLUMNS)


def _sensitivity(decisions, assumptions):
    sensitivity = assumptions['sensitivity']
    rows = []
    for _, row in decisions.iterrows():
        crop = row['crop']
        rate = float(assumptions['storage_rate_inr_per_kg_per_month'][crop])
        base_duration = float(row['storage_duration'])
        quantity = float(row['quantity_quintal'])
        current = float(row['current_price_inr_per_quintal'])
        forecast = float(row['forecast_price_inr_per_quintal'])
        base_spoilage = float(row['spoilage_rate'])
        for scenario_type, scenario_values in (
            ('storage_cost_multiplier', sensitivity['storage_cost_multipliers']),
            ('spoilage_rate', sensitivity['spoilage_rates']),
            ('future_price_multiplier', sensitivity['future_price_multipliers']),
            ('storage_duration_months', sensitivity['storage_duration_months']),
        ):
            for scenario_value in scenario_values:
                storage_rate = rate * float(scenario_value) if scenario_type == 'storage_cost_multiplier' else rate
                spoilage = float(scenario_value) if scenario_type == 'spoilage_rate' else base_spoilage
                scenario_forecast = forecast * float(scenario_value) if scenario_type == 'future_price_multiplier' else forecast
                duration = float(scenario_value) if scenario_type == 'storage_duration_months' else base_duration
                result = decide_sell_or_store_economic(
                    current, scenario_forecast, quantity, duration, storage_rate, spoilage,
                    float(assumptions['transport_cost_inr']),
                )
                rows.append({
                    'crop': crop, 'model': row['model'], 'fold': int(row['_fold']),
                    'horizon': int(row['horizon']), 'scenario_type': scenario_type,
                    'scenario_value': float(scenario_value), 'storage_duration_months': duration,
                    'storage_cost_inr': result['storage_cost_inr'], 'spoilage_rate': spoilage,
                    'future_price_inr_per_quintal': scenario_forecast,
                    'net_sell_now_value_inr': result['sell_now_value_inr'],
                    'net_store_value_inr': result['store_value_inr'],
                    'incremental_store_value_inr': result['incremental_store_value_inr'],
                    'decision': result['decision'], 'quantity_quintal': quantity,
                    'price_unit': PRICE_UNIT,
                })
    return pd.DataFrame(rows, columns=SENSITIVITY_COLUMNS)


def _paper_tables(summary, sensitivity):
    table_x = summary.rename(columns={
        'horizon': 'Horizon', 'number_of_decisions': 'N', 'sell_count': 'Sell Decisions',
        'store_count': 'Store Decisions', 'decision_agreement_percentage': 'Decision Agreement (%)',
        'mean_regret_inr': 'Mean Regret (INR)', 'median_regret_inr': 'Median Regret (INR)',
    })[[
        'crop', 'model', 'Horizon', 'N', 'Sell Decisions', 'Store Decisions',
        'Decision Agreement (%)', 'Mean Regret (INR)', 'Median Regret (INR)',
    ]].rename(columns={'crop': 'Crop', 'model': 'Model'})
    table_y = sensitivity.loc[sensitivity['scenario_type'].isin(['storage_cost_multiplier', 'spoilage_rate'])].groupby(
        ['crop', 'scenario_type', 'scenario_value'], as_index=False, sort=True
    ).agg(
        number_of_scenarios=('decision', 'size'),
        store_decision_percentage=('decision', lambda values: float(np.mean(np.asarray(values) == 'store') * 100.0)),
        mean_incremental_store_value_inr=('incremental_store_value_inr', 'mean'),
    )
    return table_x, table_y


def _write_figures(output_dir, decisions, summary, sensitivity):
    import matplotlib

    import matplotlib.pyplot as plt

    crops = sorted(decisions['crop'].unique())
    models = sorted(decisions['model'].unique())

    value_data = summary.groupby('crop')[['mean_sell_now_value_inr', 'mean_store_value_inr']].mean()
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    value_data.plot(kind='bar', ax=ax, color=['#2c7fb8', '#f28e2b'])
    ax.set_title('Retrospective sell-now and forecast-based store values')
    ax.set_xlabel('Crop')
    ax.set_ylabel('Mean scenario value (INR per 1-quintal scenario)')
    ax.legend(['Sell now', 'Store'], frameon=False)
    ax.grid(axis='y', alpha=0.25)
    fig.savefig(output_dir / 'sell_store_values_by_crop.png', dpi=300)
    plt.close(fig)

    for metric, title, filename, ylabel in (
        ('decision_agreement_percentage', 'Decision agreement by crop, model, and horizon', 'sell_store_agreement.png', 'Agreement with retrospective actual-price optimum (%)'),
        ('mean_regret_inr', 'Retrospective simulated regret by crop, model, and horizon', 'sell_store_regret.png', 'Mean regret (INR per 1-quintal scenario)'),
    ):
        pivot = summary.pivot_table(index='horizon', columns=['crop', 'model'], values=metric)
        fig, ax = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
        pivot.plot(ax=ax, marker='o')
        ax.set_title(title)
        ax.set_xlabel('Forecast horizon (quarters)')
        ax.set_ylabel(ylabel)
        ax.legend(frameon=False, fontsize=7, ncol=2)
        ax.grid(alpha=0.25)
        fig.savefig(output_dir / filename, dpi=300)
        plt.close(fig)

    for scenario_type, title, filename, x_label in (
        ('storage_cost_multiplier', 'Storage-cost scenario sensitivity', 'sell_store_storage_cost_sensitivity.png', 'Storage-cost scenario multiplier (x)'),
        ('spoilage_rate', 'Total spoilage-rate scenario sensitivity', 'sell_store_spoilage_sensitivity.png', 'Assumed spoilage over holding decision (%)'),
    ):
        group = sensitivity.loc[sensitivity['scenario_type'].eq(scenario_type)].groupby(
            ['crop', 'scenario_value'], as_index=False
        ).agg(mean_incremental_store_value_inr=('incremental_store_value_inr', 'mean'))
        fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
        for crop, data in group.groupby('crop'):
            x = data['scenario_value'] * 100 if scenario_type == 'spoilage_rate' else data['scenario_value']
            ax.plot(x, data['mean_incremental_store_value_inr'], marker='o', label=crop)
        ax.axhline(0, color='black', linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel('Mean incremental store value (INR per 1-quintal scenario)')
        ax.legend(frameon=False)
        ax.grid(alpha=0.25)
        fig.savefig(output_dir / filename, dpi=300)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for crop, group in decisions.groupby('crop'):
        forecast_error_pct = (
            np.abs(group['forecast_price_inr_per_quintal'] - group['actual_future_price_inr_per_quintal'])
            / group['actual_future_price_inr_per_quintal'].replace(0, np.nan) * 100.0
        )
        disagreement = (~group['decision_correct']).astype(float) + np.random.default_rng(0).uniform(-0.04, 0.04, len(group))
        ax.scatter(forecast_error_pct, disagreement, alpha=0.65, s=18, label=crop)
    ax.set_title('Forecast error and retrospective decision disagreement')
    ax.set_xlabel('Absolute forecast error (% of actual future price)')
    ax.set_ylabel('Decision disagreement (jittered 0/1 indicator)')
    ax.set_yticks([0, 1], ['Agreement', 'Disagreement'])
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.savefig(output_dir / 'sell_store_forecast_error_disagreement.png', dpi=300)
    plt.close(fig)


def _render_report(data_path, forecast_path, assumptions, decisions, summary, baselines, sensitivity, error_sensitivity, table_x, table_y, selected):
    crop_stats = decisions.groupby('crop').agg(
        number_of_decisions=('decision', 'size'),
        date_start=('decision_date', 'min'),
        date_end=('future_actual_date', 'max'),
    ).reset_index().to_string(index=False)
    selected_assessment = []
    for crop, model in selected.items():
        rows = decisions.loc[(decisions['crop'] == crop) & (decisions['model'] == model)]
        if rows.empty:
            selected_assessment.append(f'- {crop}: selected model `{model}` has no valid decision rows.')
            continue
        selected_assessment.append(
            f"- {crop} / {model}: N={len(rows)}, agreement={rows['decision_correct'].mean() * 100:.2f}%, "
            f"mean regret=INR {rows['regret_inr'].mean():.2f}, interval availability="
            f"{'yes' if rows['forecast_interval_available'].any() else 'no (point forecast only)'}"
        )
    storage_sens = sensitivity.loc[sensitivity['scenario_type'].eq('storage_cost_multiplier')].groupby(
        ['crop', 'scenario_value'], as_index=False
    ).agg(store_percentage=('decision', lambda v: float(np.mean(np.asarray(v) == 'store') * 100.0)), mean_incremental_value=('incremental_store_value_inr', 'mean')).to_string(index=False)
    spoilage_sens = sensitivity.loc[sensitivity['scenario_type'].eq('spoilage_rate')].groupby(
        ['crop', 'scenario_value'], as_index=False
    ).agg(store_percentage=('decision', lambda v: float(np.mean(np.asarray(v) == 'store') * 100.0)), mean_incremental_value=('incremental_store_value_inr', 'mean')).to_string(index=False)
    baseline_text = baselines.groupby('model', sort=True).agg(
        N=('number_of_decisions', 'sum') if 'number_of_decisions' in baselines else ('agreement', 'size'),
        agreement=('agreement', 'mean'),
        mean_realized_net_value_inr=('realized_net_value_inr', 'mean'),
        mean_regret_inr=('regret_inr', 'mean'),
    ).to_string()
    selected_json = json.dumps(selected, indent=2)
    return f'''# Sell-vs-Store Retrospective Validation Report

## Decision Model
For quantity Q in quintals, current price P0 and future price P1 in INR/quintal:
- Sell now = Q x P0.
- Effective stored quantity = Q x (1 - spoilage_rate).
- Storage cost = Q x 100 kg/quintal x storage_rate (INR/kg/month) x duration (months).
- Store value = effective quantity x P1 - storage cost - total transport cost.
- Incremental store value = store value - sell-now value.
- Choose `store` only when store value is strictly greater; ties choose `sell`.

The decision function accepts current price, forecast point price, quantity, duration, storage rate, spoilage assumption, and transport cost. It has no future-actual-price parameter.

## Dataset and Units
- Observed price source: `{Path(data_path).name}`, field `{PRICE_COLUMN}` labeled INR per quintal.
- Validated forecast source: `{Path(forecast_path).name}` from the Phase 2 rolling-origin validation. Failed rows are excluded.
- Quantity in this simulation: {assumptions['scenario_quantity_quintal']} quintal per decision. This is a scale-normalized scenario, not observed farmer quantity.
- All revenue, cost, value, and regret outputs are INR. All prices are INR/quintal and quantities are quintals.
- Evaluated crop/date coverage:

```text
{crop_stats}
```

## OBSERVED DATA
Historical current prices at each decision cutoff and future actual prices come from the labeled price observations represented in the Phase 2 forecast file. Rolling-origin forecasts, training cutoffs, horizons, and validated selected models come from Phase 2 artifacts. No farm acreage or farmer-specific market quantity is available for this simulation.

## ASSUMPTIONS
```json
{json.dumps(assumptions, indent=2)}
```
The storage rate values and crop spoilage values are retained from legacy code solely as configurable scenario assumptions. Their source does not document empirical calibration, and spoilage is applied once over the full holding decision. Transport cost is zero because no validated route-specific retrospective quote is present. None of these values are presented as observed farmer costs or outcomes.

## SIMULATED VARIABLES
The one-quintal quantity, storage duration, storage/spoilage costs, scenario multipliers, baseline actions, and resulting economic values are simulations. Storage duration is three months per forecast quarter for the base calculation.

## FORECAST VALUES AND UNCERTAINTY
The evaluator consumes out-of-sample forecasts and model identifiers from Phase 2; it does not retrain. The decision uses the forecast point value. Where Phase 2 native 95% ARIMA/SARIMA bounds are present, availability is marked; LSTM/Seasonal Naive have no interval and remain point-forecast-only. No heuristic interval is created. Price-multiplier sensitivity is labeled scenario analysis, not a prediction interval.

## Leakage Prevention and Historical Protocol
For each crop/model/fold/horizon, the decision date is the end of the training sample and must be strictly earlier than the future actual date. Current price is looked up only at that training cutoff. The forecast-based decision function never receives the future actual. Actual future price is passed only to a separate post-decision scoring step to calculate the retrospective actual-optimal decision, agreement, and regret. This is a historical decision simulation, not a causal farmer-benefit evaluation.

## Baselines
- Always Sell: choose sell at every decision date.
- Always Store: choose store at every decision date.
- Seasonal Naive: use the seasonal-naive out-of-sample Phase 2 forecast in the economic decision equation.
- No current heuristic baseline is included because its forecast clipping, crop multipliers, inconsistent units, and thresholds are undocumented and it is not an admissible research comparator.

Baseline results aggregated over crop/horizon rows:

```text
{baseline_text}
```

## Forecast-Error Sensitivity and Decision Agreement
The comparison is between the forecast-based action and the post-hoc action that would maximize the same simulated net value using the realized future price. False-store means forecast action was store while the hindsight action is sell; false-sell is the reverse. Regret is best hindsight net value minus realized value of the forecast-selected action. Mean absolute decision-value error compares forecast and realized economic value for the action actually selected.

```text
{error_sensitivity.to_string(index=False)}
```

Selected validated-model retrospective summaries:

{chr(10).join(selected_assessment)}

## Decision Summary
```text
{summary.to_string(index=False)}
```

## Sensitivity Analysis
The values below vary one configured scenario dimension at a time. They are sensitivity cases, not estimates of real-world probability or observed farmer conditions.

### Storage cost multipliers
```text
{storage_sens}
```

### Spoilage scenarios
```text
{spoilage_sens}
```

### Forecast price and duration scenarios
Full structured scenario rows are in `sell_store_sensitivity.csv`.

## Paper Table X: Sell-vs-Store Decision Performance
```text
{table_x.to_string(index=False)}
```

## Paper Table Y: Decision Sensitivity to Storage Cost and Spoilage
```text
{table_y.to_string(index=False)}
```

## Limitations
- Results are retrospective simulations on three rolling-origin folds, not farmer outcomes, causal effects, or income improvements.
- The evaluated quantity is a one-quintal scenario because farmer acreage/decision-specific quantity is not available.
- Legacy cost/spoilage assumptions lack observed provenance and time calibration; sensitivity results should not be interpreted as calibrated economic estimates.
- No route-specific transport quote or verified storage invoice is included.
- Future actual prices are used only for retrospective scoring and hindsight comparison, never for the forecast-based decision.
- RMSE-selected model selection is inherited unchanged from Phase 2; DM comparisons are underpowered at three paired origins and do not establish model superiority.
'''


def run_sell_store_research(
    price_data_path='price dataset (1).csv',
    predictions_path='forecast_predictions.csv',
    intervals_path='forecast_intervals.csv',
    config_path='experiment_config.json',
    assumptions_path='sell_store_assumptions.json',
    output_dir='.',
):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    assumptions = json.loads(Path(assumptions_path).read_text(encoding='utf-8'))
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    predictions = pd.read_csv(predictions_path)
    intervals = pd.read_csv(intervals_path)
    source_prices, _ = _source_prices(price_data_path)

    required_prediction_columns = {
        'crop', 'model', 'fold', 'horizon', 'train_end', 'forecast_date',
        'actual', 'predicted', 'validity_status', 'price_unit',
    }
    missing = required_prediction_columns - set(predictions.columns)
    if missing:
        raise ValueError(f'Validated prediction artifact missing columns: {sorted(missing)}')
    if not predictions['price_unit'].eq(PRICE_UNIT).all():
        raise ValueError('Forecast prices must be explicitly labeled INR per quintal')

    decisions = _decision_records(predictions, intervals, source_prices, assumptions)
    summary = _summary(decisions)
    baseline_rows = _baseline_records(decisions)
    baselines = _baseline_summary(baseline_rows)
    error_sensitivity = _forecast_error_sensitivity(decisions)
    sensitivity = _sensitivity(decisions, assumptions)
    table_x, table_y = _paper_tables(summary, sensitivity)
    selected = config.get('selected_models', {})

    decisions_out = decisions.reindex(columns=DECISION_COLUMNS)
    decisions_out.to_csv(output / 'sell_store_decisions.csv', index=False)
    summary.to_csv(output / 'sell_store_summary.csv', index=False)
    baselines.to_csv(output / 'sell_store_baseline_summary.csv', index=False)
    sensitivity.to_csv(output / 'sell_store_sensitivity.csv', index=False)
    error_sensitivity.to_csv(output / 'sell_store_forecast_error_sensitivity.csv', index=False)
    table_x.to_csv(output / 'table_x_sell_store_performance.csv', index=False)
    table_y.to_csv(output / 'table_y_sell_store_sensitivity.csv', index=False)
    report = _render_report(
        price_data_path, predictions_path, assumptions, decisions_out, summary,
        baseline_rows, sensitivity, error_sensitivity, table_x, table_y, selected,
    )
    (output / 'sell_store_validation_report.md').write_text(report, encoding='utf-8')
    _write_figures(output, decisions, summary, sensitivity)

    return {
        'decisions': decisions_out,
        'summary': summary,
        'baselines': baselines,
        'sensitivity': sensitivity,
        'forecast_error_sensitivity': error_sensitivity,
        'paper_table_x': table_x,
        'paper_table_y': table_y,
        'selected_models': selected,
    }
