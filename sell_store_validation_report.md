# Sell-vs-Store Retrospective Validation Report

## Decision Model
For quantity Q in quintals, current price P0 and future price P1 in INR/quintal:
- Sell now = Q x P0.
- Effective stored quantity = Q x (1 - spoilage_rate).
- Storage cost = Q x 100 kg/quintal x storage_rate (INR/kg/month) x duration (months).
- Store value = effective quantity x P1 - storage cost - total transport cost.
- Incremental store value = store value - sell-now value.
- Choose `store` only when store value is strictly greater; ties choose `sell`.

The decision function accepts current price, forecast point price, quantity, duration, storage rate, spoilage assumption, and transport cost. It has no future-actual-price parameter.

## Dataset and Units
- Observed price source: `price dataset (1).csv`, field `Price_INR_per_Quintal` labeled INR per quintal.
- Validated forecast source: `forecast_predictions.csv` from the Phase 2 rolling-origin validation. Failed rows are excluded.
- Quantity in this simulation: 1.0 quintal per decision. This is a scale-normalized scenario, not observed farmer quantity.
- All revenue, cost, value, and regret outputs are INR. All prices are INR/quintal and quantities are quintals.
- Evaluated crop/date coverage:

```text
  crop  number_of_decisions date_start   date_end
 Onion                   48 2011-12-31 2014-12-31
  Rice                   48 2011-12-31 2014-12-31
Tomato                   48 2012-06-30 2015-06-30
```

## OBSERVED DATA
Historical current prices at each decision cutoff and future actual prices come from the labeled price observations represented in the Phase 2 forecast file. Rolling-origin forecasts, training cutoffs, horizons, and validated selected models come from Phase 2 artifacts. No farm acreage or farmer-specific market quantity is available for this simulation.

## ASSUMPTIONS
```json
{
  "scenario_quantity_quintal": 1.0,
  "transport_cost_inr": 0.0,
  "storage_rate_inr_per_kg_per_month": {
    "Rice": 0.3,
    "Onion": 0.55,
    "Tomato": 0.6
  },
  "spoilage_rate_per_holding_decision": {
    "Rice": 0.01,
    "Onion": 0.08,
    "Tomato": 0.15
  },
  "storage_duration_months_per_forecast_quarter": 3.0,
  "sensitivity": {
    "storage_cost_multipliers": [
      0.5,
      1.0,
      1.5,
      2.0
    ],
    "spoilage_rates": [
      0.0,
      0.02,
      0.05,
      0.1
    ],
    "future_price_multipliers": [
      0.9,
      1.0,
      1.1
    ],
    "storage_duration_months": [
      3,
      6,
      9,
      12
    ]
  },
  "provenance": {
    "quantity": "Scenario quantity, not observed farmer quantity; set to 1 quintal for scale-normalized simulations.",
    "storage_rates": "Retained from legacy decision_support.py constants and interpreted as scenario INR/kg/month; not measured farmer or warehouse invoices.",
    "spoilage_rates": "Retained from legacy decision_support.py constants and applied once as total loss over the evaluated holding decision; temporal calibration is unavailable.",
    "transport_cost": "Zero because the retrospective forecast artifact does not contain a validated route-specific transport quote; zero is a scenario assumption, not an observed cost.",
    "duration": "Forecast horizon quarters converted to months using three months per quarter; scenario duration only."
  }
}
```
The storage rate values and crop spoilage values are retained from legacy code solely as configurable scenario assumptions. Their source does not document empirical calibration, and spoilage is applied once over the full holding decision. Transport cost is zero because no validated route-specific retrospective quote is present. None of these values are presented as observed farmer costs or outcomes.

## SIMULATED VARIABLES
The one-quintal quantity, storage duration, storage/spoilage costs, scenario multipliers, baseline actions, and resulting economic values are simulations. Storage duration is three months per forecast quarter for the base calculation.

