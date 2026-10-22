from decision_model import decide_sell_or_store

# This module provides decision support for crop sell/store decisions.
# It wraps the existing decision_model module to satisfy pipeline modular requirements.


def evaluate_store_vs_sell(current_price, forecast_price, quantity_kg, storage_cost, spoilage_rate, transport_cost):
    decision, profit_now, profit_store = decide_sell_or_store(current_price, forecast_price, quantity_kg, storage_cost, spoilage_rate, transport_cost)
    return {
        'decision': decision,
        'profit_now': profit_now,
        'profit_store': profit_store,
        'current_price': current_price,
        'forecast_price': forecast_price,
        'quantity_kg': quantity_kg,
        'storage_cost': storage_cost,
        'spoilage_rate': spoilage_rate,
        'transport_cost': transport_cost,
    }
