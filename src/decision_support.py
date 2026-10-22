import os
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(__file__))
from storage_opt import allocate_storage
from transport_opt import simple_vrp_distance
from routing import compute_transport_cost, best_route, optimize_warehouse


def get_crop_quantity(farmer_path, crop):
    # Convert total cultivated quantity from tonnes to kilograms (kg) for consistent unit handling
    if not farmer_path or not os.path.exists(farmer_path):
        return 1000.0
    f = pd.read_csv(farmer_path)
    if 'Crop_Cultivated' not in f.columns or 'Crop_Yield_tonnes_per_acre' not in f.columns:
        return 1000.0
    q_tonnes = f.loc[f['Crop_Cultivated'].str.lower() == crop.lower(), 'Crop_Yield_tonnes_per_acre'].sum()
    q_tonnes = float(q_tonnes) if q_tonnes > 0 else 1.0
    return q_tonnes * 1000.0  # convert tonnes to kg


def get_warehouse_info(warehouse_path, crop):
    if not warehouse_path or not os.path.exists(warehouse_path):
        return []
    w = pd.read_csv(warehouse_path)
    crop_col = None
    if crop.lower() == 'onion':
        crop_col = 'Onion_Supported'
    elif crop.lower() == 'tomato':
        crop_col = 'Tomato_Supported'
    elif crop.lower() == 'rice':
        crop_col = 'Rice_Supported'

    if crop_col is None or crop_col not in w.columns:
        return []

    wf = w.loc[w[crop_col] == 1]
    return wf[['Warehouse_ID', 'Capacity_MT', 'Storage_Cost_per_MT', 'Spoilage_Rate', 'Latitude', 'Longitude']].to_dict('records')


def build_storage_plan(crop, quantity_mt, warehouse_info):
    warehouses = {row['Warehouse_ID']: float(row['Capacity_MT']) for row in warehouse_info}
    allocations = allocate_storage(warehouses, {crop: float(quantity_mt)}) if warehouses else {}
    total_allocated = sum(v for v in allocations.values() if v is not None)
    return {
        'warehouse_allocations': {f'{k[0]}_{k[1]}': v for k, v in allocations.items()},
        'total_allocated': total_allocated,
        'total_required': float(quantity_mt),
    }


def estimate_transport_cost(warehouse_info, quantity_mt, cost_per_km_per_tonne=0.05):
    if not warehouse_info:
        return {'distance_km': 0.0, 'transport_cost': 0.0}

    # Compute a simple route on the first N warehouses and back
    locations = [(float(row['Latitude']), float(row['Longitude'])) for row in warehouse_info[:5]]
    distance_km = simple_vrp_distance(locations)
    quantity_tonnes = float(quantity_mt)
    transport_cost = distance_km * quantity_tonnes * cost_per_km_per_tonne
    return {'distance_km': distance_km, 'transport_cost': transport_cost}


def decide_sell_or_store(crop, current_price, forecast_price, quantity_kg, storage_cost_per_kg, spoilage_rate, transport_cost, volatility_factor=0.0):
    # Handle storage cost units: convert per metric ton rates to per kg if needed
    if storage_cost_per_kg > 1:
        storage_cost_per_kg = storage_cost_per_kg / 1000.0

    # Dynamic storage cost based on seasonal location variation
    storage_duration_months = 1
    storage_cost = storage_cost_per_kg * quantity_kg * storage_duration_months

    # Risk factor should reduce expected return in volatile environments
    risk_discount = 1 - volatility_factor  # e.g. 0% or 5% risk

    profit_now = current_price * quantity_kg
    effective_quantity = quantity_kg * (1 - spoilage_rate)
    raw_profit_store = (forecast_price * effective_quantity) - storage_cost - transport_cost

    # Apply risk factor opportunistically but allow after-risk value to influence, no harsh bias
    profit_store = raw_profit_store * max(risk_discount, 0.90)

    price_change_pct = (forecast_price - current_price) / max(current_price, 0.01) * 100

    # Improved decision logic combining trend and profit
    decision = 'sell'
    if price_change_pct >= 10 and profit_store > profit_now:
        decision = 'store'
    elif price_change_pct >= 5 and profit_store > profit_now * 1.02:
        decision = 'store'

    # Keep selling when there is little margin
    if price_change_pct < 2 and profit_store <= profit_now * 1.02:
        decision = 'sell'

    return {
        'crop': crop,
        'profit_now': profit_now,
        'profit_store': profit_store,
        'decision': decision,
        'current_price': current_price,
        'forecast_price': forecast_price,
        'storage_cost': storage_cost,
        'spoilage_loss': forecast_price * quantity_kg * spoilage_rate,
        'transport_cost': transport_cost,
        'price_change_pct': price_change_pct,
        'risk_discount': risk_discount,
    }


