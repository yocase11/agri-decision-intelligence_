# Performance Evaluation of the Agricultural Decision Intelligence System (ADIS)

**Report scope.** This is an artifact-grounded audit of the current research implementation. It reports model-generated forecasts, retrospective simulations, and configured optimization scenarios; it does not measure real farmer welfare, causal benefit, or realized SaaS outcomes.

## 1. Executive Summary
ADIS is an intended SaaS decision-support/decision-intelligence platform integrating agricultural price forecasting, sell/store evaluation, warehouse allocation, and transport-cost analysis. The validated implementation produces crop-specific rolling-origin forecasts, retrospective economic decisions on standardized 1-quintal scenarios, warehouse MILP assignments, and single-leg Haversine proxy routes. These results support decision support and software evaluation only; farmers remain the final decision makers.

- Rice: sarima; mean validation RMSE 104.56 INR/quintal; valid folds 3, failed folds 0
- Onion: lstm; mean validation RMSE 889.59 INR/quintal; valid folds 3, failed folds 0
- Tomato: sarima; mean validation RMSE 513.18 INR/quintal; valid folds 3, failed folds 0

Warehouse base scenarios: 36, CBC statuses {'Optimal': 36}, total violations 0. Routing proxy legs: 36, feasible 36/36. Full pytest last verified in this completion: 75 passed (14 existing model warnings).

## 2. Research Problem
Evaluate whether the integrated research pipeline can generate auditable crop forecasts, explicit scenario-based sell/store decisions, cost-minimizing warehouse allocations, and transparent transport-cost estimates from supplied artifacts. The present repository does not support causal farmer outcome evaluation or empirically validated route optimization.

## 3. System Architecture
`quarterly supplied price data → rolling-origin forecasting → retrospective sell/store simulation → warehouse allocation MILP → single-leg reference-origin transport proxy`. The research runner consumes saved upstream CSVs and does not retrain forecasts in warehouse/routing modes. Legacy interactive forecast/decision/routing paths coexist and are not treated as validated research evidence.

## 4. Dataset Summary
### Dataset inventory
| filename | rows | columns | missing_cells | duplicate_rows | crop_categories | date_range | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dataset_inventory.csv | 59 | 11 | 0 | 0 | Not applicable/not present | Not Available | Classification not documented |
| dataset_profiles.csv | 4 | 7 | 0 | 0 | Not applicable/not present | Not Available | Classification not documented |
| farmer_crop_dataset (1).csv | 450 | 5 | 0 | 0 | Onion, Rice, Tomato | Not Available | Supplied farmer-shaped dataset; real vs synthetic provenance not documented |
| farmer_decision_history.csv | 9 | 12 | 8 | 0 | Onion, Rice, Tomato | Not Available | Supplied history file; observation provenance not documented |
| forecast_dm_tests.csv | 36 | 9 | 72 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_final_table.csv | 12 | 17 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_fold_metrics.csv | 36 | 28 | 294 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_horizon_metrics.csv | 48 | 8 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_interval_metrics.csv | 30 | 8 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_intervals.csv | 144 | 10 | 216 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_model_summary.csv | 12 | 13 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| forecast_predictions.csv | 144 | 21 | 288 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2015-06-30 | Derived/model output/scenario result; not raw observations |
| forecast_validation_results.csv | 144 | 21 | 288 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2015-06-30 | Derived/model output/scenario result; not raw observations |
| model_comparison.csv | 12 | 13 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| price dataset (1).csv | 101 | 5 | 24 | 0 | Onion, Rice, Tomato | Not Available | Supplied source dataset; provenance/publication not documented in repository |
| project_artifact_inventory.csv | 195 | 4 | 0 | 0 | Not applicable/not present | Not Available | Classification not documented |
| routing_baseline_comparison.csv | 108 | 16 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| routing_results.csv | 36 | 23 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| routing_routes.csv | 36 | 23 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| routing_sensitivity.csv | 252 | 16 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| routing_summary.csv | 36 | 20 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| sell_store_baseline_summary.csv | 36 | 13 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| sell_store_decisions.csv | 144 | 26 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| sell_store_forecast_error_sensitivity.csv | 48 | 12 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| sell_store_sensitivity.csv | 2160 | 16 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| sell_store_summary.csv | 48 | 15 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_end_to_end_pipeline.csv | 36 | 21 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| table_f1_forecast_comparison.csv | 12 | 19 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_f2_forecast_horizon.csv | 48 | 12 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_f3_forecast_folds.csv | 36 | 33 | 294 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_f4_selected_models.csv | 3 | 3 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_r1_routing_performance.csv | 3 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_r2_routing_baselines.csv | 9 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_r3_routing_sensitivity.csv | 7 | 6 | 0 | 0 | Not applicable/not present | Not Available | Derived/model output/scenario result; not raw observations |
| table_r_routing_performance.csv | 9 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_s_transport_comparison.csv | 9 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss1_sell_store_by_crop.csv | 3 | 8 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss2_sell_store_models.csv | 48 | 15 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss3_decision_agreement.csv | 12 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss4_decision_regret.csv | 12 | 6 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss5_simulated_net_value.csv | 12 | 5 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss6_decision_distribution.csv | 54 | 6 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_ss_sensitivity_summary.csv | 45 | 6 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_w1_warehouse_results.csv | 3 | 9 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_w2_solver_status.csv | 1 | 2 | 0 | 0 | Not applicable/not present | Not Available | Derived/model output/scenario result; not raw observations |
| table_w3_warehouse_cost_components.csv | 3 | 4 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_w4_warehouse_baselines.csv | 12 | 7 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_w5_warehouse_utilization.csv | 103 | 6 | 0 | 0 | Not applicable/not present | Not Available | Derived/model output/scenario result; not raw observations |
| table_w6_warehouse_sensitivity.csv | 11 | 8 | 0 | 0 | Not applicable/not present | Not Available | Derived/model output/scenario result; not raw observations |
| table_w_warehouse_utilization.csv | 103 | 6 | 0 | 0 | Not applicable/not present | Not Available | Derived/model output/scenario result; not raw observations |
| table_x_sell_store_performance.csv | 48 | 9 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_y_sell_store_sensitivity.csv | 24 | 6 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| table_z_warehouse_optimization.csv | 12 | 9 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| tamilnadu_full_warehouse_dataset (1).csv | 103 | 12 | 0 | 0 | Not applicable/not present | Not Available | Supplied warehouse-shaped dataset; operational provenance not independently verified |
| warehouse_baseline_comparison.csv | 144 | 12 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |
| warehouse_optimization_results.csv | 3708 | 16 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| warehouse_sensitivity.csv | 396 | 17 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| warehouse_summary.csv | 36 | 20 | 0 | 0 | Onion, Rice, Tomato | 2011-12-31 to 2014-06-30 | Derived/model output/scenario result; not raw observations |
| warehouse_utilization.csv | 3708 | 11 | 0 | 0 | Onion, Rice, Tomato | Not Available | Derived/model output/scenario result; not raw observations |

### Repository artifact inventory
This inventory includes the project source, tests, model artifacts, configurations, reports, figures, and databases present at generation time; `.venv`, `.git`, and bytecode caches are excluded.

