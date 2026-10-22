import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX


def forecast_price_arima(price_series, steps=4, order=(1,1,1), seasonal_order=(0,0,0,0)):
    """Forecast future prices using SARIMA."""
    model = SARIMAX(price_series, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    fit = model.fit(disp=False)
    forecast = fit.forecast(steps=steps)
    return forecast


def evaluate_forecast(actual, predicted):
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    return {"mae": mae, "rmse": rmse, "mape": mape}
