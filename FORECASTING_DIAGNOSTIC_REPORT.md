# Forecasting Diagnostic Report

## Dataset and Units
- Input: `price dataset (1).csv` (101 raw rows).
- Evaluated source field: `Price_INR_per_Quintal`, whose column name explicitly identifies INR per quintal.
- No price conversion was applied; every metric in this report and the CSV outputs is in INR per quintal.
- `Price_INR_per_Quintal` is missing for later rows; those rows were excluded instead of substituting the ambiguously scaled `Final_Price` field.
- `Final_Price` scale evidence from overlapping rows:
- Onion: median Final_Price / Price_INR_per_Quintal ratio = 0.01; Final_Price excluded from evaluation.
- Rice: median Final_Price / Price_INR_per_Quintal ratio = 1.44; Final_Price excluded from evaluation.
- Tomato: median Final_Price / Price_INR_per_Quintal ratio = 0.01; Final_Price excluded from evaluation.
- Duplicate crop-quarter source rows, if present, are aggregated by arithmetic mean. Missing quarters are left missing, never filled or interpolated.

| Crop | Raw crop rows | Missing source-price rows | Source-price observations | Duplicate rows aggregated | Excluded across quarter gaps | Evaluated observations | Start quarter | End quarter | Missing quarters | Minimum price | Maximum price |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|
  crop  raw_crop_rows  missing_source_price_rows  duplicate_rows_aggregated  source_price_observations  excluded_due_to_quarter_gaps  observations  start    end missing_quarters   price_min   price_max
  Rice             34                          8                          0                         26                             0            26 2009Q1 2015Q2               [] 1498.480392 2549.786393
 Onion             34                          8                          0                         26                             0            26 2009Q1 2015Q2               []  792.729412 4084.379677
Tomato             33                          8                          0                         25                             1            24 2009Q3 2015Q2         [2009Q2]  904.264319 3297.800868

Each crop uses its longest contiguous sequence of actual quarterly observations. Observations outside that sequence are excluded where a calendar-quarter gap would otherwise distort seasonal period 4. No prices are imputed or interpolated, and the excluded gaps are listed above.

## Frequency and Fold Protocol
- Nominal frequency: quarterly.
- Forecast horizon: 4 consecutive calendar quarters per fold.
- Minimum training size: 12 observed records.
- Validation folds: the latest 3 non-overlapping rolling-origin windows available after the minimum training window.
- Training is expanding from the first available observation and ends strictly before each validation window.
- Number of fold records: 36; valid: 36; failed: 0.

### Fold definitions and sample sizes
- Onion / arima / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Onion / arima / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Onion / arima / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Onion / lstm / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Onion / lstm / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Onion / lstm / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Onion / sarima / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Onion / sarima / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Onion / sarima / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Onion / seasonal_naive / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Onion / seasonal_naive / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Onion / seasonal_naive / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Rice / arima / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Rice / arima / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Rice / arima / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Rice / lstm / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Rice / lstm / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Rice / lstm / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Rice / sarima / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Rice / sarima / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Rice / sarima / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Rice / seasonal_naive / fold 1: train 2009-03-31 to 2011-12-31 (12 observations); validation 2012-03-31 to 2012-12-31 (4 observations).
- Rice / seasonal_naive / fold 2: train 2009-03-31 to 2012-12-31 (16 observations); validation 2013-03-31 to 2013-12-31 (4 observations).
- Rice / seasonal_naive / fold 3: train 2009-03-31 to 2013-12-31 (20 observations); validation 2014-03-31 to 2014-12-31 (4 observations).
- Tomato / arima / fold 1: train 2009-09-30 to 2012-06-30 (12 observations); validation 2012-09-30 to 2013-06-30 (4 observations).
- Tomato / arima / fold 2: train 2009-09-30 to 2013-06-30 (16 observations); validation 2013-09-30 to 2014-06-30 (4 observations).
- Tomato / arima / fold 3: train 2009-09-30 to 2014-06-30 (20 observations); validation 2014-09-30 to 2015-06-30 (4 observations).
- Tomato / lstm / fold 1: train 2009-09-30 to 2012-06-30 (12 observations); validation 2012-09-30 to 2013-06-30 (4 observations).
- Tomato / lstm / fold 2: train 2009-09-30 to 2013-06-30 (16 observations); validation 2013-09-30 to 2014-06-30 (4 observations).
- Tomato / lstm / fold 3: train 2009-09-30 to 2014-06-30 (20 observations); validation 2014-09-30 to 2015-06-30 (4 observations).
- Tomato / sarima / fold 1: train 2009-09-30 to 2012-06-30 (12 observations); validation 2012-09-30 to 2013-06-30 (4 observations).
- Tomato / sarima / fold 2: train 2009-09-30 to 2013-06-30 (16 observations); validation 2013-09-30 to 2014-06-30 (4 observations).
- Tomato / sarima / fold 3: train 2009-09-30 to 2014-06-30 (20 observations); validation 2014-09-30 to 2015-06-30 (4 observations).
- Tomato / seasonal_naive / fold 1: train 2009-09-30 to 2012-06-30 (12 observations); validation 2012-09-30 to 2013-06-30 (4 observations).
- Tomato / seasonal_naive / fold 2: train 2009-09-30 to 2013-06-30 (16 observations); validation 2013-09-30 to 2014-06-30 (4 observations).
- Tomato / seasonal_naive / fold 3: train 2009-09-30 to 2014-06-30 (20 observations); validation 2014-09-30 to 2015-06-30 (4 observations).