| path | category | bytes | format |
| --- | --- | --- | --- |
| .pytest_cache/.gitignore | other project file | 39 | no extension |
| .pytest_cache/CACHEDIR.TAG | other project file | 191 | .tag |
| .pytest_cache/README.md | documentation/report | 310 | .md |
| .pytest_cache/v/cache/lastfailed | other project file | 27 | no extension |
| .pytest_cache/v/cache/nodeids | other project file | 5941 | no extension |
| ADIS_Complete_Performance_Report.html | documentation/report | 4073518 | .html |
| ADIS_Complete_Performance_Report.md | documentation/report | 115443 | .md |
| ADIS_Faculty_Summary.md | documentation/report | 1958 | .md |
| agri_price_forecast.code-workspace | configuration/runner | 160 | .code-workspace |
| AUDIT_REPORT.md | documentation/report | 8212 | .md |
| custom_ui.py | other project file | 20695 | .py |
| dataset_inventory.csv | dataset or tabular result | 25694 | .csv |
| dataset_profiles.csv | dataset or tabular result | 829 | .csv |
| demo_app.py | other project file | 200 | .py |
| END_TO_END_RESEARCH_REPORT.md | documentation/report | 180711 | .md |
| experiment_config.json | configuration/runner | 1545 | .json |
| farmer_crop_dataset (1).csv | dataset or tabular result | 11723 | .csv |
| farmer_decision_history.csv | dataset or tabular result | 1233 | .csv |
| farmer_history.db | database | 8192 | .db |
| forecast_dm_tests.csv | dataset or tabular result | 4567 | .csv |
| forecast_final_table.csv | dataset or tabular result | 3236 | .csv |
| forecast_final_validation_report.md | documentation/report | 59616 | .md |
| forecast_fold_metrics.csv | dataset or tabular result | 10318 | .csv |
| forecast_horizon_metrics.csv | dataset or tabular result | 4407 | .csv |
| forecast_interval_metrics.csv | dataset or tabular result | 2236 | .csv |
| forecast_intervals.csv | dataset or tabular result | 13515 | .csv |
| forecast_model_summary.csv | dataset or tabular result | 2317 | .csv |
| forecast_predictions.csv | dataset or tabular result | 29937 | .csv |
| forecast_validation_onion.png | figure/image | 289061 | .png |
| forecast_validation_results.csv | dataset or tabular result | 29937 | .csv |
| forecast_validation_rice.png | figure/image | 295913 | .png |
| forecast_validation_tomato.png | figure/image | 363881 | .png |
| FORECASTING_DIAGNOSTIC_REPORT.md | documentation/report | 26834 | .md |
| FORECASTING_VALIDATION_REPORT.md | documentation/report | 59616 | .md |
| generate_adis_performance_report.py | other project file | 68205 | .py |
| generate_forecasting_validation.py | other project file | 833 | .py |
| generate_performance_report.py | other project file | 9781 | .py |
| model_comparison.csv | dataset or tabular result | 2317 | .csv |
| models/decision_report.json | configuration/runner | 12954 | .json |
| models/forecast_summary.csv | dataset or tabular result | 913 | .csv |
| models/onion_arima.pkl | serialized model artifact | 57758 | .pkl |
| models/onion_best.pkl | serialized model artifact | 156996 | .pkl |
| models/onion_lstm.pkl | serialized model artifact | 150282 | .pkl |
| models/onion_sarima.pkl | serialized model artifact | 155063 | .pkl |
| models/performance_metrics_report.html | documentation/report | 24618 | .html |
| models/rice_arima.pkl | serialized model artifact | 111841 | .pkl |
| models/rice_best.pkl | serialized model artifact | 366295 | .pkl |
| models/rice_lstm.pkl | serialized model artifact | 150290 | .pkl |
| models/rice_sarima.pkl | serialized model artifact | 364878 | .pkl |
| models/tomato_arima.pkl | serialized model artifact | 111843 | .pkl |
| models/tomato_best.pkl | serialized model artifact | 366297 | .pkl |
| models/tomato_lstm.pkl | serialized model artifact | 150282 | .pkl |
| models/tomato_sarima.pkl | serialized model artifact | 364880 | .pkl |
| price dataset (1).csv | dataset or tabular result | 3848 | .csv |
| project_artifact_inventory.csv | dataset or tabular result | 11484 | .csv |
| README.md | documentation/report | 3040 | .md |
| report_actual_vs_predicted_onion.png | figure/image | 199171 | .png |
| report_actual_vs_predicted_rice.png | figure/image | 194845 | .png |
| report_actual_vs_predicted_tomato.png | figure/image | 220086 | .png |
| report_end_to_end_cost.png | figure/image | 87655 | .png |
| report_forecast_error_comparison.png | figure/image | 81160 | .png |
| report_forecast_horizon_rmse.png | figure/image | 306317 | .png |
| report_forecast_model_comparison.png | figure/image | 102245 | .png |
| report_interval_coverage.png | figure/image | 82832 | .png |
| report_routing_baselines.png | figure/image | 153301 | .png |
| report_routing_cost_comparison.png | figure/image | 87999 | .png |
| report_routing_distance_comparison.png | figure/image | 92787 | .png |
| report_routing_quantity_sensitivity.png | figure/image | 120814 | .png |
| report_routing_sensitivity.png | figure/image | 130240 | .png |
| report_sell_spoilage_sensitivity.png | figure/image | 110300 | .png |
| report_sell_storage_sensitivity.png | figure/image | 117477 | .png |
| report_sell_store_baselines.png | figure/image | 123859 | .png |
| report_sell_store_distribution.png | figure/image | 76056 | .png |
| report_sell_store_regret.png | figure/image | 90323 | .png |
| report_warehouse_cost_comparison.png | figure/image | 96734 | .png |
| report_warehouse_cost_components.png | figure/image | 116631 | .png |
| report_warehouse_storage_sensitivity.png | figure/image | 103595 | .png |
| report_warehouse_transport_sensitivity.png | figure/image | 127952 | .png |
| report_warehouse_utilization.png | figure/image | 100731 | .png |
| requirements.txt | documentation/report | 202 | .txt |
| ROUTING_AUDIT_REPORT.md | documentation/report | 7462 | .md |
| routing_baseline_comparison.csv | dataset or tabular result | 23030 | .csv |
| routing_cost_by_crop.png | figure/image | 103061 | .png |
| routing_cost_components.png | figure/image | 70787 | .png |
| routing_distance_comparison.png | figure/image | 101328 | .png |
| routing_method_comparison.png | figure/image | 152414 | .png |
| routing_quantity_sensitivity.png | figure/image | 144211 | .png |
| routing_research_assumptions.json | configuration/runner | 1206 | .json |
| routing_results.csv | dataset or tabular result | 11004 | .csv |
| routing_routes.csv | dataset or tabular result | 11004 | .csv |
| routing_sensitivity.csv | dataset or tabular result | 47665 | .csv |
| routing_sensitivity.png | figure/image | 232977 | .png |
| routing_summary.csv | dataset or tabular result | 8566 | .csv |
| routing_transport_sensitivity.png | figure/image | 149847 | .png |
| routing_validation_report.md | documentation/report | 25881 | .md |
| run_sell_store_research.py | other project file | 941 | .py |
| sell_store_agreement.png | figure/image | 302792 | .png |
| sell_store_assumptions.json | configuration/runner | 1363 | .json |
| SELL_STORE_AUDIT_REPORT.md | documentation/report | 5198 | .md |
| sell_store_baseline_summary.csv | dataset or tabular result | 4333 | .csv |
| sell_store_decisions.csv | dataset or tabular result | 40441 | .csv |
| sell_store_forecast_error_disagreement.png | figure/image | 183012 | .png |
| sell_store_forecast_error_sensitivity.csv | dataset or tabular result | 5500 | .csv |
| sell_store_regret.png | figure/image | 288451 | .png |
| sell_store_sensitivity.csv | dataset or tabular result | 334430 | .csv |
| sell_store_spoilage_sensitivity.png | figure/image | 151043 | .png |
| sell_store_storage_cost_sensitivity.png | figure/image | 193817 | .png |
| sell_store_summary.csv | dataset or tabular result | 6948 | .csv |
| sell_store_validation_report.md | documentation/report | 48026 | .md |
| sell_store_values_by_crop.png | figure/image | 97934 | .png |
| src/__init__.py | source code | 72 | .py |
| src/advanced_decision_system.py | source code | 10528 | .py |
| src/api.py | source code | 3121 | .py |
| src/app.py | source code | 22618 | .py |
| src/chatbot.py | source code | 5265 | .py |
| src/chatbot_ui.py | source code | 2001 | .py |
| src/complete_system.py | source code | 27815 | .py |
| src/create_agri_dataset.py | source code | 8333 | .py |
| src/dashboard.py | source code | 9202 | .py |
| src/decision.py | source code | 856 | .py |
| src/decision_model.py | source code | 335 | .py |
| src/decision_support.py | source code | 18818 | .py |
| src/forecast.py | source code | 2788 | .py |
| src/forecast_validation.py | source code | 52395 | .py |
| src/forecasting.py | source code | 740 | .py |
| src/mcdm.py | source code | 2654 | .py |
| src/price_pipeline.py | source code | 24666 | .py |
| src/routing.py | source code | 5457 | .py |
| src/routing_research.py | source code | 40470 | .py |
| src/run_full_pipeline.py | source code | 13178 | .py |
| src/sell_store_research.py | source code | 36706 | .py |
| src/storage_opt.py | source code | 867 | .py |
| src/train_agri_model.py | source code | 8411 | .py |
| src/train_simple_agri_model.py | source code | 5403 | .py |
| src/trained_agri_chatbot.py | source code | 6188 | .py |
| src/transport_opt.py | source code | 340 | .py |
| src/warehouse_research.py | source code | 38460 | .py |
| table_end_to_end_pipeline.csv | dataset or tabular result | 14250 | .csv |
| table_f1_forecast_comparison.csv | dataset or tabular result | 3831 | .csv |
| table_f2_forecast_horizon.csv | dataset or tabular result | 7251 | .csv |
| table_f3_forecast_folds.csv | dataset or tabular result | 14173 | .csv |
| table_f4_selected_models.csv | dataset or tabular result | 209 | .csv |
| table_r1_routing_performance.csv | dataset or tabular result | 327 | .csv |
| table_r2_routing_baselines.csv | dataset or tabular result | 963 | .csv |
| table_r3_routing_sensitivity.csv | dataset or tabular result | 537 | .csv |
| table_r_routing_performance.csv | dataset or tabular result | 964 | .csv |
| table_s_transport_comparison.csv | dataset or tabular result | 1073 | .csv |
| table_ss1_sell_store_by_crop.csv | dataset or tabular result | 380 | .csv |
| table_ss2_sell_store_models.csv | dataset or tabular result | 6717 | .csv |
| table_ss3_decision_agreement.csv | dataset or tabular result | 687 | .csv |
| table_ss4_decision_regret.csv | dataset or tabular result | 507 | .csv |
| table_ss5_simulated_net_value.csv | dataset or tabular result | 462 | .csv |
| table_ss6_decision_distribution.csv | dataset or tabular result | 1867 | .csv |
| table_ss_sensitivity_summary.csv | dataset or tabular result | 3239 | .csv |
| table_w1_warehouse_results.csv | dataset or tabular result | 384 | .csv |
| table_w2_solver_status.csv | dataset or tabular result | 42 | .csv |
| table_w3_warehouse_cost_components.csv | dataset or tabular result | 235 | .csv |
| table_w4_warehouse_baselines.csv | dataset or tabular result | 1024 | .csv |
| table_w5_warehouse_utilization.csv | dataset or tabular result | 3253 | .csv |
| table_w6_warehouse_sensitivity.csv | dataset or tabular result | 1105 | .csv |
| table_w_warehouse_utilization.csv | dataset or tabular result | 3252 | .csv |
| table_x_sell_store_performance.csv | dataset or tabular result | 2630 | .csv |
| table_y_sell_store_sensitivity.csv | dataset or tabular result | 1740 | .csv |
| table_z_warehouse_optimization.csv | dataset or tabular result | 1334 | .csv |
| tamilnadu_full_warehouse_dataset (1).csv | dataset or tabular result | 8075 | .csv |
| templates/chat.html | documentation/report | 9863 | .html |
| templates/dashboard.html | documentation/report | 28473 | .html |
| templates/login.html | documentation/report | 4083 | .html |
| templates/performance_metrics.html | documentation/report | 22152 | .html |
| templates/performance_metrics_simple.html | documentation/report | 27835 | .html |
| tests/conftest.py | test | 199 | .py |
| tests/test_complete_system.py | test | 3469 | .py |
| tests/test_decision_model.py | test | 530 | .py |
| tests/test_forecasting.py | test | 12122 | .py |
| tests/test_integrated_pipeline.py | test | 3013 | .py |
| tests/test_pipeline.py | test | 854 | .py |
| tests/test_routing_research.py | test | 13851 | .py |
| tests/test_sell_store_research.py | test | 9188 | .py |
| tests/test_warehouse_research.py | test | 8161 | .py |
| train_agri_model.bat | configuration/runner | 477 | .bat |
| update_summary.txt | documentation/report | 2972 | .txt |
| warehouse_allocation_by_warehouse.png | figure/image | 114681 | .png |
| WAREHOUSE_AUDIT_REPORT.md | documentation/report | 8371 | .md |
| warehouse_baseline_comparison.csv | dataset or tabular result | 20625 | .csv |
| warehouse_cost_by_crop_method.png | figure/image | 109895 | .png |
| warehouse_cost_components.png | figure/image | 113944 | .png |
| warehouse_optimization_results.csv | dataset or tabular result | 498085 | .csv |
| warehouse_research_assumptions.json | configuration/runner | 1498 | .json |
| warehouse_sensitivity.csv | dataset or tabular result | 75156 | .csv |
| warehouse_storage_sensitivity.png | figure/image | 130974 | .png |
| warehouse_summary.csv | dataset or tabular result | 8418 | .csv |
| warehouse_transport_sensitivity.png | figure/image | 147158 | .png |
| warehouse_utilization.csv | dataset or tabular result | 306133 | .csv |
| warehouse_utilization.png | figure/image | 119170 | .png |
| warehouse_validation_report.md | documentation/report | 27052 | .md |

### Source dataset profile
| dataset | rows | columns | missing_cells | duplicate_rows | features | crop_counts |
| --- | --- | --- | --- | --- | --- | --- |
| price dataset (1).csv | 101 | 5 | 24 | 0 | Year, Quarter, Crop, Price_INR_per_Quintal, Final_Price | {"Onion": 34, "Rice": 34, "Tomato": 33} |
| farmer_crop_dataset (1).csv | 450 | 5 | 0 | 0 | Serial_No, Farmer_ID, Crop_Cultivated, Crop_Yield_tonnes_per_acre, Season | {"Rice": 150, "Onion": 150, "Tomato": 150} |
| farmer_decision_history.csv | 9 | 12 | 8 | 0 | timestamp, crop, quantity_kg, district, decision, current_price, forecast_price, profit_now, profit_store, storage_cost, transport_cost, recommended_warehouse | Not present |
| tamilnadu_full_warehouse_dataset (1).csv | 103 | 12 | 0 | 0 | Warehouse_ID, District, Location, Latitude, Longitude, Capacity_MT, Storage_Type, Storage_Cost_per_MT, Tomato_Supported, Onion_Supported, Rice_Supported, Spoilage_Rate | Not present |

Price file rows: 101; crops: Rice, Onion, Tomato; raw quarterly labels span 2009Q1 to 2024Q4 but labeled `Price_INR_per_Quintal` prices are available only through 2015Q2 for the historical block; later `Final_Price` has inconsistent scaling. Evaluated contiguous windows: Rice 26 observations, Onion 26, Tomato 24. Evaluation unit is INR/quintal with no conversion. Price provenance/publication citation is not documented.

Farmer-shaped file: 450 rows and 150 IDs, three crops with row counts {'Rice': 150, 'Onion': 150, 'Tomato': 150}; it has yield per acre and season, but no acreage, district, coordinates, collection period, consent, or sampling documentation. It cannot establish actual decision-specific quantity or route origin. Decision-history CSV: 9 rows with 8 missing cells; SQLite `farmer_history.db` has a `history` table with zero rows. Warehouse CSV has 103 rows and 20 districts, coordinates, capacities labeled MT, crop support flags; source provenance and cost billing period are not verified.

## 5. Experimental Setup
Forecasting uses four models, three non-overlapping rolling-origin folds, 4-quarter horizons, minimum training size 12, and valid-only model selection by lowest mean validation RMSE. There are 36 crop/model/fold combinations, each with four predictions (144 total). Phase 2 evaluates only contiguous quarterly segments. Forecast units: INR/quintal. Sell/store uses selected-model forecasts, retrospective actual prices only for post-decision scoring, one-quintal scenario quantity, durations of 3 months per quarter, and configurable cost/spoilage assumptions. Warehouse scenarios are 36 independent selected-model crop/date/horizon cases, not simultaneous network demand. Routing uses 36 saved positive allocations and Haversine centroid-to-warehouse proxy distance, not road routes.

## 6. Forecasting Results
Candidate models actually evaluated: Seasonal Naive, ARIMA, SARIMA, LSTM. Table values are crop-wise across valid rolling-origin folds; no crops are pooled. MBE is mean(predicted − actual) over valid prediction rows; sMAPE is 200×abs(error)/(abs(actual)+abs(predicted)); pooled prediction MBE/SD and sMAPE are derived from valid rows. Existing fold metrics are retained for MAE/RMSE/MAPE/R².

