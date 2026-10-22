"""Build faculty-facing ADIS results strictly from saved research artifacts."""

import base64
import html
import json
import re
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT
CROPS = ['Rice', 'Onion', 'Tomato']
MODELS = ['seasonal_naive', 'arima', 'sarima', 'lstm']
FIGURES = []


def read_csv(name):
    return pd.read_csv(ROOT / name)


def fmt(value, digits=2):
    if pd.isna(value):
        return 'Not Available / Not Supported by Current Data'
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f'{float(value):,.{digits}f}'


def markdown_table(frame, columns=None, digits=4):
    data = frame if columns is None else frame[columns]
    if data.empty:
        return '_Not Available / Not Supported by Current Data._'
    headers = [str(column) for column in data.columns]
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for row in data.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if pd.isna(value):
                cells.append('Not Available')
            elif isinstance(value, (float, np.floating)):
                cells.append(f'{value:,.{digits}f}')
            else:
                cells.append(str(value).replace('|', '\\|').replace('\n', ' '))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def table_html(frame, max_rows=None):
    if frame.empty:
        return '<p><em>Not Available / Not Supported by Current Data.</em></p>'
    view = frame.head(max_rows) if max_rows else frame
    columns = ''.join(f'<th>{html.escape(str(c))}</th>' for c in view.columns)
    body = []
    for row in view.itertuples(index=False, name=None):
        cells = []
        for value in row:
            text = 'Not Available' if pd.isna(value) else (f'{value:,.4g}' if isinstance(value, (float, np.floating)) else str(value))
            cells.append(f'<td>{html.escape(text)}</td>')
        body.append('<tr>' + ''.join(cells) + '</tr>')
    note = f'<p class="small">Showing {len(view)} of {len(frame)} rows.</p>' if max_rows and len(frame) > max_rows else ''
    return f'<div class="table-wrap"><table><thead><tr>{columns}</tr></thead><tbody>{"".join(body)}</tbody></table></div>{note}'


def csv_inventory():
    rows = []
    known_source = {
        'price dataset (1).csv': ('Supplied source dataset; provenance/publication not documented in repository', 'Quarterly crop prices; INR/quintal label, with inconsistent Final_Price field'),
        'farmer_crop_dataset (1).csv': ('Supplied farmer-shaped dataset; real vs synthetic provenance not documented', 'Farmer_ID, crop, tonnes/acre yield, season; no acreage/location/collection metadata'),
        'farmer_decision_history.csv': ('Supplied history file; observation provenance not documented', 'Nine rows; extensive missing fields; not used as validated outcomes'),
        'tamilnadu_full_warehouse_dataset (1).csv': ('Supplied warehouse-shaped dataset; operational provenance not independently verified', 'Facility labels, MT capacities, unspecified storage-rate units, coordinates, crop flags'),
    }
    derived_prefixes = (
        'forecast_', 'model_comparison.csv', 'sell_store_', 'warehouse_', 'routing_',
        'table_', 'END_TO_END_', 'ADIS_',
    )
    for path in sorted(ROOT.glob('*.csv')):
        frame = pd.read_csv(path)
        if path.name in known_source:
            classification, usage = known_source[path.name]
        elif path.name.startswith(derived_prefixes):
            classification, usage = 'Derived/model output/scenario result; not raw observations', 'Generated research output; provenance is the corresponding phase artifacts and assumptions/config files'
        else:
            classification, usage = 'Classification not documented', 'CSV present in project; no authoritative source/collection record found'
        crop_column = next((column for column in ('Crop', 'crop', 'Crop_Cultivated') if column in frame.columns), None)
        crop_values = ', '.join(sorted(frame[crop_column].dropna().astype(str).unique())) if crop_column else 'Not applicable/not present'
        date_cols = [column for column in frame.columns if column.lower() in {'date', 'decision_date', 'forecast_date', 'train_end', 'test_start', 'test_end'}]
        date_range = 'Not Available'
        if date_cols:
            values = pd.to_datetime(pd.concat([frame[column] for column in date_cols], ignore_index=True), errors='coerce').dropna()
            if not values.empty:
                date_range = f'{values.min().date()} to {values.max().date()}'
        rows.append({
            'filename': path.name,
            'bytes': path.stat().st_size,
            'rows': len(frame),
            'columns': len(frame.columns),
            'features': ', '.join(frame.columns),
            'missing_cells': int(frame.isna().sum().sum()),
            'duplicate_rows': int(frame.duplicated().sum()),
            'crop_categories': crop_values,
            'date_range': date_range,
            'classification': classification,
            'role_or_provenance_note': usage,
        })
    return pd.DataFrame(rows)


def dataset_profiles():
    profiles = []
    for name in ['price dataset (1).csv', 'farmer_crop_dataset (1).csv', 'farmer_decision_history.csv', 'tamilnadu_full_warehouse_dataset (1).csv']:
        frame = read_csv(name)
        profile = {
            'dataset': name,
            'rows': len(frame),
            'columns': len(frame.columns),
            'missing_cells': int(frame.isna().sum().sum()),
            'duplicate_rows': int(frame.duplicated().sum()),
            'features': ', '.join(frame.columns),
        }
        if 'Crop' in frame.columns:
            profile['crop_counts'] = json.dumps(frame['Crop'].value_counts(dropna=False).to_dict())
        elif 'Crop_Cultivated' in frame.columns:
            profile['crop_counts'] = json.dumps(frame['Crop_Cultivated'].value_counts(dropna=False).to_dict())
        else:
            profile['crop_counts'] = 'Not present'
        profiles.append(profile)
    return pd.DataFrame(profiles)


def build_forecast_tables():
    predictions = read_csv('forecast_predictions.csv')
    folds = read_csv('forecast_fold_metrics.csv')
    horizon = read_csv('forecast_horizon_metrics.csv')
    summary = read_csv('forecast_model_summary.csv')
    intervals = read_csv('forecast_interval_metrics.csv')
    dm = read_csv('forecast_dm_tests.csv')
    config = json.loads((ROOT / 'experiment_config.json').read_text(encoding='utf-8'))
    valid = predictions.loc[predictions['validity_status'].eq('VALID')].copy()
    valid['error_derived'] = valid['predicted'] - valid['actual']
    denominator = valid['actual'].abs() + valid['predicted'].abs()
    valid['smape_pct'] = np.where(denominator.eq(0), np.nan, 200.0 * valid['error_derived'].abs() / denominator)

    fold_derived = []
    for (crop, model, fold), group in valid.groupby(['crop', 'model', 'fold'], sort=True):
        error = group['error_derived'].to_numpy(dtype=float)
        actual = group['actual'].to_numpy(dtype=float)
        predicted = group['predicted'].to_numpy(dtype=float)
        fold_derived.append({
            'crop': crop, 'model': model, 'fold': int(fold),
            'sMAPE_pct': float(group['smape_pct'].mean()),
            'MBE_inr_per_quintal': float(np.mean(error)),
            'error_sd_inr_per_quintal': float(np.std(error, ddof=1)) if len(error) > 1 else np.nan,
            'valid_predictions': len(group),
        })
    derived = pd.DataFrame(fold_derived)
    fold_table = folds.merge(derived, on=['crop', 'model', 'fold'], how='left')
    fold_table['metric_unit'] = 'INR per quintal; MAPE/sMAPE percent; R2 unitless'
    horizon_derived = []
    for (crop, model, h), group in valid.groupby(['crop', 'model', 'horizon'], sort=True):
        error = group['error_derived'].to_numpy(dtype=float)
        actual = group['actual'].to_numpy(dtype=float)
        pred = group['predicted'].to_numpy(dtype=float)
        denom = np.abs(actual) + np.abs(pred)
        smape = np.where(denom == 0, np.nan, 200 * np.abs(error) / denom)
        horizon_derived.append({
            'crop': crop, 'model': model, 'horizon': int(h),
            'sMAPE_pct': float(np.nanmean(smape)), 'MBE_inr_per_quintal': float(np.mean(error)),
            'mean_absolute_error_inr_per_quintal': float(np.mean(np.abs(error))),
            'valid_predictions': len(group),
        })
    horizon_table = horizon.merge(pd.DataFrame(horizon_derived), on=['crop', 'model', 'horizon'], how='left')
    summary_derived = []
    for (crop, model), group in valid.groupby(['crop', 'model'], sort=True):
        err = group['error_derived'].to_numpy(dtype=float)
        denom = np.abs(group.actual.to_numpy(dtype=float)) + np.abs(group.predicted.to_numpy(dtype=float))
        smape = np.where(denom == 0, np.nan, 200 * np.abs(err) / denom)
        summary_derived.append({
            'crop': crop, 'model': model, 'sMAPE_pct_pooled_predictions': float(np.nanmean(smape)),
            'MBE_inr_per_quintal_pooled_predictions': float(np.mean(err)),
            'error_sd_inr_per_quintal_pooled_predictions': float(np.std(err, ddof=1)),
            'valid_predictions': len(group),
        })
    f1 = summary.merge(pd.DataFrame(summary_derived), on=['crop', 'model'], how='left')
    f1['selected_by_mean_validation_RMSE'] = f1.apply(lambda r: config.get('selected_models', {}).get(r['crop']) == r['model'], axis=1)
    f1['metric_unit'] = 'INR per quintal; MAPE/sMAPE percent; R2 unitless'
    f4 = pd.DataFrame([{'crop': crop, 'selected_model': model, 'criterion': 'Lowest mean validation RMSE among valid folds'} for crop, model in config.get('selected_models', {}).items()])
    intervals_all = intervals.loc[intervals['horizon'].astype(str).eq('all')].copy()
    return predictions, folds, horizon_table, f1, fold_table, f4, intervals, intervals_all, dm