## FORECAST VALUES AND UNCERTAINTY
The evaluator consumes out-of-sample forecasts and model identifiers from Phase 2; it does not retrain. The decision uses the forecast point value. Where Phase 2 native 95% ARIMA/SARIMA bounds are present, availability is marked; LSTM/Seasonal Naive have no interval and remain point-forecast-only. No heuristic interval is created. Price-multiplier sensitivity is labeled scenario analysis, not a prediction interval.

## Leakage Prevention and Historical Protocol
For each crop/model/fold/horizon, the decision date is the end of the training sample and must be strictly earlier than the future actual date. Current price is looked up only at that training cutoff. The forecast-based decision function never receives the future actual. Actual future price is passed only to a separate post-decision scoring step to calculate the retrospective actual-optimal decision, agreement, and regret. This is a historical decision simulation, not a causal farmer-benefit evaluation.

## Baselines
- Always Sell: choose sell at every decision date.
- Always Store: choose store at every decision date.
- Seasonal Naive: use the seasonal-naive out-of-sample Phase 2 forecast in the economic decision equation.
- No current heuristic baseline is included because its forecast clipping, crop multipliers, inconsistent units, and thresholds are undocumented and it is not an admissible research comparator.

Baseline results aggregated over crop/horizon rows:

```text
                          N  agreement  mean_realized_net_value_inr  mean_regret_inr
model                                                                               
always_sell              36   0.777778                  1996.701460       141.149215
always_store             36   0.222222                  1513.362314       624.488361
seasonal_naive_forecast  36   0.750000                  2014.182776       123.667900
```

## Forecast-Error Sensitivity and Decision Agreement
The comparison is between the forecast-based action and the post-hoc action that would maximize the same simulated net value using the realized future price. False-store means forecast action was store while the hindsight action is sell; false-sell is the reverse. Regret is best hindsight net value minus realized value of the forecast-selected action. Mean absolute decision-value error compares forecast and realized economic value for the action actually selected.