### TABLE F1 — Forecasting model comparison by crop
| crop | model | valid_folds | failed_folds | mean_MAE | std_MAE | mean_RMSE | std_RMSE | mean_MAPE | mean_R2 | sMAPE_pct_pooled_predictions | MBE_inr_per_quintal_pooled_predictions | error_sd_inr_per_quintal_pooled_predictions | valid_predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 3 | 0 | 1,221.2622 | 727.1490 | 1,366.1336 | 759.3026 | 64.0161 | -13.1830 | 50.4920 | 340.7737 | 1,593.1905 | 12 |
| Onion | lstm | 3 | 0 | 766.7805 | 661.3918 | 889.5939 | 786.3468 | 31.8609 | -1.0763 | 39.7872 | -569.1055 | 1,088.3703 | 12 |
| Onion | sarima | 3 | 0 | 1,491.9614 | 886.4689 | 1,583.2773 | 908.2897 | 76.8859 | -18.1985 | 67.8018 | 185.8308 | 1,896.5684 | 12 |
| Onion | seasonal_naive | 3 | 0 | 1,040.3337 | 543.5447 | 1,273.6526 | 526.6698 | 50.6074 | -7.0764 | 49.6593 | -139.2415 | 1,432.1696 | 12 |
| Rice | arima | 3 | 0 | 101.0786 | 66.7703 | 123.2508 | 86.6924 | 4.5452 | -1.8873 | 4.7783 | -62.3978 | 143.2588 | 12 |
| Rice | lstm | 3 | 0 | 564.7358 | 94.6721 | 578.7580 | 83.3683 | 24.2768 | -200.7455 | 27.8137 | -564.7358 | 158.3479 | 12 |
| Rice | sarima | 3 | 0 | 85.3255 | 40.9323 | 104.5623 | 47.1783 | 3.8005 | -2.8067 | 3.8592 | 3.7150 | 119.7510 | 12 |
| Rice | seasonal_naive | 3 | 0 | 238.9107 | 78.7467 | 259.2139 | 77.3586 | 10.4142 | -19.7468 | 11.1755 | -238.9107 | 132.5191 | 12 |
| Tomato | arima | 3 | 0 | 572.9240 | 177.3296 | 782.1934 | 258.5724 | 24.3960 | -0.5788 | 29.4526 | -458.5369 | 714.8529 | 12 |
| Tomato | lstm | 3 | 0 | 653.7886 | 93.7317 | 875.5865 | 178.1144 | 27.8907 | -1.2806 | 35.6404 | -650.4242 | 639.8791 | 12 |
| Tomato | sarima | 3 | 0 | 412.5570 | 156.9961 | 513.1758 | 201.4804 | 19.0193 | 0.2817 | 20.6032 | -196.1951 | 538.1293 | 12 |
| Tomato | seasonal_naive | 3 | 0 | 491.7681 | 178.4692 | 592.5673 | 209.8544 | 23.6652 | 0.0712 | 25.0484 | -230.7236 | 610.7594 | 12 |

### TABLE F2 — Forecasting performance by horizon
| crop | model | horizon | MAE | RMSE | MAPE | sMAPE_pct | MBE_inr_per_quintal | valid_predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | 1,018.3935 | 1,366.7792 | 73.9232 | 48.6035 | 798.2528 | 3 |
| Onion | arima | 2 | 1,015.4318 | 1,466.7164 | 75.8482 | 46.3213 | 927.1211 | 3 |
| Onion | arima | 3 | 1,308.9150 | 1,530.0362 | 50.3778 | 51.1819 | -80.5342 | 3 |
| Onion | arima | 4 | 1,542.3083 | 1,846.9143 | 55.9152 | 55.8613 | -281.7449 | 3 |
| Onion | lstm | 1 | 466.4956 | 530.8115 | 30.3644 | 32.0403 | -48.2850 | 3 |
| Onion | lstm | 2 | 365.9585 | 414.2971 | 25.2525 | 25.7634 | 6.5311 | 3 |
| Onion | lstm | 3 | 981.2450 | 1,454.0517 | 31.4338 | 44.2760 | -981.2450 | 3 |
| Onion | lstm | 4 | 1,253.4229 | 1,752.4853 | 40.3929 | 57.0689 | -1,253.4229 | 3 |
| Onion | sarima | 1 | 1,160.3514 | 1,536.4208 | 79.9028 | 53.8452 | 736.9584 | 3 |
| Onion | sarima | 2 | 1,199.3076 | 1,398.3989 | 87.0886 | 80.0295 | 249.8310 | 3 |
| Onion | sarima | 3 | 1,735.2681 | 1,995.4270 | 68.6250 | 75.1730 | -292.9564 | 3 |
| Onion | sarima | 4 | 1,872.9185 | 2,242.5859 | 71.9271 | 62.1595 | 49.4902 | 3 |
| Onion | seasonal_naive | 1 | 875.6407 | 949.1311 | 74.3304 | 59.6110 | 218.0607 | 3 |
| Onion | seasonal_naive | 2 | 321.4627 | 449.8330 | 20.5175 | 24.8972 | -196.7810 | 3 |
| Onion | seasonal_naive | 3 | 1,347.3336 | 1,659.4095 | 48.5235 | 56.1636 | -337.5808 | 3 |
| Onion | seasonal_naive | 4 | 1,616.8980 | 1,934.2824 | 59.0583 | 57.9653 | -240.6650 | 3 |
| Rice | arima | 1 | 21.5787 | 21.6405 | 0.9912 | 0.9932 | -5.8552 | 3 |
| Rice | arima | 2 | 56.9126 | 63.0468 | 2.6965 | 2.7329 | -23.4047 | 3 |
| Rice | arima | 3 | 124.4302 | 161.0177 | 5.7289 | 6.0321 | -95.0635 | 3 |
| Rice | arima | 4 | 201.3930 | 245.8767 | 8.7643 | 9.3550 | -125.2679 | 3 |
| Rice | lstm | 1 | 425.0418 | 446.2771 | 18.8933 | 20.9820 | -425.0418 | 3 |
| Rice | lstm | 2 | 496.7831 | 512.1931 | 21.8422 | 24.5987 | -496.7831 | 3 |
| Rice | lstm | 3 | 624.3866 | 629.9573 | 26.6031 | 30.6998 | -624.3866 | 3 |
| Rice | lstm | 4 | 712.7317 | 713.6478 | 29.7685 | 34.9744 | -712.7317 | 3 |
| Rice | sarima | 1 | 44.3164 | 56.5643 | 2.2471 | 2.2034 | 36.2463 | 3 |
| Rice | sarima | 2 | 21.8956 | 24.6128 | 0.9732 | 0.9720 | 2.2192 | 3 |
| Rice | sarima | 3 | 100.8702 | 116.1261 | 4.5447 | 4.6586 | -20.5016 | 3 |
| Rice | sarima | 4 | 174.2197 | 188.0045 | 7.4369 | 7.6027 | -3.1038 | 3 |
| Rice | seasonal_naive | 1 | 224.7750 | 279.5055 | 9.7726 | 10.5831 | -224.7750 | 3 |
| Rice | seasonal_naive | 2 | 236.7975 | 267.4684 | 10.4146 | 11.1457 | -236.7975 | 3 |
| Rice | seasonal_naive | 3 | 254.9772 | 262.2446 | 11.1499 | 11.8714 | -254.9772 | 3 |
| Rice | seasonal_naive | 4 | 239.0932 | 272.5251 | 10.3196 | 11.1019 | -239.0932 | 3 |
| Tomato | arima | 1 | 1,278.6870 | 1,362.7534 | 45.6811 | 60.1412 | -1,278.6870 | 3 |
| Tomato | arima | 2 | 629.9060 | 867.0260 | 24.4834 | 30.8134 | -629.9060 | 3 |
| Tomato | arima | 3 | 178.7402 | 202.9457 | 14.9308 | 13.5916 | 145.9223 | 3 |
| Tomato | arima | 4 | 204.3626 | 254.4151 | 12.4887 | 13.2642 | -71.4768 | 3 |
| Tomato | lstm | 1 | 1,363.8340 | 1,402.3666 | 50.0934 | 66.9209 | -1,363.8340 | 3 |
| Tomato | lstm | 2 | 823.5602 | 999.3590 | 35.4406 | 45.0969 | -823.5602 | 3 |
| Tomato | lstm | 3 | 110.9159 | 143.9371 | 7.7332 | 8.2015 | -97.4582 | 3 |
| Tomato | lstm | 4 | 316.8443 | 455.4529 | 18.2955 | 22.3423 | -316.8443 | 3 |
| Tomato | sarima | 1 | 563.2259 | 612.4732 | 20.0062 | 22.5472 | -563.2259 | 3 |
| Tomato | sarima | 2 | 618.2497 | 822.5561 | 24.4414 | 28.1645 | -297.9125 | 3 |
| Tomato | sarima | 3 | 95.7416 | 105.2527 | 7.8731 | 7.5190 | 62.8934 | 3 |
| Tomato | sarima | 4 | 373.0109 | 391.1200 | 23.7565 | 24.1820 | 13.4647 | 3 |
| Tomato | seasonal_naive | 1 | 620.9011 | 624.3464 | 24.0301 | 27.5253 | -620.9011 | 3 |
| Tomato | seasonal_naive | 2 | 840.2789 | 1,010.5751 | 35.6233 | 37.8428 | -130.9646 | 3 |
| Tomato | seasonal_naive | 3 | 187.6938 | 224.5172 | 13.1871 | 14.3981 | -187.6938 | 3 |
| Tomato | seasonal_naive | 4 | 318.1986 | 345.2842 | 21.8201 | 20.4274 | 16.6650 | 3 |

