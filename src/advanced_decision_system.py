import math
import requests
import numpy as np
import pandas as pd
from pulp import LpProblem, lpSum, LpVariable, LpBinary, LpMinimize
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator

from src.price_pipeline import prepare_crop_timeseries, train_arima, train_sarima, train_lstm, forecast_model, forecast_lstm


def forecast_prices(price_series, forecast_horizon=4):
    if not isinstance(price_series, pd.Series):
        price_series = pd.Series(price_series)

    if len(price_series) < 8:
        raise ValueError("price_series must contain at least 8 data points")

    # train/test split for model evaluation
    train = price_series[:-forecast_horizon]
    test = price_series[-forecast_horizon:]

    # ARIMA
    arima = train_arima(train)
    arima_pred = forecast_model(arima, steps=forecast_horizon)
    arima_rmse = math.sqrt(mean_squared_error(test, arima_pred))

    # SARIMA
    sarima = train_sarima(train)
    sarima_pred = forecast_model(sarima, steps=forecast_horizon)
    sarima_rmse = math.sqrt(mean_squared_error(test, sarima_pred))

    # LSTM
    lstm_model, lstm_scaler, n_input = train_lstm(train)
    lstm_pred = forecast_lstm(lstm_model, lstm_scaler, train, steps=forecast_horizon, n_input=n_input)
    lstm_rmse = math.sqrt(mean_squared_error(test, lstm_pred))

    rmses = {
        'arima': float(arima_rmse),
        'sarima': float(sarima_rmse),
        'lstm': float(lstm_rmse)
    }

    forecasts = {
        'arima': np.array(arima_pred).flatten(),
        'sarima': np.array(sarima_pred).flatten(),
        'lstm': np.array(lstm_pred).flatten()
    }

    # ensemble: weighted blending
    weights = np.array([0.4, 0.3, 0.3])
    combined = weights[0]*forecasts['arima'] + weights[1]*forecasts['sarima'] + weights[2]*forecasts['lstm']

    # clipping realistic limits
    current_price = float(train.iloc[-1])
    combined = np.clip(combined, current_price*0.7, current_price*1.5)

    best_model = min(rmses, key=rmses.get)

    return (
        pd.Series(combined, index=pd.RangeIndex(start=1, stop=forecast_horizon+1, step=1)),
        best_model,
        rmses
    )


def optimize_selling_time(forecasts, quantity_kg, cost_params=None):
    if cost_params is None:
        cost_params = {'holding_cost_per_kg_per_period': 0.1, 'disposal_cost_per_kg': 0.03}

    n = len(forecasts)
    holding_cost = cost_params.get('holding_cost_per_kg_per_period', 0.1)
    disposal_cutoff = cost_params.get('disposal_cost_per_kg', 0.03)

    # Dynamic programming for discrete horizon: sell now vs later
    # V[t] = max profit from time t..n
    V = [0] * (n + 1)
    decision = [''] * n

    for t in reversed(range(n)):
        sell_now = forecasts[t] * quantity_kg - (holding_cost * quantity_kg * t)
        wait = V[t+1] - (holding_cost * quantity_kg)
        if sell_now >= wait:
            V[t] = sell_now
            decision[t] = 'sell_now'
        else:
            V[t] = wait
            decision[t] = 'wait'

    best_time = np.argmax([forecasts[i] - holding_cost * i for i in range(n)]) + 1
    profit = float(V[0])

    return best_time, profit, decision


def optimize_storage(warehouses, quantity):
    if not warehouses:
        return None

    model = LpProblem("ColdStorageOptimization", LpMinimize)

    x = {i: LpVariable(f"x_{i}", cat=LpBinary) for i in range(len(warehouses))}

    model += lpSum([
        x[i] * (
            0.4 * warehouses[i].get('cost', 0) +
            0.3 * warehouses[i].get('distance', 0) -
            0.3 * warehouses[i].get('capacity', 0)
        )
        for i in x
    ])

    model += lpSum([x[i] for i in x]) == 1

    for i in x:
        model += warehouses[i].get('capacity', 0) * x[i] >= quantity

    model.solve()

    selected = None
    for i in x:
        if x[i].value() == 1:
            selected = warehouses[i]
            selected['selected_index'] = i
            break

    return selected


def get_distance_matrix(farmer_location, warehouses):
    coords = [f"{farmer_location[1]},{farmer_location[0]}"]
    for w in warehouses:
        coords.append(f"{w['lon']},{w['lat']}")

    coord_str = ";".join(coords)
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_str}?annotations=distance,duration"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    if data.get('code') != 'Ok':
        raise ValueError('OSRM distance table lookup failed')

    distances = data['distances']
    durations = data['durations']
    return distances, durations