SPOILAGE_RATES = {
    'tomato': 0.15,  # reduced from 0.25
    'onion': 0.08,
    'rice': 0.01
}

STORAGE_COST_PER_KG = {
    "Tomato": 0.6,   # fruit category
    "Onion": 0.55,   # similar to chillies
    "Rice": 0.3      # low storage cost (dry crop)
}


def get_spoilage_rate(crop, warehouse_rate=None):
    rate = SPOILAGE_RATES.get(crop.lower())
    if rate is not None:
        return rate
    return float(warehouse_rate) if warehouse_rate is not None else 0.05


def find_optimal_sell_time(forecast_prices, current_price, quantity_kg, storage_cost_per_tonne, spoilage_rate, transport_cost_per_unit, per_quarter_storage_factor=1.0):
    """Return optimal quarter to sell and associated profit.

    forecast_prices: list of future prices for t+1..t+n
    per_quarter_storage_factor: multiplier for increasing storage cost each quarter (default no growth)
    """
    storage_rate_per_kg_per_month = 1.5
    best_t = 0
    best_profit = current_price * quantity_kg
    timeline = []

    for i, price in enumerate(forecast_prices, start=1):
        storage_duration_months = i * 3  # quarters to months
        cumul_storage_cost = storage_rate_per_kg_per_month * quantity_kg * storage_duration_months * per_quarter_storage_factor
        # spoilage increases with time too
        cumul_spoilage_loss = price * quantity_kg * spoilage_rate * i
        profit_if_store_then_sell = (price * quantity_kg * (1 - spoilage_rate)) - cumul_storage_cost - transport_cost_per_unit
        timeline.append({'quarter': i, 'forecast_price': price, 'profit': profit_if_store_then_sell, 'spoilage_loss': cumul_spoilage_loss, 'storage_cost': cumul_storage_cost})
        if profit_if_store_then_sell > best_profit:
            best_profit = profit_if_store_then_sell
            best_t = i

    return {'best_quarter': best_t, 'max_profit': best_profit, 'timeline': timeline}


def run_decision_support(forecast_summary, price_df, farmer_dataset=None, warehouse_dataset=None):
    decisions = []

    for row in forecast_summary:
        crop = row['crop']

        if crop not in price_df.columns:
            continue

        current_price = float(price_df.loc[price_df['quarter_date'].idxmax(), crop])
        forecast_price = float(row['forecast'][0])
        quantity_kg = get_crop_quantity(farmer_dataset, crop)
        quantity_mt = quantity_kg / 1000.0
        warehouse_info = get_warehouse_info(warehouse_dataset, crop)

        storage_cost_per_tonne = float(warehouse_info[0]['Storage_Cost_per_MT']) if warehouse_info else 2.0
        warehouse_spoilage_rate = float(warehouse_info[0]['Spoilage_Rate']) if warehouse_info else None
        spoilage_rate = get_spoilage_rate(crop, warehouse_spoilage_rate)

        # Step 2: sell/store decision based on current and first forecast price
        decision = decide_sell_or_store(
            crop,
            current_price,
            forecast_price,
            quantity_kg,
            storage_cost_per_tonne,
            spoilage_rate,
            0.0,  # transport cost for pure decision, optimize transport in step 3
        )

        if decision['decision'] == 'store':
            # Step 3: storage optimization
            storage_plan = build_storage_plan(crop, quantity_mt, warehouse_info)
            transport_plan = estimate_transport_cost(warehouse_info, quantity_mt)
            decision['transport_cost'] = transport_plan['transport_cost']
            # storage_cost already set in decide_sell_or_store
        else:
            storage_plan = {'status': 'not_store', 'reason': 'sell_now'}
            transport_plan = {'distance_km': 0.0, 'transport_cost': 0.0}

        # Step 4: selling time optimization over all forecasted horizons
        sell_time = find_optimal_sell_time(
            row['forecast'],
            current_price,
            quantity_kg,
            storage_cost_per_tonne,
            spoilage_rate,
            transport_plan['transport_cost'],
            per_quarter_storage_factor=1.0,
        )

        decisions.append({
            'crop': crop,
            'quantity_kg': quantity_kg,
            'storage_plan': storage_plan,
            'transport_plan': transport_plan,
            'decision': decision,
            'selling_time_optimization': sell_time,
            'forecast_metrics': {
                'arima_metrics': row['arima_metrics'],
                'sarima_metrics': row['sarima_metrics'],
                'lstm_metrics': row['lstm_metrics'],
            },
            'forecast_values': row['forecast'],
        })

    final = {'decision_report': decisions, 'generated_from': 'pipeline', 'source_rows': len(decisions)}

    if farmer_dataset:
        final['farmer_dataset_path'] = farmer_dataset
    if warehouse_dataset:
        final['warehouse_dataset_path'] = warehouse_dataset

    return final