### TABLE F3 — Rolling-origin fold performance
| crop | model | fold | status | train_observations | validation_observations | MAE | RMSE | MAPE | R2 | sMAPE_pct | MBE_inr_per_quintal | error_sd_inr_per_quintal | lstm_training_sequences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rice | seasonal_naive | 1 | VALID | 12 | 4 | 211.5323 | 256.1834 | 10.0703 | -1.9667 | 10.8461 | -211.5323 | 166.8695 | 0 |
| Rice | seasonal_naive | 2 | VALID | 16 | 4 | 346.0846 | 355.4374 | 14.8234 | -26.3254 | 16.1032 | -346.0846 | 93.5318 | 0 |
| Rice | seasonal_naive | 3 | VALID | 20 | 4 | 159.1153 | 166.0210 | 6.3487 | -30.9481 | 6.5772 | -159.1153 | 54.7148 | 0 |
| Rice | arima | 1 | VALID | 12 | 4 | 195.3875 | 245.7066 | 9.2453 | -1.7290 | 9.9511 | -195.3875 | 172.0290 | 0 |
| Rice | arima | 2 | VALID | 16 | 4 | 49.8272 | 56.8487 | 2.0870 | 0.3010 | 2.1152 | -49.8272 | 31.6022 | 0 |
| Rice | arima | 3 | VALID | 20 | 4 | 58.0212 | 67.1970 | 2.3034 | -4.2338 | 2.2686 | 58.0212 | 39.1404 | 0 |
| Rice | sarima | 1 | VALID | 12 | 4 | 140.5175 | 168.0885 | 6.7424 | -0.2772 | 7.0050 | -93.9115 | 160.9736 | 0 |
| Rice | sarima | 2 | VALID | 16 | 4 | 42.6115 | 55.1355 | 1.7718 | 0.3425 | 1.7475 | 32.2092 | 51.6720 | 0 |
| Rice | sarima | 3 | VALID | 20 | 4 | 72.8474 | 90.4630 | 2.8873 | -8.4855 | 2.8250 | 72.8474 | 61.9334 | 0 |
| Rice | lstm | 1 | VALID | 12 | 4 | 437.0935 | 467.4351 | 21.2976 | -8.8769 | 24.1443 | -437.0935 | 191.2932 | 8 |
| Rice | lstm | 2 | VALID | 16 | 4 | 593.5597 | 600.7919 | 25.1408 | -77.0708 | 28.8327 | -593.5597 | 107.3169 | 12 |
| Rice | lstm | 3 | VALID | 20 | 4 | 663.5541 | 668.0470 | 26.3920 | -516.2888 | 30.4641 | -663.5541 | 89.3138 | 16 |
| Onion | seasonal_naive | 1 | VALID | 12 | 4 | 396.6110 | 638.5702 | 42.8679 | -6.4375 | 27.6914 | 309.9483 | 644.6745 | 0 |
| Onion | seasonal_naive | 2 | VALID | 16 | 4 | 1,726.0316 | 1,928.2018 | 58.5093 | -2.2881 | 83.9622 | -1,726.0316 | 992.4900 | 0 |
| Onion | seasonal_naive | 3 | VALID | 20 | 4 | 998.3587 | 1,254.1858 | 50.4450 | -12.5034 | 37.3242 | 998.3587 | 876.5553 | 0 |
| Onion | arima | 1 | VALID | 12 | 4 | 302.5340 | 323.2392 | 31.5704 | -0.9057 | 26.7308 | 222.1401 | 271.1391 | 0 |
| Onion | arima | 2 | VALID | 16 | 4 | 1,280.5357 | 1,666.0204 | 36.7156 | -1.4547 | 50.4028 | -1,280.5357 | 1,230.6379 | 0 |
| Onion | arima | 3 | VALID | 20 | 4 | 2,080.7168 | 2,109.1412 | 123.7622 | -37.1884 | 74.3424 | 2,080.7168 | 398.4875 | 0 |
| Onion | sarima | 1 | VALID | 12 | 4 | 311.4042 | 333.7489 | 32.0571 | -1.0317 | 37.5574 | -173.1354 | 329.4692 | 0 |
| Onion | sarima | 2 | VALID | 16 | 4 | 1,716.9260 | 1,950.1766 | 57.7418 | -2.3635 | 84.0359 | -1,716.9260 | 1,067.9287 | 0 |
| Onion | sarima | 3 | VALID | 20 | 4 | 2,447.5539 | 2,465.9064 | 140.8588 | -51.2004 | 81.8121 | 2,447.5539 | 346.7455 | 0 |
| Onion | lstm | 1 | VALID | 12 | 4 | 209.8727 | 267.5409 | 17.8669 | -0.3055 | 19.2446 | -86.4980 | 292.3382 | 8 |
| Onion | lstm | 2 | VALID | 16 | 4 | 1,696.0408 | 1,998.9307 | 54.1894 | -2.5338 | 78.2032 | -1,696.0408 | 1,221.5670 | 12 |
| Onion | lstm | 3 | VALID | 20 | 4 | 394.4279 | 402.3100 | 23.5264 | -0.3894 | 21.9136 | 75.2224 | 456.3550 | 16 |
| Tomato | seasonal_naive | 1 | VALID | 12 | 4 | 262.2340 | 336.1362 | 14.5747 | 0.0859 | 16.1630 | -212.8376 | 300.4169 | 0 |
| Tomato | seasonal_naive | 2 | VALID | 16 | 4 | 697.4334 | 850.1683 | 31.0450 | -0.1973 | 34.7907 | -446.2857 | 835.5558 | 0 |
| Tomato | seasonal_naive | 3 | VALID | 20 | 4 | 515.6369 | 591.3975 | 25.3758 | 0.3250 | 24.1915 | -33.0476 | 681.8200 | 0 |
| Tomato | arima | 1 | VALID | 12 | 4 | 351.0227 | 418.3879 | 20.8718 | -0.4162 | 22.5400 | -211.3995 | 416.9072 | 0 |
| Tomato | arima | 2 | VALID | 16 | 4 | 785.0604 | 996.0914 | 31.5572 | -0.6436 | 39.2152 | -611.6109 | 907.8401 | 0 |
| Tomato | arima | 3 | VALID | 20 | 4 | 582.6888 | 932.1009 | 20.7591 | -0.6767 | 26.6026 | -552.6003 | 866.7525 | 0 |
| Tomato | sarima | 1 | VALID | 12 | 4 | 237.7617 | 302.4763 | 14.2123 | 0.2598 | 15.4560 | -160.6103 | 295.9644 | 0 |
| Tomato | sarima | 2 | VALID | 16 | 4 | 618.5152 | 784.6455 | 25.7151 | -0.0198 | 29.6641 | -429.9755 | 757.8827 | 0 |
| Tomato | sarima | 3 | VALID | 20 | 4 | 381.3942 | 452.4056 | 17.1305 | 0.6050 | 16.6893 | 2.0006 | 522.3878 | 0 |
| Tomato | lstm | 1 | VALID | 12 | 4 | 543.7932 | 641.3627 | 30.5216 | -2.3280 | 37.9787 | -543.7932 | 392.6576 | 8 |
| Tomato | lstm | 2 | VALID | 16 | 4 | 772.8504 | 1,072.9575 | 28.0161 | -0.9070 | 37.8322 | -762.7571 | 871.3510 | 12 |
| Tomato | lstm | 3 | VALID | 20 | 4 | 644.7221 | 912.4393 | 25.1344 | -0.6067 | 31.1103 | -644.7221 | 745.5457 | 16 |

### TABLE F4 — Selected model by crop
| crop | selected_model | criterion |
| --- | --- | --- |
| Rice | sarima | Lowest mean validation RMSE among valid folds |
| Onion | lstm | Lowest mean validation RMSE among valid folds |
| Tomato | sarima | Lowest mean validation RMSE among valid folds |

Under the specified procedure, the best-performing candidate under the validation RMSE criterion for each crop was the selected model listed in Table F4. This is not a claim of general model superiority. LSTM uses a small fold-wise training set: 8, 12, and 16 sequences in folds with 12, 16, and 20 training observations respectively, lookback at most four quarters, one LSTM layer with 32 units (plus Input and Dense output), ReLU, Adam 0.001, MSE, 20 epochs, batch size 8, MinMaxScaler fit to each training fold. Overfitting cannot be reliably diagnosed from only three validation folds and no reserved independent test set; R² and errors vary substantially.

## 7. Forecast Uncertainty
ARIMA/SARIMA use native statsmodels 95% forecast intervals; Seasonal Naive and LSTM have no statistically justified interval under the current implementation. Do not interpret absent bounds as zero uncertainty. Coverage is empirical on only three observations per crop/model/horizon (and 12 pooled per crop/model), so it is descriptive and highly uncertain.

### Coverage by crop/model/horizon and pooled
| crop | model | horizon | empirical_coverage_percentage | mean_interval_width | number_of_intervals | confidence_level | price_unit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | 66.6667 | 2,162.9777 | 3 | 0.9500 | INR per quintal |
| Onion | arima | 2 | 66.6667 | 3,264.8122 | 3 | 0.9500 | INR per quintal |
| Onion | arima | 3 | 100.0000 | 3,859.0906 | 3 | 0.9500 | INR per quintal |
| Onion | arima | 4 | 66.6667 | 4,407.0172 | 3 | 0.9500 | INR per quintal |
| Onion | sarima | 1 | 66.6667 | 2,018.5935 | 3 | 0.9500 | INR per quintal |
| Onion | sarima | 2 | 66.6667 | 2,822.7156 | 3 | 0.9500 | INR per quintal |
| Onion | sarima | 3 | 66.6667 | 3,442.7740 | 3 | 0.9500 | INR per quintal |
| Onion | sarima | 4 | 33.3333 | 3,967.1750 | 3 | 0.9500 | INR per quintal |
| Rice | arima | 1 | 100.0000 | 297.0773 | 3 | 0.9500 | INR per quintal |
| Rice | arima | 2 | 100.0000 | 429.8149 | 3 | 0.9500 | INR per quintal |
| Rice | arima | 3 | 66.6667 | 538.8856 | 3 | 0.9500 | INR per quintal |
| Rice | arima | 4 | 66.6667 | 636.1332 | 3 | 0.9500 | INR per quintal |
| Rice | sarima | 1 | 100.0000 | 320.6356 | 3 | 0.9500 | INR per quintal |
| Rice | sarima | 2 | 100.0000 | 478.5678 | 3 | 0.9500 | INR per quintal |
| Rice | sarima | 3 | 100.0000 | 594.9560 | 3 | 0.9500 | INR per quintal |
| Rice | sarima | 4 | 66.6667 | 691.8143 | 3 | 0.9500 | INR per quintal |
| Tomato | arima | 1 | 33.3333 | 1,596.9967 | 3 | 0.9500 | INR per quintal |
| Tomato | arima | 2 | 66.6667 | 1,643.4378 | 3 | 0.9500 | INR per quintal |
| Tomato | arima | 3 | 100.0000 | 1,652.8537 | 3 | 0.9500 | INR per quintal |
| Tomato | arima | 4 | 100.0000 | 1,654.3272 | 3 | 0.9500 | INR per quintal |
| Tomato | sarima | 1 | 66.6667 | 1,682.2408 | 3 | 0.9500 | INR per quintal |
| Tomato | sarima | 2 | 66.6667 | 1,693.0249 | 3 | 0.9500 | INR per quintal |
| Tomato | sarima | 3 | 100.0000 | 1,702.5490 | 3 | 0.9500 | INR per quintal |
| Tomato | sarima | 4 | 100.0000 | 1,716.1982 | 3 | 0.9500 | INR per quintal |
| Onion | arima | all | 75.0000 | 3,423.4744 | 12 | 0.9500 | INR per quintal |
| Onion | sarima | all | 58.3333 | 3,062.8145 | 12 | 0.9500 | INR per quintal |
| Rice | arima | all | 83.3333 | 475.4777 | 12 | 0.9500 | INR per quintal |
| Rice | sarima | all | 91.6667 | 521.4934 | 12 | 0.9500 | INR per quintal |
| Tomato | arima | all | 75.0000 | 1,636.9038 | 12 | 0.9500 | INR per quintal |
| Tomato | sarima | all | 83.3333 | 1,698.5032 | 12 | 0.9500 | INR per quintal |

## 7A. Forecasting Diagnostics
ARIMA/SARIMA fold outputs include optimizer convergence, AIC/BIC, residual mean and sample standard deviation, Ljung–Box p-value where the residual sample supports it, lag-1 residual autocorrelation, warning text, and forecast interval generation status. Model convergence is not treated as evidence of model quality. The repository does not contain residual normality tests or standalone residual/ACF plots for every crop/model/fold; these are not claimed. Actual-versus-predicted and interval figures are generated where prediction data supports them.

| crop | model | fold | train_observations | converged | aic | bic | residual_mean | residual_std | ljung_box_lag | ljung_box_p_value | residual_acf_lag1 | interval_generated | small_sample_warning | warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rice | arima | 1 | 12 | True | 132.3125 | 133.5062 | 150.9779 | 441.2672 | 2.0000 | Not Available | -0.2693 | True | Not Available | Not Available |
| Rice | arima | 2 | 16 | True | 180.9050 | 183.0291 | 121.5542 | 384.5602 | 3.0000 | 0.7888 | -0.1882 | True | Not Available | Not Available |
| Rice | arima | 3 | 20 | True | 223.1296 | 225.9629 | 98.0583 | 345.1664 | 4.0000 | 0.8318 | -0.1737 | True | Not Available | Not Available |
| Rice | sarima | 1 | 12 | True | 87.6628 | 87.5005 | 60.5454 | 494.0880 | 2.0000 | Not Available | -0.0072 | True | SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Rice | sarima | 2 | 16 | True | 137.3290 | 138.5227 | 68.3765 | 424.5105 | 3.0000 | 0.6585 | -0.0357 | True | SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Rice | sarima | 3 | 20 | True | 180.5184 | 182.6426 | 51.1499 | 378.9001 | 4.0000 | 0.3327 | -0.0367 | True | Not Available | Non-invertible starting seasonal moving average Using zeros as starting parameters. |
| Onion | arima | 1 | 12 | True | 175.8793 | 177.0730 | 213.2899 | 633.0909 | 2.0000 | Not Available | -0.1113 | True | Not Available | Not Available |
| Onion | arima | 2 | 16 | True | 234.5162 | 236.6404 | 85.2152 | 595.0526 | 3.0000 | 0.0378 | -0.3244 | True | Not Available | Not Available |
| Onion | arima | 3 | 20 | True | 307.4651 | 310.2984 | 175.6641 | 717.2169 | 4.0000 | 0.1845 | -0.2333 | True | Not Available | Not Available |
| Onion | sarima | 1 | 12 | True | 113.7501 | 113.5878 | -11.4637 | 687.8104 | 2.0000 | Not Available | -0.3089 | True | SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Onion | sarima | 2 | 16 | True | 173.3488 | 174.5425 | -0.6093 | 623.9724 | 3.0000 | 0.1052 | -0.2323 | True | SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Onion | sarima | 3 | 20 | True | 243.0312 | 245.1553 | 123.6438 | 695.2155 | 4.0000 | 0.3264 | -0.1750 | True | Not Available | Non-invertible starting seasonal moving average Using zeros as starting parameters. |
| Tomato | arima | 1 | 12 | True | 166.2829 | 167.4766 | 74.8216 | 704.6080 | 2.0000 | Not Available | -0.3840 | True | Not Available | Non-invertible starting MA parameters found. Using zeros as starting parameters. |
| Tomato | arima | 2 | 16 | True | 225.9402 | 228.0644 | 105.0472 | 632.4982 | 3.0000 | 0.1639 | -0.3410 | True | Not Available | Non-invertible starting MA parameters found. Using zeros as starting parameters. |
| Tomato | arima | 3 | 20 | True | 298.6990 | 301.5324 | 151.2183 | 684.5476 | 4.0000 | 0.1061 | -0.1467 | True | Not Available | Non-invertible starting MA parameters found. Using zeros as starting parameters. |
| Tomato | sarima | 1 | 12 | True | 111.5909 | 111.4286 | 37.1978 | 748.1288 | 2.0000 | Not Available | -0.5355 | True | SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Tomato | sarima | 2 | 16 | True | 169.0502 | 170.2438 | 63.8605 | 660.4387 | 3.0000 | 0.2306 | -0.4487 | True | SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. |
| Tomato | sarima | 3 | 20 | True | 237.8630 | 239.9871 | 74.5142 | 681.5074 | 4.0000 | 0.6713 | -0.0837 | True | Not Available | Non-invertible starting seasonal moving average Using zeros as starting parameters. |