```text
  crop          model  horizon  number_of_decisions  decision_agreement_percentage  decision_disagreement_percentage  false_store_rate_percentage  false_sell_rate_percentage  average_economic_regret_inr  mean_absolute_decision_value_error_inr  mean_absolute_forecast_error_inr      price_unit
 Onion          arima        1                    3                      66.666667                         33.333333                     0.000000                   33.333333                    31.964808                                0.000000                       1018.393492 INR per quintal
 Onion          arima        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                       1015.431840 INR per quintal
 Onion          arima        3                    3                      66.666667                         33.333333                     0.000000                   33.333333                   454.459287                                0.000000                       1308.915029 INR per quintal
 Onion          arima        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                   549.193463                                0.000000                       1542.308340 INR per quintal
 Onion           lstm        1                    3                      66.666667                         33.333333                     0.000000                   33.333333                    31.964808                                0.000000                        466.495553 INR per quintal
 Onion           lstm        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        365.958510 INR per quintal
 Onion           lstm        3                    3                      66.666667                         33.333333                     0.000000                   33.333333                   454.459287                                0.000000                        981.245026 INR per quintal
 Onion           lstm        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                   549.193463                                0.000000                       1253.422866 INR per quintal
 Onion         sarima        1                    3                      66.666667                         33.333333                     0.000000                   33.333333                    31.964808                                0.000000                       1160.351368 INR per quintal
 Onion         sarima        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                       1199.307628 INR per quintal
 Onion         sarima        3                    3                      66.666667                         33.333333                     0.000000                   33.333333                   454.459287                                0.000000                       1735.268073 INR per quintal
 Onion         sarima        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                   549.193463                                0.000000                       1872.918466 INR per quintal
 Onion seasonal_naive        1                    3                      33.333333                         66.666667                    33.333333                   33.333333                   251.815551                              385.911650                        875.640707 INR per quintal
 Onion seasonal_naive        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        321.462724 INR per quintal
 Onion seasonal_naive        3                    3                      66.666667                         33.333333                     0.000000                   33.333333                   454.459287                                0.000000                       1347.333571 INR per quintal
 Onion seasonal_naive        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                   549.193463                                0.000000                       1616.897966 INR per quintal
  Rice          arima        1                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                         21.578733 INR per quintal
  Rice          arima        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                         56.912555 INR per quintal
  Rice          arima        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        124.430232 INR per quintal
  Rice          arima        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                     6.099525                                0.000000                        201.393025 INR per quintal
  Rice           lstm        1                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        425.041771 INR per quintal
  Rice           lstm        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        496.783112 INR per quintal
  Rice           lstm        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        624.386552 INR per quintal
  Rice           lstm        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                     6.099525                                0.000000                        712.731695 INR per quintal
  Rice         sarima        1                    3                      66.666667                         33.333333                    33.333333                    0.000000                    29.081101                               30.759988                         44.316377 INR per quintal
  Rice         sarima        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                         21.895577 INR per quintal
  Rice         sarima        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        100.870186 INR per quintal
  Rice         sarima        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                     6.099525                                0.000000                        174.219742 INR per quintal
  Rice seasonal_naive        1                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        224.774951 INR per quintal
  Rice seasonal_naive        2                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        236.797541 INR per quintal
  Rice seasonal_naive        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        254.977236 INR per quintal
  Rice seasonal_naive        4                    3                      66.666667                         33.333333                     0.000000                   33.333333                     6.099525                                0.000000                        239.093248 INR per quintal
Tomato          arima        1                    3                       0.000000                        100.000000                     0.000000                  100.000000                   554.025850                                0.000000                       1278.687014 INR per quintal
Tomato          arima        2                    3                      66.666667                         33.333333                     0.000000                   33.333333                    98.047647                                0.000000                        629.905965 INR per quintal
Tomato          arima        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        178.740235 INR per quintal
Tomato          arima        4                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        204.362614 INR per quintal
Tomato           lstm        1                    3                       0.000000                        100.000000                     0.000000                  100.000000                   554.025850                                0.000000                       1363.833966 INR per quintal
Tomato           lstm        2                    3                      66.666667                         33.333333                     0.000000                   33.333333                    98.047647                                0.000000                        823.560151 INR per quintal
Tomato           lstm        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        110.915919 INR per quintal
Tomato           lstm        4                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        316.844308 INR per quintal
Tomato         sarima        1                    3                      33.333333                         66.666667                     0.000000                   66.666667                   116.411491                              201.029195                        563.225897 INR per quintal
Tomato         sarima        2                    3                      33.333333                         66.666667                    33.333333                   33.333333                   106.035478                              136.143310                        618.249704 INR per quintal
Tomato         sarima        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                         95.741642 INR per quintal
Tomato         sarima        4                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        373.010851 INR per quintal
Tomato seasonal_naive        1                    3                      33.333333                         66.666667                     0.000000                   66.666667                   116.411491                              155.891800                        620.901135 INR per quintal
Tomato seasonal_naive        2                    3                      33.333333                         66.666667                    33.333333                   33.333333                   106.035478                              273.467245                        840.278908 INR per quintal
Tomato seasonal_naive        3                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        187.693777 INR per quintal
Tomato seasonal_naive        4                    3                     100.000000                          0.000000                     0.000000                    0.000000                     0.000000                                0.000000                        318.198567 INR per quintal
```

Selected validated-model retrospective summaries:

- Rice / sarima: N=12, agreement=83.33%, mean regret=INR 8.80, interval availability=yes
- Onion / lstm: N=12, agreement=75.00%, mean regret=INR 258.90, interval availability=no (point forecast only)
- Tomato / sarima: N=12, agreement=66.67%, mean regret=INR 55.61, interval availability=yes

