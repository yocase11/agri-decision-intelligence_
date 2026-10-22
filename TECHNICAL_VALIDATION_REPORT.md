# Technical Validation Report

## 1. Forecast-error sensitivity

SUPPORTED RESULT: The existing forecast-error sensitivity workflow recomputes the deterministic propagation of absolute forecast error through the sell/store decision rule using the saved decision rows.

| crop | model | horizon | number_of_decisions | mean_propagated_value_error_inr | median_propagated_value_error_inr | decision_flip_rate_percentage | mean_regret_inr | mean_decision_value_error_inr | mean_absolute_forecast_error_inr | price_unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | 3 | 936.9220 | 384.9534 | 50.0000 | 31.9648 | 0.0000 | 1,018.3935 | INR per quintal |
| Onion | arima | 2 | 3 | 934.1973 | 377.4281 | 16.6667 | 0.0000 | 0.0000 | 1,015.4318 | INR per quintal |
| Onion | arima | 3 | 3 | 1,204.2018 | 1,492.1467 | 33.3333 | 454.4593 | 0.0000 | 1,308.9150 | INR per quintal |
| Onion | arima | 4 | 3 | 1,418.9237 | 1,739.5776 | 33.3333 | 549.1935 | 0.0000 | 1,542.3083 | INR per quintal |
| Onion | lstm | 1 | 3 | 429.1759 | 437.2985 | 16.6667 | 31.9648 | 0.0000 | 466.4956 | INR per quintal |
| Onion | lstm | 2 | 3 | 336.6818 | 426.8582 | 0.0000 | 0.0000 | 0.0000 | 365.9585 | INR per quintal |
| Onion | lstm | 3 | 3 | 902.7454 | 325.6830 | 16.6667 | 454.4593 | 0.0000 | 981.2450 | INR per quintal |
| Onion | lstm | 4 | 3 | 1,153.1490 | 454.9985 | 16.6667 | 549.1935 | 0.0000 | 1,253.4229 | INR per quintal |
| Onion | sarima | 1 | 3 | 1,067.5233 | 584.2823 | 33.3333 | 31.9648 | 0.0000 | 1,160.3514 | INR per quintal |
| Onion | sarima | 2 | 3 | 1,103.3630 | 887.2983 | 16.6667 | 0.0000 | 0.0000 | 1,199.3076 | INR per quintal |
| Onion | sarima | 3 | 3 | 1,596.4466 | 1,990.3901 | 33.3333 | 454.4593 | 0.0000 | 1,735.2681 | INR per quintal |
| Onion | sarima | 4 | 3 | 1,723.0850 | 2,390.8959 | 33.3333 | 549.1935 | 0.0000 | 1,872.9185 | INR per quintal |
| Onion | seasonal_naive | 1 | 3 | 805.5895 | 907.4603 | 33.3333 | 251.8156 | 385.9116 | 875.6407 | INR per quintal |
| Onion | seasonal_naive | 2 | 3 | 295.7457 | 172.0608 | 0.0000 | 0.0000 | 0.0000 | 321.4627 | INR per quintal |
| Onion | seasonal_naive | 3 | 3 | 1,239.5469 | 1,251.1247 | 16.6667 | 454.4593 | 0.0000 | 1,347.3336 | INR per quintal |
| Onion | seasonal_naive | 4 | 3 | 1,487.5461 | 1,899.2015 | 33.3333 | 549.1935 | 0.0000 | 1,616.8980 | INR per quintal |
| Rice | arima | 1 | 3 | 21.3629 | 21.3518 | 0.0000 | 0.0000 | 0.0000 | 21.5787 | INR per quintal |
| Rice | arima | 2 | 3 | 56.3434 | 49.7591 | 0.0000 | 0.0000 | 0.0000 | 56.9126 | INR per quintal |
| Rice | arima | 3 | 3 | 123.1859 | 59.9949 | 0.0000 | 0.0000 | 0.0000 | 124.4302 | INR per quintal |
| Rice | arima | 4 | 3 | 199.3791 | 113.0458 | 16.6667 | 6.0995 | 0.0000 | 201.3930 | INR per quintal |
| Rice | lstm | 1 | 3 | 420.7914 | 475.6554 | 0.0000 | 0.0000 | 0.0000 | 425.0418 | INR per quintal |
| Rice | lstm | 2 | 3 | 491.8153 | 533.4682 | 0.0000 | 0.0000 | 0.0000 | 496.7831 | INR per quintal |
| Rice | lstm | 3 | 3 | 618.1427 | 622.7562 | 0.0000 | 0.0000 | 0.0000 | 624.3866 | INR per quintal |
| Rice | lstm | 4 | 3 | 705.6044 | 718.6168 | 16.6667 | 6.0995 | 0.0000 | 712.7317 | INR per quintal |
| Rice | sarima | 1 | 3 | 43.8732 | 27.3557 | 16.6667 | 29.0811 | 30.7600 | 44.3164 | INR per quintal |
| Rice | sarima | 2 | 3 | 21.6766 | 20.6068 | 0.0000 | 0.0000 | 0.0000 | 21.8956 | INR per quintal |
| Rice | sarima | 3 | 3 | 99.8615 | 64.3337 | 0.0000 | 0.0000 | 0.0000 | 100.8702 | INR per quintal |
| Rice | sarima | 4 | 3 | 172.4775 | 160.9759 | 50.0000 | 6.0995 | 0.0000 | 174.2197 | INR per quintal |
| Rice | seasonal_naive | 1 | 3 | 222.5272 | 202.2626 | 0.0000 | 0.0000 | 0.0000 | 224.7750 | INR per quintal |
| Rice | seasonal_naive | 2 | 3 | 234.4296 | 181.9026 | 0.0000 | 0.0000 | 0.0000 | 236.7975 | INR per quintal |
| Rice | seasonal_naive | 3 | 3 | 252.4275 | 292.3488 | 0.0000 | 0.0000 | 0.0000 | 254.9772 | INR per quintal |
| Rice | seasonal_naive | 4 | 3 | 236.7023 | 234.4342 | 16.6667 | 6.0995 | 0.0000 | 239.0932 | INR per quintal |
| Tomato | arima | 1 | 3 | 1,086.8840 | 1,145.1443 | 50.0000 | 554.0259 | 0.0000 | 1,278.6870 | INR per quintal |
| Tomato | arima | 2 | 3 | 535.4201 | 342.4319 | 16.6667 | 98.0476 | 0.0000 | 629.9060 | INR per quintal |
| Tomato | arima | 3 | 3 | 151.9292 | 176.5852 | 0.0000 | 0.0000 | 0.0000 | 178.7402 | INR per quintal |
| Tomato | arima | 4 | 3 | 173.7082 | 118.2789 | 0.0000 | 0.0000 | 0.0000 | 204.3626 | INR per quintal |
| Tomato | lstm | 1 | 3 | 1,159.2589 | 1,193.2681 | 50.0000 | 554.0259 | 0.0000 | 1,363.8340 | INR per quintal |
| Tomato | lstm | 2 | 3 | 700.0261 | 400.9795 | 16.6667 | 98.0476 | 0.0000 | 823.5602 | INR per quintal |
| Tomato | lstm | 3 | 3 | 94.2785 | 64.5763 | 0.0000 | 0.0000 | 0.0000 | 110.9159 | INR per quintal |
| Tomato | lstm | 4 | 3 | 269.3177 | 109.1232 | 0.0000 | 0.0000 | 0.0000 | 316.8443 | INR per quintal |
| Tomato | sarima | 1 | 3 | 478.7420 | 603.0876 | 33.3333 | 116.4115 | 201.0292 | 563.2259 | INR per quintal |
| Tomato | sarima | 2 | 3 | 525.5122 | 408.4299 | 33.3333 | 106.0355 | 136.1433 | 618.2497 | INR per quintal |
| Tomato | sarima | 3 | 3 | 81.3804 | 71.1023 | 0.0000 | 0.0000 | 0.0000 | 95.7416 | INR per quintal |
| Tomato | sarima | 4 | 3 | 317.0592 | 249.4152 | 0.0000 | 0.0000 | 0.0000 | 373.0109 | INR per quintal |
| Tomato | seasonal_naive | 1 | 3 | 527.7660 | 513.7502 | 33.3333 | 116.4115 | 155.8918 | 620.9011 | INR per quintal |
| Tomato | seasonal_naive | 2 | 3 | 714.2371 | 820.4017 | 33.3333 | 106.0355 | 273.4672 | 840.2789 | INR per quintal |
| Tomato | seasonal_naive | 3 | 3 | 159.5397 | 104.1148 | 0.0000 | 0.0000 | 0.0000 | 187.6938 | INR per quintal |
| Tomato | seasonal_naive | 4 | 3 | 270.4688 | 225.5577 | 0.0000 | 0.0000 | 0.0000 | 318.1986 | INR per quintal |

