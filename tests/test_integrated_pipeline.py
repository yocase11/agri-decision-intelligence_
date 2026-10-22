import os
import pytest
from src.decision_support import run_single_farmer_decision, decide_sell_or_store
from src.mcdm import load_warehouses, topsis_selection
from src.routing import best_route
from src.forecast import get_current_price, load_model, forecast_next_price

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PRICE_PATH = os.path.join(BASE_DIR, 'price dataset (1).csv')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
WAREHOUSE_PATH = os.path.join(BASE_DIR, 'tamilnadu_full_warehouse_dataset (1).csv')


def test_onion_pipeline_sell_path():
    result = run_single_farmer_decision('Onion', 2000, 13.0827, 80.2707, PRICE_PATH, MODEL_DIR, None, WAREHOUSE_PATH)

    assert 'decision' in result
    assert 'current_price' in result
    assert 'forecast_price' in result
    assert result['current_price'] > 0
    assert result['forecast_price'] > 0
    assert 0.5 * result['current_price'] <= result['forecast_price'] <= 2.0 * result['current_price']

    # behavior: if forecast is lower, pipeline should recommend selling
    if result['forecast_price'] < result['current_price']:
        assert result['decision'] == 'sell'


def test_tomato_store_with_mcdm_and_routing():
    current_price = 25.0
    forecast_price = 45.0
    decision = decide_sell_or_store('Tomato', current_price, forecast_price, 1500, 2.0, 0.25, 0)

    assert decision['decision'] == 'store'
    assert decision['profit_store'] > decision['profit_now']

    warehouses = load_warehouses(WAREHOUSE_PATH, 'Tomato')
    assert warehouses

    best_wh = topsis_selection(warehouses, 9.9252, 78.1198, 1.5)
    assert best_wh is not None
    assert best_wh['topsis_score'] >= 0
    assert best_wh['distance_km'] > 0

    route = best_route(9.9252, 78.1198, float(best_wh['Latitude']), float(best_wh['Longitude']), 1500)
    assert route['distance_km'] > 0
    assert route['estimated_cost'] > 0


def test_rice_stable_decision_sell():
    decision = decide_sell_or_store('Rice', 30.0, 30.0, 3000, 2.0, 0.005, 0)
    assert decision['profit_now'] == 30.0 * 3000
    assert decision['decision'] == 'sell'


def test_edge_quantity_and_invalid_crop():
    small = run_single_farmer_decision('Onion', 100, 13.0827, 80.2707, PRICE_PATH, MODEL_DIR, None, WAREHOUSE_PATH)
    large = run_single_farmer_decision('Onion', 5000, 13.0827, 80.2707, PRICE_PATH, MODEL_DIR, None, WAREHOUSE_PATH)

    assert small['quantity_kg'] == 100
    assert large['quantity_kg'] == 5000

    invalid = run_single_farmer_decision('InvalidCrop', 1000, 11.0, 77.0, PRICE_PATH, MODEL_DIR, None, WAREHOUSE_PATH)
    assert invalid['decision'] == 'invalid_crop'
    assert invalid['current_price'] is None


def test_missing_warehouse_path_fallback():
    missing = run_single_farmer_decision('Tomato', 1500, 9.9252, 78.1198, PRICE_PATH, MODEL_DIR, None, 'nonexistent_warehouse.csv')
    assert missing['recommended_warehouse'] is None
    assert missing['route'] is None
