# Reproducibility Report

## 1. Project structure

- Source code in `src/`
- Research artifacts and generated CSVs in repository root
- Models and reports in `models/`
- Tests in `tests/`

## 2. Input datasets/files

- `price dataset (1).csv` — supplied quarterly crop price data
- `farmer_crop_dataset (1).csv` — farmer-shaped dataset; provenance not documented in the current implementation
- `farmer_decision_history.csv` — history-like file; provenance not documented in the current implementation
- `tamilnadu_full_warehouse_dataset (1).csv` — warehouse-shaped dataset; source billing and route provenance not documented
- `forecast_predictions.csv` — validated rolling-origin outputs
- `sell_store_decisions.csv` — retrospective decision artifact
- `warehouse_summary.csv` — MILP summary
- `routing_summary.csv` — Haversine proxy summary
- `forecast_model_summary.csv` — valid-fold model metrics and selected-model source
- `warehouse_sensitivity.csv` and `routing_sensitivity.csv` — saved downstream scenario results used for supported sensitivity joins

## 3. Dataset provenance

- Price dataset provenance: Not documented in the current implementation.
- Farmer dataset provenance: Not documented in the current implementation.
- Warehouse dataset provenance: Not documented in the current implementation.
- Carrier tariffs and route billing periods: Not documented in the current implementation.

## 4. Preprocessing steps

- Duplicate crop-quarter source observations are aggregated by arithmetic mean; gaps are not interpolated in the forecasting validation implementation.
- Forecast validation uses chronological rolling-origin windows with a minimum training size and valid-only prediction filtering.
- Sell/store evaluation consumes the validated forecast artifact and the current price at each decision origin.
- Warehouse allocation consumes saved selected-model scenarios and compatibility rules from the warehouse dataset.
- Routing evaluation consumes saved allocations and computes straight-line Haversine distances from a synthetic warehouse centroid reference origin.

## 5. Forecasting models

- Seasonal Naive
- ARIMA
- SARIMA
- LSTM

## 6. Rolling-origin configuration

- Horizon: 4
- Minimum training size: 12
- Validation windows: 3
- Seasonal period: 4
- Random seed: 42
- Selected models: Rice = sarima, Onion = lstm, Tomato = sarima

## 7. Forecast horizons

- The implementation evaluates a four-quarter horizon in the configured workflow.

## 8. Model selection rule

- Selected models are chosen by lowest mean validation RMSE among valid rolling-origin folds, as configured in `experiment_config.json`.
- Selected models in the current configuration: Rice = sarima; Onion = lstm; Tomato = sarima.

## 9. Prediction interval methodology

- Native 95% prediction intervals are used for ARIMA and SARIMA via `statsmodels` `get_forecast().conf_int()`.
- LSTM and Seasonal Naive do not have calibrated native probabilistic intervals in the current implementation.
- No artificial intervals are fabricated for unsupported models.

## 10. Sell/store equations

- Sell-now value = quantity × current price
- Effective stored quantity = quantity × (1 − spoilage)
- Storage cost = quantity × 100 × storage rate × duration
- Store value = effective quantity × forecast price − storage cost − transport cost
- Decision = store if store value > sell-now value; otherwise sell

## 11. Storage/spoilage assumptions

- Scenario quantity: 1.0
- Storage rates: {'Rice': 0.3, 'Onion': 0.55, 'Tomato': 0.6}
- Spoilage rates: {'Rice': 0.01, 'Onion': 0.08, 'Tomato': 0.15}
- Storage duration months per quarter: 3.0
- Forecast-error sensitivity fractions: [-0.2, -0.15, -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2]
- Sell/store sensitivity assumptions: {'storage_cost_multipliers': [0.5, 1.0, 1.5, 2.0], 'spoilage_rates': [0.0, 0.02, 0.05, 0.1], 'future_price_multipliers': [0.9, 1.0, 1.1], 'storage_duration_months': [3, 6, 9, 12]}

## 12. Warehouse MILP formulation actually implemented

- The implementation solves a continuous allocation problem to minimize storage and transport cost with an unallocated quantity penalty.
- Variables are nonnegative quantities assigned to compatible warehouses.
- Constraints enforce quantity balance and warehouse capacities.
- Solver: PuLP CBC via `PULP_CBC_CMD`.
- Warehouse cost/quantity multipliers: {'storage_cost_multipliers': [0.5, 1.0, 1.5, 2.0], 'transport_cost_multipliers': [0.5, 1.0, 1.5, 2.0], 'available_quantity_multipliers': [0.5, 1.0, 1.5]}