## 8. Statistical Comparison
Diebold–Mariano comparisons use paired rolling-origin squared errors with Bartlett HAC variance and HLN correction when sample-size rules permit. Current comparisons have only three paired origins per horizon, below the configured minimum; DM statistics and p-values are unavailable and every row is explicitly underpowered. No statistical superiority conclusion is supported.

| crop | model_a | model_b | horizon | loss_function | DM_statistic | p_value | paired_origins | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rice | sarima | seasonal_naive | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | seasonal_naive | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | seasonal_naive | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | seasonal_naive | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Rice | sarima | arima | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | arima | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | arima | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | arima | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Rice | sarima | lstm | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | lstm | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | lstm | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Rice | sarima | lstm | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Onion | lstm | seasonal_naive | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | seasonal_naive | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | seasonal_naive | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | seasonal_naive | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Onion | lstm | arima | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | arima | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | arima | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | arima | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Onion | lstm | sarima | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | sarima | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | sarima | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Onion | lstm | sarima | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Tomato | sarima | seasonal_naive | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | seasonal_naive | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | seasonal_naive | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | seasonal_naive | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Tomato | sarima | arima | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | arima | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | arima | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | arima | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |
| Tomato | sarima | lstm | 1 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | lstm | 2 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | lstm | 3 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 5); no significance conclusion. |
| Tomato | sarima | lstm | 4 | squared_error | Not Available | Not Available | 3 | Insufficient paired origins (3; requires at least 6); no significance conclusion. |

## 9. Sell-vs-Store Results
Decision model: sell-now value = Q×current price. Effective stored quantity = Q×(1−spoilage). Storage cost = Q×100 kg/quintal×assumed INR/kg/month×duration. Store value = effective quantity×forecast price−storage cost−total transport assumption. Store only when store value strictly exceeds sell-now value; ties sell. The forecast-based decision function receives no future actual. Actual prices are used only after the decision for hindsight agreement and regret.

### TABLE SS1 — Sell vs Store decisions by crop
| crop | N | sell_count | store_count | mean_sell_now_value_inr | mean_store_value_inr | mean_regret_inr | decision_agreement_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 48 | 47 | 1 | 2,277.4879 | 1,280.6935 | 272.6451 | 72.9167 |
| Rice | 48 | 47 | 1 | 2,155.9192 | 1,828.6237 | 3.3425 | 89.5833 |
| Tomato | 48 | 44 | 4 | 1,556.6972 | 849.1680 | 109.3151 | 66.6667 |

### TABLE SS2 — Model-based decision performance
| crop | model | horizon | number_of_decisions | decision_agreement_percentage | false_store_percentage | false_sell_percentage | mean_regret_inr | mean_realized_net_value_inr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | 3 | 66.6667 | 0.0000 | 33.3333 | 31.9648 | 2,277.4879 |
| Onion | arima | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,277.4879 |
| Onion | arima | 3 | 3 | 66.6667 | 0.0000 | 33.3333 | 454.4593 | 2,277.4879 |
| Onion | arima | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 549.1935 | 2,277.4879 |
| Onion | lstm | 1 | 3 | 66.6667 | 0.0000 | 33.3333 | 31.9648 | 2,277.4879 |
| Onion | lstm | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,277.4879 |
| Onion | lstm | 3 | 3 | 66.6667 | 0.0000 | 33.3333 | 454.4593 | 2,277.4879 |
| Onion | lstm | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 549.1935 | 2,277.4879 |
| Onion | sarima | 1 | 3 | 66.6667 | 0.0000 | 33.3333 | 31.9648 | 2,277.4879 |
| Onion | sarima | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,277.4879 |
| Onion | sarima | 3 | 3 | 66.6667 | 0.0000 | 33.3333 | 454.4593 | 2,277.4879 |
| Onion | sarima | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 549.1935 | 2,277.4879 |
| Onion | seasonal_naive | 1 | 3 | 33.3333 | 33.3333 | 33.3333 | 251.8156 | 2,057.6372 |
| Onion | seasonal_naive | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,277.4879 |
| Onion | seasonal_naive | 3 | 3 | 66.6667 | 0.0000 | 33.3333 | 454.4593 | 2,277.4879 |
| Onion | seasonal_naive | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 549.1935 | 2,277.4879 |
| Rice | arima | 1 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | arima | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | arima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | arima | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 6.0995 | 2,155.9192 |
| Rice | lstm | 1 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | lstm | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | lstm | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | lstm | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 6.0995 | 2,155.9192 |
| Rice | sarima | 1 | 3 | 66.6667 | 33.3333 | 0.0000 | 29.0811 | 2,126.8381 |
| Rice | sarima | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | sarima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | sarima | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 6.0995 | 2,155.9192 |
| Rice | seasonal_naive | 1 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | seasonal_naive | 2 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | seasonal_naive | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 2,155.9192 |
| Rice | seasonal_naive | 4 | 3 | 66.6667 | 0.0000 | 33.3333 | 6.0995 | 2,155.9192 |
| Tomato | arima | 1 | 3 | 0.0000 | 0.0000 | 100.0000 | 554.0259 | 1,556.6972 |
| Tomato | arima | 2 | 3 | 66.6667 | 0.0000 | 33.3333 | 98.0476 | 1,556.6972 |
| Tomato | arima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | arima | 4 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | lstm | 1 | 3 | 0.0000 | 0.0000 | 100.0000 | 554.0259 | 1,556.6972 |
| Tomato | lstm | 2 | 3 | 66.6667 | 0.0000 | 33.3333 | 98.0476 | 1,556.6972 |
| Tomato | lstm | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | lstm | 4 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | sarima | 1 | 3 | 33.3333 | 0.0000 | 66.6667 | 116.4115 | 1,994.3116 |
| Tomato | sarima | 2 | 3 | 33.3333 | 33.3333 | 33.3333 | 106.0355 | 1,548.7094 |
| Tomato | sarima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | sarima | 4 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | seasonal_naive | 1 | 3 | 33.3333 | 0.0000 | 66.6667 | 116.4115 | 1,994.3116 |
| Tomato | seasonal_naive | 2 | 3 | 33.3333 | 33.3333 | 33.3333 | 106.0355 | 1,548.7094 |
| Tomato | seasonal_naive | 3 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |
| Tomato | seasonal_naive | 4 | 3 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 1,556.6972 |

### TABLE SS3 — Decision agreement with hindsight
| crop | model | horizon | number_of_decisions | decision_agreement_percentage | false_store_percentage | false_sell_percentage |
| --- | --- | --- | --- | --- | --- | --- |
| Onion | lstm | 1 | 3 | 66.6667 | 0.0000 | 33.3333 |
| Onion | lstm | 2 | 3 | 100.0000 | 0.0000 | 0.0000 |
| Onion | lstm | 3 | 3 | 66.6667 | 0.0000 | 33.3333 |
| Onion | lstm | 4 | 3 | 66.6667 | 0.0000 | 33.3333 |
| Rice | sarima | 1 | 3 | 66.6667 | 33.3333 | 0.0000 |
| Rice | sarima | 2 | 3 | 100.0000 | 0.0000 | 0.0000 |
| Rice | sarima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 |
| Rice | sarima | 4 | 3 | 66.6667 | 0.0000 | 33.3333 |
| Tomato | sarima | 1 | 3 | 33.3333 | 0.0000 | 66.6667 |
| Tomato | sarima | 2 | 3 | 33.3333 | 33.3333 | 33.3333 |
| Tomato | sarima | 3 | 3 | 100.0000 | 0.0000 | 0.0000 |
| Tomato | sarima | 4 | 3 | 100.0000 | 0.0000 | 0.0000 |

### TABLE SS4 — Mean regret
| crop | model | horizon | number_of_decisions | mean_regret_inr | median_regret_inr |
| --- | --- | --- | --- | --- | --- |
| Onion | lstm | 1 | 3 | 31.9648 | 0.0000 |
| Onion | lstm | 2 | 3 | 0.0000 | 0.0000 |
| Onion | lstm | 3 | 3 | 454.4593 | 0.0000 |
| Onion | lstm | 4 | 3 | 549.1935 | 0.0000 |
| Rice | sarima | 1 | 3 | 29.0811 | 0.0000 |
| Rice | sarima | 2 | 3 | 0.0000 | 0.0000 |
| Rice | sarima | 3 | 3 | 0.0000 | 0.0000 |
| Rice | sarima | 4 | 3 | 6.0995 | 0.0000 |
| Tomato | sarima | 1 | 3 | 116.4115 | 6.3621 |
| Tomato | sarima | 2 | 3 | 106.0355 | 23.9635 |
| Tomato | sarima | 3 | 3 | 0.0000 | 0.0000 |
| Tomato | sarima | 4 | 3 | 0.0000 | 0.0000 |

### TABLE SS5 — Mean simulated net value
| crop | model | horizon | number_of_decisions | mean_realized_net_value_inr |
| --- | --- | --- | --- | --- |
| Onion | lstm | 1 | 3 | 2,277.4879 |
| Onion | lstm | 2 | 3 | 2,277.4879 |
| Onion | lstm | 3 | 3 | 2,277.4879 |
| Onion | lstm | 4 | 3 | 2,277.4879 |
| Rice | sarima | 1 | 3 | 2,126.8381 |
| Rice | sarima | 2 | 3 | 2,155.9192 |
| Rice | sarima | 3 | 3 | 2,155.9192 |
| Rice | sarima | 4 | 3 | 2,155.9192 |
| Tomato | sarima | 1 | 3 | 1,994.3116 |
| Tomato | sarima | 2 | 3 | 1,548.7094 |
| Tomato | sarima | 3 | 3 | 1,556.6972 |
| Tomato | sarima | 4 | 3 | 1,556.6972 |

### TABLE SS6 — Sell/store distribution
| crop | model | horizon | decision | decision_count | decision_percentage |
| --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | sell | 3 | 100.0000 |
| Onion | arima | 2 | sell | 3 | 100.0000 |
| Onion | arima | 3 | sell | 3 | 100.0000 |
| Onion | arima | 4 | sell | 3 | 100.0000 |
| Onion | lstm | 1 | sell | 3 | 100.0000 |
| Onion | lstm | 2 | sell | 3 | 100.0000 |
| Onion | lstm | 3 | sell | 3 | 100.0000 |
| Onion | lstm | 4 | sell | 3 | 100.0000 |
| Onion | sarima | 1 | sell | 3 | 100.0000 |
| Onion | sarima | 2 | sell | 3 | 100.0000 |
| Onion | sarima | 3 | sell | 3 | 100.0000 |
| Onion | sarima | 4 | sell | 3 | 100.0000 |
| Onion | seasonal_naive | 1 | sell | 2 | 66.6667 |
| Onion | seasonal_naive | 1 | store | 1 | 33.3333 |
| Onion | seasonal_naive | 2 | sell | 3 | 100.0000 |
| Onion | seasonal_naive | 3 | sell | 3 | 100.0000 |
| Onion | seasonal_naive | 4 | sell | 3 | 100.0000 |
| Rice | arima | 1 | sell | 3 | 100.0000 |
| Rice | arima | 2 | sell | 3 | 100.0000 |
| Rice | arima | 3 | sell | 3 | 100.0000 |
| Rice | arima | 4 | sell | 3 | 100.0000 |
| Rice | lstm | 1 | sell | 3 | 100.0000 |
| Rice | lstm | 2 | sell | 3 | 100.0000 |
| Rice | lstm | 3 | sell | 3 | 100.0000 |
| Rice | lstm | 4 | sell | 3 | 100.0000 |
| Rice | sarima | 1 | sell | 2 | 66.6667 |
| Rice | sarima | 1 | store | 1 | 33.3333 |
| Rice | sarima | 2 | sell | 3 | 100.0000 |
| Rice | sarima | 3 | sell | 3 | 100.0000 |
| Rice | sarima | 4 | sell | 3 | 100.0000 |
| Rice | seasonal_naive | 1 | sell | 3 | 100.0000 |
| Rice | seasonal_naive | 2 | sell | 3 | 100.0000 |
| Rice | seasonal_naive | 3 | sell | 3 | 100.0000 |
| Rice | seasonal_naive | 4 | sell | 3 | 100.0000 |
| Tomato | arima | 1 | sell | 3 | 100.0000 |
| Tomato | arima | 2 | sell | 3 | 100.0000 |
| Tomato | arima | 3 | sell | 3 | 100.0000 |
| Tomato | arima | 4 | sell | 3 | 100.0000 |
| Tomato | lstm | 1 | sell | 3 | 100.0000 |
| Tomato | lstm | 2 | sell | 3 | 100.0000 |
| Tomato | lstm | 3 | sell | 3 | 100.0000 |
| Tomato | lstm | 4 | sell | 3 | 100.0000 |
| Tomato | sarima | 1 | sell | 2 | 66.6667 |
| Tomato | sarima | 1 | store | 1 | 33.3333 |
| Tomato | sarima | 2 | sell | 2 | 66.6667 |
| Tomato | sarima | 2 | store | 1 | 33.3333 |
| Tomato | sarima | 3 | sell | 3 | 100.0000 |
| Tomato | sarima | 4 | sell | 3 | 100.0000 |
| Tomato | seasonal_naive | 1 | sell | 2 | 66.6667 |
| Tomato | seasonal_naive | 1 | store | 1 | 33.3333 |
| Tomato | seasonal_naive | 2 | sell | 2 | 66.6667 |
| Tomato | seasonal_naive | 2 | store | 1 | 33.3333 |
| Tomato | seasonal_naive | 3 | sell | 3 | 100.0000 |
| Tomato | seasonal_naive | 4 | sell | 3 | 100.0000 |