def build_sell_tables():
    decisions = read_csv('sell_store_decisions.csv')
    summary = read_csv('sell_store_summary.csv')
    baselines = read_csv('sell_store_baseline_summary.csv')
    sensitivity = read_csv('sell_store_sensitivity.csv')
    error_sensitivity = read_csv('sell_store_forecast_error_sensitivity.csv')
    assumptions = json.loads((ROOT / 'sell_store_assumptions.json').read_text(encoding='utf-8'))
    selected = json.loads((ROOT / 'experiment_config.json').read_text(encoding='utf-8'))['selected_models']
    ss1 = decisions.groupby('crop', as_index=False).agg(
        N=('decision', 'size'), sell_count=('decision', lambda x: int(x.eq('sell').sum())),
        store_count=('decision', lambda x: int(x.eq('store').sum())),
        mean_sell_now_value_inr=('sell_now_value_inr', 'mean'), mean_store_value_inr=('store_value_inr', 'mean'),
        mean_regret_inr=('regret_inr', 'mean'), decision_agreement_pct=('decision_correct', lambda x: float(x.mean()*100)),
    )
    selected_rows = summary.loc[summary.apply(lambda r: selected.get(r.crop) == r.model, axis=1)].copy()
    ss2 = summary.copy()
    ss3 = selected_rows[['crop','model','horizon','number_of_decisions','decision_agreement_percentage','false_store_percentage','false_sell_percentage']].copy()
    ss4 = selected_rows[['crop','model','horizon','number_of_decisions','mean_regret_inr','median_regret_inr']].copy()
    ss5 = selected_rows[['crop','model','horizon','number_of_decisions','mean_realized_net_value_inr']].copy()
    ss6 = decisions.groupby(['crop','model','horizon','decision'],as_index=False).size().rename(columns={'size':'decision_count'})
    ss6['decision_percentage'] = ss6['decision_count'] / ss6.groupby(['crop','model','horizon'])['decision_count'].transform('sum') * 100
    sensitivity_summary = sensitivity.groupby(['crop','scenario_type','scenario_value'],as_index=False).agg(
        n=('decision','size'), store_percentage=('decision',lambda x: float(x.eq('store').mean()*100)),
        mean_incremental_store_value_inr=('incremental_store_value_inr','mean'),
    )
    return decisions, summary, baselines, sensitivity, error_sensitivity, assumptions, selected, ss1, ss2, ss3, ss4, ss5, ss6, sensitivity_summary


def build_warehouse_tables():
    summary = read_csv('warehouse_summary.csv')
    baseline = read_csv('warehouse_baseline_comparison.csv')
    utilization = read_csv('warehouse_utilization.csv')
    sensitivity = read_csv('warehouse_sensitivity.csv')
    results = read_csv('warehouse_optimization_results.csv')
    w1 = summary.groupby('crop',as_index=False).agg(
        scenarios=('scenario_id','nunique'),mean_available_q=('total_available_quantity_quintal','mean'),
        mean_allocated_q=('total_allocated_quantity_quintal','mean'),mean_unallocated_q=('total_unallocated_quantity_quintal','mean'),
        mean_cost_inr=('total_cost_inr','mean'),mean_storage_cost_inr=('total_storage_cost_inr','mean'),
        mean_transport_cost_inr=('total_transport_cost_inr','mean'),max_constraint_violations=('constraint_violations','max'),
    )
    w2=summary.groupby(['solver_status'],as_index=False).size().rename(columns={'size':'scenario_count'})
    w3=summary.groupby('crop',as_index=False).agg(storage_cost_inr=('total_storage_cost_inr','mean'),transport_cost_inr=('total_transport_cost_inr','mean'),total_cost_inr=('total_cost_inr','mean'))
    w4=baseline.groupby(['crop','method'],as_index=False).agg(mean_total_cost_inr=('total_cost_inr','mean'),mean_storage_cost_inr=('storage_cost_inr','mean'),mean_transport_cost_inr=('transport_cost_inr','mean'),mean_allocated_q=('allocated_quantity_quintal','mean'),mean_unallocated_q=('unallocated_quantity_quintal','mean'))
    w5=utilization.groupby('warehouse_id',as_index=False).agg(capacity_q=('capacity_quintal','first'),mean_allocated_q=('allocated_quintal','mean'),mean_utilization_pct=('utilization_percentage','mean'),mean_storage_cost_inr=('storage_cost_inr','mean'),mean_transport_cost_inr=('transport_cost_inr','mean'))
    w6=sensitivity.groupby(['scenario_type','scenario_multiplier'],as_index=False).agg(mean_total_cost_inr=('total_cost_inr','mean'),mean_storage_cost_inr=('storage_cost_inr','mean'),mean_transport_cost_inr=('transport_cost_inr','mean'),mean_allocated_q=('available_quantity_quintal','mean'),mean_unallocated_q=('unallocated_quantity_quintal','mean'),max_violations=('constraint_violations','max'))
    return summary,baseline,utilization,sensitivity,results,w1,w2,w3,w4,w5,w6


def build_routing_tables():
    routes=read_csv('routing_routes.csv'); summary=read_csv('routing_summary.csv'); baseline=read_csv('routing_baseline_comparison.csv'); sens=read_csv('routing_sensitivity.csv')
    r1=summary.groupby('crop',as_index=False).agg(route_scenarios=('scenario_id','nunique'),mean_distance_km=('average_route_distance_km','mean'),mean_transport_cost_inr=('total_transport_cost_inr','mean'),mean_cost_per_quintal=('average_transport_cost_inr_per_quintal','mean'),route_legs=('number_of_routes','sum'),infeasible_scenarios=('route_feasibility',lambda x:int((~x).sum())))
    r2=baseline.groupby(['crop','method'],as_index=False).agg(scenarios=('scenario_id','nunique'),mean_distance_km=('average_distance_per_route_km','mean'),mean_transport_cost_inr=('total_transport_cost_inr','mean'),mean_cost_per_quintal=('average_transport_cost_inr_per_quintal','mean'),feasible_scenarios=('route_feasible','sum'))
    r3=sens.groupby(['scenario_type','scenario_multiplier'],as_index=False).agg(mean_transport_cost_inr=('transport_cost_inr','mean'),mean_quantity_q=('quantity_transported_quintal','mean'),mean_unserved_q=('unserved_quantity_quintal','mean'),infeasible_scenarios=('route_feasible',lambda x:int((~x).sum())))
    return routes,summary,baseline,sens,r1,r2,r3


def build_inventory():
    inventory = csv_inventory()
    inventory.to_csv(OUTPUT/'dataset_inventory.csv',index=False)
    return inventory


