import os
import sys
import pandas as pd

# support direct execution from project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.price_pipeline import load_price_data, clean_price_data, run_crop_pipeline, save_model
from src.decision_support import run_decision_support, save_decision_report


def load_and_prepare_price_data(path):
    raw = pd.read_csv(path)
    raw['QuarterLabel'] = raw['Year'].astype(str) + raw['Quarter'].str.replace('.*Q', 'Q', regex=True)
    pivot = raw.pivot_table(index='QuarterLabel', columns='Crop', values='Final_Price', aggfunc='mean').reset_index()
    pivot['Quarter'] = pivot['QuarterLabel']
    pivot['quarter_date'] = pd.PeriodIndex(pivot['Quarter'], freq='Q').to_timestamp('D', how='start')
    return clean_price_data(pivot)


def run_full_pipeline(
    dataset_path,
    model_dir,
    crops=None,
    forecast_steps=4,
    test_steps=4,
    farmer_dataset=None,
    warehouse_dataset=None,
    sell_store_research=False,
    validated_predictions_path=None,
    validated_intervals_path=None,
    validation_config_path=None,
    sell_store_assumptions_path=None,
    sell_store_output_dir=None,
    warehouse_research=False,
    sell_store_results_path=None,
    warehouse_research_output_dir=None,
    warehouse_research_assumptions_path=None,
    routing_research=False,
    warehouse_results_path=None,
    routing_research_output_dir=None,
    routing_research_assumptions_path=None,
):
    research_modes = [sell_store_research, warehouse_research, routing_research]
    if sum(bool(mode) for mode in research_modes) > 1:
        raise ValueError('Choose only one isolated research mode per pipeline invocation')

    if routing_research:
        from src.routing_research import run_routing_research

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        result = run_routing_research(
            warehouse_results_path=warehouse_results_path or os.path.join(project_root, 'warehouse_optimization_results.csv'),
            warehouse_summary_path=os.path.join(project_root, 'warehouse_summary.csv'),
            warehouse_dataset_path=warehouse_dataset or os.path.join(project_root, 'tamilnadu_full_warehouse_dataset (1).csv'),
            warehouse_assumptions_path=os.path.join(project_root, 'warehouse_research_assumptions.json'),
            routing_assumptions_path=routing_research_assumptions_path or os.path.join(project_root, 'routing_research_assumptions.json'),
            forecast_horizon_metrics_path=os.path.join(project_root, 'forecast_horizon_metrics.csv'),
            forecast_fold_metrics_path=os.path.join(project_root, 'forecast_fold_metrics.csv'),
            forecast_predictions_path=os.path.join(project_root, 'forecast_predictions.csv'),
            sell_store_summary_path=os.path.join(project_root, 'sell_store_summary.csv'),
            output_dir=routing_research_output_dir or project_root,
        )
        return {'mode': 'routing_research', **result}

    if warehouse_research:
        from src.warehouse_research import run_warehouse_research

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        result = run_warehouse_research(
            sell_store_results=sell_store_results_path or os.path.join(project_root, 'sell_store_decisions.csv'),
            warehouse_dataset=warehouse_dataset or os.path.join(project_root, 'tamilnadu_full_warehouse_dataset (1).csv'),
            output_dir=warehouse_research_output_dir or project_root,
            config_path=validation_config_path or os.path.join(project_root, 'experiment_config.json'),
            assumptions_path=warehouse_research_assumptions_path or os.path.join(project_root, 'warehouse_research_assumptions.json'),
        )
        return {'mode': 'warehouse_research', **result}

    if sell_store_research:
        from src.sell_store_research import run_sell_store_research

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        result = run_sell_store_research(
            price_data_path=dataset_path,
            predictions_path=validated_predictions_path or os.path.join(project_root, 'forecast_predictions.csv'),
            intervals_path=validated_intervals_path or os.path.join(project_root, 'forecast_intervals.csv'),
            config_path=validation_config_path or os.path.join(project_root, 'experiment_config.json'),
            assumptions_path=sell_store_assumptions_path or os.path.join(project_root, 'sell_store_assumptions.json'),
            output_dir=sell_store_output_dir or project_root,
        )
        return {'mode': 'validated_sell_store_research', **result}

    if crops is None:
        crops = ['Onion', 'Tomato', 'Rice']

    os.makedirs(model_dir, exist_ok=True)

    df = load_and_prepare_price_data(dataset_path)

    # Convert all prices to ₹ per kg
    if 'Rice' in df.columns:
        df['Rice'] = df['Rice'] / 144.0

    summary = []

    for crop in crops:
        print(f"Running pipeline for {crop}...")
        result = run_crop_pipeline(df, crop, forecast_steps=forecast_steps, test_steps=test_steps)
        best_name = result['best_model']
        best_model = result['arima' if best_name == 'arima' else 'sarima']['model']
        model_path = os.path.join(model_dir, f"{crop.lower()}_best.pkl")
        save_model(best_model, model_path)

        summary.append({
            'crop': crop,
            'best_model': best_name,
            'forecast': result['ensemble'].tolist(),
            'forecast_validation': result.get('forecast_validation', {}),
            'arima_metrics': result['arima']['metrics'],
            'sarima_metrics': result['sarima']['metrics'],
            'lstm_metrics': result['lstm']['metrics'],
            'model_path': model_path,
        })

        print(f"{crop} finished: best={best_name} -> saved {model_path}\n")

    out_path = os.path.join(model_dir, 'forecast_summary.csv')
    out_df = pd.DataFrame([{
        'crop': row['crop'],
        'best_model': row['best_model'],
        'future_1': row['forecast'][0],
        'future_2': row['forecast'][1],
        'future_3': row['forecast'][2],
        'future_4': row['forecast'][3],
        'arima_mae': row['arima_metrics']['mae'],
        'arima_rmse': row['arima_metrics']['rmse'],
        'arima_mape': row['arima_metrics']['mape'],
        'sarima_mae': row['sarima_metrics']['mae'],
        'sarima_rmse': row['sarima_metrics']['rmse'],
        'sarima_mape': row['sarima_metrics']['mape'],
        'lstm_mae': row['lstm_metrics']['mae'],
        'lstm_rmse': row['lstm_metrics']['rmse'],
        'lstm_mape': row['lstm_metrics']['mape'],
    } for row in summary])
    out_df.to_csv(out_path, index=False)
    print(f"Forecast summary saved to {out_path}")

    decision_report = run_decision_support(summary, df, farmer_dataset=farmer_dataset, warehouse_dataset=warehouse_dataset)
    decision_path = os.path.join(model_dir, 'decision_report.json')
    save_decision_report(decision_report, decision_path)
    print(f"Decision report saved to {decision_path}")

    return {'forecast_summary': summary, 'decision_report_path': decision_path}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run full price forecasting pipeline for crops')
    parser.add_argument('--dataset', type=str, default=r'C:\Users\yoges\agrii\price dataset (1).csv', help='Path to price dataset')
    parser.add_argument('--model-dir', type=str, default=r'C:\Users\yoges\agrii\models', help='Directory to save models and summaries')
    parser.add_argument('--crops', type=str, default='Onion,Tomato,Rice', help='Comma-separated crop list')
    parser.add_argument('--forecast-steps', type=int, default=4, help='Forecast horizon (quarters)')
    parser.add_argument('--test-steps', type=int, default=4, help='Validation steps based on tail data')
    parser.add_argument('--farmer-dataset', type=str, default=r'C:\Users\yoges\agrii\farmer_crop_dataset (1).csv', help='Farmer dataset for quantity estimation')
    parser.add_argument('--warehouse-dataset', type=str, default=r'C:\Users\yoges\agrii\tamilnadu_full_warehouse_dataset (1).csv', help='Warehouse dataset for storage optimization')
    parser.add_argument('--sell-store-research', action='store_true', help='Evaluate sell/store decisions from existing validated rolling-origin artifacts; does not retrain forecasting models')
    parser.add_argument('--validated-predictions', type=str, default=None, help='Phase 2 forecast_predictions.csv path')
    parser.add_argument('--validated-intervals', type=str, default=None, help='Phase 2 forecast_intervals.csv path')
    parser.add_argument('--validation-config', type=str, default=None, help='Phase 2 experiment_config.json path')
    parser.add_argument('--sell-store-assumptions', type=str, default=None, help='Explicit scenario assumptions JSON')
    parser.add_argument('--sell-store-output-dir', type=str, default=None, help='Directory for sell/store research outputs')
    parser.add_argument('--warehouse-research', action='store_true', help='Run warehouse allocation research from existing sell/store outputs; does not retrain forecasts or alter sell/store results')
    parser.add_argument('--sell-store-results', type=str, default=None, help='Existing sell_store_decisions.csv path for warehouse research')
    parser.add_argument('--warehouse-output-dir', type=str, default=None, help='Directory for warehouse research outputs')
    parser.add_argument('--warehouse-assumptions', type=str, default=None, help='Warehouse research scenario assumptions JSON')
    parser.add_argument('--routing-research', action='store_true', help='Run scenario-based routing evaluation from saved warehouse allocations; does not rerun upstream phases')
    parser.add_argument('--warehouse-results', type=str, default=None, help='Saved warehouse_optimization_results.csv path')
    parser.add_argument('--routing-output-dir', type=str, default=None, help='Directory for routing research outputs')
    parser.add_argument('--routing-assumptions', type=str, default=None, help='Routing scenario assumptions JSON')
    args = parser.parse_args()

    crop_list = [c.strip() for c in args.crops.split(',') if c.strip()]
    results = run_full_pipeline(
        args.dataset,
        args.model_dir,
        crops=crop_list,
        forecast_steps=args.forecast_steps,
        test_steps=args.test_steps,
        farmer_dataset=args.farmer_dataset,
        warehouse_dataset=args.warehouse_dataset,
        sell_store_research=args.sell_store_research,
        validated_predictions_path=args.validated_predictions,
        validated_intervals_path=args.validated_intervals,
        validation_config_path=args.validation_config,
        sell_store_assumptions_path=args.sell_store_assumptions,
        sell_store_output_dir=args.sell_store_output_dir,
        warehouse_research=args.warehouse_research,
        sell_store_results_path=args.sell_store_results,
        warehouse_research_output_dir=args.warehouse_output_dir,
        warehouse_research_assumptions_path=args.warehouse_assumptions,
        routing_research=args.routing_research,
        warehouse_results_path=args.warehouse_results,
        routing_research_output_dir=args.routing_output_dir,
        routing_research_assumptions_path=args.routing_assumptions,
    )
    print('\nFull pipeline completed:')
    if results.get('mode') == 'routing_research':
        print('Mode:', results['mode'])
        print('Route rows:', len(results['routes']))
        print('Scenario summaries:', len(results['summary']))
        print('Baseline comparisons:', len(results['baselines']))
        print('Sensitivity rows:', len(results['sensitivity']))
        print('Route feasibility:', results['summary']['route_feasibility'].value_counts().to_dict())
    elif results.get('mode') == 'warehouse_research':
        print('Mode:', results['mode'])
        print('Allocation rows:', len(results['results']))
        print('Scenario summaries:', len(results['summary']))
        print('Baseline comparisons:', len(results['baselines']))
        print('Sensitivity rows:', len(results['sensitivity']))
        print('Solver statuses:', results['summary']['solver_status'].value_counts().to_dict())
        print('Constraint violations:', int(results['summary']['constraint_violations'].sum()))
    elif results.get('mode') == 'validated_sell_store_research':
        print('Mode:', results['mode'])
        print('Decision rows:', len(results['decisions']))
        print('Decision summary rows:', len(results['summary']))
        print('Baseline summary rows:', len(results['baselines']))
        print('Sensitivity rows:', len(results['sensitivity']))
        print('Selected models:', results['selected_models'])
    else:
        print(results)
