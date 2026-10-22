# ADIS Faculty Summary

**Problem:** integrate crop-price forecasting, retrospective sell/store decision simulation, warehouse allocation, and transport-cost scenario analysis for agricultural decision support. Farmers remain final decision makers.

**Models:** Seasonal Naive, ARIMA, SARIMA, LSTM; three rolling-origin folds and four-quarter horizon. RMSE-selected candidates: Rice SARIMA, Onion LSTM, Tomato SARIMA. Selections are procedure-specific; DM comparisons are underpowered and no superiority claim is supported.

**Forecasting:** see report Tables F1-F4; prices and errors are INR/quintal. Native intervals exist only for ARIMA/SARIMA. Effective LSTM sequence counts are 8-16 per fold.

**Sell/store:** selected-model retrospective cases: Rice 12, agreement 83.33%, mean regret INR 8.80; Onion 12, 75.00%, INR 258.90; Tomato 12, 66.67%, INR 55.61. One-quintal scenario, not farmer outcomes.

**Warehouse:** 36 independent scenarios, CBC Optimal 36/36, zero constraint violations, full scenario quantity allocated. Scenario storage-cost interpretation is assumed INR/MT/month; warehouse provenance is unverified.

**Routing:** 36 single-leg Haversine reference proxies, feasible 36/36. Not road routes or a CVRP. No farmer origins, customer demands, fleet, or route observations.

**Software:** complete pytest suite 75 passed, 14 warnings, 0 failures. Protected upstream outputs verified unchanged during routing reruns; independent distance, cost, allocation link, and sensitivity checks passed.

**Limitations:** small quarterly sample and fold count; unverified source provenance; configured cost/spoilage/transport assumptions; no causal farmer welfare, profit, route, or road-network evidence.

**Supported claim:** ADIS is an auditable research prototype for decision support and scenario evaluation. **Not supported:** guaranteed profit, causal benefits, actual road-route optimality, or universal forecast superiority.
