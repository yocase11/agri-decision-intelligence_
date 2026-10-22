from pathlib import Path

from src.forecast_validation import run_forecasting_validation


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / 'price dataset (1).csv'


def main():
    result = run_forecasting_validation(
        data_path=DATA_PATH,
        random_seed=42,
        horizon=4,
        min_train_size=12,
        validation_windows=3,
        output_dir=ROOT,
    )
    print(f"Prediction rows: {result['prediction_rows']}")
    print(f"Selected models by crop: {result['selected_models']}")
    print(f"Failed folds: {len(result['failed_folds'])}")
    for _, row in result['failed_folds'].iterrows():
        print(f"FAILED {row['crop']} / {row['model']} / fold {row['fold']}: {row['failure_reason']}")
    print('Artifacts written to', ROOT)


if __name__ == '__main__':
    main()