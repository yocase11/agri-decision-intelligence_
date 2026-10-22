from src.decision_support import decide_sell_or_store


def test_decide_sell_or_store():
    # current price 100/kg, forecast 120/kg, qty 1000 kg (1 ton), spoilage 15%, storage 2.0 per MT, transport 0
    result = decide_sell_or_store('Onion', 100, 120, 1000, 2.0, 0.15, 0.0)
    assert result['decision'] == 'store'
    assert result['profit_now'] == 100000


def test_decide_sell_or_store_sell():
    result = decide_sell_or_store('Onion', 100, 105, 1000, 2.0, 0.15, 2000.0)
    assert result['decision'] == 'sell'
