def decide_sell_or_store(current_price, future_price, quantity, storage_cost, spoilage_loss, transport_cost):
    profit_now = current_price * quantity
    profit_store = (future_price * quantity) - storage_cost - spoilage_loss - transport_cost
    return "store" if profit_store > profit_now else "sell", profit_now, profit_store