## Model Configurations
- Seasonal naive baseline: seasonal period = 4 quarters; repeat the most recent four observed values.
- ARIMA: order (1, 1, 1), seasonal order (0, 0, 0, 0), stationarity and invertibility enforced.
- SARIMA: order (0, 1, 1), seasonal order (0, 1, 1, 4), stationarity and invertibility enforced; L-BFGS optimizer, maximum 500 iterations.
- LSTM: input shape `(window, 1)`; Input layer, LSTM with 32 units and ReLU, Dense(1) output; no dropout; Adam optimizer, learning rate 0.001; MSE loss; 20 epochs; batch size 8; MinMaxScaler fitted on training data only; window = min(4, training observations - 1); random seed = 42; shuffle disabled.

### LSTM effective training sequences per fold
  crop  fold  train_observations  lstm_training_sequences
  Rice     1                  12                        8
  Rice     2                  16                       12
  Rice     3                  20                       16
 Onion     1                  12                        8
 Onion     2                  16                       12
 Onion     3                  20                       16
Tomato     1                  12                        8
Tomato     2                  16                       12
Tomato     3                  20                       16

The LSTM sample is small: each fold has only the listed training observations minus its lookback window as supervised sequences. This small effective sample makes its scores sensitive to initialization and should not support a claim of general superiority.

## SARIMA Diagnostics
For every SARIMA fold, `converged`, AIC, BIC, finite forecast minimum/maximum, captured warning text, and failure reason are recorded below and in `forecast_fold_metrics.csv`.

```text
  crop  fold status converged        aic        bic  forecast_min  forecast_max                                                                                                                           warning failure_reason
  Rice     1  VALID      True  87.662803  87.500533   1882.210546   1944.467543 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
  Rice     2  VALID      True 137.329005 138.522691   2256.716800   2541.327093 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
  Rice     3  VALID      True 180.518428 182.642579   2500.759479   2689.931437                                               Non-invertible starting seasonal moving average Using zeros as starting parameters.               
 Onion     1  VALID      True 113.750072 113.587803    419.942905   1313.706435 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
 Onion     2  VALID      True 173.348835 174.542521    671.302318   1485.579796 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
 Onion     3  VALID      True 243.031196 245.155346   3622.442432   4903.643271                                               Non-invertible starting seasonal moving average Using zeros as starting parameters.               
Tomato     1  VALID      True 111.590905 111.428635   1272.497935   1815.510257 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
Tomato     2  VALID      True 169.050162 170.243848   1324.333052   1991.430881 Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.               
Tomato     3  VALID      True 237.862977 239.987127   1551.634980   2588.286064                                               Non-invertible starting seasonal moving average Using zeros as starting parameters.               
```

## Failed Folds
```text
None.
```

Invalid predictions remain explicitly marked `FAILED` in the prediction-level output when a numeric forecast was produced. Failed folds have NaN fold metrics and are excluded from horizon/model summaries and model selection. No fallback or fabricated prediction is substituted.