def calculate_cost(distance_km, quantity_kg, storage_cost, modifiers=None):
    if modifiers is None:
        modifiers = {'transport_rate_per_km_per_ton': 5.0, 'fuel_per_km': 1.5, 'permit': 100, 'tolls': 50, 'driver_wage_per_km': 2.0}

    t_rate = modifiers['transport_rate_per_km_per_ton']
    q_ton = quantity_kg / 1000.0
    base_transport = distance_km * t_rate * q_ton

    fuel = distance_km * modifiers.get('fuel_per_km', 1.5)
    driver = distance_km * modifiers.get('driver_wage_per_km', 2.0)
    permit = modifiers.get('permit', 100)
    tolls = modifiers.get('tolls', 50)

    return base_transport + fuel + driver + permit + tolls + storage_cost


def optimize_warehouse_vrp(farmer_location, warehouses, quantity_kg, modifiers=None):
    if not warehouses:
        return None

    try:
        distances, durations = get_distance_matrix(farmer_location, warehouses)
    except Exception:
        distances = None
        durations = None

    best = None
    best_cost = float('inf')

    for i, w in enumerate(warehouses):
        if w.get('capacity', 0) < quantity_kg:
            continue

        if distances is not None:
            distance_km = distances[0][i+1] / 1000.0
            time_min = durations[0][i+1] / 60.0
        else:
            # fallback can use Haversine
            from math import radians, sin, cos, sqrt, atan2
            lat1, lon1 = farmer_location
            lat2, lon2 = w['lat'], w['lon']
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
            distance_km = R * 2 * atan2(sqrt(a), sqrt(1-a))
            time_min = distance_km * 2

        storage_cost = w.get('cost', 0) * quantity_kg
        total_cost = calculate_cost(distance_km, quantity_kg, storage_cost, modifiers)

        if total_cost < best_cost:
            best_cost = total_cost
            best = {
                'warehouse': w,
                'distance_km': float(round(distance_km, 2)),
                'travel_time_min': float(round(time_min,2)),
                'transport_cost': float(round(total_cost,2)),
                'used_osrm': distances is not None
            }

    return best


def vrp_milp(distance_matrix, warehouses, quantity_kg):
    # single-origin assignment as simplified VRP
    m = LpProblem('vrp_milp', LpMinimize)
    n = len(warehouses)

    x = {i: LpVariable(f'x_{i}', cat=LpBinary) for i in range(n)}

    cost = []
    for i in range(n):
        dist = distance_matrix[0][i+1]/1000.0
        cost.append((i, dist * 5.0 * (quantity_kg/1000.0)))

    m += lpSum([x[i] * c for i, c in cost])
    m += lpSum([x[i] for i in range(n)]) == 1

    for i in range(n):
        m += warehouses[i].get('capacity', 0) * x[i] >= quantity_kg

    m.solve()

    for i in range(n):
        if x[i].value() == 1:
            return warehouses[i]

    return None


def tabu_search(initial_routes, warehouses, quantity_kg, iterations=50):
    best = initial_routes
    best_cost = sum([w['transport_cost'] for w in best]) if best else float('inf')
    tabu = []

    for _ in range(iterations):
        new = list(best)
        if len(warehouses) > 1:
            i, j = np.random.choice(len(new), 2, replace=False) if len(new) > 1 else (0, 0)
            new[i], new[j] = new[j], new[i]

        new_cost = sum([w.get('transport_cost', 0) for w in new])
        if new_cost < best_cost and new not in tabu:
            best = new
            best_cost = new_cost
            tabu.append(new)
            if len(tabu) > 10:
                tabu.pop(0)

    return best


def genetic_algorithm(population, warehouses, quantity_kg, generations=30):
    def route_cost(route):
        return sum([w.get('transport_cost', 0) for w in route])

    pop = population
    for _ in range(generations):
        pop = sorted(pop, key=route_cost)[:max(2, len(pop)//2)]
        children = []
        for i in range(len(pop)-1):
            p1, p2 = pop[i], pop[i+1]
            cut = len(p1)//2
            child = p1[:cut] + [x for x in p2 if x not in p1[:cut]]
            children.append(child)
        pop.extend(children)

    return min(pop, key=route_cost)


def optimize_transport(farmer_location, warehouses, quantity, modifiers=None, use_vrp=True):
    best = optimize_warehouse_vrp(farmer_location, warehouses, quantity, modifiers)

    if not best:
        # fallback to first eligible warehouse
        for w in warehouses:
            if w.get('capacity', 0) >= quantity:
                best = {
                    'warehouse': w,
                    'distance_km': 0,
                    'travel_time_min': 0,
                    'transport_cost': 0,
                    'used_osrm': False
                }
                break

    return best


def run_full_system(price_series, warehouses, farmer_location, quantity):
    forecasts, model_used, rmses = forecast_prices(price_series)

    best_time, profit, selling_plan = optimize_selling_time(forecasts.values, quantity)

    best_warehouse = optimize_storage(warehouses, quantity)

    route = optimize_transport(farmer_location, warehouses, quantity)

    return {
        'model_used': model_used,
        'rmses': rmses,
        'forecasts': forecasts.tolist(),
        'best_selling_time': best_time,
        'selling_profit': float(round(profit, 2)),
        'selling_plan': selling_plan,
        'warehouse': best_warehouse,
        'route': route,
    }
