import pandas as pd
from src.price_pipeline import load_price_data, clean_price_data, prepare_crop_timeseries, run_crop_pipeline


def test_prepare_crop_timeseries_and_pipeline():
    data = {
        'Quarter': ['2009Q1', '2009Q2', '2009Q3', '2009Q4', '2010Q1', '2010Q2', '2010Q3', '2010Q4', '2011Q1', '2011Q2']
        , 'onion': [100, 102, 105, 110, 115, 120, 118, 122, 125, 130]
    }
    df = pd.DataFrame(data)
    df = load_price_data(path='tests/tmp_price_data.csv') if False else df
    df['quarter_date'] = pd.PeriodIndex(df['Quarter'], freq='Q').to_timestamp('D', how='start')
    df = clean_price_data(df)

    ts = prepare_crop_timeseries(df, 'onion')
    assert len(ts) == 10

    out = run_crop_pipeline(df, 'onion', forecast_steps=2, test_steps=2)
    assert out['crop'] == 'onion'
    assert 'future_forecast' in out