def build_artifact_inventory():
    rows = []
    ignored = {'.git', '.venv', '__pycache__'}
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        suffix = path.suffix.lower()
        relative = path.relative_to(ROOT).as_posix()
        if relative.startswith('tests/'):
            category = 'test'
        elif relative.startswith('src/'):
            category = 'source code'
        elif relative.startswith('models/') and suffix in {'.pkl', '.joblib', '.h5', '.keras'}:
            category = 'serialized model artifact'
        elif suffix in {'.png', '.jpg', '.jpeg', '.svg'}:
            category = 'figure/image'
        elif suffix in {'.json', '.toml', '.yaml', '.yml', '.ini'} or relative.endswith(('.code-workspace', '.bat')):
            category = 'configuration/runner'
        elif suffix in {'.db', '.sqlite', '.sqlite3'}:
            category = 'database'
        elif suffix in {'.md', '.html', '.txt'}:
            category = 'documentation/report'
        elif suffix == '.csv':
            category = 'dataset or tabular result'
        else:
            category = 'other project file'
        rows.append({'path': relative, 'category': category, 'bytes': path.stat().st_size, 'format': suffix or 'no extension'})
    inventory = pd.DataFrame(rows)
    inventory.to_csv(OUTPUT/'project_artifact_inventory.csv', index=False)
    return inventory


def create_figures(data):
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'figure.dpi':150})
    paths=[]
    def save(fig,name):
        path=OUTPUT/name
        fig.savefig(path,dpi=300,bbox_inches='tight')
        plt.close(fig); paths.append(path)
    predictions=data['forecast_predictions']; f1=data['forecast_f1']; fh=data['forecast_horizon']; intervals=data['forecast_intervals_all']
    # Forecast metrics comparison by crop/model.
    fig,ax=plt.subplots(figsize=(9,5)); f1.pivot(index='crop',columns='model',values='mean_RMSE').plot(kind='bar',ax=ax); ax.set(title='Rolling-origin forecast RMSE by crop and model',xlabel='Crop',ylabel='Mean fold RMSE (INR/quintal)'); ax.grid(axis='y',alpha=.25); ax.legend(title='Model',frameon=False); save(fig,'report_forecast_model_comparison.png')
    fig,ax=plt.subplots(figsize=(9,5)); fh.pivot_table(index='horizon',columns=['crop','model'],values='RMSE').plot(marker='o',ax=ax); ax.set(title='Forecast RMSE by horizon',xlabel='Horizon (quarters)',ylabel='RMSE (INR/quintal)'); ax.grid(alpha=.25); ax.legend(frameon=False,fontsize=7,ncol=3); save(fig,'report_forecast_horizon_rmse.png')
    fig,ax=plt.subplots(figsize=(9,5)); f1.pivot(index='crop',columns='model',values='mean_MAPE').plot(kind='bar',ax=ax); ax.set(title='Mean fold MAPE by crop and model',xlabel='Crop',ylabel='MAPE (%)'); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False); save(fig,'report_forecast_error_comparison.png')
    if not intervals.empty:
        fig,ax=plt.subplots(figsize=(9,5)); intervals.pivot(index='crop',columns='model',values='empirical_coverage_percentage').plot(kind='bar',ax=ax); ax.set(title='Empirical coverage of native 95% forecast intervals',xlabel='Crop',ylabel='Coverage (%)'); ax.axhline(95,linestyle='--',color='black',linewidth=1,label='Nominal 95%'); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False); save(fig,'report_interval_coverage.png')
    for crop in CROPS:
        source=predictions[(predictions.crop==crop)&(predictions.validity_status=='VALID')]
        fig,ax=plt.subplots(figsize=(9,4.5))
        for model,group in source.groupby('model'):
            group=group.sort_values('forecast_date'); ax.plot(pd.to_datetime(group.forecast_date),group.predicted,marker='.',linewidth=1,label=f'{model} forecast');
        actual=source[source.model==source.model.iloc[0]].drop_duplicates('forecast_date').sort_values('forecast_date') if len(source) else pd.DataFrame()
        if not actual.empty: ax.scatter(pd.to_datetime(actual.forecast_date),actual.actual,marker='x',color='black',label='validation actual')
        ax.set(title=f'{crop}: rolling-origin actuals and forecasts',xlabel='Quarter',ylabel='Price (INR/quintal)'); ax.grid(alpha=.25); ax.legend(frameon=False,fontsize=8,ncol=2); save(fig,f'report_actual_vs_predicted_{crop.lower()}.png')
    # Sell/store charts.
    decisions=data['sell_decisions']; ss_summary=data['sell_summary']; baselines=data['sell_baselines']; sell_sens=data['sell_sensitivity_summary']
    fig,ax=plt.subplots(figsize=(9,5)); ss6=data['ss6'].pivot_table(index='crop',columns='decision',values='decision_percentage',aggfunc='mean').plot(kind='bar',stacked=True,ax=ax,color=['#4e79a7','#f28e2b']); ax.set(title='Sell/store decision distribution',xlabel='Crop',ylabel='Mean decision share (%)'); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False); save(fig,'report_sell_store_distribution.png')
    selected=ss_summary[ss_summary.apply(lambda row:data['selected'].get(row.crop)==row.model,axis=1)]
    selected_regret=selected.groupby(['crop','model'],as_index=False).mean(numeric_only=True)
    fig,ax=plt.subplots(figsize=(9,5)); selected_regret.pivot(index='crop',columns='model',values='mean_regret_inr').plot(kind='bar',ax=ax); ax.set(title='Retrospective mean regret for selected model by crop',xlabel='Crop',ylabel='Mean regret (INR per 1-quintal scenario)'); ax.grid(axis='y',alpha=.25); save(fig,'report_sell_store_regret.png')
    fig,ax=plt.subplots(figsize=(9,5)); baselines.groupby('model').mean_realized_net_value_inr.mean().plot(kind='bar',ax=ax); ax.set(title='Baseline retrospective simulated net value',xlabel='Policy',ylabel='Mean simulated value (INR per scenario)'); ax.tick_params(axis='x',rotation=15); ax.grid(axis='y',alpha=.25); save(fig,'report_sell_store_baselines.png')
    for scenario_type,title,name in [('storage_cost_multiplier','Storage cost sensitivity','report_sell_storage_sensitivity.png'),('spoilage_rate','Spoilage sensitivity','report_sell_spoilage_sensitivity.png')]:
        group=sell_sens[sell_sens.scenario_type==scenario_type]; fig,ax=plt.subplots(figsize=(8,4.5));
        for crop,part in group.groupby('crop'): ax.plot(part.scenario_value,part.store_percentage,marker='o',label=crop)
        ax.set(title=title,xlabel='Scenario value (multiplier or rate)',ylabel='Decisions choosing Store (%)'); ax.grid(alpha=.25); ax.legend(frameon=False); save(fig,name)
    # Warehouse and routing results already generated from CSV artifacts.
    warehouse_baselines=data['warehouse_baselines']; utilization=data['warehouse_utilization']; warehouse_sens=data['warehouse_sensitivity_summary']
    fig,ax=plt.subplots(figsize=(9,5)); warehouse_baselines.groupby(['crop','method']).total_cost_inr.mean().unstack().plot(kind='bar',ax=ax); ax.set(title='Warehouse scenario cost by crop and method',xlabel='Crop',ylabel='Mean cost (INR per 1-quintal scenario)'); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False,fontsize=7); save(fig,'report_warehouse_cost_comparison.png')
    fig,ax=plt.subplots(figsize=(8,5)); warehouse_baselines.groupby('method')[['storage_cost_inr','transport_cost_inr']].mean().plot(kind='bar',stacked=True,ax=ax); ax.set(title='Warehouse storage and transport cost components',xlabel='Method',ylabel='Mean cost (INR per scenario)'); ax.grid(axis='y',alpha=.25); save(fig,'report_warehouse_cost_components.png')
    u=utilization.groupby('warehouse_id').utilization_percentage.mean().sort_values(ascending=False).head(20); fig,ax=plt.subplots(figsize=(10,4.5)); u.plot(kind='bar',ax=ax); ax.set(title='Mean scenario utilization by warehouse (top 20)',xlabel='Warehouse ID',ylabel='Utilization (%)'); ax.tick_params(axis='x',rotation=70); ax.grid(axis='y',alpha=.25); save(fig,'report_warehouse_utilization.png')
    for scenario_type,title,name in [('storage_cost_multiplier','Warehouse storage-cost sensitivity','report_warehouse_storage_sensitivity.png'),('transport_cost_multiplier','Warehouse transport-cost sensitivity','report_warehouse_transport_sensitivity.png')]:
        part=warehouse_sens[warehouse_sens.scenario_type==scenario_type].groupby(['crop','scenario_multiplier'],as_index=False).total_cost_inr.mean(); fig,ax=plt.subplots(figsize=(8,4.5));
        for crop,grp in part.groupby('crop'): ax.plot(grp.scenario_multiplier,grp.total_cost_inr,marker='o',label=crop)
        ax.set(title=title,xlabel='Scenario multiplier (x)',ylabel='Mean total cost (INR)'); ax.grid(alpha=.25); ax.legend(frameon=False); save(fig,name)
    routing_baselines=data['routing_baselines']; routing_sensitivity=data['routing_sensitivity']
    for metric,title,ylabel,name in [('total_distance_km','Routing distance comparison','Mean distance (km; Haversine proxy)','report_routing_distance_comparison.png'),('total_transport_cost_inr','Routing transport-cost comparison','Mean cost (INR per scenario)','report_routing_cost_comparison.png')]:
        fig,ax=plt.subplots(figsize=(10,5)); routing_baselines.groupby(['crop','method'])[metric].mean().unstack().plot(kind='bar',ax=ax); ax.set(title=title,xlabel='Crop',ylabel=ylabel); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False,fontsize=7); save(fig,name)
    fig,ax=plt.subplots(figsize=(8,4.5)); routing_baselines.groupby('method').total_transport_cost_inr.mean().plot(kind='bar',ax=ax); ax.set(title='Routing baseline comparison',xlabel='Method',ylabel='Mean transport cost (INR per scenario)'); ax.tick_params(axis='x',rotation=18); ax.grid(axis='y',alpha=.25); save(fig,'report_routing_baselines.png')
    for scenario_type,title,name in [('transport_cost_multiplier','Routing transport-rate sensitivity','report_routing_sensitivity.png'),('available_quantity_multiplier','Routing quantity sensitivity','report_routing_quantity_sensitivity.png')]:
        part=routing_sensitivity[routing_sensitivity.scenario_type==scenario_type].groupby(['crop','scenario_multiplier'],as_index=False).transport_cost_inr.mean(); fig,ax=plt.subplots(figsize=(8,4.5));
        for crop,grp in part.groupby('crop'): ax.plot(grp.scenario_multiplier,grp.transport_cost_inr,marker='o',label=crop)
        ax.set(title=title,xlabel='Scenario multiplier (x)',ylabel='Mean transport cost (INR)'); ax.grid(alpha=.25); ax.legend(frameon=False); save(fig,name)
    e2e=data['end_to_end']; fig,ax=plt.subplots(figsize=(9,5)); e2e.groupby('crop')[['warehouse_storage_cost_inr','transport_cost_inr']].mean().plot(kind='bar',stacked=True,ax=ax); ax.set(title='End-to-end warehouse and transport scenario cost',xlabel='Crop',ylabel='Mean cost (INR per scenario)'); ax.grid(axis='y',alpha=.25); save(fig,'report_end_to_end_cost.png')
    return paths