## Decision Summary
```text
  crop          model  horizon  number_of_decisions  sell_count  store_count  decision_agreement_percentage  false_store_percentage  false_sell_percentage  mean_sell_now_value_inr  mean_store_value_inr  mean_regret_inr  median_regret_inr      price_unit  mean_realized_net_value_inr
 Onion          arima        1                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1860.658160        31.964808           0.000000 INR per quintal                  2277.487938
 Onion          arima        2                    3           3            0                     100.000000                0.000000               0.000000              2277.487938           1738.637760         0.000000           0.000000 INR per quintal                  2277.487938
 Onion          arima        3                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1547.233135       454.459287           0.000000 INR per quintal                  2277.487938
 Onion          arima        4                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1397.495443       549.193463           0.000000 INR per quintal                  2277.487938
 Onion           lstm        1                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1081.843318        31.964808           0.000000 INR per quintal                  2277.487938
 Onion           lstm        2                    3           3            0                     100.000000                0.000000               0.000000              2277.487938            891.694912         0.000000           0.000000 INR per quintal                  2277.487938
 Onion           lstm        3                    3           3            0                      66.666667                0.000000              33.333333              2277.487938            718.579160       454.459287           0.000000 INR per quintal                  2277.487938
 Onion           lstm        4                    3           3            0                      66.666667                0.000000              33.333333              2277.487938            503.551670       549.193463           0.000000 INR per quintal                  2277.487938
 Onion         sarima        1                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1804.267247        31.964808           0.000000 INR per quintal                  2277.487938
 Onion         sarima        2                    3           3            0                     100.000000                0.000000               0.000000              2277.487938           1115.530881         0.000000           0.000000 INR per quintal                  2277.487938
 Onion         sarima        3                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1351.804710       454.459287           0.000000 INR per quintal                  2277.487938
 Onion         sarima        4                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1702.231714       549.193463           0.000000 INR per quintal                  2277.487938
 Onion seasonal_naive        1                    3           2            1                      33.333333               33.333333              33.333333              2277.487938           1326.881426       251.815551          95.894425 INR per quintal                  2057.637196
 Onion seasonal_naive        2                    3           3            0                     100.000000                0.000000               0.000000              2277.487938            704.647816         0.000000           0.000000 INR per quintal                  2277.487938
 Onion seasonal_naive        3                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1310.750221       454.459287           0.000000 INR per quintal                  2277.487938
 Onion seasonal_naive        4                    3           3            0                      66.666667                0.000000              33.333333              2277.487938           1435.288903       549.193463           0.000000 INR per quintal                  2277.487938
  Rice          arima        1                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           2073.315424         0.000000           0.000000 INR per quintal                  2155.919240
  Rice          arima        2                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           2011.097526         0.000000           0.000000 INR per quintal                  2155.919240
  Rice          arima        3                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1949.645175         0.000000           0.000000 INR per quintal                  2155.919240
  Rice          arima        4                    3           3            0                      66.666667                0.000000              33.333333              2155.919240           1887.047121         6.099525           0.000000 INR per quintal                  2155.919240
  Rice           lstm        1                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1658.320745         0.000000           0.000000 INR per quintal                  2155.919240
  Rice           lstm        2                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1542.452909         0.000000           0.000000 INR per quintal                  2155.919240
  Rice           lstm        3                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1425.615324         0.000000           0.000000 INR per quintal                  2155.919240
  Rice           lstm        4                    3           3            0                      66.666667                0.000000              33.333333              2155.919240           1305.457986         6.099525           0.000000 INR per quintal                  2155.919240
  Rice         sarima        1                    3           2            1                      66.666667               33.333333               0.000000              2155.919240           2114.995976        29.081101           0.000000 INR per quintal                  2126.838140
  Rice         sarima        2                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           2036.465216         0.000000           0.000000 INR per quintal                  2155.919240
  Rice         sarima        3                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           2023.461415         0.000000           0.000000 INR per quintal                  2155.919240
  Rice         sarima        4                    3           3            0                      66.666667                0.000000              33.333333              2155.919240           2007.989604         6.099525           0.000000 INR per quintal                  2155.919240
  Rice seasonal_naive        1                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1856.584896         0.000000           0.000000 INR per quintal                  2155.919240
  Rice seasonal_naive        2                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1799.838624         0.000000           0.000000 INR per quintal                  2155.919240
  Rice seasonal_naive        3                    3           3            0                     100.000000                0.000000               0.000000              2155.919240           1791.330546         0.000000           0.000000 INR per quintal                  2155.919240
  Rice seasonal_naive        4                    3           3            0                      66.666667                0.000000              33.333333              2155.919240           1774.360048         6.099525           0.000000 INR per quintal                  2155.919240
Tomato          arima        1                    3           3            0                       0.000000                0.000000             100.000000              1556.697202           1023.839091       554.025850         342.872376 INR per quintal                  1556.697202
Tomato          arima        2                    3           3            0                      66.666667                0.000000              33.333333              1556.697202            885.060106        98.047647           0.000000 INR per quintal                  1556.697202
Tomato          arima        3                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            705.973252         0.000000           0.000000 INR per quintal                  1556.697202
Tomato          arima        4                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            528.272125         0.000000           0.000000 INR per quintal                  1556.697202
Tomato           lstm        1                    3           3            0                       0.000000                0.000000             100.000000              1556.697202            951.464181       554.025850         342.872376 INR per quintal                  1556.697202
Tomato           lstm        2                    3           3            0                      66.666667                0.000000              33.333333              1556.697202            720.454048        98.047647           0.000000 INR per quintal                  1556.697202
Tomato           lstm        3                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            499.099836         0.000000           0.000000 INR per quintal                  1556.697202
Tomato           lstm        4                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            319.709739         0.000000           0.000000 INR per quintal                  1556.697202
Tomato         sarima        1                    3           2            1                      33.333333                0.000000              66.666667              1556.697202           1631.981040       116.411491           6.362099 INR per quintal                  1994.311561
Tomato         sarima        2                    3           2            1                      33.333333               33.333333              33.333333              1556.697202           1167.254546       106.035478          23.963492 INR per quintal                  1548.709372
Tomato         sarima        3                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            635.398691         0.000000           0.000000 INR per quintal                  1556.697202
Tomato         sarima        4                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            600.472359         0.000000           0.000000 INR per quintal                  1556.697202
Tomato seasonal_naive        1                    3           2            1                      33.333333                0.000000              66.666667              1556.697202           1582.957088       116.411491           6.362099 INR per quintal                  1994.311561
Tomato seasonal_naive        2                    3           2            1                      33.333333               33.333333              33.333333              1556.697202           1309.160283       106.035478          23.963492 INR per quintal                  1548.709372
Tomato seasonal_naive        3                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            422.399611         0.000000           0.000000 INR per quintal                  1556.697202
Tomato seasonal_naive        4                    3           3            0                     100.000000                0.000000               0.000000              1556.697202            603.192622         0.000000           0.000000 INR per quintal                  1556.697202
```

