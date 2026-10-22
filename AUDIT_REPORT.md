# Agricultural Decision Intelligence System (ADIS) Audit Report

## Scope
This report documents the current implementation status of the project as inspected in the workspace. The review follows the requested scientific audit workflow and focuses on whether the implementation is reproducible, internally consistent, and valid for research-grade decision support.

## Executive summary
The project contains a working application and several ML/optimization modules, but the current implementation does not yet satisfy the scientific standards requested in the review brief. The dominant issues are:

- no leakage-free forecasting validation protocol;
- model selection is not implemented as a strict validation-driven process;
- ensemble weighting is hard-coded rather than justified by validation evidence;
- decision logic mixes inconsistent units and hidden assumptions;
- warehouse optimization is not minimizing the required logistics objective;
- routing logic is not formally compared across methods; and
- uncertainty intervals are treated as heuristics, not statistically valid prediction intervals.

The good news is that the repository is organized sensibly and the main execution flow is identifiable. The required next step is to convert the current demonstration pipeline into a validated experimentation pipeline with clear train/validation/test separation and explicit decision rules.

## Findings by file

| File | Function | Current behavior | Scientific problem | Severity | Recommended correction | Code modification required |
|---|---|---|---|---|---|---|
| src/complete_system.py | forecast_prices | Tries trained model, then falls back to ARIMA/SARIMA/LSTM evaluation on a train/test split created from the same series. | The code explicitly uses the final window as test data and selects the lowest RMSE model on the same evaluation window, but does not implement a proper walk-forward protocol or a clear validation set consistent across crops. | High | Replace with strict chronological split and rolling-origin validation. Use the same test horizon for every crop/model. | Yes |
| src/price_pipeline.py | train_arima, train_sarima, train_lstm, ensemble_forecast | Fits models to the full series or a single training window and then computes forecast metrics later. | No formal leakage control; no out-of-sample validation with unseen future periods; ensemble weights are fixed at 0.4, 0.3, 0.3 without evidence. | High | Use time-aware split + walk-forward validation; estimate weights from validation performance only if an ensemble is retained. | Yes |
| src/decision_support.py | decide_sell_or_store | Converts storage costs inconsistently and applies opportunistic risk discounts. | Hidden unit conversions and heuristic thresholds can change decisions without explicit economic justification. | High | Define explicit formulas in kg/MT/₹/kg/₹/MT, with a single authoritative function and a validated risk term. | Yes |
| src/decision_support.py | find_optimal_sell_time | Compares storing versus selling on a fixed forecast list but does not reconcile against a final system decision. | May generate a different recommendation than the sell/store module, creating contradictory outputs. | High | Use one unified decision framework across sell now vs store until period X. | Yes |
| src/storage_opt.py | allocate_storage | Maximizes assigned quantity instead of total logistics cost. | This does not meet the scientific objective defined in the review brief. It is a capacity allocator, not a cost-optimized warehouse allocation model. | High | Reformulate as a cost-minimization MILP with storage + transport + spoilage cost. | Yes |
| src/routing.py | optimize_warehouse / best_route | Uses direct OSRM or haversine route estimates, but no formal route optimization and no baseline comparison. | The implementation cannot justify improved routing performance without comparing against direct/nearest/simple heuristic baselines. | Medium | Implement a reproducible benchmark set and compare direct, heuristic, and proposed routing under the same instances. | Yes |
| custom_ui.py | dashboard data endpoints | Uses a web dashboard with live forecasting and decision logic but ties behavior to absolute local Windows paths. | Reproducibility is weak; the app is not portable across machines and environments. | Medium | Use repository-relative paths and explicit configuration. | Yes |
| src/complete_system.py | _compute_forecast_metrics | Computes multiple metrics but not the required walk-forward output format. | The project reports model quality metrics but not the audit-required fold-level validation outputs. | High | Output per-fold predictions and aggregate metrics using the same test periods across models. | Yes |
| src/complete_system.py | forecast_prices | Uses clipping to current_price*0.7..1.5 as a stabilizer. | This is a heuristic mask, not a valid uncertainty interval and not an evidence-based uncertainty calibration. | High | Replace with proper prediction intervals and empirical coverage checks. | Yes |
| src/advanced_decision_system.py | ensemble logic | Uses a fixed weighted blend of ARIMA, SARIMA, LSTM forecasts. | The weights are not validated and may not improve RMSE over the best single model. | High | Only retain an ensemble if validation data supports a measurable improvement. | Yes |

## Key scientific issues

### 1) Time-series leakage risk
The forecasting stack is built around time-series models, but the current pipeline does not enforce a strict chronological evaluation workflow. In particular, several modules fit models using a full or partially recent series before evaluating on a final window, which risks using future information in the training set.

### 2) No proper walk-forward validation
The project does not currently generate fold-level out-of-sample predictions with train/end dates and does not report aggregate metrics over repeated rolling-origin splits.

### 3) Inconsistent units and assumptions
The decision logic mixes crop quantity in kg, storage cost in ₹/MT and ₹/kg, and transport costs in implicitly different units, making the model hard to audit and easy to misinterpret.

### 4) Hard-coded ensemble weights
The project uses fixed weights for model combination without experimental evidence that these weights outperform the best individual model.

### 5) Optimization objective mismatch
Warehouse allocation is formulated as a quantity maximizer rather than a cost minimizer. This does not match the stated objective of minimizing total logistics cost plus spoilage cost.

### 6) Heuristic uncertainty handling
The current ±8% or ±10% range is not statistically defensible as a confidence interval. It should be labeled as a heuristic band unless a valid prediction interval is implemented and validated.

## Severity assessment

- High: forecasting leakage, invalid validation, unit inconsistency, contradictory sell/store logic, warehouse optimization mismatch, uncertainty misuse.
- Medium: routing comparison, reproducibility, portability, missing explicit experiment config.
- Low: UI polish and dashboard aesthetics are not scientifically problematic, but they should not replace rigorous evaluation outputs.

## Recommended correction path
1. Implement chronological train/validation/test splits for each crop.
2. Add rolling-origin walk-forward evaluation tables and metrics.
3. Replace hard-coded ensembles with validation-based model selection.
4. Consolidate decision logic into a single value function with explicit units.
5. Re-formulate warehouse allocation as a true logistics cost minimization problem.
6. Benchmark routing methods using the same inputs and same evaluation protocol.
7. Generate reproducible artifact files (CSV, JSON, plots) from the validated pipeline.
8. Only then prepare the revised manuscript.

## Conclusion
The project has strong engineering scaffolding but still needs a research-grade validation backbone before it is suitable for paper revision. The main issues are not cosmetic; they affect the scientific validity of the forecasting, decision logic, and optimization claims.