Selected-model retrospective summaries: Tomato sarima: N=3, agreement=66.67%, mean regret INR 31.96; Tomato sarima: N=3, agreement=100.00%, mean regret INR 0.00; Tomato sarima: N=3, agreement=66.67%, mean regret INR 454.46; Tomato sarima: N=3, agreement=66.67%, mean regret INR 549.19; Tomato sarima: N=3, agreement=66.67%, mean regret INR 29.08; Tomato sarima: N=3, agreement=100.00%, mean regret INR 0.00; Tomato sarima: N=3, agreement=100.00%, mean regret INR 0.00; Tomato sarima: N=3, agreement=66.67%, mean regret INR 6.10; Tomato sarima: N=3, agreement=33.33%, mean regret INR 116.41; Tomato sarima: N=3, agreement=33.33%, mean regret INR 106.04; Tomato sarima: N=3, agreement=100.00%, mean regret INR 0.00; Tomato sarima: N=3, agreement=100.00%, mean regret INR 0.00. Results use simulated 1-quintal quantities and are not farmer income or causal outcomes.

## 10. Sell/Store Baselines
| model | number_of_decisions | mean_agreement | mean_simulated_net_value_inr | mean_regret_inr |
| --- | --- | --- | --- | --- |
| always_sell | 36 | 77.7778 | 1,996.7015 | 141.1492 |
| always_store | 36 | 22.2222 | 1,513.3623 | 624.4884 |
| seasonal_naive_forecast | 36 | 75.0000 | 2,014.1828 | 123.6679 |

## 11. Sell/Store Sensitivity
All available scenarios are included in `sell_store_sensitivity.csv`; summary by crop/scenario is below. Inputs are assumptions, not probability distributions. Forecast-error sensitivity is in `sell_store_forecast_error_sensitivity.csv`.

| crop | scenario_type | scenario_value | n | store_percentage | mean_incremental_store_value_inr |
| --- | --- | --- | --- | --- | --- |
| Onion | future_price_multiplier | 0.9000 | 48 | 2.0833 | -1,166.1138 |
| Onion | future_price_multiplier | 1.0000 | 48 | 2.0833 | -996.7944 |
| Onion | future_price_multiplier | 1.1000 | 48 | 4.1667 | -827.4751 |
| Onion | spoilage_rate | 0.0000 | 48 | 4.1667 | -849.5602 |
| Onion | spoilage_rate | 0.0200 | 48 | 4.1667 | -886.3687 |
| Onion | spoilage_rate | 0.0500 | 48 | 2.0833 | -941.5816 |
| Onion | spoilage_rate | 0.1000 | 48 | 2.0833 | -1,033.6030 |
| Onion | storage_cost_multiplier | 0.5000 | 48 | 4.1667 | -790.5444 |
| Onion | storage_cost_multiplier | 1.0000 | 48 | 2.0833 | -996.7944 |
| Onion | storage_cost_multiplier | 1.5000 | 48 | 2.0833 | -1,203.0444 |
| Onion | storage_cost_multiplier | 2.0000 | 48 | 2.0833 | -1,409.2944 |
| Onion | storage_duration_months | 3.0000 | 48 | 4.1667 | -749.2944 |
| Onion | storage_duration_months | 6.0000 | 48 | 4.1667 | -914.2944 |
| Onion | storage_duration_months | 9.0000 | 48 | 2.0833 | -1,079.2944 |
| Onion | storage_duration_months | 12.0000 | 48 | 2.0833 | -1,244.2944 |
| Rice | future_price_multiplier | 0.9000 | 48 | 0.0000 | -532.6579 |
| Rice | future_price_multiplier | 1.0000 | 48 | 2.0833 | -327.2956 |
| Rice | future_price_multiplier | 1.1000 | 48 | 39.5833 | -121.9332 |
| Rice | spoilage_rate | 0.0000 | 48 | 2.0833 | -306.5519 |
| Rice | spoilage_rate | 0.0200 | 48 | 0.0000 | -348.0393 |
| Rice | spoilage_rate | 0.0500 | 48 | 0.0000 | -410.2703 |
| Rice | spoilage_rate | 0.1000 | 48 | 0.0000 | -513.9886 |
| Rice | storage_cost_multiplier | 0.5000 | 48 | 10.4167 | -214.7956 |
| Rice | storage_cost_multiplier | 1.0000 | 48 | 2.0833 | -327.2956 |
| Rice | storage_cost_multiplier | 1.5000 | 48 | 0.0000 | -439.7956 |
| Rice | storage_cost_multiplier | 2.0000 | 48 | 0.0000 | -552.2956 |
| Rice | storage_duration_months | 3.0000 | 48 | 18.7500 | -192.2956 |
| Rice | storage_duration_months | 6.0000 | 48 | 6.2500 | -282.2956 |
| Rice | storage_duration_months | 9.0000 | 48 | 2.0833 | -372.2956 |
| Rice | storage_duration_months | 12.0000 | 48 | 0.0000 | -462.2956 |
| Tomato | future_price_multiplier | 0.9000 | 48 | 8.3333 | -837.4460 |
| Tomato | future_price_multiplier | 1.0000 | 48 | 8.3333 | -707.5292 |
| Tomato | future_price_multiplier | 1.1000 | 48 | 8.3333 | -577.6124 |
| Tomato | spoilage_rate | 0.0000 | 48 | 14.5833 | -478.2642 |
| Tomato | spoilage_rate | 0.0200 | 48 | 14.5833 | -508.8329 |
| Tomato | spoilage_rate | 0.0500 | 48 | 8.3333 | -554.6859 |
| Tomato | spoilage_rate | 0.1000 | 48 | 8.3333 | -631.1075 |
| Tomato | storage_cost_multiplier | 0.5000 | 48 | 8.3333 | -482.5292 |
| Tomato | storage_cost_multiplier | 1.0000 | 48 | 8.3333 | -707.5292 |
| Tomato | storage_cost_multiplier | 1.5000 | 48 | 8.3333 | -932.5292 |
| Tomato | storage_cost_multiplier | 2.0000 | 48 | 8.3333 | -1,157.5292 |
| Tomato | storage_duration_months | 3.0000 | 48 | 10.4167 | -437.5292 |
| Tomato | storage_duration_months | 6.0000 | 48 | 8.3333 | -617.5292 |
| Tomato | storage_duration_months | 9.0000 | 48 | 8.3333 | -797.5292 |
| Tomato | storage_duration_months | 12.0000 | 48 | 8.3333 | -977.5292 |

## 12. Warehouse Optimization
The allocation MILP minimizes storage plus transport allocation costs and a shortage penalty on unallocated quantity. Variables are continuous quintal allocations to compatible warehouses; capacity is MT×10. CBC status is Optimal for all 36 scenarios, zero infeasible solutions, zero unallocated quantity, and zero constraint violations. The 1-quintal scenario was fully allocated. No CBC numeric gap was exposed.

### TABLE W1 — Warehouse optimization results by crop
| crop | scenarios | mean_available_q | mean_allocated_q | mean_unallocated_q | mean_cost_inr | mean_storage_cost_inr | mean_transport_cost_inr | max_constraint_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 12 | 1.0000 | 1.0000 | 0.0000 | 24.2575 | 1.2863 | 22.9713 | 0 |
| Rice | 12 | 1.0000 | 1.0000 | 0.0000 | 24.2575 | 1.2863 | 22.9713 | 0 |
| Tomato | 12 | 1.0000 | 1.0000 | 0.0000 | 13.0523 | 1.9950 | 11.0573 | 0 |

### TABLE W2 — Solver status
| solver_status | scenario_count |
| --- | --- |
| Optimal | 36 |

### TABLE W3 — Cost components
| crop | storage_cost_inr | transport_cost_inr | total_cost_inr |
| --- | --- | --- | --- |
| Onion | 1.2863 | 22.9713 | 24.2575 |
| Rice | 1.2863 | 22.9713 | 24.2575 |
| Tomato | 1.9950 | 11.0573 | 13.0523 |

### TABLE W4 — Warehouse baseline comparison
| crop | method | mean_total_cost_inr | mean_storage_cost_inr | mean_transport_cost_inr | mean_allocated_q | mean_unallocated_q |
| --- | --- | --- | --- | --- | --- | --- |
| Onion | Existing Method | 119.8314 | 1.5675 | 118.2639 | 1.0000 | 0.0000 |
| Onion | Lowest Storage Cost | 92.2986 | 1.1400 | 91.1586 | 1.0000 | 0.0000 |
| Onion | MILP | 24.2575 | 1.2863 | 22.9713 | 1.0000 | 0.0000 |
| Onion | Nearest Feasible | 24.4946 | 1.8600 | 22.6346 | 1.0000 | 0.0000 |
| Rice | Existing Method | 119.8314 | 1.5675 | 118.2639 | 1.0000 | 0.0000 |
| Rice | Lowest Storage Cost | 31.8389 | 1.1550 | 30.6839 | 1.0000 | 0.0000 |
| Rice | MILP | 24.2575 | 1.2863 | 22.9713 | 1.0000 | 0.0000 |
| Rice | Nearest Feasible | 24.4946 | 1.8600 | 22.6346 | 1.0000 | 0.0000 |
| Tomato | Existing Method | 120.8158 | 1.2900 | 119.5258 | 1.0000 | 0.0000 |
| Tomato | Lowest Storage Cost | 72.7810 | 1.1850 | 71.5960 | 1.0000 | 0.0000 |
| Tomato | MILP | 13.0523 | 1.9950 | 11.0573 | 1.0000 | 0.0000 |
| Tomato | Nearest Feasible | 13.0523 | 1.9950 | 11.0573 | 1.0000 | 0.0000 |