## Metric Formulas
For the complete forecast vector in each fold, with error defined as predicted minus actual:
- MAE = mean(abs(actual - predicted))
- RMSE = sqrt(mean((actual - predicted)^2))
- MAPE = mean(abs((actual - predicted) / actual)) * 100
- R2 = 1 - SSE/SST, with SSE = sum((actual - predicted)^2), SST = sum((actual - mean(actual))^2)
- Metrics are expressed in INR per quintal, except MAPE (percent) and R2 (unitless). MAPE is undefined if any actual value is zero; R2 is undefined when the validation vector has zero variance.

## Fold-Level Metrics
Each MAE, RMSE, MAPE, and R2 value below is computed once across all forecast steps in that fold, not attached as a per-step fold score.

```text
  crop          model  fold status  train_observations  validation_observations         MAE        RMSE       MAPE          R2  lstm_training_sequences
  Rice seasonal_naive     1  VALID                  12                        4  211.532250  256.183439  10.070341   -1.966741                        0
  Rice seasonal_naive     2  VALID                  16                        4  346.084649  355.437382  14.823435  -26.325413                        0
  Rice seasonal_naive     3  VALID                  20                        4  159.115333  166.020996   6.348738  -30.948103                        0
  Rice          arima     1  VALID                  12                        4  195.387474  245.706616   9.245288   -1.729049                        0
  Rice          arima     2  VALID                  16                        4   49.827229   56.848724   2.086981    0.300992                        0
  Rice          arima     3  VALID                  20                        4   58.021206   67.196997   2.303407   -4.233820                        0
  Rice         sarima     1  VALID                  12                        4  140.517514  168.088477   6.742354   -0.277184                        0
  Rice         sarima     2  VALID                  16                        4   42.611489   55.135526   1.771824    0.342488                        0
  Rice         sarima     3  VALID                  20                        4   72.847408   90.462979   2.887307   -8.485513                        0
  Rice           lstm     1  VALID                  12                        4  437.093491  467.435066  21.297559   -8.876888                        8
  Rice           lstm     2  VALID                  16                        4  593.559745  600.791862  25.140807  -77.070798                       12
  Rice           lstm     3  VALID                  20                        4  663.554111  668.046987  26.391981 -516.288795                       16
 Onion seasonal_naive     1  VALID                  12                        4  396.610955  638.570160  42.867859   -6.437501                        0
 Onion seasonal_naive     2  VALID                  16                        4 1726.031565 1928.201819  58.509329   -2.288141                        0
 Onion seasonal_naive     3  VALID                  20                        4  998.358707 1254.185792  50.445039  -12.503435                        0
 Onion          arima     1  VALID                  12                        4  302.534009  323.239159  31.570422   -0.905714                        0
 Onion          arima     2  VALID                  16                        4 1280.535722 1666.020412  36.715639   -1.454744                        0
 Onion          arima     3  VALID                  20                        4 2080.716794 2109.141197 123.762192  -37.188432                        0
 Onion         sarima     1  VALID                  12                        4  311.404229  333.748904  32.057067   -1.031653                        0
 Onion         sarima     2  VALID                  16                        4 1716.926027 1950.176614  57.741805   -2.363515                        0
 Onion         sarima     3  VALID                  20                        4 2447.553896 2465.906404 140.858781  -51.200384                        0
 Onion           lstm     1  VALID                  12                        4  209.872701  267.540876  17.866948   -0.305540                        8
 Onion           lstm     2  VALID                  16                        4 1696.040843 1998.930726  54.189441   -2.533792                       12
 Onion           lstm     3  VALID                  20                        4  394.427922  402.310005  23.526369   -0.389448                       16
Tomato seasonal_naive     1  VALID                  12                        4  262.234042  336.136191  14.574665    0.085880                        0
Tomato seasonal_naive     2  VALID                  16                        4  697.433393  850.168302  31.045008   -0.197279                        0
Tomato seasonal_naive     3  VALID                  20                        4  515.636856  591.397495  25.375817    0.325015                        0
Tomato          arima     1  VALID                  12                        4  351.022708  418.387949  20.871772   -0.416221                        0
Tomato          arima     2  VALID                  16                        4  785.060377  996.091424  31.557163   -0.643554                        0
Tomato          arima     3  VALID                  20                        4  582.688786  932.100856  20.759117   -0.676722                        0
Tomato         sarima     1  VALID                  12                        4  237.761692  302.476263  14.212341    0.259789                        0
Tomato         sarima     2  VALID                  16                        4  618.515222  784.645475  25.715052   -0.019841                        0
Tomato         sarima     3  VALID                  20                        4  381.394157  452.405560  17.130524    0.605006                        0
Tomato           lstm     1  VALID                  12                        4  543.793237  641.362664  30.521619   -2.327975                        8
Tomato           lstm     2  VALID                  16                        4  772.850401 1072.957528  28.016066   -0.907000                       12
Tomato           lstm     3  VALID                  20                        4  644.722121  912.439254  25.134379   -0.606731                       16
```