## Sensitivity Analysis
The values below vary one configured scenario dimension at a time. They are sensitivity cases, not estimates of real-world probability or observed farmer conditions.

### Storage cost multipliers
```text
  crop  scenario_value  store_percentage  mean_incremental_value
 Onion             0.5          4.166667             -790.544408
 Onion             1.0          2.083333             -996.794408
 Onion             1.5          2.083333            -1203.044408
 Onion             2.0          2.083333            -1409.294408
  Rice             0.5         10.416667             -214.795582
  Rice             1.0          2.083333             -327.295582
  Rice             1.5          0.000000             -439.795582
  Rice             2.0          0.000000             -552.295582
Tomato             0.5          8.333333             -482.529164
Tomato             1.0          8.333333             -707.529164
Tomato             1.5          8.333333             -932.529164
Tomato             2.0          8.333333            -1157.529164
```

### Spoilage scenarios
```text
  crop  scenario_value  store_percentage  mean_incremental_value
 Onion            0.00          4.166667             -849.560188
 Onion            0.02          4.166667             -886.368743
 Onion            0.05          2.083333             -941.581576
 Onion            0.10          2.083333            -1033.602963
  Rice            0.00          2.083333             -306.551909
  Rice            0.02          0.000000             -348.039255
  Rice            0.05          0.000000             -410.270275
  Rice            0.10          0.000000             -513.988642
Tomato            0.00         14.583333             -478.264216
Tomato            0.02         14.583333             -508.832876
Tomato            0.05          8.333333             -554.685865
Tomato            0.10          8.333333             -631.107514
```