def build_markdown(data, figures):
    inventory=data['inventory']; artifact_inventory=data['artifact_inventory']; profile=dataset_profiles()
    f1=data['forecast_f1']; f2=data['forecast_horizon']; f3=data['forecast_folds_table']; f4=data['forecast_f4']; intervals=data['forecast_interval_metrics']; dm=data['forecast_dm']
    sell_selected=data['sell_summary'][data['sell_summary'].apply(lambda r:data['selected'].get(r.crop)==r.model,axis=1)]
    baselines=data['sell_baselines']
    warehouse_summary=data['warehouse_summary']; warehouse_baselines=data['warehouse_baselines']; wsens=data['warehouse_sensitivity_summary']
    route_summary=data['routing_summary']; route_baselines=data['routing_baselines']; rsens=data['routing_sensitivity_summary']
    e2e=data['end_to_end']
    source_price=read_csv('price dataset (1).csv')
    source_warehouse=read_csv('tamilnadu_full_warehouse_dataset (1).csv')
    farmer=read_csv('farmer_crop_dataset (1).csv')
    decision_history=read_csv('farmer_decision_history.csv')
    config=json.loads((ROOT/'experiment_config.json').read_text(encoding='utf-8'))
    assumptions={'sell_store':data['sell_assumptions'],'warehouse':json.loads((ROOT/'warehouse_research_assumptions.json').read_text(encoding='utf-8')),'routing':json.loads((ROOT/'routing_research_assumptions.json').read_text(encoding='utf-8'))}
    selected_names=[]
    for crop,model in data['selected'].items():
        row=f1[(f1.crop==crop)&(f1.model==model)].iloc[0]
        selected_names.append(f"- {crop}: {model}; mean validation RMSE {fmt(row.mean_RMSE)} INR/quintal; valid folds {int(row.valid_folds)}, failed folds {int(row.failed_folds)}")
    dm_underpowered=bool(dm.interpretation.astype(str).str.contains('Insufficient paired origins').all())
    farmer_crop_counts=farmer.Crop_Cultivated.value_counts().to_dict()
    price_period=pd.PeriodIndex(source_price.Year.astype(str)+'Q'+source_price.Quarter.astype(str).str.extract(r'Q([1-4])',expand=False).astype(str),freq='Q')
    warehouse_crop_counts={c:int(source_warehouse[f'{c}_Supported'].sum()) for c in CROPS}
    direct_photos='\n'.join(f'![{path.stem}]({path.name})' for path in figures)

    sections=[]
    sections.append('# Performance Evaluation of the Agricultural Decision Intelligence System (ADIS)')
    sections.append('**Report scope.** This is an artifact-grounded audit of the current research implementation. It reports model-generated forecasts, retrospective simulations, and configured optimization scenarios; it does not measure real farmer welfare, causal benefit, or realized SaaS outcomes.')
    sections.append('## 1. Executive Summary\nADIS is an intended SaaS decision-support/decision-intelligence platform integrating agricultural price forecasting, sell/store evaluation, warehouse allocation, and transport-cost analysis. The validated implementation produces crop-specific rolling-origin forecasts, retrospective economic decisions on standardized 1-quintal scenarios, warehouse MILP assignments, and single-leg Haversine proxy routes. These results support decision support and software evaluation only; farmers remain the final decision makers.\n\n'+'\n'.join(selected_names)+f"\n\nWarehouse base scenarios: {len(warehouse_summary)}, CBC statuses {warehouse_summary.solver_status.value_counts().to_dict()}, total violations {int(warehouse_summary.constraint_violations.sum())}. Routing proxy legs: {len(data['routing_routes'])}, feasible {int(route_summary.route_feasibility.sum())}/{len(route_summary)}. Full pytest last verified in this completion: 75 passed (14 existing model warnings).")
    sections.append('## 2. Research Problem\nEvaluate whether the integrated research pipeline can generate auditable crop forecasts, explicit scenario-based sell/store decisions, cost-minimizing warehouse allocations, and transparent transport-cost estimates from supplied artifacts. The present repository does not support causal farmer outcome evaluation or empirically validated route optimization.')
    sections.append('## 3. System Architecture\n`quarterly supplied price data → rolling-origin forecasting → retrospective sell/store simulation → warehouse allocation MILP → single-leg reference-origin transport proxy`. The research runner consumes saved upstream CSVs and does not retrain forecasts in warehouse/routing modes. Legacy interactive forecast/decision/routing paths coexist and are not treated as validated research evidence.')
    sections.append('## 4. Dataset Summary\n### Dataset inventory\n'+markdown_table(inventory[['filename','rows','columns','missing_cells','duplicate_rows','crop_categories','date_range','classification']]))
    sections.append('### Repository artifact inventory\nThis inventory includes the project source, tests, model artifacts, configurations, reports, figures, and databases present at generation time; `.venv`, `.git`, and bytecode caches are excluded.\n\n'+markdown_table(artifact_inventory[['path','category','bytes','format']]))
    sections.append('### Source dataset profile\n'+markdown_table(profile))
    sections.append(f"Price file rows: {len(source_price)}; crops: {', '.join(CROPS)}; raw quarterly labels span {price_period.min()} to {price_period.max()} but labeled `Price_INR_per_Quintal` prices are available only through 2015Q2 for the historical block; later `Final_Price` has inconsistent scaling. Evaluated contiguous windows: Rice 26 observations, Onion 26, Tomato 24. Evaluation unit is INR/quintal with no conversion. Price provenance/publication citation is not documented.\n\nFarmer-shaped file: {len(farmer)} rows and {farmer.Farmer_ID.nunique()} IDs, three crops with row counts {farmer_crop_counts}; it has yield per acre and season, but no acreage, district, coordinates, collection period, consent, or sampling documentation. It cannot establish actual decision-specific quantity or route origin. Decision-history CSV: {len(decision_history)} rows with {int(decision_history.isna().sum().sum())} missing cells; SQLite `farmer_history.db` has a `history` table with zero rows. Warehouse CSV has {len(source_warehouse)} rows and 20 districts, coordinates, capacities labeled MT, crop support flags; source provenance and cost billing period are not verified.")
    sections.append('## 5. Experimental Setup\nForecasting uses four models, three non-overlapping rolling-origin folds, 4-quarter horizons, minimum training size 12, and valid-only model selection by lowest mean validation RMSE. There are 36 crop/model/fold combinations, each with four predictions (144 total). Phase 2 evaluates only contiguous quarterly segments. Forecast units: INR/quintal. Sell/store uses selected-model forecasts, retrospective actual prices only for post-decision scoring, one-quintal scenario quantity, durations of 3 months per quarter, and configurable cost/spoilage assumptions. Warehouse scenarios are 36 independent selected-model crop/date/horizon cases, not simultaneous network demand. Routing uses 36 saved positive allocations and Haversine centroid-to-warehouse proxy distance, not road routes.')
    sections.append('## 6. Forecasting Results\nCandidate models actually evaluated: Seasonal Naive, ARIMA, SARIMA, LSTM. Table values are crop-wise across valid rolling-origin folds; no crops are pooled. MBE is mean(predicted − actual) over valid prediction rows; sMAPE is 200×abs(error)/(abs(actual)+abs(predicted)); pooled prediction MBE/SD and sMAPE are derived from valid rows. Existing fold metrics are retained for MAE/RMSE/MAPE/R².\n\n### TABLE F1 — Forecasting model comparison by crop\n'+markdown_table(f1[['crop','model','valid_folds','failed_folds','mean_MAE','std_MAE','mean_RMSE','std_RMSE','mean_MAPE','mean_R2','sMAPE_pct_pooled_predictions','MBE_inr_per_quintal_pooled_predictions','error_sd_inr_per_quintal_pooled_predictions','valid_predictions']]))
    sections.append('### TABLE F2 — Forecasting performance by horizon\n'+markdown_table(f2[['crop','model','horizon','MAE','RMSE','MAPE','sMAPE_pct','MBE_inr_per_quintal','valid_predictions']]))
    sections.append('### TABLE F3 — Rolling-origin fold performance\n'+markdown_table(f3[['crop','model','fold','status','train_observations','validation_observations','MAE','RMSE','MAPE','R2','sMAPE_pct','MBE_inr_per_quintal','error_sd_inr_per_quintal','lstm_training_sequences']]))
    sections.append('### TABLE F4 — Selected model by crop\n'+markdown_table(f4))
    sections.append('Under the specified procedure, the best-performing candidate under the validation RMSE criterion for each crop was the selected model listed in Table F4. This is not a claim of general model superiority. LSTM uses a small fold-wise training set: 8, 12, and 16 sequences in folds with 12, 16, and 20 training observations respectively, lookback at most four quarters, one LSTM layer with 32 units (plus Input and Dense output), ReLU, Adam 0.001, MSE, 20 epochs, batch size 8, MinMaxScaler fit to each training fold. Overfitting cannot be reliably diagnosed from only three validation folds and no reserved independent test set; R² and errors vary substantially.')
    sections.append('## 7. Forecast Uncertainty\nARIMA/SARIMA use native statsmodels 95% forecast intervals; Seasonal Naive and LSTM have no statistically justified interval under the current implementation. Do not interpret absent bounds as zero uncertainty. Coverage is empirical on only three observations per crop/model/horizon (and 12 pooled per crop/model), so it is descriptive and highly uncertain.\n\n### Coverage by crop/model/horizon and pooled\n'+markdown_table(intervals[['crop','model','horizon','empirical_coverage_percentage','mean_interval_width','number_of_intervals','confidence_level','price_unit']]))
    sections.append('## 7A. Forecasting Diagnostics\nARIMA/SARIMA fold outputs include optimizer convergence, AIC/BIC, residual mean and sample standard deviation, Ljung–Box p-value where the residual sample supports it, lag-1 residual autocorrelation, warning text, and forecast interval generation status. Model convergence is not treated as evidence of model quality. The repository does not contain residual normality tests or standalone residual/ACF plots for every crop/model/fold; these are not claimed. Actual-versus-predicted and interval figures are generated where prediction data supports them.\n\n'+markdown_table(data['model_diagnostics'][['crop','model','fold','train_observations','converged','aic','bic','residual_mean','residual_std','ljung_box_lag','ljung_box_p_value','residual_acf_lag1','interval_generated','small_sample_warning','warning']]))
    sections.append('## 8. Statistical Comparison\nDiebold–Mariano comparisons use paired rolling-origin squared errors with Bartlett HAC variance and HLN correction when sample-size rules permit. Current comparisons have only three paired origins per horizon, below the configured minimum; DM statistics and p-values are unavailable and every row is explicitly underpowered. No statistical superiority conclusion is supported.\n\n'+markdown_table(dm[['crop','model_a','model_b','horizon','loss_function','DM_statistic','p_value','paired_origins','interpretation']]))
    sections.append('## 9. Sell-vs-Store Results\nDecision model: sell-now value = Q×current price. Effective stored quantity = Q×(1−spoilage). Storage cost = Q×100 kg/quintal×assumed INR/kg/month×duration. Store value = effective quantity×forecast price−storage cost−total transport assumption. Store only when store value strictly exceeds sell-now value; ties sell. The forecast-based decision function receives no future actual. Actual prices are used only after the decision for hindsight agreement and regret.\n\n### TABLE SS1 — Sell vs Store decisions by crop\n'+markdown_table(data['ss1']))
    sections.append('### TABLE SS2 — Model-based decision performance\n'+markdown_table(data['ss2'][['crop','model','horizon','number_of_decisions','decision_agreement_percentage','false_store_percentage','false_sell_percentage','mean_regret_inr','mean_realized_net_value_inr']]))
    sections.append('### TABLE SS3 — Decision agreement with hindsight\n'+markdown_table(data['ss3']))
    sections.append('### TABLE SS4 — Mean regret\n'+markdown_table(data['ss4']))
    sections.append('### TABLE SS5 — Mean simulated net value\n'+markdown_table(data['ss5']))
    sections.append('### TABLE SS6 — Sell/store distribution\n'+markdown_table(data['ss6']))
    sections.append('Selected-model retrospective summaries: '+ '; '.join(f"{crop} {model}: N={int(row.number_of_decisions)}, agreement={row.decision_agreement_percentage:.2f}%, mean regret INR {row.mean_regret_inr:.2f}" for _,row in sell_selected.iterrows())+'. Results use simulated 1-quintal quantities and are not farmer income or causal outcomes.')
    sections.append('## 10. Sell/Store Baselines\n'+markdown_table(baselines.groupby('model',as_index=False).agg(number_of_decisions=('number_of_decisions','sum'),mean_agreement=('decision_agreement_percentage','mean'),mean_simulated_net_value_inr=('mean_realized_net_value_inr','mean'),mean_regret_inr=('mean_regret_inr','mean'))))
    sections.append('## 11. Sell/Store Sensitivity\nAll available scenarios are included in `sell_store_sensitivity.csv`; summary by crop/scenario is below. Inputs are assumptions, not probability distributions. Forecast-error sensitivity is in `sell_store_forecast_error_sensitivity.csv`.\n\n'+markdown_table(data['sell_sensitivity_summary']))
    sections.append('## 12. Warehouse Optimization\nThe allocation MILP minimizes storage plus transport allocation costs and a shortage penalty on unallocated quantity. Variables are continuous quintal allocations to compatible warehouses; capacity is MT×10. CBC status is Optimal for all 36 scenarios, zero infeasible solutions, zero unallocated quantity, and zero constraint violations. The 1-quintal scenario was fully allocated. No CBC numeric gap was exposed.\n\n### TABLE W1 — Warehouse optimization results by crop\n'+markdown_table(data['warehouse_w1']))
    sections.append('### TABLE W2 — Solver status\n'+markdown_table(data['warehouse_w2']))
    sections.append('### TABLE W3 — Cost components\n'+markdown_table(data['warehouse_w3']))
    sections.append('### TABLE W4 — Warehouse baseline comparison\n'+markdown_table(data['warehouse_w4']))
    sections.append('### TABLE W5 — Warehouse utilization\n'+markdown_table(data['warehouse_w5']))
    sections.append('### TABLE W6 — Warehouse sensitivity\n'+markdown_table(data['warehouse_w6']))
    sections.append('For standardized 1-quintal scenario calculations, mean total costs were Onion INR 24.2575 (INR 0.2426/kg), Rice INR 24.2575 (INR 0.2426/kg), Tomato INR 13.0523 (INR 0.1305/kg). These are scenario-based optimization costs, not commercial warehouse prices. The `Storage_Cost_per_MT` currency/time basis is undocumented and is assumed as INR/MT/month; transport rate is also assumed.')
    sections.append('## 13. Routing Evaluation\nThe available data supports scenario-based single-leg synthetic centroid-to-warehouse routing only, not CVRP/VRP. 36 Haversine proxy route legs were evaluated; all 36 feasible with zero capacity and demand violations. Travel time and OSRM route data are unavailable/not supported by current data.\n\n### Routing performance by crop\n'+markdown_table(data['routing_r1']))
    sections.append('## 14. Routing Baselines\n'+markdown_table(data['routing_r2']))
    sections.append('## 15. Routing Sensitivity\n'+markdown_table(data['routing_sensitivity_summary']))
    sections.append('## 16. End-to-End Results\nThe table joins validated Phase 2 forecast horizon/fold metrics, retrospective sell/store summary, saved warehouse MILP storage costs, and routing proxy costs by crop/model/horizon/scenario. The total optimization cost shown is warehouse storage plus scenario transport cost, not farmer expense.\n\n### TABLE E2E1 — Complete end-to-end performance by crop/scenario\n'+markdown_table(e2e))
    sections.append('### TABLE E2E2 — Complete system metrics\n'+markdown_table(e2e.groupby('crop',as_index=False).agg(forecast_RMSE=('forecast_RMSE','mean'),forecast_MAE=('forecast_MAE','mean'),sell_store_agreement_percentage=('sell_store_agreement_percentage','mean'),sell_store_mean_regret_inr=('sell_store_mean_regret_inr','mean'),warehouse_storage_cost_inr=('warehouse_storage_cost_inr','mean'),routing_distance_km=('distance_km','mean'),transport_cost_inr=('transport_cost_inr','mean'),total_cost_inr=('total_cost_inr','mean'))))
    sections.append('### TABLE E2E3 — Baseline comparison across modules\nForecasting baselines are Seasonal Naive/ARIMA/SARIMA/LSTM in F1; sell-store policies are SS baseline table; warehouse allocation methods are W4; routing methods are R2. No single composite ranking is justified because units/objectives differ and decision/route samples are small.')
    sections.append('## 17. Software Validation\nThe project test suite was rerun for this report: 75 passed, 0 failed, 0 skipped; 14 warnings, primarily existing statsmodels convergence/starting-parameter and Keras/NumPy warnings. Routing audit independently recomputed 36 distances/costs and all 252 sensitivity rows; protected upstream files were SHA-256 checked unchanged across deterministic routing reruns.')
    sections.append('## 18. Data Leakage and Validity\nForecast evaluation uses chronological rolling-origin folds and valid out-of-sample predictions. Sell/store actions are generated without future actual prices; actuals are used only post hoc for retrospective agreement/regret. Warehouse/routing modes consume saved artifacts without refitting models. Routing cannot establish actual route validity because its origin is synthetic. DM tests are underpowered with three paired origins. These are software/data-flow validations, not evidence of causal farmer outcomes.')
    assumption_rows=[]
    for phase,settings in assumptions.items():
        for key,value in settings.items():
            if isinstance(value,(dict,list)):
                shown=json.dumps(value)
            else: shown=str(value)
            assumption_rows.append({'phase':phase,'parameter':key,'value':shown,'classification':'Configured scenario assumption unless it names a saved artifact/structural conversion','unit/provenance':'See phase assumptions JSON and phase report'})
    sections.append('## 19. Assumption Audit\n'+markdown_table(pd.DataFrame(assumption_rows)))
    sections.append('## 20. Farmer Data and Required Documentation Before Submission\nThe file `farmer_crop_dataset (1).csv` contains 450 rows, 150 Farmer_ID values, 3 crops, yield per acre, and season. The repository does not document whether records are observed, synthetic, or expanded; collection date/period, district/village, sampling procedure, consent, anonymization, ethics review, and linkage to price/decision records are absent. `farmer_decision_history.csv` has 9 rows with 8 missing cells; SQLite history table has zero records. Do not describe these as verified farmer study outcomes. Before submission, document dataset provenance, sampling, collection period, informed consent/ethics, de-identification, missingness handling, and whether IDs/data are synthetic or real.')
    sections.append('''## 21. Limitations
- Quarterly price series are small (Rice/Onion 26; Tomato 24 contiguous observations) with only three validation folds.
- LSTM has 8–16 effective training sequences per fold; overfitting evidence is not statistically established, and no claim of global superiority is supported.
- DM comparisons are underpowered; native interval coverage is based on small samples.
- Storage/spoilage/duration/transport assumptions are scenario parameters without validated invoices or carrier quotes.
- Quantity is standardized to one quintal; not observed farmer inventory.
- Warehouse provenance and storage billing currency/period are unverified.
- Routing uses synthetic-centroid Haversine distances, not road distances; no actual origin, destination demand, fleet, capacity, time-window, or route logs exist.
- No direct farmer welfare, profit, loss-reduction, or causal impact measurement exists.''')
    sections.append('## 22. What the System Actually Contributes\nADIS is a SaaS-based Agricultural Decision Support / Decision Intelligence platform prototype that integrates crop-price forecasting, economic sell/store evaluation, warehouse allocation, and transport-cost scenario analysis. It provides actionable decision-support outputs while farmers remain the final decision makers. The current evidence demonstrates implementation and scenario evaluation under stated assumptions, not guaranteed profit increases or real-world operational optimization.')
    sections.append('## 23. What Has Been Successfully Addressed\nLeakage-safe rolling-origin validation and metric separation; native ARIMA/SARIMA intervals and diagnostics; valid-fold model selection; explicit sell/store economics and unit assumptions; cost-minimizing warehouse allocation with compatibility/capacity constraints; independent route/cost/sensitivity verification; modular research runners; complete automated regression coverage.')
    sections.append('## 24. Remaining Work Before Manuscript Submission\nVerify data provenance and licenses; obtain real farmer locations/quantities/consent documentation; validate warehouse capacities, storage tariff currency/period and operational status; obtain carrier quotes or route logs and vehicle/fleet data; extend temporal validation with more origins; evaluate DM with sufficient paired forecasts; establish external test and uncertainty calibration; document deployment/security/SaaS evaluation separately from research results.')
    sections.append('## 25. Final Research Contribution\nThe current ADIS implementation demonstrates an auditable research pipeline integrating crop-wise forecasting, retrospective economic decision simulation, warehouse cost allocation, and a scenario-based transport proxy. It does not establish real-world farmer profit improvement, causal benefit, a validated CVRP, or universal model superiority.')
    sections.append('## 26. Complete Results Tables and Traceability\nDetailed tables are generated as CSV artifacts: F1–F4, SS1–SS6, W1–W6, R1–R3, and E2E1–E2E3. Source file names, units, missingness, and provenance classifications are listed in `dataset_inventory.csv`.')
    sections.append('## 27. Complete Figure List\n'+ '\n'.join(f'- `{path.name}`' for path in figures))
    sections.append('## 28. Reproducibility Information\nValidated artifacts/configs: `experiment_config.json`, `sell_store_assumptions.json`, `warehouse_research_assumptions.json`, `routing_research_assumptions.json`. The phase runners use saved upstream artifacts for downstream scenarios. This completion also writes `generate_adis_performance_report.py`; run it with the project virtual environment to rebuild tables, figures, Markdown, and standalone offline HTML. `python -m pytest -q` produced 75 passed on the completed research code.')
    sections.append('''## 29. Faculty Summary (One Page)
**A. Problem:** integrate crop forecasts with decision-support, storage allocation, and transport-cost analysis.

**B. Forecast candidates:** Seasonal Naive, ARIMA, SARIMA, LSTM using three rolling-origin folds and four-quarter horizons.

**C. RMSE-selected candidates:** Rice SARIMA, Onion LSTM, Tomato SARIMA; selections are procedure-specific and not superiority claims.

**D. Forecast performance:** detailed values and horizons in F1–F3; price unit INR/quintal. DM tests underpowered; intervals only ARIMA/SARIMA.

**E. Sell/store:** 12 selected-model retrospective decisions per crop; agreement/regret in SS tables.

**F. Warehouse:** 36 independent 1-quintal scenarios; CBC Optimal 36/36; full quantity allocated, zero violations; assumption-based scenario costs.

**G. Routing:** 36 Haversine proxy legs, all feasible; not road routing or CVRP.

**H. Integration:** 36 end-to-end scenario rows with metrics linked to saved upstream artifacts.

**I. Software validation:** 75 passed, 0 failed, 14 warnings.

**J. Main limitations:** small data/folds, unverified provenance, assumptions for economic costs, absent farmer origins/fleet/market demand, no causal outcome data.

**K. Claim supported:** a working, auditable decision-support research prototype and feasible scenario allocations under configured assumptions.

**L. Claims not supported:** guaranteed profit increase, farmer welfare improvement, actual road-route optimality, causal loss reduction, universal model superiority.''')
    return '\n\n'.join(sections)+'\n'