SCENARIO ASSUMPTION: The propagated value error is a deterministic scenario sensitivity calculation, not a calibrated statistical uncertainty model.

LIMITATION: Forecast errors do not imply an empirical probability distribution for farmer outcomes.

## 2. Prediction-interval decision robustness

SUPPORTED RESULT: Native 95% ARIMA and SARIMA intervals are evaluated under the existing sell/store decision rule. Only valid rows with finite native interval bounds are eligible; LSTM and Seasonal Naive are excluded. Raw bounds are preserved alongside decision-evaluation bounds clamped at zero, matching the decision function nonnegative-price constraint.

| crop | model | horizon | number_of_predictions | decision_stability_rate | decision_sensitive_rate | robust_sell_decisions | robust_store_decisions | sensitive_decisions | mean_value_range_inr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | arima | 1 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 578.1400 |
| Onion | arima | 2 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 962.9634 |
| Onion | arima | 3 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 1,044.9269 |
| Onion | arima | 4 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 1,147.2354 |
| Onion | sarima | 1 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 455.3323 |
| Onion | sarima | 2 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 183.0997 |
| Onion | sarima | 3 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 657.9928 |
| Onion | sarima | 4 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 1,249.6443 |
| Rice | arima | 1 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 64.4495 |
| Rice | arima | 2 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 67.9366 |
| Rice | arima | 3 | 3 | 33.3333 | 66.6667 | 1 | 0 | 2 | 71.7584 |
| Rice | arima | 4 | 3 | 33.3333 | 66.6667 | 1 | 0 | 2 | 74.8344 |
| Rice | sarima | 1 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 117.7914 |
| Rice | sarima | 2 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 117.4370 |
| Rice | sarima | 3 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 162.0454 |
| Rice | sarima | 4 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 194.5184 |
| Tomato | arima | 1 | 3 | 33.3333 | 66.6667 | 1 | 0 | 2 | 214.5528 |
| Tomato | arima | 2 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 185.6563 |
| Tomato | arima | 3 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 133.8376 |
| Tomato | arima | 4 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 76.2001 |
| Tomato | sarima | 1 | 3 | 0.0000 | 100.0000 | 0 | 0 | 3 | 790.2362 |
| Tomato | sarima | 2 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 417.7895 |
| Tomato | sarima | 3 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 116.2723 |
| Tomato | sarima | 4 | 3 | 66.6667 | 33.3333 | 2 | 0 | 1 | 125.8132 |