### TABLE W5 — Warehouse utilization
| warehouse_id | capacity_q | mean_allocated_q | mean_utilization_pct | mean_storage_cost_inr | mean_transport_cost_inr |
| --- | --- | --- | --- | --- | --- |
| WH001 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH002 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH003 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH004 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH005 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH006 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH007 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH008 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH009 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH010 | 150.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH011 | 3,150.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH012 | 400.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH013 | 400.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH014 | 400.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH015 | 400.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH016 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH017 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH018 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH019 | 10,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH020 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH021 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH022 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH023 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH024 | 1,100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH025 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH026 | 300.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH027 | 300.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH028 | 50.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH029 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH030 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH031 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH032 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH033 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH034 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH035 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH036 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH037 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH038 | 10,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH039 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH040 | 250.0000 | 0.3333 | 0.1333 | 0.6650 | 3.6858 |
| WH041 | 750.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH042 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH043 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH044 | 750.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH045 | 3,750.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH046 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH047 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH048 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH049 | 2,200.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH050 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH051 | 6,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH052 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH053 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH054 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH055 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH056 | 250.0000 | 0.5000 | 0.2000 | 0.7335 | 11.5418 |
| WH057 | 50.0000 | 0.1667 | 0.3333 | 0.1240 | 3.7724 |
| WH058 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH059 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH060 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH061 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH062 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH063 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH064 | 70.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH065 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH066 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH067 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH068 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH069 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH070 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH071 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH072 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH073 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH074 | 20,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH075 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH076 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH077 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH078 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH079 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH080 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH081 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH082 | 1,250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH083 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH084 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH085 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH086 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH087 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH088 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH089 | 50.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH090 | 5,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH091 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH092 | 380.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH093 | 500.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH094 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH095 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH096 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH097 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH098 | 50.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH099 | 1,000.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH100 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH101 | 250.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH102 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| WH103 | 100.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### TABLE W6 — Warehouse sensitivity
| scenario_type | scenario_multiplier | mean_total_cost_inr | mean_storage_cost_inr | mean_transport_cost_inr | mean_allocated_q | mean_unallocated_q | max_violations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| available_quantity_multiplier | 0.5000 | 10.2612 | 0.7612 | 9.5000 | 0.5000 | 0.0000 | 0 |
| available_quantity_multiplier | 1.0000 | 20.5224 | 1.5225 | 18.9999 | 1.0000 | 0.0000 | 0 |
| available_quantity_multiplier | 1.5000 | 30.7837 | 2.2837 | 28.4999 | 1.5000 | 0.0000 | 0 |
| storage_cost_multiplier | 0.5000 | 19.7178 | 0.8675 | 18.8503 | 1.0000 | 0.0000 | 0 |
| storage_cost_multiplier | 1.0000 | 20.5224 | 1.5225 | 18.9999 | 1.0000 | 0.0000 | 0 |
| storage_cost_multiplier | 1.5000 | 21.2837 | 2.2837 | 18.9999 | 1.0000 | 0.0000 | 0 |
| storage_cost_multiplier | 2.0000 | 22.0348 | 2.9600 | 19.0748 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 0.5000 | 11.0174 | 1.4800 | 9.5374 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 1.0000 | 20.5224 | 1.5225 | 18.9999 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 1.5000 | 29.9952 | 1.6075 | 28.3877 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 2.0000 | 39.4356 | 1.7350 | 37.7006 | 1.0000 | 0.0000 | 0 |

For standardized 1-quintal scenario calculations, mean total costs were Onion INR 24.2575 (INR 0.2426/kg), Rice INR 24.2575 (INR 0.2426/kg), Tomato INR 13.0523 (INR 0.1305/kg). These are scenario-based optimization costs, not commercial warehouse prices. The `Storage_Cost_per_MT` currency/time basis is undocumented and is assumed as INR/MT/month; transport rate is also assumed.

## 13. Routing Evaluation
The available data supports scenario-based single-leg synthetic centroid-to-warehouse routing only, not CVRP/VRP. 36 Haversine proxy route legs were evaluated; all 36 feasible with zero capacity and demand violations. Travel time and OSRM route data are unavailable/not supported by current data.

### Routing performance by crop
| crop | route_scenarios | mean_distance_km | mean_transport_cost_inr | mean_cost_per_quintal | route_legs | infeasible_scenarios |
| --- | --- | --- | --- | --- | --- | --- |
| Onion | 12 | 45.9426 | 22.9713 | 22.9713 | 12 | 0 |
| Rice | 12 | 45.9426 | 22.9713 | 22.9713 | 12 | 0 |
| Tomato | 12 | 22.1145 | 11.0573 | 11.0573 | 12 | 0 |

## 14. Routing Baselines
| crop | method | scenarios | mean_distance_km | mean_transport_cost_inr | mean_cost_per_quintal | feasible_scenarios |
| --- | --- | --- | --- | --- | --- | --- |
| Onion | Legacy best_route offline formula | 12 | 45.9450 | 22.9675 | 22.9675 | 12 |
| Onion | Nearest feasible warehouse | 12 | 45.2692 | 22.6346 | 22.6346 | 12 |
| Onion | Warehouse MILP allocation + Haversine | 12 | 45.9426 | 22.9713 | 22.9713 | 12 |
| Rice | Legacy best_route offline formula | 12 | 45.9450 | 22.9675 | 22.9675 | 12 |
| Rice | Nearest feasible warehouse | 12 | 45.2692 | 22.6346 | 22.6346 | 12 |
| Rice | Warehouse MILP allocation + Haversine | 12 | 45.9426 | 22.9713 | 22.9713 | 12 |
| Tomato | Legacy best_route offline formula | 12 | 22.1100 | 11.0600 | 11.0600 | 12 |
| Tomato | Nearest feasible warehouse | 12 | 22.1145 | 11.0573 | 11.0573 | 12 |
| Tomato | Warehouse MILP allocation + Haversine | 12 | 22.1145 | 11.0573 | 11.0573 | 12 |

## 15. Routing Sensitivity
| scenario_type | scenario_multiplier | mean_transport_cost_inr | mean_quantity_q | mean_unserved_q | infeasible_scenarios |
| --- | --- | --- | --- | --- | --- |
| available_quantity_multiplier | 0.5000 | 9.5000 | 0.5000 | 0.0000 | 0 |
| available_quantity_multiplier | 1.0000 | 18.9999 | 1.0000 | 0.0000 | 0 |
| available_quantity_multiplier | 1.5000 | 28.4999 | 1.5000 | 0.0000 | 0 |
| transport_cost_multiplier | 0.5000 | 9.5000 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 1.0000 | 18.9999 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 1.5000 | 28.4999 | 1.0000 | 0.0000 | 0 |
| transport_cost_multiplier | 2.0000 | 37.9999 | 1.0000 | 0.0000 | 0 |

## 16. End-to-End Results
The table joins validated Phase 2 forecast horizon/fold metrics, retrospective sell/store summary, saved warehouse MILP storage costs, and routing proxy costs by crop/model/horizon/scenario. The total optimization cost shown is warehouse storage plus scenario transport cost, not farmer expense.

### TABLE E2E1 — Complete end-to-end performance by crop/scenario
| crop | forecast_model | forecast_horizon | forecast_RMSE | forecast_MAE | forecast_R2 | sell_store_agreement_percentage | sell_store_mean_regret_inr | warehouse_method | warehouse_storage_cost_inr | allocated_quantity_quintal | unallocated_quantity_quintal | routing_method | distance_km | transport_cost_inr | total_cost_inr | route_distance_source | scenario_id | decision_date | metric_provenance | price_unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rice | sarima | 1 | 56.5643 | 44.3164 | -0.2772 | 66.6667 | 29.0811 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Rice_sarima_2011-12-31_h1 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 2 | 24.6128 | 21.8956 | -0.2772 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Rice_sarima_2011-12-31_h2 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 3 | 116.1261 | 100.8702 | -0.2772 | 100.0000 | 0.0000 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Rice_sarima_2011-12-31_h3 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 4 | 188.0045 | 174.2197 | -0.2772 | 66.6667 | 6.0995 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Rice_sarima_2011-12-31_h4 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 1 | 56.5643 | 44.3164 | 0.3425 | 66.6667 | 29.0811 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Rice_sarima_2012-12-31_h1 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 2 | 24.6128 | 21.8956 | 0.3425 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Rice_sarima_2012-12-31_h2 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 3 | 116.1261 | 100.8702 | 0.3425 | 100.0000 | 0.0000 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Rice_sarima_2012-12-31_h3 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 4 | 188.0045 | 174.2197 | 0.3425 | 66.6667 | 6.0995 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Rice_sarima_2012-12-31_h4 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 1 | 56.5643 | 44.3164 | -8.4855 | 66.6667 | 29.0811 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Rice_sarima_2013-12-31_h1 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 2 | 24.6128 | 21.8956 | -8.4855 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Rice_sarima_2013-12-31_h2 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 3 | 116.1261 | 100.8702 | -8.4855 | 100.0000 | 0.0000 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Rice_sarima_2013-12-31_h3 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Rice | sarima | 4 | 188.0045 | 174.2197 | -8.4855 | 66.6667 | 6.0995 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Rice_sarima_2013-12-31_h4 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 1 | 530.8115 | 466.4956 | -0.3055 | 66.6667 | 31.9648 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Onion_lstm_2011-12-31_h1 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 2 | 414.2971 | 365.9585 | -0.3055 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Onion_lstm_2011-12-31_h2 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 3 | 1,454.0517 | 981.2450 | -0.3055 | 66.6667 | 454.4593 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Onion_lstm_2011-12-31_h3 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 4 | 1,752.4853 | 1,253.4229 | -0.3055 | 66.6667 | 549.1935 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Onion_lstm_2011-12-31_h4 | 2011-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 1 | 530.8115 | 466.4956 | -2.5338 | 66.6667 | 31.9648 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Onion_lstm_2012-12-31_h1 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 2 | 414.2971 | 365.9585 | -2.5338 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Onion_lstm_2012-12-31_h2 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 3 | 1,454.0517 | 981.2450 | -2.5338 | 66.6667 | 454.4593 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Onion_lstm_2012-12-31_h3 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 4 | 1,752.4853 | 1,253.4229 | -2.5338 | 66.6667 | 549.1935 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Onion_lstm_2012-12-31_h4 | 2012-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 1 | 530.8115 | 466.4956 | -0.3894 | 66.6667 | 31.9648 | MILP | 0.7440 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 45.2692 | 22.6346 | 23.3786 | Haversine proxy only | Onion_lstm_2013-12-31_h1 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 2 | 414.2971 | 365.9585 | -0.3894 | 100.0000 | 0.0000 | MILP | 0.9780 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.0615 | Haversine proxy only | Onion_lstm_2013-12-31_h2 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 3 | 1,454.0517 | 981.2450 | -0.3894 | 66.6667 | 454.4593 | MILP | 1.4670 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 24.5505 | Haversine proxy only | Onion_lstm_2013-12-31_h3 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Onion | lstm | 4 | 1,752.4853 | 1,253.4229 | -0.3894 | 66.6667 | 549.1935 | MILP | 1.9560 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 46.1671 | 23.0835 | 25.0395 | Haversine proxy only | Onion_lstm_2013-12-31_h4 | 2013-12-31 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 1 | 612.4732 | 563.2259 | 0.2598 | 33.3333 | 116.4115 | MILP | 0.7980 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 11.8553 | Haversine proxy only | Tomato_sarima_2012-06-30_h1 | 2012-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 2 | 822.5561 | 618.2497 | 0.2598 | 33.3333 | 106.0355 | MILP | 1.5960 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 12.6533 | Haversine proxy only | Tomato_sarima_2012-06-30_h2 | 2012-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 3 | 105.2527 | 95.7416 | 0.2598 | 100.0000 | 0.0000 | MILP | 2.3940 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 13.4513 | Haversine proxy only | Tomato_sarima_2012-06-30_h3 | 2012-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 4 | 391.1200 | 373.0109 | 0.2598 | 100.0000 | 0.0000 | MILP | 3.1920 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 14.2493 | Haversine proxy only | Tomato_sarima_2012-06-30_h4 | 2012-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 1 | 612.4732 | 563.2259 | -0.0198 | 33.3333 | 116.4115 | MILP | 0.7980 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 11.8553 | Haversine proxy only | Tomato_sarima_2013-06-30_h1 | 2013-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 2 | 822.5561 | 618.2497 | -0.0198 | 33.3333 | 106.0355 | MILP | 1.5960 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 12.6533 | Haversine proxy only | Tomato_sarima_2013-06-30_h2 | 2013-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 3 | 105.2527 | 95.7416 | -0.0198 | 100.0000 | 0.0000 | MILP | 2.3940 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 13.4513 | Haversine proxy only | Tomato_sarima_2013-06-30_h3 | 2013-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 4 | 391.1200 | 373.0109 | -0.0198 | 100.0000 | 0.0000 | MILP | 3.1920 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 14.2493 | Haversine proxy only | Tomato_sarima_2013-06-30_h4 | 2013-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 1 | 612.4732 | 563.2259 | 0.6050 | 33.3333 | 116.4115 | MILP | 0.7980 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 11.8553 | Haversine proxy only | Tomato_sarima_2014-06-30_h1 | 2014-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 2 | 822.5561 | 618.2497 | 0.6050 | 33.3333 | 106.0355 | MILP | 1.5960 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 12.6533 | Haversine proxy only | Tomato_sarima_2014-06-30_h2 | 2014-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 3 | 105.2527 | 95.7416 | 0.6050 | 100.0000 | 0.0000 | MILP | 2.3940 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 13.4513 | Haversine proxy only | Tomato_sarima_2014-06-30_h3 | 2014-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |
| Tomato | sarima | 4 | 391.1200 | 373.0109 | 0.6050 | 100.0000 | 0.0000 | MILP | 3.1920 | 1.0000 | 0.0000 | single_leg_reference_origin_to_warehouse | 22.1145 | 11.0573 | 14.2493 | Haversine proxy only | Tomato_sarima_2014-06-30_h4 | 2014-06-30 | forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv | INR per quintal |