## 13. Solver actually used

- `pulp` with CBC solver (`PULP_CBC_CMD`)

## 14. Routing formulation actually implemented

- The routing layer computes Haversine straight-line distances from the synthetic warehouse centroid reference origin to the assigned warehouse destinations.
- It does not implement a real VRP/CVRP or capacity-constrained customer routing problem.
- This is explicitly a scenario/reference-origin proxy, not a real-world route optimizer.
- Routing cost/quantity multipliers: {'transport_cost_multipliers': [0.5, 1.0, 1.5, 2.0], 'available_quantity_multipliers': [0.5, 1.0, 1.5]}

## 15. Sensitivity experiments

- Forecast error perturbations: -20%, -15%, -10%, -5%, 0%, +5%, +10%, +15%, +20%
- Storage cost multipliers: [0.5, 1.0, 1.5, 2.0]
- Spoilage rates: [0.0, 0.02, 0.05, 0.1]
- Transport cost multipliers: [0.5, 1.0, 1.5, 2.0]
- Quantity multipliers: [0.5, 1.0, 1.5]
- Downstream cost sensitivity is reported only where a matching selected-model scenario exists in the saved warehouse/routing sensitivity artifact; unsupported layer/parameter combinations remain unavailable.
- These are scenario sensitivity analyses, not empirical parameter distributions.

## 16. Ablation experiments

- The stage-wise table reports supported output metrics for A. Forecasting only, B. Forecasting + Sell/Store, C. Forecasting + Sell/Store + Warehouse, and D. Full implemented pipeline.
- Metrics are averaged across all saved selected-model scenarios for each crop/model (the available origin-by-horizon rows).
- `available_metrics` and `unavailable_metrics` identify stage-specific metrics; the table is descriptive, not a causal ablation or cross-stage scalar comparison.

## 17. Software/library versions

- Python: 3.13.6
- numpy: 2.4.4
- pandas: 3.0.2
- scipy: 1.17.1
- statsmodels: 0.14.6
- scikit-learn: 1.8.0
- tensorflow: 2.21.0
- keras: 3.14.0
- pulp: 3.3.0
- pytest: 9.0.2
- `requirements.txt` lists package names without version pins; the versions above are from the selected project virtual environment at report-generation time.

## 18. Exact commands required to reproduce the experiments

```powershell
Set-Location C:\Users\yoges\agrii
& C:\Users\yoges\agrii\.venv\Scripts\python.exe -m src.robustness_audit
& C:\Users\yoges\agrii\.venv\Scripts\python.exe -m pytest -q
```

The robustness command regenerates the audit CSVs and reports from the upstream CSV artifacts listed above; it does not refit forecast models or rerun the warehouse MILP/routing phases. The repository does not define a single command that rebuilds all upstream research artifacts.

## 19. Generated artifacts

- `forecast_predictions.csv`
- `sell_store_decisions.csv`
- `warehouse_summary.csv`
- `routing_summary.csv`
- `TECHNICAL_VALIDATION_REPORT.md`
- `REPRODUCIBILITY_REPORT.md`
- `prediction_interval_decision_robustness.csv`
- `prediction_interval_robustness_summary.csv`
- `end_to_end_parameter_sensitivity.csv`
- `end_to_end_parameter_sensitivity_summary.csv`
- `module_ablation_results.csv`
- `module_ablation_summary.csv`

## 20. Test commands and results

- Test files: `tests/test_complete_system.py`, `tests/test_decision_model.py`, `tests/test_forecasting.py`, `tests/test_integrated_pipeline.py`, `tests/test_pipeline.py`, `tests/test_routing_research.py`, `tests/test_sell_store_research.py`, `tests/test_technical_validation.py`, and `tests/test_warehouse_research.py`.
- Full-suite command: `& C:\Users\yoges\agrii\.venv\Scripts\python.exe -m pytest -q`.
- The full suite is run after artifact generation as the final validation step; its observed result is reported with the artifact handoff.

## 21. Known warnings

- Existing statsmodels convergence warnings and keras input-shape warnings are present but do not invalidate the current validated artifact set.

## 22. Explicit limitations

- The repository does not contain validated farmer-level causal outcomes.
- The warehouse and routing outputs are scenario-driven and not real operational procurement or carrier data.
- No probabilistic interval is created for models that do not have valid native intervals.
- The rolling-origin design is limited to the available quarterly series length.
- No real-world cost savings claim is supported by the Haversine proxy.