### Forecast price and duration scenarios
Full structured scenario rows are in `sell_store_sensitivity.csv`.

## Paper Table X: Sell-vs-Store Decision Performance
```text
  Crop          Model  Horizon  N  Sell Decisions  Store Decisions  Decision Agreement (%)  Mean Regret (INR)  Median Regret (INR)
 Onion          arima        1  3               3                0               66.666667          31.964808             0.000000
 Onion          arima        2  3               3                0              100.000000           0.000000             0.000000
 Onion          arima        3  3               3                0               66.666667         454.459287             0.000000
 Onion          arima        4  3               3                0               66.666667         549.193463             0.000000
 Onion           lstm        1  3               3                0               66.666667          31.964808             0.000000
 Onion           lstm        2  3               3                0              100.000000           0.000000             0.000000
 Onion           lstm        3  3               3                0               66.666667         454.459287             0.000000
 Onion           lstm        4  3               3                0               66.666667         549.193463             0.000000
 Onion         sarima        1  3               3                0               66.666667          31.964808             0.000000
 Onion         sarima        2  3               3                0              100.000000           0.000000             0.000000
 Onion         sarima        3  3               3                0               66.666667         454.459287             0.000000
 Onion         sarima        4  3               3                0               66.666667         549.193463             0.000000
 Onion seasonal_naive        1  3               2                1               33.333333         251.815551            95.894425
 Onion seasonal_naive        2  3               3                0              100.000000           0.000000             0.000000
 Onion seasonal_naive        3  3               3                0               66.666667         454.459287             0.000000
 Onion seasonal_naive        4  3               3                0               66.666667         549.193463             0.000000
  Rice          arima        1  3               3                0              100.000000           0.000000             0.000000
  Rice          arima        2  3               3                0              100.000000           0.000000             0.000000
  Rice          arima        3  3               3                0              100.000000           0.000000             0.000000
  Rice          arima        4  3               3                0               66.666667           6.099525             0.000000
  Rice           lstm        1  3               3                0              100.000000           0.000000             0.000000
  Rice           lstm        2  3               3                0              100.000000           0.000000             0.000000
  Rice           lstm        3  3               3                0              100.000000           0.000000             0.000000
  Rice           lstm        4  3               3                0               66.666667           6.099525             0.000000
  Rice         sarima        1  3               2                1               66.666667          29.081101             0.000000
  Rice         sarima        2  3               3                0              100.000000           0.000000             0.000000
  Rice         sarima        3  3               3                0              100.000000           0.000000             0.000000
  Rice         sarima        4  3               3                0               66.666667           6.099525             0.000000
  Rice seasonal_naive        1  3               3                0              100.000000           0.000000             0.000000
  Rice seasonal_naive        2  3               3                0              100.000000           0.000000             0.000000
  Rice seasonal_naive        3  3               3                0              100.000000           0.000000             0.000000
  Rice seasonal_naive        4  3               3                0               66.666667           6.099525             0.000000
Tomato          arima        1  3               3                0                0.000000         554.025850           342.872376
Tomato          arima        2  3               3                0               66.666667          98.047647             0.000000
Tomato          arima        3  3               3                0              100.000000           0.000000             0.000000
Tomato          arima        4  3               3                0              100.000000           0.000000             0.000000
Tomato           lstm        1  3               3                0                0.000000         554.025850           342.872376
Tomato           lstm        2  3               3                0               66.666667          98.047647             0.000000
Tomato           lstm        3  3               3                0              100.000000           0.000000             0.000000
Tomato           lstm        4  3               3                0              100.000000           0.000000             0.000000
Tomato         sarima        1  3               2                1               33.333333         116.411491             6.362099
Tomato         sarima        2  3               2                1               33.333333         106.035478            23.963492
Tomato         sarima        3  3               3                0              100.000000           0.000000             0.000000
Tomato         sarima        4  3               3                0              100.000000           0.000000             0.000000
Tomato seasonal_naive        1  3               2                1               33.333333         116.411491             6.362099
Tomato seasonal_naive        2  3               2                1               33.333333         106.035478            23.963492
Tomato seasonal_naive        3  3               3                0              100.000000           0.000000             0.000000
Tomato seasonal_naive        4  3               3                0              100.000000           0.000000             0.000000
```