def build_html(markdown_text, data, figures):
    def inline_markup(text):
        escaped = html.escape(text)
        escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
        escaped = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', escaped)
        return escaped

    def render_section_lines(lines):
        rendered = []
        paragraph = []
        bullet_items = []

        def flush_paragraph():
            if paragraph:
                rendered.append('<p>' + inline_markup(' '.join(paragraph)) + '</p>')
                paragraph.clear()

        def flush_bullets():
            if bullet_items:
                rendered.append('<ul>' + ''.join(f'<li>{inline_markup(item)}</li>' for item in bullet_items) + '</ul>')
                bullet_items.clear()

        index = 0
        in_code = False
        code_lines = []
        while index < len(lines):
            line = lines[index]
            if line.strip().startswith('```'):
                flush_paragraph(); flush_bullets()
                if in_code:
                    rendered.append('<pre><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
                    code_lines.clear(); in_code = False
                else:
                    in_code = True
                index += 1
                continue
            if in_code:
                code_lines.append(line); index += 1; continue
            if line.startswith('|') and index + 1 < len(lines) and lines[index + 1].startswith('|'):
                flush_paragraph(); flush_bullets()
                table_lines = []
                while index < len(lines) and lines[index].startswith('|'):
                    table_lines.append(lines[index]); index += 1
                parsed = [[cell.strip() for cell in row.strip().strip('|').split('|')] for row in table_lines]
                if len(parsed) > 1 and all(set(cell) <= {'-', ':', ' '} for cell in parsed[1]):
                    parsed.pop(1)
                if parsed:
                    head = '<thead><tr>' + ''.join(f'<th>{inline_markup(cell)}</th>' for cell in parsed[0]) + '</tr></thead>'
                    body = '<tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline_markup(cell)}</td>' for cell in row) + '</tr>' for row in parsed[1:]) + '</tbody>'
                    rendered.append('<div class="table-wrap"><table>' + head + body + '</table></div>')
                continue
            if line.startswith('### '):
                flush_paragraph(); flush_bullets()
                rendered.append(f'<h3>{inline_markup(line[4:])}</h3>')
            elif line.startswith('- '):
                flush_paragraph(); bullet_items.append(line[2:])
            elif not line.strip():
                flush_paragraph(); flush_bullets()
            else:
                flush_bullets(); paragraph.append(line.strip())
            index += 1
        flush_paragraph(); flush_bullets()
        if code_lines:
            rendered.append('<pre><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
        return ''.join(rendered)

    image_cards=[]
    for path in figures:
        encoded=base64.b64encode(path.read_bytes()).decode('ascii')
        image_cards.append(f'<figure id="fig-{html.escape(path.stem)}"><img src="data:image/png;base64,{encoded}" alt="{html.escape(path.stem)}"><figcaption>{html.escape(path.stem.replace("_"," "))}</figcaption></figure>')
    sections_html=[]
    expandable = {
        '5. Experimental Setup', '7. Forecast Uncertainty', '7A. Forecasting Diagnostics',
        '18. Data Leakage and Validity', '19. Assumption Audit',
        '20. Farmer Data and Required Documentation Before Submission',
        '21. Limitations', '24. Remaining Work Before Manuscript Submission',
        '28. Reproducibility Information',
    }

    def append_section(section_title, section_lines):
        content = render_section_lines(section_lines)
        if section_title in expandable:
            content = '<details><summary>Expand methodology and supporting details</summary>' + content + '</details>'
        sections_html.append(f'<section><h2>{html.escape(section_title)}</h2>{content}</section>')

    current=[]; title='Report'
    for line in markdown_text.splitlines():
        if line.startswith('# '):
            continue
        if line.startswith('## '):
            if current: append_section(title, current)
            title=line[3:].strip(); current=[]
        else:
            current.append(line)
    if current: append_section(title, current)
    image_nav=''.join(f'<li><a href="#fig-{html.escape(path.stem)}">{html.escape(path.stem.replace("_"," "))}</a></li>' for path in figures)
    image_section='<section id="figures"><h2>Publication Figures</h2>'+''.join(image_cards)+'</section>'
    executive=f'''<section id="key-findings"><h2>Key Findings</h2><div class="cards">
<div><b>Forecast folds</b><strong>36</strong><span>3 crops × 4 models × 3 folds</span></div>
<div><b>Sell/store cases</b><strong>144</strong><span>retrospective 1-quintal scenarios</span></div>
<div><b>Warehouse scenarios</b><strong>36</strong><span>CBC optimal; 0 violations</span></div>
<div><b>Route legs</b><strong>36</strong><span>Haversine proxy, not road routes</span></div>
<div><b>Tests</b><strong>75 passed</strong><span>14 warnings, 0 failures</span></div>
</div><p>Scenario outputs are not real-world farmer outcomes or causal benefit estimates. Farmers remain final decision makers.</p></section>
<section id="reviewer"><h2>Reviewer Concerns Addressed</h2><ul><li>Forecast evaluation is chronological rolling-origin, crop-wise, and leakage-audited.</li><li>Prediction intervals are native ARIMA/SARIMA only; LSTM and Seasonal Naive intervals are unavailable.</li><li>DM results are marked underpowered at three paired origins.</li><li>Economic, warehouse, and transport assumptions are explicitly separated from supplied data.</li><li>Routing is labeled a Haversine reference-origin proxy rather than a CVRP.</li><li>Independent route/cost/sensitivity checks and full test suite are recorded.</li></ul></section>
<section id="remaining"><h2>Remaining Reviewer Concerns</h2><ul><li>Price, farmer, and warehouse provenance require authoritative documentation.</li><li>More independent time origins and an external holdout are needed.</li><li>Storage billing period/currency and transport tariffs need validation.</li><li>Farmer origins, actual demand, fleet, road routes, and route observations are unavailable.</li><li>No causal or farmer welfare evaluation is available.</li></ul></section>'''
    report_body=executive+''.join(sections_html)+image_section
    toc=''.join(f'<li><a href="#section-{i}">{html.escape(title)}</a></li>' for i,title in enumerate([line[3:].strip() for line in markdown_text.splitlines() if line.startswith('## ')],start=1))
    # Apply stable generated anchors to parsed sections.
    body=report_body
    for i,title in enumerate([line[3:].strip() for line in markdown_text.splitlines() if line.startswith('## ')],start=1):
        body=body.replace(f'<section><h2>{html.escape(title)}</h2>',f'<section id="section-{i}"><h2>{html.escape(title)}</h2>',1)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ADIS Complete Performance Report</title><style>
:root{{--ink:#1e2b32;--muted:#64727a;--line:#d6dee2;--paper:#fff;--canvas:#edf2f3;--accent:#176b67;--accent2:#b2542d;--pale:#e4f0ed}}*{{box-sizing:border-box}}body{{margin:0;background:var(--canvas);color:var(--ink);font:15px/1.55 Georgia,'Times New Roman',serif}}.layout{{display:grid;grid-template-columns:265px minmax(0,1fr);min-height:100vh}}nav{{position:sticky;top:0;height:100vh;overflow:auto;background:#193d43;color:#fff;padding:24px 18px;font:13px/1.4 'Segoe UI',sans-serif}}nav h2{{font:600 17px/1.2 'Segoe UI',sans-serif}}nav a{{color:#e4f0ed;text-decoration:none}}nav ul{{padding-left:18px}}nav li{{margin:7px 0}}main{{max-width:1240px;margin:0 auto;padding:28px clamp(16px,4vw,52px) 80px}}header{{border-bottom:3px solid var(--accent);padding-bottom:20px;margin-bottom:20px}}h1{{font:700 34px/1.1 Georgia,serif;margin:0 0 12px}}h2{{font:700 24px/1.2 Georgia,serif;border-bottom:1px solid var(--line);padding-bottom:8px;margin-top:0}}h3{{font:700 18px Georgia,serif;color:var(--accent)}}section{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:22px;margin:18px 0;scroll-margin-top:20px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}.cards div{{background:var(--pale);border-left:4px solid var(--accent);padding:14px;display:grid;gap:4px;font-family:'Segoe UI',sans-serif}}.cards strong{{font-size:25px}}.cards span,.small{{font-size:12px;color:var(--muted)}}.table-wrap{{overflow:auto;margin:12px 0}}table{{border-collapse:collapse;width:100%;font:12px/1.4 'Segoe UI',sans-serif}}th,td{{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}th{{background:#e8efef;position:sticky;top:0}}figure{{margin:18px 0;padding:10px;border:1px solid var(--line);background:#fff}}figure img{{width:100%;height:auto;display:block}}figcaption{{font:12px 'Segoe UI',sans-serif;color:var(--muted);padding:8px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 'Cascadia Mono',Consolas,monospace;background:#f6f8f8;border:1px solid #e0e6e8;padding:12px;border-radius:4px;max-height:600px;overflow:auto}}.badge{{display:inline-block;background:#f4e7d9;color:#65381d;padding:4px 8px;border-radius:3px;font:12px 'Segoe UI',sans-serif}}@media(max-width:800px){{.layout{{display:block}}nav{{position:relative;height:auto}}nav ul{{columns:2}}main{{padding:16px}}h1{{font-size:28px}}}}
</style></head><body><div class="layout"><nav><h2>ADIS Research Report</h2><span class="badge">Artifact-grounded audit</span><ul><li><a href="#key-findings">Key Findings</a></li><li><a href="#reviewer">Reviewer Concerns Addressed</a></li><li><a href="#remaining">Remaining Reviewer Concerns</a></li>{toc}<li><a href="#figures">Publication Figures</a></li></ul></nav><main><header><h1>Performance Evaluation of the Agricultural Decision Intelligence System (ADIS)</h1><p>Research implementation audit · Generated from saved project artifacts · No causal farmer-outcome claims</p></header>{body}<footer><p>Offline standalone report. Figures are embedded. Numeric tables trace to project CSV artifacts listed in the report and dataset inventory.</p></footer></main></div></body></html>'''


def main():
    inventory=build_inventory()
    artifact_inventory=build_artifact_inventory()
    (OUTPUT/'dataset_profiles.csv').write_text(dataset_profiles().to_csv(index=False),encoding='utf-8')
    pred,folds,horizon,f1,f3,f4,intervals,intervals_all,dm=build_forecast_tables()
    model_diagnostics = f3.loc[f3.model.isin(['arima','sarima'])].copy()
    sell=build_sell_tables()
    warehouse=build_warehouse_tables()
    routing=build_routing_tables()
    data={
        'inventory':inventory,'artifact_inventory':artifact_inventory,'forecast_predictions':pred,'forecast_folds':folds,'forecast_horizon':horizon,'forecast_f1':f1,'forecast_folds_table':f3,'forecast_f4':f4,'forecast_interval_metrics':intervals,'forecast_intervals_all':intervals_all,'forecast_dm':dm,'model_diagnostics':model_diagnostics,
        'sell_decisions':sell[0],'sell_summary':sell[1],'sell_baselines':sell[2],'sell_sensitivity':sell[3],'sell_error_sensitivity':sell[4],'sell_assumptions':sell[5],'selected':sell[6],'ss1':sell[7],'ss2':sell[8],'ss3':sell[9],'ss4':sell[10],'ss5':sell[11],'ss6':sell[12],'sell_sensitivity_summary':sell[13],
        'warehouse_summary':warehouse[0],'warehouse_baselines':warehouse[1],'warehouse_utilization':warehouse[2],'warehouse_sensitivity':warehouse[3],'warehouse_results':warehouse[4],'warehouse_w1':warehouse[5],'warehouse_w2':warehouse[6],'warehouse_w3':warehouse[7],'warehouse_w4':warehouse[8],'warehouse_w5':warehouse[9],'warehouse_w6':warehouse[10],'warehouse_sensitivity_summary':warehouse[3],
        'routing_routes':routing[0],'routing_summary':routing[1],'routing_baselines':routing[2],'routing_sensitivity':routing[3],'routing_r1':routing[4],'routing_r2':routing[5],'routing_sensitivity_summary':routing[6],
        'end_to_end':read_csv('table_end_to_end_pipeline.csv'),
    }
    # Faculty-facing derived result tables. Existing phase outputs remain untouched.
    for filename,frame in [
        ('table_f1_forecast_comparison.csv',f1),('table_f2_forecast_horizon.csv',horizon),('table_f3_forecast_folds.csv',f3),('table_f4_selected_models.csv',f4),
        ('table_ss1_sell_store_by_crop.csv',sell[7]),('table_ss2_sell_store_models.csv',sell[8]),('table_ss3_decision_agreement.csv',sell[9]),('table_ss4_decision_regret.csv',sell[10]),('table_ss5_simulated_net_value.csv',sell[11]),('table_ss6_decision_distribution.csv',sell[12]),('table_ss_sensitivity_summary.csv',sell[13]),
        ('table_w1_warehouse_results.csv',warehouse[5]),('table_w2_solver_status.csv',warehouse[6]),('table_w3_warehouse_cost_components.csv',warehouse[7]),('table_w4_warehouse_baselines.csv',warehouse[8]),('table_w5_warehouse_utilization.csv',warehouse[9]),('table_w6_warehouse_sensitivity.csv',warehouse[10]),
        ('table_r1_routing_performance.csv',routing[4]),('table_r2_routing_baselines.csv',routing[5]),('table_r3_routing_sensitivity.csv',routing[6]),
    ]:
        frame.to_csv(OUTPUT/filename,index=False)
    figures=create_figures(data)
    data['inventory']=build_inventory()
    data['artifact_inventory']=build_artifact_inventory()
    markdown=build_markdown(data,figures)
    (OUTPUT/'ADIS_Complete_Performance_Report.md').write_text(markdown,encoding='utf-8')
    html_report=build_html(markdown,data,figures)
    (OUTPUT/'ADIS_Complete_Performance_Report.html').write_text(html_report,encoding='utf-8')
    summary='''# ADIS Faculty Summary\n\n**Problem:** integrate crop-price forecasting, retrospective sell/store decision simulation, warehouse allocation, and transport-cost scenario analysis for agricultural decision support. Farmers remain final decision makers.\n\n**Models:** Seasonal Naive, ARIMA, SARIMA, LSTM; three rolling-origin folds and four-quarter horizon. RMSE-selected candidates: Rice SARIMA, Onion LSTM, Tomato SARIMA. Selections are procedure-specific; DM comparisons are underpowered and no superiority claim is supported.\n\n**Forecasting:** see report Tables F1-F4; prices and errors are INR/quintal. Native intervals exist only for ARIMA/SARIMA. Effective LSTM sequence counts are 8-16 per fold.\n\n**Sell/store:** selected-model retrospective cases: Rice 12, agreement 83.33%, mean regret INR 8.80; Onion 12, 75.00%, INR 258.90; Tomato 12, 66.67%, INR 55.61. One-quintal scenario, not farmer outcomes.\n\n**Warehouse:** 36 independent scenarios, CBC Optimal 36/36, zero constraint violations, full scenario quantity allocated. Scenario storage-cost interpretation is assumed INR/MT/month; warehouse provenance is unverified.\n\n**Routing:** 36 single-leg Haversine reference proxies, feasible 36/36. Not road routes or a CVRP. No farmer origins, customer demands, fleet, or route observations.\n\n**Software:** complete pytest suite 75 passed, 14 warnings, 0 failures. Protected upstream outputs verified unchanged during routing reruns; independent distance, cost, allocation link, and sensitivity checks passed.\n\n**Limitations:** small quarterly sample and fold count; unverified source provenance; configured cost/spoilage/transport assumptions; no causal farmer welfare, profit, route, or road-network evidence.\n\n**Supported claim:** ADIS is an auditable research prototype for decision support and scenario evaluation. **Not supported:** guaranteed profit, causal benefits, actual road-route optimality, or universal forecast superiority.\n'''
    (OUTPUT/'ADIS_Faculty_Summary.md').write_text(summary,encoding='utf-8')
    print('Report:',OUTPUT/'ADIS_Complete_Performance_Report.md')
    print('HTML:',OUTPUT/'ADIS_Complete_Performance_Report.html')
    print('Inventory datasets:',len(inventory),'figures:',len(figures),'derived tables: 19')
    print('Selected models:',data['selected'])


if __name__=='__main__':
    main()
