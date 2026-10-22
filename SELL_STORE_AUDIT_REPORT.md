# Sell-vs-Store Pipeline Audit

## Scope
This audit covers the existing sell/store decision implementation and its direct callers. No decision logic has been changed before this report was created. Warehouse optimization, routing, and dashboard UI are out of scope for this phase.

## Main Decision Entry Points
- `src/decision_support.py::decide_sell_or_store` is called by `run_decision_support` and `run_single_farmer_decision`.
- `src/decision_model.py::decide_sell_or_store` is a second implementation used through `src/decision.py`; its argument named `spoilage_loss` is subtracted as a currency amount even though the wrapper passes a spoilage rate.
- `src/run_full_pipeline.py` builds legacy forecasts and passes them to `run_decision_support`.
- `src/api.py` and `src/app.py` call `run_single_farmer_decision`.
- `src/complete_system.py::optimize_selling_time` implements another sell-time policy with its own cost and spoilage assumptions.
- Existing tests assert behavior of the legacy heuristic, not unit consistency or retrospective forecast-error performance.

## Forecast Input and Selection
The legacy paths do not use `experiment_config.json` or `forecast_predictions.csv` model selection. `run_single_farmer_decision` loads `<crop>_best.pkl`; the full pipeline forecasts with legacy/full-series model routes. It reads `Final_Price`, whereas the validated Phase 2 research source is `Price_INR_per_Quintal`.

The single-farmer path also:
- clips forecasts to 0.7x–1.5x current price;
- multiplies Onion forecasts by 1.08 and Tomato forecasts by 1.05;
- uses heuristic sell/store margins including 2%, 5%, 10%, and an additional 5% post-warehouse threshold;
- does not use the validated native ARIMA/SARIMA prediction intervals.

The legacy ensemble code in `src/price_pipeline.py` uses fixed weights and ±8% bounds. Those outputs are not suitable for final research results and will not be used by the new retrospective evaluator.

## Existing Economic Assumptions
`src/decision_support.py` contains crop-specific spoilage assumptions (Tomato 15%, Onion 8%, Rice 1%) and storage constants (0.6, 0.55, 0.3) described as per kg, but with no documented time basis or data provenance. The function hard-codes one month. It also divides rates greater than 1 by 1000 to infer per-tonne units. `find_optimal_sell_time` separately hard-codes 1.5 per kg per month and advances storage duration by three months per quarter.

`src/complete_system.py` separately defaults to 10% spoilage and 0.5 storage cost per kg. These are configurable code assumptions, not measured farmer-level rates.

Warehouse data has `Storage_Cost_per_MT` and `Spoilage_Rate`; the source schema does not clearly specify the cost period, and route costs are handled by other modules. Those fields are not silently converted into the research evaluator's economics.

## Quantity and Price Units
The validated Phase 2 prices are INR per quintal. Legacy APIs and UI accept `quantity_kg`; farmer yield data is tonnes per acre but contains no farm acreage. `get_crop_quantity` sums yields per acre and multiplies by 1000 as if the sum were total tonnes, which is not justified without acreage. Some paths divide by 1000 to derive metric tonnes, while others multiply prices by kg quantities directly. These paths therefore mix incompatible units.

There is no validated farmer-specific quantity available in the historical price/forecast evaluation artifact. Any retrospective economic output must therefore use a clearly labeled scenario quantity in quintals and must not be presented as observed farmer outcomes.

## Leakage and Evaluation Gap
The existing decision path has no rolling-origin sell/store evaluation. Forecasts are made by legacy APIs and the decision code does not record a decision timestamp, horizon-aligned actual future price, decision agreement, or economic regret. Forecast errors from Phase 2 are available in `forecast_predictions.csv`; they provide a leakage-safe retrospective basis. A decision evaluator can use each row's training end/current price and prediction, then use the future actual only afterward to score the decision.

## Falsifiable Local Hypothesis
The legacy decisions are not valid research estimates because they use undocumented threshold/forecast adjustments and multiply INR-per-quintal price by quantities expressed in kg. A unit-explicit economic calculation using Phase 2 out-of-sample forecasts, a scenario quantity in quintals, and named storage/spoilage assumptions should produce auditable components and should agree with the direct sell/store net-value inequality without arbitrary margins.

## Planned Research Boundary
The new research evaluator will consume Phase 2 rolling-origin prediction rows and the selected-model configuration; it will not train models or call `get_or_train_models`, full-data ensemble logic, warehouse optimization, or routing. Existing hard-coded cost/spoilage values will be retained only as documented configurable assumptions for scenario analysis, not described as observed data. Forecast intervals remain unavailable for LSTM and Seasonal Naive, and no interval will be fabricated.
