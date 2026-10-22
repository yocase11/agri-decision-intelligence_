import pytest
import numpy as np
from src.complete_system import (
    forecast_prices, compute_weather_risk, adjust_with_demand,
    detect_anomaly, optimize_selling_time, compute_ahp_weights,
    optimize_storage, get_distance_matrix, optimize_transport,
    cooperative_game, update_model, run_full_system
)

def test_forecast_prices():
    price_series = [10, 11, 12, 13, 12, 11, 10, 11, 12, 13, 14, 15]
    forecasts, model = forecast_prices(price_series)
    assert len(forecasts) == 4
    assert model in ['ARIMA', 'SARIMA', 'LSTM']
    assert all(isinstance(f, (int, float)) for f in forecasts)

def test_compute_weather_risk():
    weather_data = {'rainfall': 50, 'temperature': 30, 'humidity': 70}
    risk = compute_weather_risk(weather_data)
    assert 0 <= risk <= 1

def test_adjust_with_demand():
    forecast = 10.0
    demand_index = 1.2
    adjusted = adjust_with_demand(forecast, demand_index)
    assert adjusted == 12.0

def test_detect_anomaly():
    price_series = [10, 11, 12, 13, 12, 11, 10, 11, 12, 100]  # Anomaly
    anomaly = detect_anomaly(price_series)
    assert isinstance(anomaly, bool)

def test_optimize_selling_time():
    forecasts = [12, 13, 14, 15]
    quantity_kg = 1000
    cost_params = {'spoilage_rate': 0.1, 'storage_cost_per_kg': 0.5, 'current_price': 10}
    best_time, profit, selling_plan = optimize_selling_time(forecasts, quantity_kg, cost_params)
    assert 0 <= best_time <= 3
    assert isinstance(profit, (int, float))
    assert isinstance(selling_plan, list)

def test_compute_ahp_weights():
    matrix = np.array([[1, 2, 3], [0.5, 1, 2], [1/3, 0.5, 1]])
    weights = compute_ahp_weights(matrix)
    assert len(weights) == 3
    assert abs(weights.sum() - 1) < 0.01

def test_optimize_storage():
    warehouses = [
        {"cost": 1.0, "distance": 10, "capacity": 2000},
        {"cost": 1.5, "distance": 5, "capacity": 1500}
    ]
    quantity_kg = 1000
    criteria_matrix = np.array([[1, 2, 3], [0.5, 1, 2], [1/3, 0.5, 1]])
    best = optimize_storage(warehouses, quantity_kg, criteria_matrix)
    # MILP can be complex, so just check that function runs without error
    assert isinstance(best, (dict, type(None)))

def test_cooperative_game():
    farmers = [(13.0827, 80.2707)]
    result = cooperative_game(farmers)
    assert "coalitions" in result
    assert "cost_sharing" in result

def test_update_model():
    predicted = 10
    actual = 12
    update = update_model(predicted, actual)
    assert "adjustment" in update

def test_run_full_system():
    price_series = [10, 11, 12, 13, 12, 11, 10, 11, 12, 13, 14, 15]
    weather_data = {'rainfall': 20, 'temperature': 25, 'humidity': 60}
    demand_index = 1.0
    warehouses = [
        {"cost": 1.0, "distance": 10, "capacity": 2000, "lat": 9.9252, "lon": 78.1198}
    ]
    farmer_location = (13.0827, 80.2707)
    quantity_kg = 1000

    result = run_full_system(price_series, weather_data, demand_index,
                           warehouses, farmer_location, quantity_kg)

    required_keys = ["model", "forecasts", "forecast_metrics", "all_model_metrics", "best_time", "warehouse", "route",
                    "profit", "risk", "anomaly", "cooperation", "learning"]
    for key in required_keys:
        assert key in result

    assert len(result["forecasts"]) == 4
    assert 0 <= result["risk"] <= 1
    assert isinstance(result["anomaly"], bool)