SCENARIO ASSUMPTION: The interval-based decision classification is a deterministic robustness check over the saved interval scenarios and does not imply probabilistic forecast validity for non-native models.

LIMITATION: The current data support only the existing three rolling-origin windows and thus limited interval coverage.

## 3. End-to-end parameter sensitivity

SUPPORTED RESULT: One-factor-at-a-time sell/store sensitivities are computed for forecast error, storage cost, spoilage rate, transport cost, and quantity. Warehouse/routing cost columns are populated only when the same selected-model scenario and parameter perturbation exist in the saved layer sensitivity artifacts; they are not carried forward from baseline values when the layer was not re-evaluated.

| parameter | parameter_value | parameter_unit | number_of_scenarios | decision_flip_rate | mean_regret_inr | mean_storage_cost_inr | mean_warehouse_total_cost_inr | mean_transport_proxy_cost_inr | mean_total_scenario_cost_inr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forecast_error | -0.2000 | forecast_fraction | 144 | 1.3889 | 127.6619 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | -0.1500 | forecast_fraction | 144 | 0.6944 | 127.8283 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | -0.1000 | forecast_fraction | 144 | 0.6944 | 127.8283 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | -0.0500 | forecast_fraction | 144 | 0.6944 | 127.8283 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | 0.0000 | forecast_fraction | 144 | 0.0000 | 128.4342 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | 0.0500 | forecast_fraction | 144 | 6.9444 | 136.5287 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | 0.1000 | forecast_fraction | 144 | 13.1944 | 165.6584 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | 0.1500 | forecast_fraction | 144 | 22.2222 | 195.2560 | 362.5000 | Not Available | Not Available | Not Available |
| forecast_error | 0.2000 | forecast_fraction | 144 | 27.0833 | 188.5304 | 362.5000 | Not Available | Not Available | Not Available |
| quantity | 0.5000 | multiplier | 144 | 0.0000 | 64.2171 | 181.2500 | 10.2612 | 9.5000 | 19.7612 |
| quantity | 1.0000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 20.5224 | 18.9999 | 39.5224 |
| quantity | 1.5000 | multiplier | 144 | 0.0000 | 192.6513 | 543.7500 | 30.7837 | 28.4999 | 59.2836 |
| spoilage | 0.0000 | spoilage_rate | 144 | 2.7778 | 190.8723 | 362.5000 | Not Available | Not Available | Not Available |
| spoilage | 0.0200 | spoilage_rate | 144 | 3.4722 | 179.7672 | 362.5000 | Not Available | Not Available | Not Available |
| spoilage | 0.0500 | spoilage_rate | 144 | 0.6944 | 163.0517 | 362.5000 | Not Available | Not Available | Not Available |
| spoilage | 0.1000 | spoilage_rate | 144 | 0.6944 | 135.7901 | 362.5000 | Not Available | Not Available | Not Available |
| storage_cost | 0.5000 | multiplier | 144 | 3.4722 | 187.0905 | 181.2500 | 19.7178 | Not Available | Not Available |
| storage_cost | 1.0000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 20.5224 | Not Available | Not Available |
| storage_cost | 1.5000 | multiplier | 144 | 0.6944 | 103.1329 | 543.7500 | 21.2837 | Not Available | Not Available |
| storage_cost | 2.0000 | multiplier | 144 | 0.6944 | 82.8714 | 725.0000 | 22.0348 | Not Available | Not Available |
| transport_cost | 0.5000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 11.0174 | 9.5000 | 20.5174 |
| transport_cost | 1.0000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 20.5224 | 18.9999 | 39.5224 |
| transport_cost | 1.5000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 29.9952 | 28.4999 | 58.4951 |
| transport_cost | 2.0000 | multiplier | 144 | 0.0000 | 128.4342 | 362.5000 | 39.4356 | 37.9999 | 77.4355 |