### TABLE E2E2 — Complete system metrics
| crop | forecast_RMSE | forecast_MAE | sell_store_agreement_percentage | sell_store_mean_regret_inr | warehouse_storage_cost_inr | routing_distance_km | transport_cost_inr | total_cost_inr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 1,037.9114 | 766.7805 | 75.0000 | 258.9044 | 1.2863 | 45.9426 | 22.9713 | 24.2575 |
| Rice | 96.3269 | 85.3255 | 83.3333 | 8.7952 | 1.2863 | 45.9426 | 22.9713 | 24.2575 |
| Tomato | 482.8505 | 412.5570 | 66.6667 | 55.6117 | 1.9950 | 22.1145 | 11.0573 | 13.0523 |

### TABLE E2E3 — Baseline comparison across modules
Forecasting baselines are Seasonal Naive/ARIMA/SARIMA/LSTM in F1; sell-store policies are SS baseline table; warehouse allocation methods are W4; routing methods are R2. No single composite ranking is justified because units/objectives differ and decision/route samples are small.

## 17. Software Validation
The project test suite was rerun for this report: 75 passed, 0 failed, 0 skipped; 14 warnings, primarily existing statsmodels convergence/starting-parameter and Keras/NumPy warnings. Routing audit independently recomputed 36 distances/costs and all 252 sensitivity rows; protected upstream files were SHA-256 checked unchanged across deterministic routing reruns.

## 18. Data Leakage and Validity
Forecast evaluation uses chronological rolling-origin folds and valid out-of-sample predictions. Sell/store actions are generated without future actual prices; actuals are used only post hoc for retrospective agreement/regret. Warehouse/routing modes consume saved artifacts without refitting models. Routing cannot establish actual route validity because its origin is synthetic. DM tests are underpowered with three paired origins. These are software/data-flow validations, not evidence of causal farmer outcomes.

## 19. Assumption Audit
| phase | parameter | value | classification | unit/provenance |
| --- | --- | --- | --- | --- |
| sell_store | scenario_quantity_quintal | 1.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | transport_cost_inr | 0.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | storage_rate_inr_per_kg_per_month | {"Rice": 0.3, "Onion": 0.55, "Tomato": 0.6} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | spoilage_rate_per_holding_decision | {"Rice": 0.01, "Onion": 0.08, "Tomato": 0.15} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | storage_duration_months_per_forecast_quarter | 3.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | sensitivity | {"storage_cost_multipliers": [0.5, 1.0, 1.5, 2.0], "spoilage_rates": [0.0, 0.02, 0.05, 0.1], "future_price_multipliers": [0.9, 1.0, 1.1], "storage_duration_months": [3, 6, 9, 12]} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| sell_store | provenance | {"quantity": "Scenario quantity, not observed farmer quantity; set to 1 quintal for scale-normalized simulations.", "storage_rates": "Retained from legacy decision_support.py constants and interpreted as scenario INR/kg/month; not measured farmer or warehouse invoices.", "spoilage_rates": "Retained from legacy decision_support.py constants and applied once as total loss over the evaluated holding decision; temporal calibration is unavailable.", "transport_cost": "Zero because the retrospective forecast artifact does not contain a validated route-specific transport quote; zero is a scenario assumption, not an observed cost.", "duration": "Forecast horizon quarters converted to months using three months per quarter; scenario duration only."} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | capacity_source_unit | metric_tonne | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | capacity_target_unit | quintal | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | quintals_per_metric_tonne | 10.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | storage_rate_currency | INR | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | storage_rate_source_unit | per_metric_tonne | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | storage_rate_time_unit | month | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | storage_rate_interpretation | Configurable assumption: Storage_Cost_per_MT is treated as INR per metric tonne per month because the source file does not state currency or billing period. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | transport_rate_inr_per_km_per_metric_tonne | 5.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | transport_rate_interpretation | Scenario assumption retained from routing.compute_transport_cost default; not an observed carrier quote. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | transport_distance_method | haversine_straight_line_from_warehouse_coordinate_centroid | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | origin_override_latitude | None | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | origin_override_longitude | None | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | origin_interpretation | No farmer origins are available. Unless both overrides are set, use the arithmetic centroid of warehouse coordinates as a synthetic reference origin; resulting distances are straight-line proxies, not road distances or farmer routes. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | unallocated_penalty_inr_per_quintal | 1000000.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | unallocated_penalty_interpretation | Computational feasibility penalty only, not included in reported storage-plus-transport total cost and not an observed economic loss. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| warehouse | sensitivity | {"storage_cost_multipliers": [0.5, 1.0, 1.5, 2.0], "transport_cost_multipliers": [0.5, 1.0, 1.5, 2.0], "available_quantity_multipliers": [0.5, 1.0, 1.5]} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | routing_problem_class | scenario-based single-leg reference-origin-to-warehouse transport evaluation | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | not_a_vrp | True | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | origin_method | warehouse coordinate centroid from warehouse_research_assumptions.json | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | origin_is_farmer_location | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | destination_source | warehouse_id joined to supplied warehouse dataset coordinates | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | distance_method | Haversine straight-line distance | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | distance_unit | km | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | road_distance_available | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | osrm_enabled | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | osrm_reason | The route origin is a synthetic warehouse centroid, not an observed farmer/customer origin; the evaluator will not request road routes for synthetic coordinates. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | transport_rate_inr_per_km_per_metric_tonne | 5.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | transport_rate_provenance | Scenario assumption inherited from routing.compute_transport_cost default; not an observed carrier quote. | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | quintals_per_metric_tonne | 10.0 | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | vehicle_fleet_available | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | vehicle_capacity_available | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | travel_time_reported | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | time_windows_available | False | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |
| routing | sensitivity | {"transport_cost_multipliers": [0.5, 1.0, 1.5, 2.0], "available_quantity_multipliers": [0.5, 1.0, 1.5]} | Configured scenario assumption unless it names a saved artifact/structural conversion | See phase assumptions JSON and phase report |

## 20. Farmer Data and Required Documentation Before Submission
The file `farmer_crop_dataset (1).csv` contains 450 rows, 150 Farmer_ID values, 3 crops, yield per acre, and season. The repository does not document whether records are observed, synthetic, or expanded; collection date/period, district/village, sampling procedure, consent, anonymization, ethics review, and linkage to price/decision records are absent. `farmer_decision_history.csv` has 9 rows with 8 missing cells; SQLite history table has zero records. Do not describe these as verified farmer study outcomes. Before submission, document dataset provenance, sampling, collection period, informed consent/ethics, de-identification, missingness handling, and whether IDs/data are synthetic or real.

## 21. Limitations
- Quarterly price series are small (Rice/Onion 26; Tomato 24 contiguous observations) with only three validation folds.
- LSTM has 8–16 effective training sequences per fold; overfitting evidence is not statistically established, and no claim of global superiority is supported.
- DM comparisons are underpowered; native interval coverage is based on small samples.
- Storage/spoilage/duration/transport assumptions are scenario parameters without validated invoices or carrier quotes.
- Quantity is standardized to one quintal; not observed farmer inventory.
- Warehouse provenance and storage billing currency/period are unverified.
- Routing uses synthetic-centroid Haversine distances, not road distances; no actual origin, destination demand, fleet, capacity, time-window, or route logs exist.
- No direct farmer welfare, profit, loss-reduction, or causal impact measurement exists.

## 22. What the System Actually Contributes
ADIS is a SaaS-based Agricultural Decision Support / Decision Intelligence platform prototype that integrates crop-price forecasting, economic sell/store evaluation, warehouse allocation, and transport-cost scenario analysis. It provides actionable decision-support outputs while farmers remain the final decision makers. The current evidence demonstrates implementation and scenario evaluation under stated assumptions, not guaranteed profit increases or real-world operational optimization.

## 23. What Has Been Successfully Addressed
Leakage-safe rolling-origin validation and metric separation; native ARIMA/SARIMA intervals and diagnostics; valid-fold model selection; explicit sell/store economics and unit assumptions; cost-minimizing warehouse allocation with compatibility/capacity constraints; independent route/cost/sensitivity verification; modular research runners; complete automated regression coverage.

## 24. Remaining Work Before Manuscript Submission
Verify data provenance and licenses; obtain real farmer locations/quantities/consent documentation; validate warehouse capacities, storage tariff currency/period and operational status; obtain carrier quotes or route logs and vehicle/fleet data; extend temporal validation with more origins; evaluate DM with sufficient paired forecasts; establish external test and uncertainty calibration; document deployment/security/SaaS evaluation separately from research results.

## 25. Final Research Contribution
The current ADIS implementation demonstrates an auditable research pipeline integrating crop-wise forecasting, retrospective economic decision simulation, warehouse cost allocation, and a scenario-based transport proxy. It does not establish real-world farmer profit improvement, causal benefit, a validated CVRP, or universal model superiority.

## 26. Complete Results Tables and Traceability
Detailed tables are generated as CSV artifacts: F1–F4, SS1–SS6, W1–W6, R1–R3, and E2E1–E2E3. Source file names, units, missingness, and provenance classifications are listed in `dataset_inventory.csv`.

## 27. Complete Figure List
- `report_forecast_model_comparison.png`
- `report_forecast_horizon_rmse.png`
- `report_forecast_error_comparison.png`
- `report_interval_coverage.png`
- `report_actual_vs_predicted_rice.png`
- `report_actual_vs_predicted_onion.png`
- `report_actual_vs_predicted_tomato.png`
- `report_sell_store_distribution.png`
- `report_sell_store_regret.png`
- `report_sell_store_baselines.png`
- `report_sell_storage_sensitivity.png`
- `report_sell_spoilage_sensitivity.png`
- `report_warehouse_cost_comparison.png`
- `report_warehouse_cost_components.png`
- `report_warehouse_utilization.png`
- `report_warehouse_storage_sensitivity.png`
- `report_warehouse_transport_sensitivity.png`
- `report_routing_distance_comparison.png`
- `report_routing_cost_comparison.png`
- `report_routing_baselines.png`
- `report_routing_sensitivity.png`
- `report_routing_quantity_sensitivity.png`
- `report_end_to_end_cost.png`

## 28. Reproducibility Information
Validated artifacts/configs: `experiment_config.json`, `sell_store_assumptions.json`, `warehouse_research_assumptions.json`, `routing_research_assumptions.json`. The phase runners use saved upstream artifacts for downstream scenarios. This completion also writes `generate_adis_performance_report.py`; run it with the project virtual environment to rebuild tables, figures, Markdown, and standalone offline HTML. `python -m pytest -q` produced 75 passed on the completed research code.

## 29. Faculty Summary (One Page)
**A. Problem:** integrate crop forecasts with decision-support, storage allocation, and transport-cost analysis.

**B. Forecast candidates:** Seasonal Naive, ARIMA, SARIMA, LSTM using three rolling-origin folds and four-quarter horizons.

**C. RMSE-selected candidates:** Rice SARIMA, Onion LSTM, Tomato SARIMA; selections are procedure-specific and not superiority claims.

**D. Forecast performance:** detailed values and horizons in F1–F3; price unit INR/quintal. DM tests underpowered; intervals only ARIMA/SARIMA.

**E. Sell/store:** 12 selected-model retrospective decisions per crop; agreement/regret in SS tables.

**F. Warehouse:** 36 independent 1-quintal scenarios; CBC Optimal 36/36; full quantity allocated, zero violations; assumption-based scenario costs.

**G. Routing:** 36 Haversine proxy legs, all feasible; not road routing or CVRP.

**H. Integration:** 36 end-to-end scenario rows with metrics linked to saved upstream artifacts.

**I. Software validation:** 75 passed, 0 failed, 14 warnings.

**J. Main limitations:** small data/folds, unverified provenance, assumptions for economic costs, absent farmer origins/fleet/market demand, no causal outcome data.

**K. Claim supported:** a working, auditable decision-support research prototype and feasible scenario allocations under configured assumptions.

**L. Claims not supported:** guaranteed profit increase, farmer welfare improvement, actual road-route optimality, causal loss reduction, universal model superiority.