## Paper Table Y: Decision Sensitivity to Storage Cost and Spoilage
```text
  crop           scenario_type  scenario_value  number_of_scenarios  store_decision_percentage  mean_incremental_store_value_inr
 Onion           spoilage_rate            0.00                   48                   4.166667                       -849.560188
 Onion           spoilage_rate            0.02                   48                   4.166667                       -886.368743
 Onion           spoilage_rate            0.05                   48                   2.083333                       -941.581576
 Onion           spoilage_rate            0.10                   48                   2.083333                      -1033.602963
 Onion storage_cost_multiplier            0.50                   48                   4.166667                       -790.544408
 Onion storage_cost_multiplier            1.00                   48                   2.083333                       -996.794408
 Onion storage_cost_multiplier            1.50                   48                   2.083333                      -1203.044408
 Onion storage_cost_multiplier            2.00                   48                   2.083333                      -1409.294408
  Rice           spoilage_rate            0.00                   48                   2.083333                       -306.551909
  Rice           spoilage_rate            0.02                   48                   0.000000                       -348.039255
  Rice           spoilage_rate            0.05                   48                   0.000000                       -410.270275
  Rice           spoilage_rate            0.10                   48                   0.000000                       -513.988642
  Rice storage_cost_multiplier            0.50                   48                  10.416667                       -214.795582
  Rice storage_cost_multiplier            1.00                   48                   2.083333                       -327.295582
  Rice storage_cost_multiplier            1.50                   48                   0.000000                       -439.795582
  Rice storage_cost_multiplier            2.00                   48                   0.000000                       -552.295582
Tomato           spoilage_rate            0.00                   48                  14.583333                       -478.264216
Tomato           spoilage_rate            0.02                   48                  14.583333                       -508.832876
Tomato           spoilage_rate            0.05                   48                   8.333333                       -554.685865
Tomato           spoilage_rate            0.10                   48                   8.333333                       -631.107514
Tomato storage_cost_multiplier            0.50                   48                   8.333333                       -482.529164
Tomato storage_cost_multiplier            1.00                   48                   8.333333                       -707.529164
Tomato storage_cost_multiplier            1.50                   48                   8.333333                       -932.529164
Tomato storage_cost_multiplier            2.00                   48                   8.333333                      -1157.529164
```

## Limitations
- Results are retrospective simulations on three rolling-origin folds, not farmer outcomes, causal effects, or income improvements.
- The evaluated quantity is a one-quintal scenario because farmer acreage/decision-specific quantity is not available.
- Legacy cost/spoilage assumptions lack observed provenance and time calibration; sensitivity results should not be interpreted as calibrated economic estimates.
- No route-specific transport quote or verified storage invoice is included.
- Future actual prices are used only for retrospective scoring and hindsight comparison, never for the forecast-based decision.
- RMSE-selected model selection is inherited unchanged from Phase 2; DM comparisons are underpowered at three paired origins and do not establish model superiority.
