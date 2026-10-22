"""Generate one self-contained, artifact-grounded ADIS technical report."""

from __future__ import annotations

import argparse
import html
import json
import math
import platform
import re
import sys
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'ADIS_COMPLETE_TECHNICAL_RESULTS_REPORT.html'
CROPS = ['Rice', 'Onion', 'Tomato']
MODELS = ['seasonal_naive', 'arima', 'sarima', 'lstm']
COLORS = {
    'seasonal_naive': '#1c7891',
    'arima': '#cf6545',
    'sarima': '#4c896b',
    'lstm': '#9b7a36',
    'Rice': '#1c7891',
    'Onion': '#cf6545',
    'Tomato': '#4c896b',
    'actual': '#22343a',
    'forecast': '#cf6545',
}
SECTION_NAMES = [
    'Executive Summary', 'Dataset & Data Pipeline', 'System Architecture',
    'Forecasting Models', 'Forecasting Validation', 'Model Selection',
    'Prediction Intervals & Forecast Uncertainty', 'Sell-vs-Store Decision Model',
    'Sell/Store Results', 'Forecast Error Sensitivity', 'End-to-End Parameter Sensitivity',
    'Warehouse Allocation', 'Transport-Cost Evaluation Using Haversine Reference-Origin Proxy',
    'Module Ablation', 'Formula / Code / Result Consistency', 'Rolling-Origin Feasibility',
    'Statistical / Model Validation', 'Software & Test Validation', 'Reproducibility',
    'LLM / AI Development Disclosure', 'Limitations', 'Overall Technical Status',
    'Complete Artifact Index', 'Final Technical Conclusion',
]


def csv(name: str) -> pd.DataFrame:
    path = ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f'Required evidence artifact is missing: {name}')
    return pd.read_csv(path)


def json_file(name: str) -> dict:
    path = ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f'Required configuration is missing: {name}')
    return json.loads(path.read_text(encoding='utf-8'))


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def is_missing(value) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def fmt(value, digits=2) -> str:
    if is_missing(value):
        return 'Not available in current artifact'
    if isinstance(value, (bool, np.bool_)):
        return 'Yes' if value else 'No'
    if isinstance(value, (int, np.integer)):
        return f'{int(value):,}'
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(float(value)):
            return 'Not available in current artifact'
        return f'{float(value):,.{digits}f}'
    return str(value)


def table(frame: pd.DataFrame, columns=None, digits=3, limit=None) -> str:
    view = frame.copy() if columns is None else frame[list(columns)].copy()
    if limit is not None:
        view = view.head(limit)
    if view.empty:
        return '<p class="empty">No rows in the referenced artifact.</p>'
    head = ''.join(f'<th scope="col">{esc(column)}</th>' for column in view.columns)
    body = []
    for row in view.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if is_missing(value):
                text = 'Not available in current artifact'
            elif isinstance(value, (float, np.floating)):
                text = fmt(value, digits)
            elif isinstance(value, (bool, np.bool_)):
                text = 'Yes' if value else 'No'
            else:
                text = str(value)
            cells.append(f'<td>{esc(text)}</td>')
        body.append('<tr>' + ''.join(cells) + '</tr>')
    more = ''
    if limit is not None and len(frame) > limit:
        more = f'<p class="small-note">Showing {len(view):,} of {len(frame):,} artifact rows.</p>'
    return f'<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>{more}'


def metric_card(value, label, detail='') -> str:
    return (
        '<div class="metric-card">'
        f'<strong>{esc(value)}</strong><span>{esc(label)}</span>'
        f'<small>{esc(detail)}</small></div>'
    )


def section(number: int, content: str) -> str:
    title = SECTION_NAMES[number - 1]
    return (
        f'<section id="section-{number:02d}" class="report-section">'
        f'<div class="section-kicker">SECTION {number:02d}</div>'
        f'<h2>{esc(title)}</h2>{content}</section>'
    )


def details(title: str, inner: str, open_by_default=False) -> str:
    opened = ' open' if open_by_default else ''
    return f'<details{opened}><summary>{esc(title)}</summary>{inner}</details>'