## Horizon-Level Metrics
Metrics below pool valid predictions across folds for each crop/model/horizon.

```text
  crop          model  horizon         MAE        RMSE      MAPE  number_of_predictions      price_unit
 Onion          arima        1 1018.393492 1366.779223 73.923194                      3 INR per quintal
 Onion          arima        2 1015.431840 1466.716385 75.848198                      3 INR per quintal
 Onion          arima        3 1308.915029 1530.036167 50.377794                      3 INR per quintal
 Onion          arima        4 1542.308340 1846.914310 55.915152                      3 INR per quintal
 Onion           lstm        1  466.495553  530.811495 30.364408                      3 INR per quintal
 Onion           lstm        2  365.958510  414.297106 25.252550                      3 INR per quintal
 Onion           lstm        3  981.245026 1454.051660 31.433814                      3 INR per quintal
 Onion           lstm        4 1253.422866 1752.485334 40.392907                      3 INR per quintal
 Onion         sarima        1 1160.351368 1536.420832 79.902795                      3 INR per quintal
 Onion         sarima        2 1199.307628 1398.398936 87.088572                      3 INR per quintal
 Onion         sarima        3 1735.268073 1995.426962 68.625048                      3 INR per quintal
 Onion         sarima        4 1872.918466 2242.585877 71.927124                      3 INR per quintal
 Onion seasonal_naive        1  875.640707  949.131137 74.330357                      3 INR per quintal
 Onion seasonal_naive        2  321.462724  449.833014 20.517467                      3 INR per quintal
 Onion seasonal_naive        3 1347.333571 1659.409542 48.523467                      3 INR per quintal
 Onion seasonal_naive        4 1616.897966 1934.282412 59.058344                      3 INR per quintal
  Rice          arima        1   21.578733   21.640491  0.991248                      3 INR per quintal
  Rice          arima        2   56.912555   63.046827  2.696481                      3 INR per quintal
  Rice          arima        3  124.430232  161.017725  5.728903                      3 INR per quintal
  Rice          arima        4  201.393025  245.876702  8.764269                      3 INR per quintal
  Rice           lstm        1  425.041771  446.277090 18.893292                      3 INR per quintal
  Rice           lstm        2  496.783112  512.193071 21.842204                      3 INR per quintal
  Rice           lstm        3  624.386552  629.957257 26.603145                      3 INR per quintal
  Rice           lstm        4  712.731695  713.647750 29.768488                      3 INR per quintal
  Rice         sarima        1   44.316377   56.564276  2.247092                      3 INR per quintal
  Rice         sarima        2   21.895577   24.612821  0.973247                      3 INR per quintal
  Rice         sarima        3  100.870186  116.126101  4.544711                      3 INR per quintal
  Rice         sarima        4  174.219742  188.004533  7.436931                      3 INR per quintal
  Rice seasonal_naive        1  224.774951  279.505542  9.772643                      3 INR per quintal
  Rice seasonal_naive        2  236.797541  267.468358 10.414555                      3 INR per quintal
  Rice seasonal_naive        3  254.977236  262.244641 11.149937                      3 INR per quintal
  Rice seasonal_naive        4  239.093248  272.525145 10.319552                      3 INR per quintal
Tomato          arima        1 1278.687014 1362.753365 45.681116                      3 INR per quintal
Tomato          arima        2  629.905965  867.026014 24.483384                      3 INR per quintal
Tomato          arima        3  178.740235  202.945657 14.930830                      3 INR per quintal
Tomato          arima        4  204.362614  254.415064 12.488738                      3 INR per quintal
Tomato           lstm        1 1363.833966 1402.366600 50.093407                      3 INR per quintal
Tomato           lstm        2  823.560151  999.359018 35.440575                      3 INR per quintal
Tomato           lstm        3  110.915919  143.937075  7.733221                      3 INR per quintal
Tomato           lstm        4  316.844308  455.452899 18.295550                      3 INR per quintal
Tomato         sarima        1  563.225897  612.473227 20.006238                      3 INR per quintal
Tomato         sarima        2  618.249704  822.556076 24.441421                      3 INR per quintal
Tomato         sarima        3   95.741642  105.252694  7.873094                      3 INR per quintal
Tomato         sarima        4  373.010851  391.120001 23.756470                      3 INR per quintal
Tomato seasonal_naive        1  620.901135  624.346412 24.030098                      3 INR per quintal
Tomato seasonal_naive        2  840.278908 1010.575070 35.623339                      3 INR per quintal
Tomato seasonal_naive        3  187.693777  224.517220 13.187092                      3 INR per quintal
Tomato seasonal_naive        4  318.198567  345.284193 21.820126                      3 INR per quintal
```