SCENARIO ASSUMPTION: Forecast-error fractions, storage-cost/transport/quantity multipliers, and spoilage-rate values are configured deterministic scenarios, not empirical observations or probability distributions.

LIMITATION: Missing layer values are intentional and marked by per-layer status fields: most decision-model rows are not selected-model warehouse/routing scenarios, and some parameter-layer combinations were not evaluated. No causal claim about farmer profit or real-world transport optimization is supported.

## 4. Formula/code/result consistency

SUPPORTED RESULT: Material mismatches = 0; all formula checks pass = True

SCENARIO ASSUMPTION: The formulas are evaluated against the saved decision artifact under the current scenario definitions.

LIMITATION: This is a code-to-artifact consistency check, not a causal validation of real-world operations.

## 5. Rolling-origin feasibility

SUPPORTED RESULT: Maximum feasible rolling-origin windows observed in the real data = 3; configured windows = 3

SCENARIO ASSUMPTION: The configured design is the maximum non-overlapping validation setup supported by the available quarterly series.

LIMITATION: No additional rolling-origin windows are created beyond the actual series support.

## 6. Module ablation

| stage | comparison_scope | available_metrics | unavailable_metrics | average_forecast_rmse | average_decision_agreement_percentage | average_regret_inr | average_warehouse_total_cost_inr | average_routing_transport_cost_inr | average_total_cost_inr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Forecasting only | DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION | forecast_RMSE; forecast_MAE; forecast_R2 | decision_agreement_percentage; mean_regret_inr; mean_realized_net_value_inr; warehouse_cost_metrics; routing_metrics; final_total_cost_inr | 502.4440 | Not Available | Not Available | Not Available | Not Available | Not Available |
| B. Forecasting + Sell/Store | DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION | decision_agreement_percentage; mean_regret_inr; mean_realized_net_value_inr | forecast_metrics; warehouse_cost_metrics; routing_metrics; final_total_cost_inr | Not Available | 75.0000 | 107.7704 | Not Available | Not Available | Not Available |
| C. Forecasting + Sell/Store + Warehouse | DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION | warehouse_total_cost_inr; warehouse_storage_cost_inr; warehouse_transport_cost_inr | forecast_metrics; decision_metrics; routing_metrics; final_total_cost_inr | Not Available | Not Available | Not Available | 20.5224 | Not Available | Not Available |
| D. Full implemented ADIS pipeline | DESCRIPTIVE_STAGE_OUTPUT; NOT_CAUSAL_ABLATION | warehouse_total_cost_inr; routing_transport_cost_inr; routing_distance_km; final_total_cost_inr | forecast_metrics; decision_metrics | Not Available | Not Available | Not Available | 20.5224 | 18.9999 | 39.5224 |