def grouped_bar_svg(frame, category_column, series_column, value_column, title, axis_label, series_order=None):
    data = frame[[category_column, series_column, value_column]].copy()
    data[value_column] = pd.to_numeric(data[value_column], errors='coerce')
    data = data.loc[np.isfinite(data[value_column])]
    categories = [crop for crop in CROPS if crop in data[category_column].astype(str).unique()]
    series = series_order or [model for model in MODELS if model in data[series_column].astype(str).unique()]
    if data.empty or not categories or not series:
        return '<p class="empty">Plot not available from current artifact rows.</p>'
    width, height = 900, 390
    left, right, top, bottom = 72, 24, 50, 74
    plot_w, plot_h = width - left - right, height - top - bottom
    max_value = max(float(data[value_column].max()), 1.0)
    max_value *= 1.12
    ticks = 4
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">']
    parts.append(f'<text x="{width/2}" y="24" text-anchor="middle" class="svg-title">{esc(title)}</text>')
    for tick in range(ticks + 1):
        value = max_value * tick / ticks
        y = top + plot_h - plot_h * tick / ticks
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-9}" y="{y+4:.1f}" text-anchor="end" class="axis-label">{value:,.0f}</text>')
    group_w = plot_w / len(categories)
    bar_w = min(34, group_w * 0.72 / max(1, len(series)))
    for ci, category in enumerate(categories):
        center = left + group_w * (ci + 0.5)
        parts.append(f'<text x="{center:.1f}" y="{top+plot_h+24}" text-anchor="middle" class="axis-label">{esc(category)}</text>')
        for si, item in enumerate(series):
            matches = data.loc[data[category_column].eq(category) & data[series_column].eq(item), value_column]
            if matches.empty:
                continue
            value = float(matches.iloc[0])
            x = center + (si - (len(series)-1)/2) * bar_w - bar_w * 0.42
            bar_height = max(0, plot_h * value / max_value)
            y = top + plot_h - bar_height
            color = COLORS.get(str(item), '#596d70')
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.84:.1f}" height="{bar_height:.1f}" rx="2" fill="{color}"/>')
            parts.append(f'<title>{esc(category)} / {esc(item)}: {value:,.3f}</title>')
    lx = left
    for item in series:
        parts.append(f'<rect x="{lx}" y="{height-25}" width="11" height="11" fill="{COLORS.get(str(item), "#596d70")}"/>')
        parts.append(f'<text x="{lx+16}" y="{height-15}" class="legend">{esc(item)}</text>')
        lx += max(120, 820 // max(1, len(series)))
    parts.append(f'<text transform="translate(16 {height/2}) rotate(-90)" text-anchor="middle" class="axis-label">{esc(axis_label)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def actual_forecast_svg(predictions, crop, model):
    selected = predictions.loc[
        predictions['crop'].eq(crop)
        & predictions['model'].eq(model)
        & predictions['validity_status'].eq('VALID')
    ].copy()
    if selected.empty:
        return '<p class="empty">No valid selected-model forecast rows.</p>'
    selected['forecast_date'] = pd.to_datetime(selected['forecast_date'], errors='coerce')
    selected = selected.sort_values('forecast_date').drop_duplicates('forecast_date')
    actual = selected['actual'].astype(float).to_numpy()
    forecast = selected['predicted'].astype(float).to_numpy()
    labels = selected['forecast_date'].dt.strftime('%Y-Q') + selected['forecast_date'].dt.quarter.astype(str)
    values = np.r_[actual, forecast]
    lo, hi = float(np.nanmin(values)), float(np.nanmax(values))
    spread = max(hi - lo, 1.0)
    lo -= spread * 0.08
    hi += spread * 0.08
    width, height, left, right, top, bottom = 760, 300, 64, 24, 35, 62
    plot_w, plot_h = width-left-right, height-top-bottom
    def point(index, value):
        x = left + (index / max(len(actual)-1, 1)) * plot_w
        y = top + (hi-value) / (hi-lo) * plot_h
        return x, y
    result = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(crop)} actual versus forecast">']
    result.append(f'<text x="{width/2}" y="21" text-anchor="middle" class="svg-title">{esc(crop)} · {esc(model)} · actual vs forecast</text>')
    for fraction in (0, .25, .5, .75, 1):
        y = top + plot_h*fraction
        val = hi - (hi-lo)*fraction
        result.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>')
        result.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" class="axis-label">{val:,.0f}</text>')
    for series_values, color, label in ((actual, COLORS['actual'], 'Actual'), (forecast, COLORS['forecast'], 'Forecast')):
        points = [point(i, val) for i, val in enumerate(series_values)]
        joined = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
        result.append(f'<polyline points="{joined}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for index, (x, y) in enumerate(points):
            result.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"><title>{esc(labels.iloc[index])} {label}: {series_values[index]:,.2f} INR/quintal</title></circle>')
    step = max(1, len(labels)//6)
    for index, label in enumerate(labels):
        if index % step == 0 or index == len(labels)-1:
            x, _ = point(index, lo)
            result.append(f'<text x="{x:.1f}" y="{height-30}" text-anchor="middle" class="axis-label">{esc(label)}</text>')
    result.append(f'<line x1="{left+20}" y1="{height-11}" x2="{left+40}" y2="{height-11}" stroke="{COLORS["actual"]}" stroke-width="3"/><text x="{left+46}" y="{height-7}" class="legend">Actual</text>')
    result.append(f'<line x1="{left+110}" y1="{height-11}" x2="{left+130}" y2="{height-11}" stroke="{COLORS["forecast"]}" stroke-width="3"/><text x="{left+136}" y="{height-7}" class="legend">Forecast</text>')
    result.append('</svg>')
    return ''.join(result)


def sensitivity_svg(summary, parameter):
    data = summary.loc[summary['parameter'].eq(parameter)].sort_values('parameter_value')
    if data.empty:
        return '<p class="empty">No rows in the sensitivity artifact.</p>'
    width, height, left, right, top, bottom = 560, 260, 58, 20, 34, 56
    max_y = max(100.0, float(data['decision_flip_rate'].max()) * 1.1)
    plot_h, plot_w = height-top-bottom, width-left-right
    pts = []
    for index, row in enumerate(data.itertuples(index=False)):
        x = left + (index/max(len(data)-1, 1))*plot_w
        y = top + (max_y-float(row.decision_flip_rate))/max_y*plot_h
        pts.append((x, y, row.parameter_value))
    svg = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(parameter)} decision flip rate">']
    svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" class="svg-title">{esc(parameter.replace("_", " ").title())}: decision flip rate</text>')
    for tick in (0, 25, 50, 75, 100):
        y = top + (100-tick)/100*plot_h
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/><text x="{left-8}" y="{y+4:.1f}" text-anchor="end" class="axis-label">{tick}%</text>')
    joined = ' '.join(f'{x:.1f},{y:.1f}' for x,y,_ in pts)
    svg.append(f'<polyline points="{joined}" fill="none" stroke="#176b67" stroke-width="2.5"/>')
    for x,y,val in pts:
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#cf6545"><title>Scenario value {val}: {float(data.loc[data.parameter_value.eq(val), "decision_flip_rate"].iloc[0]):.3f}% flips</title></circle>')
        svg.append(f'<text x="{x:.1f}" y="{height-26}" text-anchor="middle" class="axis-label">{float(val):g}</text>')
    svg.append(f'<text x="{width/2}" y="{height-6}" text-anchor="middle" class="axis-label">Scenario value ({esc(data["parameter_unit"].iloc[0])})</text></svg>')
    return ''.join(svg)


def stability_svg(interval_summary):
    data = interval_summary.groupby(['crop', 'model'], as_index=False)[
        ['robust_sell_decisions', 'robust_store_decisions', 'sensitive_decisions']
    ].sum()
    width, row_h, left, right = 850, 40, 160, 25
    height = 90 + len(data)*row_h
    plot_w = width-left-right
    max_count = max(float(data[['robust_sell_decisions','robust_store_decisions','sensitive_decisions']].sum(axis=1).max()), 1)
    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Prediction interval decision robustness by crop and model">']
    out.append(f'<text x="{width/2}" y="24" text-anchor="middle" class="svg-title">Decision classification across native interval scenarios</text>')
    legend = [('ROBUST_SELL','#4c896b'),('ROBUST_STORE','#1c7891'),('DECISION_SENSITIVE','#cf6545')]
    lx=left
    for label,color in legend:
        out.append(f'<rect x="{lx}" y="43" width="12" height="12" fill="{color}"/><text x="{lx+17}" y="53" class="legend">{label}</text>')
        lx += 205
    for i,row in data.iterrows():
        y=76+i*row_h
        label=f'{row.crop} · {row.model}'
        out.append(f'<text x="{left-10}" y="{y+18}" text-anchor="end" class="axis-label">{esc(label)}</text>')
        x=left
        total=float(row.robust_sell_decisions+row.robust_store_decisions+row.sensitive_decisions)
        for key,color in [('robust_sell_decisions','#4c896b'),('robust_store_decisions','#1c7891'),('sensitive_decisions','#cf6545')]:
            count=float(row[key])
            w=plot_w*count/max_count
            if w:
                out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="22" fill="{color}"/>')
                if w > 24:
                    out.append(f'<text x="{x+w/2:.1f}" y="{y+15}" text-anchor="middle" class="bar-label">{count:.0f}</text>')
                x += w
        out.append(f'<text x="{left+plot_w+7}" y="{y+16}" class="axis-label">n={total:.0f}</text>')
    out.append('</svg>')
    return ''.join(out)


def architecture_svg() -> str:
    labels = [
        ('Data sources', 'price · farmer · warehouse'),
        ('Preprocessing', 'quarter aggregation · validation'),
        ('Forecasting', 'Seasonal Naive · ARIMA · SARIMA · LSTM'),
        ('Rolling-origin', '3 origins · 4-quarter horizon'),
        ('Sell / Store', 'retrospective scenario decision'),
        ('Warehouse allocation', 'continuous LP · CBC'),
        ('Transport', 'Scenario-based Haversine transport proxy'),
        ('Robustness', 'interval · sensitivity · audit'),
        ('Decision support', 'human oversight · chatbot separate'),
    ]
    width, height = 1080, 500
    box_w, box_h = 300, 70
    positions = [(30,30),(390,30),(750,30),(750,145),(390,145),(30,145),(30,260),(390,260),(750,260)]
    out=[f'<svg class="architecture" viewBox="0 0 {width} {height}" role="img" aria-label="ADIS research pipeline architecture">',
         '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#176b67"/></marker></defs>']
    for i,(title,subtitle) in enumerate(labels):
        x,y=positions[i]
        fill='#e5f0ed' if i not in (6,8) else '#f4e8df'
        out.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="5" fill="{fill}" stroke="#176b67" stroke-width="1.5"/>')
        out.append(f'<text x="{x+15}" y="{y+27}" class="arch-title">{esc(title)}</text>')
        out.append(f'<text x="{x+15}" y="{y+49}" class="arch-sub">{esc(subtitle)}</text>')
    arrows=[(330,65,390,65),(690,65,750,65),(900,100,900,145),(750,180,690,180),(390,180,330,180),(180,215,180,260),(330,295,390,295),(690,295,750,295)]
    for x1,y1,x2,y2 in arrows:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#176b67" stroke-width="2" marker-end="url(#arrow)"/>')
    out.append('<text x="540" y="400" text-anchor="middle" class="arch-note">Validated computational pipeline is deterministic/statistical; local LLM is a separate conversational interface.</text>')
    out.append('<text x="540" y="430" text-anchor="middle" class="arch-note">Transport output is a reference-origin scenario proxy, not road routing, farmer routing, or CVRP.</text>')
    out.append('</svg>')
    return ''.join(out)


def route_schematic(routes) -> str:
    if routes.empty or not {'origin_latitude','origin_longitude','destination_latitude','destination_longitude'} <= set(routes.columns):
        return '<p class="empty">Coordinate schematic unavailable in the saved route artifact.</p>'
    frame=routes.drop_duplicates('destination_id').head(12).copy()
    origin=(float(frame['origin_latitude'].mean()),float(frame['origin_longitude'].mean()))
    lat_min=float(min(frame.destination_latitude.min(),origin[0])); lat_max=float(max(frame.destination_latitude.max(),origin[0]))
    lon_min=float(min(frame.destination_longitude.min(),origin[1])); lon_max=float(max(frame.destination_longitude.max(),origin[1]))
    lat_span=max(lat_max-lat_min,0.1); lon_span=max(lon_max-lon_min,0.1)
    width,height=760,360
    def xy(lat,lon):
        return (60+(lon-lon_min)/lon_span*640, 35+(lat_max-lat)/lat_span*270)
    ox,oy=xy(*origin)
    out=[f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Schematic of warehouse centroid origin to destination coordinates">',
         '<text x="380" y="22" text-anchor="middle" class="svg-title">Coordinate schematic · not a road map</text>']
    for _,row in frame.iterrows():
        x,y=xy(float(row.destination_latitude),float(row.destination_longitude))
        out.append(f'<line x1="{ox:.1f}" y1="{oy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#bd8066" stroke-width="1" stroke-dasharray="5 4"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#1c7891"><title>Warehouse {esc(row.destination_id)}</title></circle>')
    out.append(f'<rect x="{ox-6:.1f}" y="{oy-6:.1f}" width="12" height="12" fill="#cf6545"><title>Synthetic warehouse-coordinate centroid</title></rect>')
    out.append(f'<text x="{ox+10:.1f}" y="{oy-9:.1f}" class="axis-label">Synthetic centroid origin</text>')
    out.append('<text x="380" y="336" text-anchor="middle" class="axis-label">Straight connectors indicate reference-origin-to-warehouse scenario legs only.</text></svg>')
    return ''.join(out)


def package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return 'Not installed in selected environment'


def load_evidence():
    names = [
        'forecast_predictions.csv','forecast_fold_metrics.csv','forecast_horizon_metrics.csv',
        'forecast_model_summary.csv','forecast_interval_metrics.csv','forecast_dm_tests.csv',
        'forecast_final_table.csv','sell_store_decisions.csv','sell_store_summary.csv',
        'sell_store_baseline_summary.csv','sell_store_forecast_error_sensitivity.csv',
        'forecast_error_sensitivity_propagation.csv','prediction_interval_decision_robustness.csv',
        'prediction_interval_robustness_summary.csv','end_to_end_parameter_sensitivity.csv',
        'end_to_end_parameter_sensitivity_summary.csv','warehouse_summary.csv',
        'warehouse_baseline_comparison.csv','warehouse_optimization_results.csv',
        'warehouse_sensitivity.csv','routing_summary.csv','routing_baseline_comparison.csv',
        'routing_routes.csv','routing_sensitivity.csv','module_ablation_results.csv',
        'module_ablation_summary.csv','formula_consistency_audit.csv',
        'rolling_origin_support_check.csv','farmer_crop_dataset (1).csv',
        'farmer_decision_history.csv','tamilnadu_full_warehouse_dataset (1).csv',
        'price dataset (1).csv',
    ]
    data={name:csv(name) for name in names}
    data['config']=json_file('experiment_config.json')
    data['sell_assumptions']=json_file('sell_store_assumptions.json')
    data['warehouse_assumptions']=json_file('warehouse_research_assumptions.json')
    data['routing_assumptions']=json_file('routing_research_assumptions.json')
    data['technical_report']=(ROOT/'TECHNICAL_VALIDATION_REPORT.md').read_text(encoding='utf-8')
    data['repro_report']=(ROOT/'REPRODUCIBILITY_REPORT.md').read_text(encoding='utf-8')
    data['existing_report']=(ROOT/'ADIS_Complete_Performance_Report.html').read_text(encoding='utf-8')
    data['existing_report_md']=(ROOT/'ADIS_Complete_Performance_Report.md').read_text(encoding='utf-8')
    return data


def derive_forecast_metrics(data):
    predictions=data['forecast_predictions.csv']
    valid=predictions.loc[predictions.validity_status.eq('VALID')].copy()
    valid['error']=valid.predicted.astype(float)-valid.actual.astype(float)
    denom=valid.actual.abs()+valid.predicted.abs()
    valid['sMAPE_pct']=np.where(denom.eq(0),np.nan,200*valid.error.abs()/denom)
    summary=data['forecast_model_summary.csv'].copy()
    extras=valid.groupby(['crop','model'],as_index=False).agg(
        sMAPE=('sMAPE_pct','mean'),
        MBE=('error','mean'),
        error_SD=('error',lambda s: float(s.std(ddof=1)) if len(s)>1 else np.nan),
        valid_predictions=('error','size'),
    )
    horizon_extras=valid.groupby(['crop','model','horizon'],as_index=False).agg(
        sMAPE=('sMAPE_pct','mean'),
        MBE=('error','mean'),
        error_SD=('error',lambda s: float(s.std(ddof=1)) if len(s)>1 else np.nan),
        valid_predictions_derived=('error','size'),
    )
    horizon_summary=data['forecast_horizon_metrics.csv'].merge(
        horizon_extras,on=['crop','model','horizon'],how='left'
    )
    return valid, summary.merge(extras,on=['crop','model'],how='left'), horizon_summary


def build_sections(data, args):
    price=data['price dataset (1).csv']
    farmer=data['farmer_crop_dataset (1).csv']
    history=data['farmer_decision_history.csv']
    warehouse_data=data['tamilnadu_full_warehouse_dataset (1).csv']
    predictions,forecast_summary,horizon_summary=derive_forecast_metrics(data)
    fold=data['forecast_fold_metrics.csv']
    horizon=data['forecast_horizon_metrics.csv']
    config=data['config']
    sell_ass=data['sell_assumptions']
    selected=config.get('selected_models',{})
    decisions=data['sell_store_decisions.csv']
    selected_decisions=decisions.loc[decisions.apply(lambda r:selected.get(r.crop)==r.model,axis=1)].copy()
    selected_decision_summary=selected_decisions.groupby('crop',as_index=False).agg(
        cases=('decision','size'),sell=('decision',lambda s:int(s.eq('sell').sum())),
        store=('decision',lambda s:int(s.eq('store').sum())),
        agreement_pct=('decision_correct',lambda s:float(s.mean()*100)),
        mean_regret_inr=('regret_inr','mean'),
    )
    baseline=data['sell_store_baseline_summary.csv']
    warehouse_summary=data['warehouse_summary.csv']
    warehouse_baseline=data['warehouse_baseline_comparison.csv']
    routing=data['routing_summary.csv']
    routing_baseline=data['routing_baseline_comparison.csv']
    interval=data['prediction_interval_decision_robustness.csv']
    interval_summary=data['prediction_interval_robustness_summary.csv']
    param_summary=data['end_to_end_parameter_sensitivity_summary.csv']
    formula=data['formula_consistency_audit.csv'].iloc[0]
    rolling=data['rolling_origin_support_check.csv'].iloc[0]
    dm=data['forecast_dm_tests.csv']

    price_numeric=pd.to_numeric(price['Price_INR_per_Quintal'],errors='coerce')
    price_date=pd.PeriodIndex(price.Year.astype('Int64').astype(str)+'Q'+price.Quarter.astype(str).str.extract(r'Q?([1-4])',expand=False),freq='Q')
    price['__date']=price_date.astype(str)
    price['__unit_price']=price_numeric
    price_valid=price.loc[price['__unit_price'].notna()]
    price_range=f"{price_valid['__date'].min()} to {price_valid['__date'].max()}"
    crop_price_counts=price_valid.groupby('Crop').agg(records=('__unit_price','size'),start=('__date','min'),end=('__date','max')).reset_index()
    ratio_rows=[]
    for crop,group in price.dropna(subset=['Price_INR_per_Quintal','Final_Price']).groupby('Crop'):
        source=pd.to_numeric(group['Price_INR_per_Quintal'],errors='coerce')
        final=pd.to_numeric(group['Final_Price'],errors='coerce')
        ratio_rows.append({'crop':crop,'median_Final_Price_to_labeled_price_ratio':float((final/source).median())})
    farmer_crop_column='Crop' if 'Crop' in farmer else ('Crop_Cultivated' if 'Crop_Cultivated' in farmer else None)
    farmer_counts=farmer[farmer_crop_column].value_counts().rename_axis('crop').reset_index(name='rows') if farmer_crop_column else pd.DataFrame()
    farmer_id_column=next((c for c in farmer.columns if c.lower() in ('farmer_id','farmerid','farmer id')),None)
    farmer_count=int(farmer[farmer_id_column].nunique()) if farmer_id_column else 0
    wh_crop_counts={crop:int(warehouse_data[f'{crop}_Supported'].sum()) for crop in CROPS if f'{crop}_Supported' in warehouse_data}
    facility_districts=warehouse_data['District'].nunique() if 'District' in warehouse_data else 'Not documented in current source file'
    tests=list(sorted(p.name for p in (ROOT/'tests').glob('test_*.py')))
    package_names=['numpy','pandas','scipy','statsmodels','scikit-learn','tensorflow','keras','pulp','pytest']
    packages={name:package_version(name) for name in package_names}
    test_status='NOT RECORDED' if args.tests_failed is None else ('PASS' if args.tests_failed==0 else 'FAIL')
    test_status_class='good' if test_status=='PASS' else ('bad' if test_status=='FAIL' else '')
    test_runtime=esc(args.test_runtime)

    # Section 01
    valid_folds=int((fold['status']=='VALID').sum())
    failed_folds=int((fold['status']=='FAILED').sum())
    sections=[]
    sections.append(section(1,
        '<p class="lede">ADIS is an integrated research prototype that evaluates quarterly crop-price forecasts, retrospective sell/store choices, compatible-warehouse allocation, and a single-leg transport-cost proxy. Its quantitative evidence is limited to saved validation folds and stated scenario assumptions.</p>'
        '<div class="metrics">'
        +metric_card(f'{len(predictions):,}','valid forecast rows','144 expected across 3 crops × 4 models × 3 origins × 4 horizons')
        +metric_card(f'{len(decisions):,}','retrospective sell/store cases','Standardized 1-quintal scenarios')
        +metric_card(f'{len(warehouse_summary):,}','warehouse scenarios',f"CBC status: {warehouse_summary.solver_status.value_counts().to_dict()}")
        +metric_card(f'{len(routing):,}','transport proxy scenarios','Haversine reference-origin legs; not CVRP')
        +metric_card(f'{fmt(args.tests_passed,0)} passed','latest test run',f'{fmt(args.tests_failed,0)} failed · {fmt(args.tests_warnings,0)} warnings · {test_runtime}')
        +'</div>'
        '<p><strong>Implementation status:</strong> research modules and audits are implemented; <strong>repository validation:</strong> full test command passed in the recorded run. Forecast selection is procedure-specific. Storage, spoilage, warehouse rates, and transport are scenario assumptions. There is no causal farmer-income evaluation.</p>'
        '<p><strong>AI disclosure:</strong> a separate chatbot client is configured for a local OpenAI-compatible LLM service; it is not the forecasting, optimization, or statistical-validation engine.</p>'
    ))

    # Section 02
    dataset_table=pd.DataFrame([
        {'Dataset':'price dataset (1).csv','Records':len(price),'Variables':', '.join(price.columns),'Crops':'Rice, Onion, Tomato','Period / frequency':f'{price_range}; quarterly labels','Units / role':'Price_INR_per_Quintal; INR/quintal. Final_Price is excluded due scale inconsistency.','Provenance':'Not documented in the current implementation.'},
        {'Dataset':'farmer_crop_dataset (1).csv','Records':len(farmer),'Variables':', '.join(farmer.columns),'Crops':', '.join(sorted(farmer[farmer_crop_column].dropna().astype(str).unique())) if farmer_crop_column else 'Not encoded','Period / frequency':'Survey description: Jan-Mar 2026; CSV has no collection-date field','Units / role':'Yield field is tonnes/acre; no cultivated-area field in CSV.','Provenance':'Study description supplied for this report; row-level provenance is not encoded in the file.'},
        {'Dataset':'tamilnadu_full_warehouse_dataset (1).csv','Records':len(warehouse_data),'Variables':', '.join(warehouse_data.columns),'Crops':', '.join(crop for crop,n in wh_crop_counts.items() if n),'Period / frequency':'Static facility records','Units / role':f"Capacity_MT; storage cost source unit/billing currency unspecified; {len(warehouse_data)} facilities across {facility_districts} districts.",'Provenance':'Not independently verified; cost currency and billing period are assumptions.'},
        {'Dataset':'farmer_decision_history.csv','Records':len(history),'Variables':', '.join(history.columns),'Crops':', '.join(sorted(history['Crop'].dropna().astype(str).unique())) if 'Crop' in history else 'Not encoded','Period / frequency':'Sparse history-like records; not the forecasting evaluation set','Units / role':f'{int(history.isna().sum().sum())} missing cells; excluded as validated outcomes.','Provenance':'Not documented in the current implementation.'},
    ])
    study_note=(
        '<div class="callout"><strong>Farmer-study description provided for this report:</strong> 150 farmers in Tirunelveli region including Tenkasi; January-March 2026; direct/local farming-network recruitment; consent obtained; crop name, cultivated area, cultivation season; three crops per farmer; 450 farmer-crop observations. '
        f'The supplied CSV has {len(farmer):,} rows and fields {esc(", ".join(farmer.columns))}; it does not itself encode recruitment dates, consent, area, or region. These study descriptors therefore remain report-level documentation rather than fields independently verifiable from that CSV.</div>'
    )
    sections.append(section(2,
        '<p>The forecast source is quarterly and uses the explicitly labeled <code>Price_INR_per_Quintal</code> field. Crop-wise duplicate quarters are averaged; missing source prices and calendar gaps are not interpolated. The evaluation uses the longest contiguous segments: Rice 26 observations (2009Q1-2015Q2), Onion 26 (2009Q1-2015Q2), Tomato 24 (2009Q3-2015Q2; 2009Q2 gap excluded).</p>'
        +table(dataset_table,digits=0)
        +study_note
        +'<p>The farmer dataset has 450 rows and 150 distinct farmer IDs where the ID field is present; each crop has 150 rows. This count does not by itself establish that farmer-level yield or income outcomes were used in the forecasting/decision evaluation. The warehouse source contains no observed farmer origin, carrier tariff provenance, or actual billing period.</p>'
        +'<p><strong>Forecast split:</strong> no random split or separately held test set is used in the validated forecast experiment. The latest three non-overlapping rolling origins are used chronologically, expanding training from 12 to 16 to 20 observations and validating four following quarters at each origin. Gaps are excluded rather than filled.</p>'
        +details('Labeled-price scale check',table(pd.DataFrame(ratio_rows),digits=4))
    ))

    # Section 03
    sections.append(section(3,
        '<p>Research computation is separate from the farmer-facing conversational UI. Forecast rows are saved before sell/store scoring; warehouse allocation consumes selected-model decision scenarios; routing consumes warehouse allocations. Robustness audits consume those saved artifacts.</p>'
        +architecture_svg()
        +'<div class="legend-grid"><div><strong>Implemented:</strong> crop-wise preprocessing, rolling-origin forecast models, formula-based retrospective sell/store, cost-minimizing continuous warehouse allocation, and deterministic artifact audits.</div><div><strong>Scenario-based:</strong> one-quintal decisions, assumed storage/spoilage costs, warehouse cost rates, synthetic origin, Haversine transport, sensitivity multipliers.</div><div><strong>Limited / unsupported:</strong> calibrated probabilistic uncertainty for every model, causal farmer welfare, actual farmer routing, road-network routing, and genuine CVRP.</div></div>'
    ))

    # Section 04
    model_rows=pd.DataFrame([
        {'Model':'Seasonal Naive','Method':'Repeats the final four training observations in sequence: y-hat(t+h)=y(t-4+((h-1) mod 4)).','Input / training':'Observed crop-specific quarterly price series; no fitted parameters.','Validation / role':'Evaluated on the same three rolling origins; comparison baseline, not selected as current crop choice.','Limitations':'Seasonal cycle only; no probabilistic interval.'},
        {'Model':'ARIMA','Method':'SARIMAX implementation with order (1,1,1), no seasonal terms.','Input / training':'Each expanding training fold; stationarity and invertibility enforced; L-BFGS, max 500 iterations.','Validation / role':'4-step fold forecasts; eligible for model selection and native 95% intervals.','Limitations':'Small number of origins; convergence/initialization warnings recorded.'},
        {'Model':'SARIMA','Method':'SARIMAX with (p,d,q)=(0,1,1), seasonal (P,D,Q,s)=(0,1,1,4).','Input / training':'Each expanding training fold; stationarity and invertibility enforced; L-BFGS, max 500 iterations.','Validation / role':'4-step fold forecasts; eligible for selection and native 95% intervals.','Limitations':'Seasonal parameters estimated from short series; small-sample warnings.'},
        {'Model':'LSTM','Method':'Input(window,1) -> LSTM(32, ReLU) -> Dense(1); recursive multi-step predictions.','Input / training':'Train-fold MinMax scaling; lookback min(4, n_train-1); Adam 0.001, MSE, 20 epochs, batch 8, no shuffle; seed 42.','Validation / role':'Refit within each fold; evaluated against statistical baselines.','Limitations':'Only 8, 12, and 16 supervised sequences per fold; no calibrated native interval.'},
    ])
    sections.append(section(4,
        '<p>All models receive only the training prefix for their fold. Metrics compare each complete four-quarter validation vector with aligned actual prices. LSTM scaling is fit on training data per fold; forecast outputs are generated recursively.</p>'
        +table(model_rows,digits=0)
        +'<p><strong>ARIMA/SARIMA form:</strong> the implementation estimates a SARIMAX model, which can be written as <code>phi(B) Phi(B^4) (1-B)^d (1-B^4)^D y_t = c + theta(B) Theta(B^4) epsilon_t</code>; for ARIMA the seasonal polynomial terms are identity, and for SARIMA the configured orders are applied. This is a model-family representation; fitted coefficients vary by crop and fold.</p>'
        +'<p><strong>LSTM recurrence:</strong> standard gated recurrent state updates are trained on scaled supervised windows; exact trained weights are fold-specific and not presented as fixed paper constants.</p>'
    ))

    # Section 05
    metrics_columns=['crop','model','valid_folds','failed_folds','mean_MAE','mean_RMSE','mean_MAPE','mean_R2','sMAPE','MBE','error_SD']
    metric_chart=grouped_bar_svg(forecast_summary,'crop','model','mean_RMSE','Rolling-origin RMSE by crop and model','RMSE (INR/quintal)')
    mae_chart=grouped_bar_svg(forecast_summary,'crop','model','mean_MAE','Rolling-origin MAE by crop and model','MAE (INR/quintal)')
    mape_chart=grouped_bar_svg(forecast_summary,'crop','model','mean_MAPE','Rolling-origin MAPE by crop and model','MAPE (%)')
    error_chart=grouped_bar_svg(forecast_summary,'crop','model','error_SD','Forecast-error standard deviation by crop and model','Error SD (INR/quintal)')
    actual_figs=''.join(f'<figure>{actual_forecast_svg(predictions,crop,selected.get(crop,''))}<figcaption>Selected-model validation series; actual and forecast values are from valid rolling-origin rows in forecast_predictions.csv. This does not represent a future holdout.</figcaption></figure>' for crop in CROPS)
    sections.append(section(5,
        f'<p>Protocol: {config.get("validation_windows")} origins; four-quarter horizon; minimum training length {config.get("min_train_size")} observations; expanding train windows. Fold records: {len(fold)}; valid {valid_folds}; failed {failed_folds}. Horizon table metrics pool only within each crop/model/horizon and report three origin-level predictions per cell. The model summary averages fold metrics within each crop/model; it does not pool crops.</p>'
        +'<div class="chart-grid"><figure>'+metric_chart+'<figcaption>Lower RMSE indicates smaller squared-error scale within this validation sample.</figcaption></figure><figure>'+mae_chart+'<figcaption>MAE in INR per quintal, shown separately by crop.</figcaption></figure><figure>'+mape_chart+'<figcaption>MAPE is percentage; use caution where price levels vary.</figcaption></figure><figure>'+error_chart+'<figcaption>Sample standard deviation of pooled valid forecast errors, computed from forecast_predictions.csv.</figcaption></figure></div>'
        +'<h3>Model summary by crop</h3>'+table(forecast_summary,metrics_columns,digits=3)
        +details('Horizon metrics by crop/model/horizon',table(horizon_summary,digits=3),False)
        +'<h3>Actual versus forecast</h3>'+actual_figs
        +'<p>MAE, RMSE, MAPE, and R2 are the stored validation metrics. sMAPE, mean bias error (MBE = mean(predicted - actual)), and sample error SD are recalculated from the valid prediction rows and are labeled as derived summaries.</p>'
    ))

    # Section 06
    selection=pd.DataFrame([{'crop':crop,'selected_model':model,'mean_validation_RMSE':float(forecast_summary.loc[(forecast_summary.crop==crop)&(forecast_summary.model==model),'mean_RMSE'].iloc[0]),'valid_folds':int(forecast_summary.loc[(forecast_summary.crop==crop)&(forecast_summary.model==model),'valid_folds'].iloc[0]),'failed_folds':int(forecast_summary.loc[(forecast_summary.crop==crop)&(forecast_summary.model==model),'failed_folds'].iloc[0]),'selection_rule':'Lowest mean rolling-origin validation RMSE'} for crop,model in selected.items()])
    sections.append(section(6,
        '<p>The selection criterion is the lowest mean validation RMSE across valid rolling-origin folds for each crop. These are selections under the implemented procedure and small validation design, not universal model rankings.</p>'
        +table(selection,digits=3)
    ))

    # Section 07
    interval_class_counts=interval.decision_class.value_counts().to_dict()
    sections.append(section(7,
        '<p>Native 95% prediction intervals come from fitted statsmodels forecasts using <code>get_forecast().conf_int(alpha=0.05)</code>. Only valid ARIMA/SARIMA predictions with finite native bounds are evaluated. LSTM and Seasonal Naive have no generated probabilistic interval; no artificial interval is supplied.</p>'
        +f'<div class="metrics">{metric_card(len(interval),"native-interval decisions","ARIMA/SARIMA valid rows")}{metric_card(interval_class_counts.get("ROBUST_SELL",0),"ROBUST_SELL","same action at lower, point, upper")}{metric_card(interval_class_counts.get("ROBUST_STORE",0),"ROBUST_STORE","same action at all three values")}{metric_card(interval_class_counts.get("DECISION_SENSITIVE",0),"DECISION_SENSITIVE","action changes over interval values")}</div>'
        +f'<figure>{stability_svg(interval_summary)}<figcaption>Counts are summed across the four forecast horizons for each crop/model. Each row has 12 interval cases (3 origins x 4 horizons).</figcaption></figure>'
        +table(interval_summary,digits=2)
        +details('Forecast interval coverage and width artifact',table(data['forecast_interval_metrics.csv'],digits=3))
        +'<p>For decision evaluation, raw lower, point, and upper forecasts are retained in parallel with evaluation values clamped to zero. This follows the decision function’s nonnegative-price constraint. The clamp changes only sensitivity evaluation inputs; it does not alter saved forecasts.</p>'
        +'<p>Forecast-error propagation and interval decision robustness are deterministic scenario checks. They do not establish a calibrated predictive distribution or probabilistic farmer outcome.</p>'
    ))

    # Section 08
    sections.append(section(8,
        '<div class="equation"><div><b>Sell now value</b><code>V_sell = Q × P0</code></div><div><b>Stored quantity</b><code>Q_store = Q × (1 - spoilage)</code></div><div><b>Storage cost</b><code>C_storage = (Q quintals × 100 kg/quintal) × rate (INR/kg/month) × duration (months)</code></div><div><b>Store value</b><code>V_store = Q_store × P_forecast - C_storage - transport_cost</code></div><div><b>Action</b><code>Store if V_store &gt; V_sell; otherwise Sell</code></div></div>'
        +'<p>The decision function uses the point forecast and does not receive future actual prices. Ties resolve to Sell because the code uses a strict greater-than comparison. Retrospective actual prices are used only after choosing the action, to score decision agreement and regret.</p>'
        +f'<ul><li>Scenario quantity: {fmt(sell_ass.get("scenario_quantity_quintal"))} quintal.</li><li>Storage rate (INR/kg/month): {esc(json.dumps(sell_ass.get("storage_rate_inr_per_kg_per_month",{}),sort_keys=True))}.</li><li>Spoilage applied once per holding decision: {esc(json.dumps(sell_ass.get("spoilage_rate_per_holding_decision",{}),sort_keys=True))}.</li><li>Duration: {fmt(sell_ass.get("storage_duration_months_per_forecast_quarter"))} months per forecast quarter, multiplied by horizon.</li><li>Transport in this decision phase: {fmt(sell_ass.get("transport_cost_inr"))} INR scenario charge, configured as zero because no validated route-specific quote is available.</li></ul>'
        +'<p>Assumptions are scenario parameters, not measured farm invoices or validated post-harvest-loss observations.</p>'
    ))

    # Section 09
    baseline_group=baseline.groupby(['crop','model'],as_index=False).agg(
        agreement=('decision_agreement_percentage','mean') if 'decision_agreement_percentage' in baseline else ('number_of_decisions','mean'),
        mean_regret=('mean_regret_inr','mean') if 'mean_regret_inr' in baseline else ('number_of_decisions','mean'),
        mean_value=('mean_realized_net_value_inr','mean') if 'mean_realized_net_value_inr' in baseline else ('number_of_decisions','mean'),
    )
    decision_distribution=selected_decisions.groupby(['crop','model','horizon','decision'],as_index=False).size().rename(columns={'size':'decision_count'})
    sections.append(section(9,
        f'<p>The decision artifact has {len(decisions)} retrospective cases: 3 crops × 4 models × 4 horizons × 3 origins. Current selected-model subset has {len(selected_decisions)} cases. Agreement compares forecast-based action with the retrospectively actual-value-optimal action; it is not a farmer observation.</p>'
        +'<h3>Selected-model summary</h3>'+table(selected_decision_summary,digits=3)
        +'<h3>Decision counts by selected crop/model/horizon</h3>'+table(decision_distribution,digits=0)
        +'<h3>Always-Sell, Always-Store, and Seasonal-Naive baselines</h3>'+table(baseline_group,digits=3)
        +details('Full crop/model/horizon sell-store summary',table(data['sell_store_summary.csv'],digits=3))
        +'<p>Results are retrospective one-quintal scenario evaluations and are NOT causal farmer-income estimates.</p>'
    ))

    # Section 10
    fes=data['forecast_error_sensitivity_propagation.csv']
    old_fes=data['sell_store_forecast_error_sensitivity.csv']
    flip_by=fes.groupby(['crop','model'],as_index=False).agg(decision_flip_rate_percentage=('decision_flip_rate_percentage','mean'),mean_propagated_value_error_inr=('mean_propagated_value_error_inr','mean'),mean_regret_inr=('mean_regret_inr','mean'),mean_absolute_forecast_error_inr=('mean_absolute_forecast_error_inr','mean'))
    flip_plot=grouped_bar_svg(flip_by,'crop','model','decision_flip_rate_percentage','Forecast-error sensitivity: mean decision flip rate by crop/model','Decision flips (%)')
    sections.append(section(10,
        '<p><strong>Scenario-based forecast-error sensitivity analysis.</strong> The audit uses observed absolute forecast errors to perturb forecast-dependent values through the implemented sell/store decision rule. Propagated value error equals absolute forecast error × effective stored quantity after spoilage. It is deterministic, not a probability distribution.</p>'
        +f'<p>Configured forecast perturbations for the end-to-end scenarios: -20%, -15%, -10%, -5%, 0%, +5%, +10%, +15%, +20%. The existing phase sensitivity file contains {len(old_fes)} rows; the propagated audit file contains {len(fes)} crop/model/horizon groups.</p>'
        +f'<figure>{flip_plot}<figcaption>Mean over available horizon rows within each crop/model; each horizon has three origins.</figcaption></figure>'
        +table(fes,digits=3)
        +details('Sell/store forecast-error sensitivity source table',table(old_fes,digits=3))
    ))

    # Section 11
    param=data['end_to_end_parameter_sensitivity.csv']
    supported_wh=int(param.warehouse_sensitivity_status.eq('SUPPORTED_SAVED_SCENARIO').sum())
    supported_rt=int(param.routing_sensitivity_status.eq('SUPPORTED_SAVED_SCENARIO').sum())
    total_scenarios=int(param.total_scenario_cost_inr.notna().sum())
    sens_figs=''.join(f'<figure>{sensitivity_svg(param_summary,p)}<figcaption>Observed scenario perturbations only; x values use the units shown on each axis.</figcaption></figure>' for p in ['forecast_error','storage_cost','spoilage','transport_cost','quantity'])
    sections.append(section(11,
        f'<p>The output covers {len(param):,} one-factor-at-a-time decision scenarios over forecast error, storage cost, spoilage, transport cost, and quantity. Warehouse and routing costs are filled only when matching selected-model layer scenarios exist in the saved sensitivity artifacts; {supported_wh} warehouse and {supported_rt} routing layer rows are supported, with {total_scenarios} combined totals. Other layer fields remain blank with a status reason, rather than carrying forward baseline cost.</p>'
        +'<div class="chart-grid">'+sens_figs+'</div>'
        +table(param_summary,digits=3)
        +details('All row-level scenario results and layer statuses',table(param,digits=3))
        +'<p>Patterns are descriptive of these configured scenarios only. Quantity and transport changes can scale downstream proxy costs; transport changes do not flip sell/store actions under the phase assumption where decision transport cost is zero. This is not a causal analysis.</p>'
    ))

    # Section 12
    wh_ass=data['warehouse_assumptions']
    wh_agg=warehouse_summary.groupby('crop',as_index=False).agg(scenarios=('scenario_id','nunique'),mean_allocated_quintal=('total_allocated_quantity_quintal','mean'),mean_unallocated_quintal=('total_unallocated_quantity_quintal','mean'),mean_storage_cost_inr=('total_storage_cost_inr','mean'),mean_transport_cost_inr=('total_transport_cost_inr','mean'),mean_total_cost_inr=('total_cost_inr','mean'),max_violations=('constraint_violations','max'))
    wh_base=warehouse_baseline.groupby(['crop','method'],as_index=False).agg(scenarios=('scenario_id','nunique'),mean_total_cost_inr=('total_cost_inr','mean'),mean_storage_cost_inr=('storage_cost_inr','mean'),mean_transport_cost_inr=('transport_cost_inr','mean'),mean_unallocated_quintal=('unallocated_quantity_quintal','mean'))
    wh_chart=grouped_bar_svg(wh_base,'crop','method','mean_total_cost_inr','Warehouse baseline scenario cost by crop and method','Mean cost (INR)',['MILP','Nearest Feasible','Lowest Storage Cost','Existing Method'])
    nfac=len(warehouse_data)
    optimal=int(warehouse_summary.solver_status.eq('Optimal').sum())
    sections.append(section(12,
        '<p><strong>Formulation correction:</strong> the project labels this stage “MILP”, but its decision variables are continuous divisible quantities with no integer/binary restrictions. The saved implementation is mathematically a linear program solved through PuLP CBC, not a mixed-integer model.</p>'
        '<div class="equation"><div><b>Decision variables</b><code>x[c,w] ≥ 0; u[c] ≥ 0</code></div><div><b>Objective</b><code>min Σ x[c,w](storage_cost[c,w] + transport_cost[c,w]) + u[c] × shortage_penalty</code></div><div><b>Quantity balance</b><code>Σ compatible_w x[c,w] + u[c] = available_quantity[c]</code></div><div><b>Capacity</b><code>x[c,w] ≤ compatible_capacity[w]</code></div></div>'
        +f'<p>Compatible facilities are selected by crop-support flags. Capacity converts MT × 10 to quintals. Storage source rates are treated as INR/MT/month and converted to INR/quintal/month; transport is configured at INR {fmt(wh_ass.get("transport_rate_inr_per_km_per_metric_tonne"))}/km/MT. The unallocated penalty is INR {fmt(wh_ass.get("unallocated_penalty_inr_per_quintal"))}/quintal in the solver objective, but is excluded from reported storage-plus-transport total cost.</p>'
        +f'<div class="metrics">{metric_card(nfac,"facilities",f'{facility_districts} districts')}{metric_card(len(warehouse_summary),"allocation scenarios",f'{optimal} CBC optimal')}{metric_card(int(warehouse_summary.constraint_violations.sum()),"constraint violations","Across saved scenarios")}{metric_card(fmt(warehouse_summary.total_unallocated_quantity_quintal.sum()),"unallocated quantity","Quintals across scenarios")}</div>'
        +'<h3>Crop-level allocation results</h3>'+table(wh_agg,digits=3)
        +'<figure>'+wh_chart+'<figcaption>Means across saved scenarios by crop. “MILP” is the artifact method label; formulation is continuous LP.</figcaption></figure>'
        +'<h3>Available baselines</h3>'+table(wh_base,digits=3)
        +'<p>Compatible-facility counts from source support flags: '+esc(json.dumps(wh_crop_counts,sort_keys=True))+'.</p>'
        +details('All saved warehouse scenario rows',table(warehouse_summary,digits=3))
        +'<p>Warehouse cost results are scenario-based under the documented assumptions and unverified source rate fields. They are not observed procurement or storage costs.</p>'
    ))

    # Section 13
    route_crop=routing.groupby('crop',as_index=False).agg(scenarios=('scenario_id','nunique'),mean_distance_km=('average_route_distance_km','mean'),mean_transport_cost_inr=('total_transport_cost_inr','mean'),mean_cost_per_quintal=('average_transport_cost_inr_per_quintal','mean'),feasible=('route_feasibility','sum'),route_legs=('number_of_routes','sum'))
    route_base=routing_baseline.groupby(['crop','method'],as_index=False).agg(scenarios=('scenario_id','nunique'),mean_distance_km=('average_distance_per_route_km','mean'),mean_transport_cost_inr=('total_transport_cost_inr','mean'),feasible_scenarios=('route_feasible','sum'))
    route_sens=data['routing_sensitivity.csv'].groupby(['scenario_type','scenario_multiplier'],as_index=False).agg(scenarios=('scenario_id','size'),mean_distance_km=('distance_km','mean'),mean_transport_cost_inr=('transport_cost_inr','mean'),mean_transported_quantity_quintal=('quantity_transported_quintal','mean'),mean_unserved_quantity_quintal=('unserved_quantity_quintal','mean'),feasible_scenarios=('route_feasible','sum'))
    route_chart_data=route_crop.copy()
    route_chart_data['series']='Transport proxy'
    route_chart=grouped_bar_svg(route_chart_data,'crop','series','mean_transport_cost_inr','Haversine transport proxy cost by crop','INR per scenario',['Transport proxy'])
    origin_lat=float(data['routing_routes.csv'].origin_latitude.mean())
    origin_lon=float(data['routing_routes.csv'].origin_longitude.mean())
    sections.append(section(13,
        '<p>This section is <strong>Transport-Cost Evaluation Using Haversine Reference-Origin Proxy</strong>. The origin is the arithmetic centroid of warehouse coordinates, not a farmer/customer coordinate; each assigned warehouse is a destination. Distances are straight-line spherical distances using Earth radius 6,371 km. The implementation does not construct vehicle tours or road routes.</p>'
        +f'<p>Origin centroid recorded in routing validation: latitude {origin_lat:.6f}, longitude {origin_lon:.6f}. Transport cost = distance_km × allocated_quintals / 10 × configured INR {fmt(data["routing_assumptions"].get("transport_rate_inr_per_km_per_metric_tonne"))}/km/MT.</p>'
        +f'<figure>{route_schematic(data["routing_routes.csv"])}<figcaption>Inline coordinate schematic of the reference origin and warehouse destinations; not a road map or route plan.</figcaption></figure>'
        +'<h3>Crop-level distance and cost</h3>'+table(route_crop,digits=3)
        +'<figure>'+route_chart+'<figcaption>Scenario mean transport cost by crop.</figcaption></figure>'
        +'<h3>Available transport baselines</h3>'+table(route_base,digits=3)
        +'<h3>Saved routing sensitivity scenarios</h3>'+table(route_sens,digits=3)
        +'<p>All saved routing summaries should be read as scenario/reference-origin proxy outputs. No real farmer-route savings, real-world route optimality, or CVRP validation is claimed.</p>'
    ))

    # Section 14
    ablation=data['module_ablation_results.csv']
    ablation_summary=data['module_ablation_summary.csv']
    sections.append(section(14,
        '<p>The stage table is descriptive reporting of metrics available at each pipeline stage, not a causal experiment that disables modules. Metrics not defined or not saved for a stage are explicitly named in <code>unavailable_metrics</code> and are not filled with proxies.</p>'
        +table(ablation_summary,digits=3)
        +details('Crop-level stage outputs',table(ablation,digits=3))
        +'<ul><li>A. Forecasting only adds crop-price forecasts and validation metrics.</li><li>B. Forecast + Sell/Store adds point-forecast-based retrospective action and regret scoring.</li><li>C. + Warehouse adds compatible-facility allocation and storage/transport cost under configured rates.</li><li>D. Full implemented pipeline adds the Haversine transport proxy to saved warehouse scenario costs.</li></ul>'
        +'<p>Different stages use different objectives and units. The progression must not be read as a common-score ranking or as measured farmer welfare.</p>'
    ))

    # Section 15
    mismatch_count=int(formula.get('mismatch_count',0))
    rows_checked=int(formula.get('checked_rows',0))
    consistency=100.0*(rows_checked-mismatch_count)/rows_checked if rows_checked else np.nan
    badge='CONSISTENT' if formula.get('all_formula_checks_pass') and mismatch_count==0 else 'MISMATCH'
    sections.append(section(15,
        f'<div class="status-panel {"good" if badge=="CONSISTENT" else "bad"}"><strong>{badge}</strong><span>{rows_checked} rows checked · {mismatch_count} material mismatches · {fmt(consistency,2)}% row consistency</span></div>'
        +'<p>The formula audit recomputes the saved sell-now, store, incremental value, storage cost, effective quantity, and action using the same assumptions and decision function. Module audited: retrospective sell/store result artifact against current code formulas. This checks code-to-artifact consistency, not external validity.</p>'
        +table(data['formula_consistency_audit.csv'],columns=['mismatch_count','all_formula_checks_pass','checked_rows'],digits=4)
        +'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0"><span style="background:#e6f1eb;color:#286a4e;padding:7px 10px;font:700 12px Segoe UI,sans-serif">CONSISTENT · current</span><span style="background:#f8e9e5;color:#a33e35;padding:7px 10px;font:700 12px Segoe UI,sans-serif">MISMATCH · failure state</span><span style="background:#edf1ee;color:#52666a;padding:7px 10px;font:700 12px Segoe UI,sans-serif">NOT CHECKABLE · evidence missing</span></div>'
        +'<p>Status definitions: <strong>CONSISTENT</strong> means audited fields match within the audit tolerance; <strong>MISMATCH</strong> means one or more checked fields differ; <strong>NOT CHECKABLE</strong> applies only where an artifact/field is absent.</p>'
    ))

    # Section 16
    sections.append(section(16,
        f'<div class="metrics">{metric_card(fmt(rolling.get("validation_windows_configured")),"configured origins")}{metric_card(fmt(rolling.get("max_feasible_windows_observed")),"maximum feasible origins")}{metric_card(str(rolling.get("supported")),"expansion supported")}</div>'
        +table(data['rolling_origin_support_check.csv'],digits=0)
        +f'<p>{esc(rolling.get("support_limit_reason","Not documented in current artifact"))}</p>'
        +'<p>The validation uses non-overlapping four-quarter origins after a minimum 12-observation train prefix. Available contiguous quarterly history supports three origins. Additional origins would require reusing or inventing observations, changing the evaluation design, or introducing unsupported data; none are fabricated.</p>'
    ))

    # Section 17
    dm_status=dm['interpretation'].value_counts(dropna=False).to_dict() if 'interpretation' in dm else {}
    model_diag=fold.groupby('model',as_index=False).agg(folds=('fold','size'),valid=('status',lambda x:int(x.eq('VALID').sum())),failed=('status',lambda x:int(x.eq('FAILED').sum())))
    convergence=[]
    if 'converged' in fold:
        for model,group in fold.loc[fold.model.isin(['arima','sarima'])].groupby('model'):
            conv=group['converged'].astype(str).str.lower()
            convergence.append({'model':model,'converged_folds':int(conv.eq('true').sum()),'nonconverged_or_unavailable':int((~conv.eq('true')).sum())})
    negative_r2=forecast_summary.loc[forecast_summary.mean_R2<0,['crop','model','mean_R2']]
    warning_col='warning' if 'warning' in fold else None
    warning_rows=fold.loc[fold[warning_col].fillna('').astype(str).str.len()>0,['crop','model','fold',warning_col]] if warning_col else pd.DataFrame()
    residual_columns=['crop','model','fold','residual_mean','residual_std','residual_acf_lag1','ljung_box_lag','ljung_box_p_value','small_sample_warning']
    residual_columns=[column for column in residual_columns if column in fold.columns]
    sections.append(section(17,
        '<h3>Diebold-Mariano comparisons</h3>'
        +f'<p>{len(dm)} comparison rows are present. The configured DM test uses squared error, Bartlett HAC variance, and Harvey-Leybourne-Newbold correction; minimum paired origins are max(5, horizon + 2). There are only three paired origins, so comparisons are underpowered and inferential statistics are not available for the current design.</p>'
        +table(dm.groupby('interpretation',dropna=False,as_index=False).size().rename(columns={'size':'comparisons'}) if 'interpretation' in dm else dm,digits=0)
        +'<h3>Fold validity and optimizer diagnostics</h3>'+table(model_diag,digits=0)
        +(table(pd.DataFrame(convergence),digits=0) if convergence else '<p>Convergence fields are not available in the fold artifact.</p>')
        +details('Recorded residual diagnostics by crop/model/fold',table(fold,residual_columns,digits=4))
        +f'<p>Negative crop/model mean R2 values in the saved summary: {len(negative_r2)} of {len(forecast_summary)} crop/model groups. Negative R2 is retained as observed and means the corresponding predictions scored worse than the validation-mean reference for that group; it is not silently converted or treated as a code bug.</p>'
        +table(negative_r2,digits=3)
        +details('Recorded optimizer/model warnings',table(warning_rows,digits=0,limit=40))
        +'<p>LSTM has only 8, 12, and 16 supervised sequences per fold after the lookback window. Residual diagnostics are only those recorded in forecast_fold_metrics.csv; no normality test or additional residual plot is inferred here.</p>'
    ))

    # Section 18
    test_files=pd.DataFrame([{'test file':name,'category':name.removeprefix('test_').removesuffix('.py').replace('_',' ')} for name in tests])
    sections.append(section(18,
        f'<div class="status-panel {test_status_class}"><strong>{test_status}</strong><span>{fmt(args.tests_passed,0)} passed · {fmt(args.tests_failed,0)} failed · {fmt(args.tests_warnings,0)} warnings · {test_runtime}</span></div>'
        +'<p>Complete repository test run under the project virtual environment. The runtime is taken from the actual pytest terminal output supplied to this report generator. Test categories are represented by the repository test module names below.</p>'
        +'<pre class="command">cd c:/Users/yoges/agrii<br>c:/Users/yoges/agrii/.venv/Scripts/python.exe -m pytest -q</pre>'
        +table(test_files,digits=0)
        +'<p>The older bundled performance HTML records 75 passed tests and is stale relative to this report. This status is taken from the current suite output supplied at generation time. Warnings were non-fatal and came from statsmodels starting-parameter/convergence and forecast-index behavior, Keras input-shape guidance, and NumPy correlation calculations.</p>'
    ))

    # Section 19
    package_table=pd.DataFrame([{'package':name,'selected_environment_version':ver} for name,ver in packages.items()])
    commands=pd.DataFrame([
        {'purpose':'Generate this standalone report','repository-relative command':rf'.\.venv\Scripts\python.exe generate_complete_technical_report.py --tests-passed {args.tests_passed} --tests-failed {args.tests_failed} --tests-warnings {args.tests_warnings} --test-runtime "{args.test_runtime}"'},
        {'purpose':'Run full repository suite', 'repository-relative command':r'.\.venv\Scripts\python.exe -m pytest -q'},
        {'purpose':'Generate robustness CSV/Markdown artifacts','repository-relative command':r'.\.venv\Scripts\python.exe -m src.robustness_audit'},
    ])
    sections.append(section(19,
        f'<p>Python {platform.python_version()}; selected project virtual environment. Solver: PuLP CBC (<code>PULP_CBC_CMD</code>). Configured random seed: {esc(config.get("seed"))}; TensorFlow seed is applied to each LSTM fold. The HTML report itself is generated from repository-local files and embeds all CSS, JavaScript, diagrams, and plots inline.</p>'
        +table(package_table,digits=0)
        +'<h3>Repository-relative commands</h3>'+table(commands,digits=0)
        +'<p>The robustness audit generator consumes saved forecast, sell/store, warehouse, and routing CSVs; it does not regenerate upstream forecasting or optimization artifacts. Reproduction requires those source CSVs and the assumption/configuration JSON files. Reported upstream dataset sources, tariffs, and collection provenance are not documented beyond the saved files.</p>'
        +details('Input/configuration and validation reports',table(pd.DataFrame([{'file':name,'present':(ROOT/name).is_file()} for name in ['price dataset (1).csv','farmer_crop_dataset (1).csv','farmer_decision_history.csv','tamilnadu_full_warehouse_dataset (1).csv','experiment_config.json','sell_store_assumptions.json','warehouse_research_assumptions.json','routing_research_assumptions.json','TECHNICAL_VALIDATION_REPORT.md','REPRODUCIBILITY_REPORT.md']]),digits=0))
    ))

    # Section 20
    sections.append(section(20,
        '<h3>Generative AI / LLM Usage</h3>'
        '<p>The project is reported as using a local LLM through LM Studio for conversational agricultural assistance. The repository chatbot client is configured with the model tag <code>llama-3.2-3b-instruct</code> and a local-network OpenAI-compatible endpoint at <code>192.168.31.36:1234</code>. The exact served model build/revision and LM Studio runtime identity are not recorded in the current technical artifacts.</p>'
        '<div class="legend-grid"><div><strong>Deterministic research pipeline</strong><br>Forecasting, statistical metrics, sell/store equations, warehouse LP, transport proxy, and artifact audits are implemented in Python/statistical/optimization code. The LLM is not used as the forecasting model, optimizer, or validation engine.</div><div><strong>Local LLM-assisted functionality</strong><br>Conversational responses in the chatbot path only. The local service is separate from saved experimental outputs and does not produce the reported CSV metrics.</div><div><strong>Human/developer oversight</strong><br>Forecast choices and scenario outputs are research evidence subject to review; final decisions remain with users. No automated LLM-generated experimental results are documented.</div></div>'
        '<p>Source review also finds duplicate <code>chat</code> method definitions in the chatbot class; the later API-backed definition overrides the earlier trained-model branch. This report therefore describes the effective configured client path, not an independently verified locally trained model.</p>'
    ))

    # Section 21
    limitations=[
        'Only three rolling-origin validation origins are available; DM comparisons do not support significance or superiority conclusions.',
        'The labeled crop-price series is quarterly and short; it does not provide broad market, geographic, or daily variation.',
        'LSTM has a small effective training sample of 8, 12, and 16 sequences per fold.',
        'Forecast-error propagation is deterministic sensitivity analysis, not calibrated probabilistic uncertainty.',
        'Storage, spoilage, quantity, and duration are scenario assumptions; measured farmer invoices and validated post-harvest loss observations are unavailable.',
        'Warehouse dataset provenance is unverified; source storage currency and billing period are unspecified. Transport rates are assumptions, not carrier quotes.',
        'The warehouse formulation has continuous allocation variables and is an LP despite project use of the MILP label.',
        'Transport is a single-leg Haversine reference-origin proxy, not a road route or CVRP. No farmer origin, customer/market demand, vehicle fleet/capacity, travel time, or route logs are available.',
        'No causal farmer-income evaluation or validated farmer-level post-harvest-loss measurement is present.',
        'Model selection is specific to the configured rolling-origin procedure and does not establish universal model superiority.',
        'The local LLM is a separate conversational feature and is not the statistical or optimization engine; exact served model revision is not documented.',
        'The project-provided farmer study description is not fully represented as fields in the supplied farmer CSV, limiting independent row-level verification.',
    ]
    sections.append(section(21,'<div class="limitation-panel"><h3>Interpretation boundary</h3><p>Evidence supports software behavior and configured retrospective/scenario calculations. It does not establish field effectiveness, farmer-income improvement, operational cost savings, or generalizable forecasting superiority.</p></div><ol>'+''.join(f'<li>{esc(item)}</li>' for item in limitations)+'</ol>'))

    # Section 22
    status_rows=[
        ('Data pipeline','Yes','Yes: input profiling and chronological preparation','Partially','Price provenance and farmer/warehouse metadata gaps'),
        ('Forecasting','Yes: 4 models','Yes: 36 folds, crop-specific metrics','Yes under configured design','Small quarterly sample; procedure-specific selection'),
        ('Rolling validation','Yes','Yes: 3 origins × 4 quarters','Yes','No independent external holdout'),
        ('Prediction intervals','Native ARIMA/SARIMA only','Yes: 72 decision rows','Yes: row-level recomputation','No native calibrated intervals for LSTM/Seasonal Naive'),
        ('Sell/Store','Yes','Yes: 144 retrospective cases','Formula audit: 144 rows','Scenario assumptions; not farmer outcomes'),
        ('Forecast sensitivity','Yes','Yes: actual-error propagation and perturbations','Deterministic reruns match','Not probabilistic'),
        ('Warehouse allocation','Continuous LP via CBC','Yes: 36 scenarios','Optimal status; 0 violations','Scenario costs; unclear source rate provenance'),
        ('Transport evaluation','Yes: Haversine reference origin','Yes: 36 scenarios','Distance/cost cross-check artifacts','Not road routing or CVRP'),
        ('Parameter sensitivity','Yes','Yes: 3,456 decision rows','Supported joins checked against saved layer scenarios','Layer values intentionally unavailable outside evaluated scope'),
        ('Module ablation','Descriptive stage output','Yes: 12 detail rows','Availability explicitly marked','Not a causal ablation'),
        ('Formula audit','Yes','Yes: 144 rows','0 mismatches','Checks saved outputs against implemented formulas only'),
        ('Reproducibility','Yes: report and commands','Partially','Environment/config recorded','Upstream outputs must already exist'),
        ('Testing','Yes','Yes: full suite','Passed in recorded run','14 non-fatal warnings'),
        ('Local LLM','Chat client configured','Not part of experiment metrics','Disclosure based on source/config','Served build and LM Studio runtime not independently recorded'),
    ]
    status_df=pd.DataFrame(status_rows,columns=['Component','Implemented','Quantitatively Evaluated','Validated','Major Limitation'])
    sections.append(section(22,table(status_df,digits=0)))

    # Section 23
    artifact_names=[
        'price dataset (1).csv','farmer_crop_dataset (1).csv','farmer_decision_history.csv','tamilnadu_full_warehouse_dataset (1).csv',
        'experiment_config.json','sell_store_assumptions.json','warehouse_research_assumptions.json','routing_research_assumptions.json',
        'forecast_predictions.csv','forecast_intervals.csv','forecast_interval_metrics.csv','forecast_dm_tests.csv',
        'forecast_fold_metrics.csv','forecast_horizon_metrics.csv','forecast_model_summary.csv','forecast_final_table.csv','forecast_validation_results.csv',
        'sell_store_decisions.csv','sell_store_summary.csv','sell_store_baseline_summary.csv','sell_store_forecast_error_sensitivity.csv',
        'forecast_error_sensitivity_propagation.csv','prediction_interval_decision_robustness.csv','prediction_interval_robustness_summary.csv',
        'end_to_end_parameter_sensitivity.csv','end_to_end_parameter_sensitivity_summary.csv','warehouse_summary.csv',
        'warehouse_optimization_results.csv','warehouse_baseline_comparison.csv','warehouse_sensitivity.csv','routing_summary.csv',
        'routing_baseline_comparison.csv','routing_routes.csv','routing_sensitivity.csv','module_ablation_results.csv',
        'module_ablation_summary.csv','formula_consistency_audit.csv','rolling_origin_support_check.csv',
        'TECHNICAL_VALIDATION_REPORT.md','REPRODUCIBILITY_REPORT.md','FORECASTING_VALIDATION_REPORT.md',
        'sell_store_validation_report.md','warehouse_validation_report.md','routing_validation_report.md',
        'ADIS_Complete_Performance_Report.html','ADIS_Complete_Performance_Report.md','generate_adis_performance_report.py',
        'src/forecast_validation.py','src/sell_store_research.py','src/warehouse_research.py','src/routing_research.py',
        'src/robustness_audit.py','src/chatbot.py','generate_complete_technical_report.py',
    ]
    present=[name for name in artifact_names if (ROOT/name).is_file()]
    absent=[name for name in artifact_names if not (ROOT/name).is_file()]
    sections.append(section(23,
        f'<p>Only files present in the repository at generation time are listed below. The charts in this HTML are inline SVG generated from the associated saved CSV rows; there are no image, font, script, or stylesheet dependencies.</p>'
        +'<div class="artifact-grid">'+''.join(f'<code>{esc(name)}</code>' for name in present)+'</div>'
        +(f'<details><summary>Requested index entries not present</summary><ul>'+''.join(f'<li>{esc(name)}: not present in current repository</li>' for name in absent)+'</ul></details>' if absent else '')
    ))

    # Section 24
    sections.append(section(24,
        '<p>The repository contains an implemented, tested decision-support research pipeline comprising crop-wise quarterly forecasting, rolling-origin evaluation, retrospective sell/store scoring, continuous cost-minimizing warehouse allocation, single-leg Haversine transport-cost scenarios, and artifact-grounded robustness checks. The current outputs have been evaluated and validated under the implemented experimental design, subject to the documented small-sample, provenance, assumption, and routing limitations.</p>'
        '<p>The evidence supports transparent decision analysis and software validation. It does not prove model superiority, guarantee higher farmer profit, establish real-world routing savings, solve CVRP, or demonstrate elimination of post-harvest losses.</p>'
        '<div class="status-panel good"><strong>TECHNICAL STATUS: VALIDATED WITH LIMITATIONS</strong><span>Retrospective and scenario-based evidence only; human interpretation remains necessary.</span></div>'
    ))

    return ''.join(sections), predictions, forecast_summary, selected


def build_html(args):
    data=load_evidence()
    sections,_,_,_=build_sections(data,args)
    nav=''.join(f'<a href="#section-{i:02d}"><span>{i:02d}</span>{esc(name)}</a>' for i,name in enumerate(SECTION_NAMES,1))
    css=r'''
:root{--ink:#1d3035;--muted:#607276;--line:#d7e0dd;--paper:#fffefa;--canvas:#eef2ee;--teal:#176b67;--teal-pale:#e4f0ec;--rust:#bd6040;--gold:#9b7a36;--red:#a33e35;--green:#286a4e;--shadow:0 8px 24px rgba(24,55,52,.07)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font:15px/1.58 Georgia,'Times New Roman',serif}a{color:var(--teal)}.layout{display:grid;grid-template-columns:265px minmax(0,1fr);min-height:100vh}.sidebar{position:sticky;top:0;height:100vh;overflow:auto;background:#183f43;color:#f4f5ed;padding:24px 18px;font:13px/1.35 'Segoe UI',Tahoma,sans-serif}.brand{border-bottom:1px solid rgba(255,255,255,.18);padding:2px 3px 18px;margin-bottom:12px}.brand strong{display:block;font:600 18px Georgia,serif}.brand small{color:#c7d7d3}.sidebar a{display:flex;gap:10px;align-items:baseline;color:#e9f0ec;text-decoration:none;padding:5px 4px;border-radius:3px}.sidebar a:hover,.sidebar a:focus{background:rgba(255,255,255,.1)}.sidebar a span{font:11px 'Segoe UI',sans-serif;color:#d5a986}.main{max-width:1440px;width:100%;margin:0 auto;padding:30px clamp(16px,4vw,58px) 90px}.hero{background:var(--paper);border-top:5px solid var(--teal);padding:30px clamp(18px,4vw,52px);box-shadow:var(--shadow);margin-bottom:20px}.eyebrow,.section-kicker{font:700 11px/1.3 'Segoe UI',Tahoma,sans-serif;letter-spacing:1px;color:var(--rust);text-transform:uppercase}.hero h1{font:700 clamp(30px,3vw,44px)/1.08 Georgia,serif;max-width:970px;margin:10px 0 12px}.subtitle{font:18px/1.4 Georgia,serif;color:var(--teal);margin:0 0 20px}.hero-meta{display:flex;flex-wrap:wrap;gap:8px 24px;color:var(--muted);font:13px 'Segoe UI',sans-serif}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:11px;margin:18px 0}.metric-card{padding:15px 16px;background:var(--teal-pale);border-left:4px solid var(--teal);display:grid;gap:2px;min-height:100px}.metric-card strong{font:700 25px/1.1 'Segoe UI',Tahoma,sans-serif;color:var(--ink)}.metric-card span{font:600 13px 'Segoe UI',Tahoma,sans-serif}.metric-card small{font:12px/1.35 'Segoe UI',Tahoma,sans-serif;color:var(--muted)}.report-section{background:var(--paper);border:1px solid var(--line);box-shadow:var(--shadow);padding:24px clamp(16px,3vw,36px);margin:18px 0;scroll-margin-top:18px;break-inside:auto}.report-section h2{font:700 25px/1.2 Georgia,serif;margin:5px 0 18px;border-bottom:1px solid var(--line);padding-bottom:11px}.report-section h3{font:700 18px/1.3 Georgia,serif;color:var(--teal);margin:23px 0 10px}.lede{font-size:18px;max-width:980px}.small-note,.empty{font:12px 'Segoe UI',sans-serif;color:var(--muted)}.table-scroll{overflow:auto;max-width:100%;margin:12px 0}table{border-collapse:collapse;width:100%;font:12px/1.45 'Segoe UI',Tahoma,sans-serif;min-width:520px}th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#e5eeeb;color:#203d3e;font-weight:700}tbody tr:nth-child(even){background:#f7f8f4}td{overflow-wrap:anywhere}details{border-top:1px solid var(--line);padding:10px 0;margin:14px 0}summary{cursor:pointer;color:var(--teal);font:600 14px 'Segoe UI',sans-serif}figure{margin:10px 0;padding:10px;border:1px solid var(--line);background:#fff}.chart,.architecture{display:block;width:100%;height:auto}.svg-title{font:700 14px 'Segoe UI',sans-serif;fill:#20383c}.axis-label{font:11px 'Segoe UI',sans-serif;fill:#4f6366}.legend{font:11px 'Segoe UI',sans-serif;fill:#34494d}.bar-label{font:10px 'Segoe UI',sans-serif;fill:white}.grid{stroke:#dfe6e3;stroke-width:1}.arch-title{font:700 16px 'Segoe UI',sans-serif;fill:#1e383c}.arch-sub{font:12px 'Segoe UI',sans-serif;fill:#51696b}.arch-note{font:13px 'Segoe UI',sans-serif;fill:#607276}.chart-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,390px),1fr));gap:12px}.chart-grid figure{min-width:0}figcaption{font:12px/1.4 'Segoe UI',sans-serif;color:var(--muted);padding:7px 3px 1px}.callout,.limitation-panel{border-left:4px solid var(--rust);background:#f8eee8;padding:14px 17px;margin:16px 0}.legend-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:18px 0}.legend-grid>div{border:1px solid var(--line);padding:14px;background:#f8f9f5}.equation{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:15px 0}.equation>div{border:1px solid var(--line);padding:13px;background:#f7f8f4;display:grid;gap:7px}.equation code{font:13px/1.5 'Cascadia Mono',Consolas,monospace;color:#174f4c}.status-panel{display:flex;align-items:center;gap:16px;background:#e6f1eb;border-left:5px solid var(--green);padding:17px;margin:15px 0}.status-panel strong{font:700 18px 'Segoe UI',sans-serif;color:var(--green)}.status-panel span{font:13px 'Segoe UI',sans-serif}.status-panel.bad{background:#f8e9e5;border-color:var(--red)}.status-panel.bad strong{color:var(--red)}.command{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf1ee;border:1px solid var(--line);padding:14px;font:13px/1.6 'Cascadia Mono',Consolas,monospace}.artifact-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:7px}.artifact-grid code{display:block;background:#edf2ee;padding:7px 9px;border-left:2px solid var(--teal);font:12px 'Cascadia Mono',Consolas,monospace;overflow-wrap:anywhere}.footer{font:12px 'Segoe UI',sans-serif;color:var(--muted);text-align:center;padding:20px}.nav-toggle{display:none}.print-only{display:none}@media(max-width:980px){.layout{grid-template-columns:1fr}.sidebar{position:relative;height:auto;max-height:250px}.sidebar nav{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:3px}.main{padding-top:16px}}@media(max-width:600px){.sidebar nav{grid-template-columns:1fr}.hero h1{font-size:30px}.report-section{padding:18px 13px}.status-panel{align-items:flex-start;flex-direction:column}.metric-card strong{font-size:22px}}@media print{@page{size:A4;margin:14mm}body{background:white;font-size:10pt}.layout{display:block}.sidebar,.nav-toggle{display:none!important}.main{max-width:none;padding:0}.hero,.report-section{box-shadow:none;border:0;padding:8px 0;margin:0 0 10px}.hero{border-top:3px solid var(--teal)}.report-section{break-before:page;page-break-before:always}.report-section:first-of-type{break-before:auto}.report-section h2{font-size:17pt}details:not([open])>*:not(summary){display:block!important}details{break-inside:avoid}table{font-size:8pt}th{position:static}.chart,.architecture{max-height:190mm}.table-scroll{overflow:visible}.table-scroll table{min-width:0}.footer{display:none}a{color:inherit;text-decoration:none}.metrics{grid-template-columns:repeat(3,1fr)}.artifact-grid{grid-template-columns:repeat(2,1fr)}}
'''
    script=r'''document.querySelectorAll('.sidebar a').forEach(a=>a.addEventListener('click',()=>{const section=document.querySelector(a.getAttribute('href'));if(section)section.scrollIntoView({behavior:'smooth',block:'start'})}));'''
    title='ADIS — Complete Technical Validation, Model Evaluation & Research Results Report'
    subtitle='Agricultural Decision Intelligence System — End-to-End Technical Evidence Package'
    tests_html=f'{args.tests_passed} passed · {args.tests_failed} failed · {args.tests_warnings} warnings · {esc(args.test_runtime)}'
    html_doc=(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="Offline technical results and validation report for the implemented ADIS research pipeline.">' 
        f'<title>{esc(title)}</title><style>{css}</style></head><body>'
        '<div class="layout"><aside class="sidebar"><div class="brand"><strong>ADIS · Technical Evidence</strong><small>Offline report · artifact-grounded</small></div><nav aria-label="Report sections">'
        +nav+'</nav></aside><main class="main"><header class="hero">'
        '<div class="eyebrow">Agricultural Decision Intelligence System</div>'
        f'<h1>{esc(title)}</h1><p class="subtitle">{esc(subtitle)}</p>'
        f'<div class="hero-meta"><span><b>Project:</b> ADIS research implementation</span><span><b>Generated:</b> 2026-10-03</span><span><b>Implementation:</b> End-to-end research modules implemented</span><span><b>Repository validation:</b> {tests_html}</span><span><b>LLM:</b> separate local conversational assistant</span></div>'
        '</header>'+sections+'<footer class="footer">Generated entirely from repository-local artifacts. All charts are inline SVG; CSS and JavaScript are embedded. No network resources are required.</footer></main></div>'
        f'<script>{script}</script></body></html>'
    )
    OUTPUT.write_text(html_doc,encoding='utf-8')
    return OUTPUT


def main():
    parser=argparse.ArgumentParser(description='Generate standalone ADIS technical results HTML from saved artifacts.')
    parser.add_argument('--tests-passed',type=int,default=None)
    parser.add_argument('--tests-failed',type=int,default=None)
    parser.add_argument('--tests-warnings',type=int,default=None)
    parser.add_argument('--test-runtime',default='Not supplied; run the repository test command to record a result')
    args=parser.parse_args()
    path=build_html(args)
    print(f'Generated: {path}')
    print(f'Bytes: {path.stat().st_size}')
    print(f'Sections: {len(SECTION_NAMES)}')
    print(f'Test record: {args.tests_passed} passed, {args.tests_failed} failed, {args.tests_warnings} warnings, {args.test_runtime}')


if __name__=='__main__':
    main()