## Model-Level Summary
Means and population standard deviations are across valid fold metrics. Failed folds are separately counted and excluded from these summaries.

```text
  crop          model  valid_folds  failed_folds    mean_MAE   mean_RMSE  mean_MAPE     mean_R2    std_MAE   std_RMSE  std_MAPE     std_R2      price_unit
 Onion          arima            3             0 1221.262175 1366.133589  64.016085  -13.182963 727.149008 759.302576 42.299065  16.975910 INR per quintal
 Onion           lstm            3             0  766.780489  889.593869  31.860920   -1.076260 661.391847 786.346775 15.956805   1.031200 INR per quintal
 Onion         sarima            3             0 1491.961384 1583.277308  76.885885  -18.198517 886.468901 908.289684 46.435080  23.342177 INR per quintal
 Onion seasonal_naive            3             0 1040.333742 1273.652590  50.607409   -7.076359 543.544673 526.669834  6.386635   4.194772 INR per quintal
  Rice          arima            3             0  101.078636  123.250779   4.545225   -1.887292  66.770267  86.692352  3.324620   1.854708 INR per quintal
  Rice           lstm            3             0  564.735782  578.757972  24.276782 -200.745494  94.672131  83.368279  2.167670 224.852965 INR per quintal
  Rice         sarima            3             0   85.325470  104.562327   3.800495   -2.806736  40.932253  47.178286  2.129472   4.023463 INR per quintal
  Rice seasonal_naive            3             0  238.910744  259.213939  10.414172  -19.746753  78.746715  77.358601  3.468313  12.713219 INR per quintal
Tomato          arima            3             0  572.923957  782.193410  24.396017   -0.578832 177.329615 258.572373  5.063904   0.115778 INR per quintal
Tomato           lstm            3             0  653.788586  875.586482  27.890688   -1.280569  93.731697 178.114433  2.201118   0.750704 INR per quintal
Tomato         sarima            3             0  412.557024  513.175766  19.019306    0.281651 156.996084 201.480439  4.882193   0.255561 INR per quintal
Tomato seasonal_naive            3             0  491.768097  592.567329  23.665164    0.071205 178.469245 209.854361  6.831925   0.213478 INR per quintal
```

## Model Selection
For each crop, select the model with the lowest mean validation RMSE across valid folds. No final test set is used. A model with no valid folds is not selectable.

- Rice: sarima
- Onion: lstm
- Tomato: sarima

## Limitations
- The explicitly labeled source price series is incomplete after the historical block; the differently scaled `Final_Price` field is not substituted.
- To keep seasonal period 4 calendar-correct, observations outside the longest contiguous quarterly segment are excluded rather than bridging missing quarters.
- Small fold counts limit precision of mean and standard-deviation estimates.
- LSTM has few effective sequences per fold and is reported as a comparison model, not presumed superior.
- SARIMA and ARIMA fits may fail convergence or numerical validity checks; such folds remain visible but contribute no metrics or selection scores.