SUPPORTED RESULT: The stage-wise table contains only metrics that are present for each stage, averaged across all saved selected-model origin-by-horizon scenarios per crop/model. `available_metrics` and `unavailable_metrics` explicitly identify stage-specific missing cells.

SCENARIO ASSUMPTION: This is descriptive stage-wise reporting, not an intervention that disables modules; therefore it is not a causal ablation experiment.

LIMITATION: Different stages use different objective functions and units; they should not be interpreted as a direct performance ranking across all modules.

## 7. Reproducibility

SUPPORTED RESULT: Reproducibility notes are available in [REPRODUCIBILITY_REPORT.md](REPRODUCIBILITY_REPORT.md).

SCENARIO ASSUMPTION: Only the repository-defined implementation, assumptions, and saved artifacts are documented here.

LIMITATION: Missing provenance for source datasets and carrier tariffs remains explicitly documented as not available in the current implementation.

## 8. Test validation

SUPPORTED RESULT: The full repository test suite is executed under the project virtual environment and remains passing.

SCENARIO ASSUMPTION: The test suite validates the implemented pipeline and the new structured robustness checks.

LIMITATION: Warnings are retained from the underlying pipeline libraries and are not evidence of model superiority.

## 9. Explicit limitations

- No causal farmer-profit improvement claims are supported.
- Routing remains a Haversine scenario/reference-origin proxy and not a real CVRP.
- No probabilistic uncertainty is claimed where the implementation provides no native interval.
- No real-world operational cost or tariff validation is available from the current repository artifacts.
- The analysis is restricted to the supported, documented, and reproducible implementation.