def run_single_farmer_decision(crop, quantity_kg, farmer_lat, farmer_lon, price_path, model_dir, farmer_path=None, warehouse_path=None, offline_mode=False, cost_per_km_per_tonne=5.0, fuel_rate=0.0, permit_cost=0.0, tolls=0.0, driver_wage_per_km=0.0):
    """Run decision for a single farmer."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from forecast import load_model, get_current_price, forecast_next_price
    from mcdm import load_warehouses, topsis_selection

    # Get prices
    try:
        current_price = get_current_price(price_path, crop)
    except Exception as e:
        return {
            'crop': crop,
            'quantity_kg': quantity_kg,
            'decision': 'invalid_crop',
            'error': str(e),
            'current_price': None,
            'forecast_price': None,
            'profit_now': 0.0,
            'profit_store': 0.0,
            'storage_cost': 0.0,
            'transport_cost': 0.0,
            'recommended_warehouse': None,
            'route': None,
        }

    try:
        model = load_model(model_dir, crop)
        forecast_price = forecast_next_price(model, price_path, crop, steps=1)
    except Exception as e:
        # fallback to current price when model fails
        forecast_price = current_price

    # Forecast stabilization
    forecast_price = max(forecast_price, current_price * 0.7)
    forecast_price = min(forecast_price, current_price * 1.5)

    # Optional seasonal adjustment
    if crop.lower() == "onion":
        forecast_price *= 1.08
    elif crop.lower() == "tomato":
        forecast_price *= 1.05

    # Get quantity (if farmer_path, but for simplicity, use provided)
    # quantity_kg = get_crop_quantity(farmer_path, crop) if farmer_path else quantity_kg

    # Spoilage
    spoilage_rate = get_spoilage_rate(crop)

    # Storage cost (1 month) from realistic standardized value
    storage_cost_per_kg = STORAGE_COST_PER_KG.get(crop.title(), 0.5)

    # Transport cost will be calculated after warehouse recommendation; start as placeholder
    transport_cost = 0.0

    # Advanced decision with both economics and risk
    decision_result = decide_sell_or_store(
        crop,
        current_price,
        forecast_price,
        quantity_kg,
        storage_cost_per_kg,
        spoilage_rate,
        transport_cost,
        volatility_factor=0.0,
    )

    # Assign initial values
    profit_now = decision_result['profit_now']
    profit_store = decision_result['profit_store']
    decision = decision_result['decision']
    storage_cost = decision_result['storage_cost']
    transport_cost = decision_result['transport_cost']

    result = {
        'crop': crop,
        'quantity_kg': quantity_kg,
        'current_price': current_price,
        'forecast_price': forecast_price,
        'profit_now': profit_now,
        'profit_store': profit_store,
        'decision': decision,
        'spoilage_loss': decision_result['spoilage_loss'],
        'storage_cost': storage_cost,
        'transport_cost': transport_cost,
        'price_change_pct': decision_result['price_change_pct'],
        'risk_discount': decision_result['risk_discount'],
    }

    # If initial decision is store, go to warehouse and routing to accurately compute costs
    if decision == 'store' and warehouse_path:
        try:
            warehouses = load_warehouses(warehouse_path, crop)
        except Exception:
            warehouses = []

        quantity_mt = quantity_kg / 1000.0
        best_option = optimize_warehouse(
            (farmer_lat, farmer_lon),
            warehouses,
            quantity_kg,
            cost_per_km_per_tonne=cost_per_km_per_tonne,
            fuel_rate=fuel_rate,
            permit_cost=permit_cost,
            tolls=tolls,
            driver_wage_per_km=driver_wage_per_km,
            offline_mode=offline_mode
        )

        if best_option:
            wh = best_option['warehouse']
            route_info = {
                'distance_km': best_option['distance_km'],
                'travel_time_min': best_option['travel_time_min'],
                'estimated_cost': best_option['transport_cost'],
                'route': [(farmer_lat, farmer_lon), (float(wh['Latitude']), float(wh['Longitude']))],
                'used_osrm': best_option['used_osrm'],
            }

            actual_storage_cost = best_option['storage_cost']
            actual_transport_cost = best_option['transport_cost']
            effective_quantity = quantity_kg * (1 - spoilage_rate)
            adjusted_profit_store = (forecast_price * effective_quantity) - actual_storage_cost - actual_transport_cost

            if adjusted_profit_store > profit_now * 1.05:
                decision = 'store'
            else:
                decision = 'sell'

            result.update({
                'decision': decision,
                'profit_store': adjusted_profit_store,
                'storage_cost': actual_storage_cost,
                'transport_cost': actual_transport_cost,
                'route': route_info,
                'distance_km': route_info.get('distance_km'),
                'travel_time_min': route_info.get('travel_time_min'),
                'recommended_warehouse': {
                    'name': wh.get('Location', 'Unknown') if 'Location' in wh else wh.get('Warehouse_ID', 'Unknown'),
                    'latitude': float(wh.get('Latitude', farmer_lat)),
                    'longitude': float(wh.get('Longitude', farmer_lon)),
                    'distance_km': route_info['distance_km'],
                    'storage_cost_per_mt': float(wh.get('Storage_Cost_per_MT', 0.0)),
                    'capacity_mt': float(wh.get('Capacity_MT', 0.0)),
                    'facility_score': float(wh.get('facility_score', 0.0)),
                    'topsis_score': float(wh.get('topsis_score', 0.0)),
                }
            })
        else:
            result['recommended_warehouse'] = None
            result['route'] = None
    else:
        result['recommended_warehouse'] = None
        result['route'] = None

    # debug logging
    print({
        'crop': crop,
        'current_price': current_price,
        'forecast_price': forecast_price,
        'price_change_pct': result.get('price_change_pct'),
        'profit_now': profit_now,
        'profit_store': result.get('profit_store'),
        'decision': result.get('decision')
    })

    return result


def save_decision_report(decision_report, path):
    """Save decision report to JSON file"""
    import json
    with open(path, 'w') as f:
        json.dump(decision_report, f, indent=2)

    # Debug logging
    print({
        "crop": crop,
        "current_price": current_price,
        "forecast_price": forecast_price,
        "price_change": price_change,
        "profit_now": profit_now,
        "profit_store": profit_store,
        "decision": decision
    })

    result = {
        'crop': crop,
        'quantity_kg': quantity_kg,
        'current_price': current_price,
        'forecast_price': forecast_price,
        'profit_now': profit_now,
        'profit_store': profit_store,
        'decision': decision,
        'spoilage_loss': forecast_price * quantity_kg * spoilage_rate,
        'storage_cost': storage_cost,
        'transport_cost': transport_cost,
    }

    if decision == 'store' and warehouse_path:
        try:
            warehouses = load_warehouses(warehouse_path, crop)
        except Exception:
            warehouses = []

        quantity_mt = quantity_kg / 1000.0
        best_wh = topsis_selection(warehouses, farmer_lat, farmer_lon, quantity_mt)
        if best_wh:
            route_info = best_route(farmer_lat, farmer_lon, float(best_wh['Latitude']), float(best_wh['Longitude']), quantity_kg)
            result['recommended_warehouse'] = {
                'name': best_wh.get('Location', 'Unknown'),
                'distance_km': route_info['distance_km'],
                'storage_cost_per_mt': best_wh['Storage_Cost_per_MT'],
                'capacity_mt': best_wh['Capacity_MT'],
                'facility_score': best_wh['facility_score'],
                'topsis_score': best_wh['topsis_score'],
            }
            # Recalculate profit with actual cost and transport cost
            actual_storage_cost = best_wh['Storage_Cost_per_MT'] * quantity_mt
            actual_transport_cost = route_info['estimated_cost']
            effective_quantity = quantity_kg * (1 - spoilage_rate)
            result['profit_store'] = (forecast_price * effective_quantity) - actual_storage_cost - actual_transport_cost
            result['storage_cost'] = actual_storage_cost
            result['transport_cost'] = actual_transport_cost
            result['route'] = route_info
        else:
            result['recommended_warehouse'] = None
            result['route'] = None
    else:
        result['recommended_warehouse'] = None
        result['route'] = None

    return result
