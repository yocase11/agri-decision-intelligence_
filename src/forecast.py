import pickle
import os
import requests
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(__file__))
from price_pipeline import prepare_crop_timeseries, load_price_data, clean_price_data


def fetch_agmarknet_price(crop, district='Chennai'):
    try:
        # Placeholder; replace with actual Agmarknet API endpoint and key when available
        url = 'https://api.agmarknet.gov.in/some-endpoint'
        params = {'commodity': crop, 'district': district}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # adapt according to API response
            price = float(data.get('price', 0))
            return price
    except Exception:
        pass
    return None


def load_model(model_dir, crop):
    """Load the best trained model for the crop."""
    model_path = os.path.join(model_dir, f"{crop.lower()}_best.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model for {crop} not found at {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def get_current_price(price_path, crop, district='Chennai'):
    """Get the latest price for the crop, with Agmarknet fallback."""
    live_price = fetch_agmarknet_price(crop, district)
    if live_price is not None and live_price > 0:
        return live_price

    df = load_price_data(price_path)
    crop_df = df[df['Crop'] == crop].sort_values('quarter_date')
    if crop_df.empty:
        raise ValueError(f"No data for crop {crop}")
    current_price = crop_df['Final_Price'].iloc[-1]
    if crop == 'Rice':
        current_price /= 144.0  # convert to ₹/kg
    return current_price


def forecast_next_price(model, price_path, crop, steps=1):
    """Forecast next price using the model."""
    df = load_price_data(price_path)
    crop_df = df[df['Crop'] == crop].sort_values('quarter_date')
    if crop_df.empty:
        raise ValueError(f"No data for crop {crop}")
    ts = crop_df.set_index('quarter_date')['Final_Price'].asfreq('QS').dropna()
    if crop == 'Rice':
        ts = ts / 144.0  # convert to ₹/kg

    if hasattr(model, 'predict'):  # ARIMA/SARIMA
        from price_pipeline import forecast_model
        forecast = forecast_model(model, steps=steps)
        values = [float(x) for x in forecast.values]
        return values[0] if steps == 1 else values
    else:  # LSTM
        lstm_model, scaler, n_input = model
        from price_pipeline import forecast_lstm
        forecast = forecast_lstm(lstm_model, scaler, ts, steps=steps, n_input=n_input)
        values = [float(x) for x in forecast.values]
        return values[0] if steps == 1 else values