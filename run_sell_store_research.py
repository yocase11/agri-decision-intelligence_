from pathlib import Path

from src.sell_store_research import run_sell_store_research


ROOT = Path(__file__).resolve().parent


def main():
    result = run_sell_store_research(
        price_data_path=ROOT / 'price dataset (1).csv',
        predictions_path=ROOT / 'forecast_predictions.csv',
        intervals_path=ROOT / 'forecast_intervals.csv',
        config_path=ROOT / 'experiment_config.json',
        assumptions_path=ROOT / 'sell_store_assumptions.json',
        output_dir=ROOT,
    )
    print('Sell/store decisions:', len(result['decisions']))
    print('Decision summary rows:', len(result['summary']))
    print('Baseline summary rows:', len(result['baselines']))
    print('Sensitivity scenarios:', len(result['sensitivity']))
    print('Selected forecast models:', result['selected_models'])
    print('Report:', ROOT / 'sell_store_validation_report.md')


if __name__ == '__main__':
    main()
