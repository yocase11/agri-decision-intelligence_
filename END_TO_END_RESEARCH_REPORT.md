# ADIS End-to-End Research Report

This report consolidates existing forecasting, retrospective sell/store, warehouse allocation, and scenario-based routing evaluations. It does not retrain models or regenerate upstream research calculations.

## Routing classification
The available data supports scenario-based single-leg reference-origin-to-warehouse transport evaluation only. It does not support a genuine CVRP or actual farmer-route analysis.

## Consolidated scenario table
```text
  crop forecast_model  forecast_horizon  forecast_RMSE  forecast_MAE  forecast_R2  sell_store_agreement_percentage  sell_store_mean_regret_inr warehouse_method  warehouse_storage_cost_inr  allocated_quantity_quintal  unallocated_quantity_quintal                           routing_method  distance_km  transport_cost_inr  total_cost_inr route_distance_source                 scenario_id decision_date                                                                                  metric_provenance      price_unit
  Rice         sarima                 1      56.564276     44.316377    -0.277184                        66.666667                   29.081101             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only   Rice_sarima_2011-12-31_h1    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 2      24.612821     21.895577    -0.277184                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only   Rice_sarima_2011-12-31_h2    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 3     116.126101    100.870186    -0.277184                       100.000000                    0.000000             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only   Rice_sarima_2011-12-31_h3    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 4     188.004533    174.219742    -0.277184                        66.666667                    6.099525             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only   Rice_sarima_2011-12-31_h4    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 1      56.564276     44.316377     0.342488                        66.666667                   29.081101             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only   Rice_sarima_2012-12-31_h1    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 2      24.612821     21.895577     0.342488                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only   Rice_sarima_2012-12-31_h2    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 3     116.126101    100.870186     0.342488                       100.000000                    0.000000             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only   Rice_sarima_2012-12-31_h3    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 4     188.004533    174.219742     0.342488                        66.666667                    6.099525             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only   Rice_sarima_2012-12-31_h4    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 1      56.564276     44.316377    -8.485513                        66.666667                   29.081101             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only   Rice_sarima_2013-12-31_h1    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 2      24.612821     21.895577    -8.485513                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only   Rice_sarima_2013-12-31_h2    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 3     116.126101    100.870186    -8.485513                       100.000000                    0.000000             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only   Rice_sarima_2013-12-31_h3    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
  Rice         sarima                 4     188.004533    174.219742    -8.485513                        66.666667                    6.099525             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only   Rice_sarima_2013-12-31_h4    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 1     530.811495    466.495553    -0.305540                        66.666667                   31.964808             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only    Onion_lstm_2011-12-31_h1    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 2     414.297106    365.958510    -0.305540                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only    Onion_lstm_2011-12-31_h2    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 3    1454.051660    981.245026    -0.305540                        66.666667                  454.459287             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only    Onion_lstm_2011-12-31_h3    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 4    1752.485334   1253.422866    -0.305540                        66.666667                  549.193463             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only    Onion_lstm_2011-12-31_h4    2011-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 1     530.811495    466.495553    -2.533792                        66.666667                   31.964808             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only    Onion_lstm_2012-12-31_h1    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 2     414.297106    365.958510    -2.533792                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only    Onion_lstm_2012-12-31_h2    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 3    1454.051660    981.245026    -2.533792                        66.666667                  454.459287             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only    Onion_lstm_2012-12-31_h3    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 4    1752.485334   1253.422866    -2.533792                        66.666667                  549.193463             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only    Onion_lstm_2012-12-31_h4    2012-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 1     530.811495    466.495553    -0.389448                        66.666667                   31.964808             MILP                       0.744                         1.0                           0.0 single_leg_reference_origin_to_warehouse    45.269168           22.634584       23.378584  Haversine proxy only    Onion_lstm_2013-12-31_h1    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 2     414.297106    365.958510    -0.389448                       100.000000                    0.000000             MILP                       0.978                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.061528  Haversine proxy only    Onion_lstm_2013-12-31_h2    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 3    1454.051660    981.245026    -0.389448                        66.666667                  454.459287             MILP                       1.467                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       24.550528  Haversine proxy only    Onion_lstm_2013-12-31_h3    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
 Onion           lstm                 4    1752.485334   1253.422866    -0.389448                        66.666667                  549.193463             MILP                       1.956                         1.0                           0.0 single_leg_reference_origin_to_warehouse    46.167055           23.083528       25.039528  Haversine proxy only    Onion_lstm_2013-12-31_h4    2013-12-31 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 1     612.473227    563.225897     0.259789                        33.333333                  116.411491             MILP                       0.798                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       11.855253  Haversine proxy only Tomato_sarima_2012-06-30_h1    2012-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 2     822.556076    618.249704     0.259789                        33.333333                  106.035478             MILP                       1.596                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       12.653253  Haversine proxy only Tomato_sarima_2012-06-30_h2    2012-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 3     105.252694     95.741642     0.259789                       100.000000                    0.000000             MILP                       2.394                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       13.451253  Haversine proxy only Tomato_sarima_2012-06-30_h3    2012-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 4     391.120001    373.010851     0.259789                       100.000000                    0.000000             MILP                       3.192                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       14.249253  Haversine proxy only Tomato_sarima_2012-06-30_h4    2012-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 1     612.473227    563.225897    -0.019841                        33.333333                  116.411491             MILP                       0.798                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       11.855253  Haversine proxy only Tomato_sarima_2013-06-30_h1    2013-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 2     822.556076    618.249704    -0.019841                        33.333333                  106.035478             MILP                       1.596                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       12.653253  Haversine proxy only Tomato_sarima_2013-06-30_h2    2013-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 3     105.252694     95.741642    -0.019841                       100.000000                    0.000000             MILP                       2.394                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       13.451253  Haversine proxy only Tomato_sarima_2013-06-30_h3    2013-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 4     391.120001    373.010851    -0.019841                       100.000000                    0.000000             MILP                       3.192                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       14.249253  Haversine proxy only Tomato_sarima_2013-06-30_h4    2013-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 1     612.473227    563.225897     0.605006                        33.333333                  116.411491             MILP                       0.798                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       11.855253  Haversine proxy only Tomato_sarima_2014-06-30_h1    2014-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 2     822.556076    618.249704     0.605006                        33.333333                  106.035478             MILP                       1.596                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       12.653253  Haversine proxy only Tomato_sarima_2014-06-30_h2    2014-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 3     105.252694     95.741642     0.605006                       100.000000                    0.000000             MILP                       2.394                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       13.451253  Haversine proxy only Tomato_sarima_2014-06-30_h3    2014-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
Tomato         sarima                 4     391.120001    373.010851     0.605006                       100.000000                    0.000000             MILP                       3.192                         1.0                           0.0 single_leg_reference_origin_to_warehouse    22.114505           11.057253       14.249253  Haversine proxy only Tomato_sarima_2014-06-30_h4    2014-06-30 forecast_horizon_metrics.csv; sell_store_decisions.csv; warehouse_summary.csv; routing_summary.csv INR per quintal
```

## Routing evidence
# Routing Research Validation Report

## OBJECTIVE
Quantify single-leg transport distance and cost from saved warehouse allocations under a stated reference-origin scenario. This is a scenario-based transport routing evaluation, not a farmer route study or a CVRP.

## DATA SOURCES
- Warehouse destination coordinates and compatibility: supplied warehouse dataset; provenance is not independently verified.
- Scenario allocation and quantity: protected `warehouse_optimization_results.csv` and `warehouse_summary.csv`.
- Upstream validated selected model and decision metadata: `sell_store_decisions.csv` and `experiment_config.json`.
- Routing origin: warehouse coordinate centroid; synthetic reference proxy, not a farmer/customer location, coordinate (10.872450, 77.896333).

## OBSERVED / SUPPLIED DATA
Available per route scenario are crop, scenario ID, decision date, horizon, selected model, allocated quantity, warehouse ID, warehouse coordinates, and the warehouse evaluator's Haversine distance. No actual farmer origin, market/customer destination, customer demand, vehicle fleet/capacity, time windows, or observed route logs are supplied. These are not inferred.

## ASSUMPTIONS
```json
{
  "routing_problem_class": "scenario-based single-leg reference-origin-to-warehouse transport evaluation",
  "not_a_vrp": true,
  "origin_method": "warehouse coordinate centroid from warehouse_research_assumptions.json",
  "origin_is_farmer_location": false,
  "destination_source": "warehouse_id joined to supplied warehouse dataset coordinates",
  "distance_method": "Haversine straight-line distance",
  "distance_unit": "km",
  "road_distance_available": false,
  "osrm_enabled": false,
  "osrm_reason": "The route origin is a synthetic warehouse centroid, not an observed farmer/customer origin; the evaluator will not request road routes for synthetic coordinates.",
  "transport_rate_inr_per_km_per_metric_tonne": 5.0,
  "transport_rate_provenance": "Scenario assumption inherited from routing.compute_transport_cost default; not an observed carrier quote.",
  "quintals_per_metric_tonne": 10.0,
  "vehicle_fleet_available": false,
  "vehicle_capacity_available": false,
  "travel_time_reported": false,
  "time_windows_available": false,
  "sensitivity": {
    "transport_cost_multipliers": [
      0.5,
      1.0,
      1.5,
      2.0
    ],
    "available_quantity_multipliers": [
      0.5,
      1.0,
      1.5
    ]
  }
}
```
The transport rate is a configurable INR/km/MT scenario assumption, not a carrier quote. 1 quintal is converted to 0.1 metric tonne. The route source is Haversine straight-line distance in km, not road distance. OSRM was not queried because the origin is a synthetic centroid rather than an observed traveler origin.

## SIMULATED VALUES
Each saved warehouse allocation is evaluated as one independent single-leg reference-origin-to-warehouse scenario. Scenario quantities and distances are not observed farmer trips. No vehicle count, travel time, route sequence, or time-window metric is reported because the required data is absent.

## OPTIMIZED VALUES
The warehouse destination is the already selected MILP allocation. The routing evaluator does not change warehouse assignments and does not rewrite warehouse outputs. It independently recomputes the Haversine length and quantity-based transport cost for each allocated warehouse line.

## ROUTING / VRP FORMULATION
This is not a CVRP or multi-vehicle VRP. It is a single-leg cost calculation:
`transport_cost_inr = distance_km * (quantity_quintal / 10) * assumed_transport_rate_inr_per_km_per_metric_tonne`
Each selected warehouse has one direct proxy leg from `WAREHOUSE_CENTROID_REFERENCE` to the supplied warehouse coordinates. There are no intermediate nodes, routing decisions, vehicle capacities, multiple vehicles, customer demands, or time windows in the data.

## BASELINES
- `Warehouse MILP allocation + Haversine`: saved assigned warehouse and saved allocation quantity, with independent distance/cost recomputation.
- `Nearest feasible warehouse`: nearest crop-compatible facility with enough capacity; split to further feasible facilities only if needed.
- `Legacy best_route offline formula`: existing single-leg `best_route` with offline mode, which uses Haversine and the same configured base transport rate.

```text
  crop                                method  scenarios  mean_distance_km  mean_transport_cost_inr  mean_cost_per_quintal  feasible_scenarios
 Onion     Legacy best_route offline formula         12         45.945000                22.967500              22.967500                  12
 Onion            Nearest feasible warehouse         12         45.269168                22.634584              22.634584                  12
 Onion Warehouse MILP allocation + Haversine         12         45.942584                22.971292              22.971292                  12
  Rice     Legacy best_route offline formula         12         45.945000                22.967500              22.967500                  12
  Rice            Nearest feasible warehouse         12         45.269168                22.634584              22.634584                  12
  Rice Warehouse MILP allocation + Haversine         12         45.942584                22.971292              22.971292                  12
Tomato     Legacy best_route offline formula         12         22.110000                11.060000              11.060000                  12
Tomato            Nearest feasible warehouse         12         22.114505                11.057253              11.057253                  12
Tomato Warehouse MILP allocation + Haversine         12         22.114505                11.057253              11.057253                  12
```
No OSRM comparison is reported because actual origin coordinates are unavailable and OSRM results on a synthetic centroid would not be empirical road-route evidence.

## RESULTS
```text
  crop                 scenario_id decision_date  horizon  model  allocated_quantity_quintal  unallocated_quantity_quintal  total_route_distance_km  average_route_distance_km  total_transport_cost_inr  average_transport_cost_inr_per_quintal  number_of_routes  route_feasibility  capacity_violations  demand_violations  haversine_route_count  osrm_route_count      distance_source      price_unit                           routing_method
  Rice   Rice_sarima_2011-12-31_h1    2011-12-31        1 sarima                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2011-12-31_h2    2011-12-31        2 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2011-12-31_h3    2011-12-31        3 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2011-12-31_h4    2011-12-31        4 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2012-12-31_h1    2012-12-31        1 sarima                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2012-12-31_h2    2012-12-31        2 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2012-12-31_h3    2012-12-31        3 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2012-12-31_h4    2012-12-31        4 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2013-12-31_h1    2013-12-31        1 sarima                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2013-12-31_h2    2013-12-31        2 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2013-12-31_h3    2013-12-31        3 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
  Rice   Rice_sarima_2013-12-31_h4    2013-12-31        4 sarima                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2011-12-31_h1    2011-12-31        1   lstm                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2011-12-31_h2    2011-12-31        2   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2011-12-31_h3    2011-12-31        3   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2011-12-31_h4    2011-12-31        4   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2012-12-31_h1    2012-12-31        1   lstm                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2012-12-31_h2    2012-12-31        2   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2012-12-31_h3    2012-12-31        3   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2012-12-31_h4    2012-12-31        4   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2013-12-31_h1    2013-12-31        1   lstm                         1.0                           0.0                45.269168                  45.269168                 22.634584                               22.634584                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2013-12-31_h2    2013-12-31        2   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2013-12-31_h3    2013-12-31        3   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
 Onion    Onion_lstm_2013-12-31_h4    2013-12-31        4   lstm                         1.0                           0.0                46.167055                  46.167055                 23.083528                               23.083528                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2012-06-30_h1    2012-06-30        1 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2012-06-30_h2    2012-06-30        2 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2012-06-30_h3    2012-06-30        3 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2012-06-30_h4    2012-06-30        4 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2013-06-30_h1    2013-06-30        1 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2013-06-30_h2    2013-06-30        2 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2013-06-30_h3    2013-06-30        3 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2013-06-30_h4    2013-06-30        4 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2014-06-30_h1    2014-06-30        1 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2014-06-30_h2    2014-06-30        2 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2014-06-30_h3    2014-06-30        3 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
Tomato Tomato_sarima_2014-06-30_h4    2014-06-30        4 sarima                         1.0                           0.0                22.114505                  22.114505                 11.057253                               11.057253                 1               True                    0                  0                      1                 0 Haversine proxy only INR per quintal single_leg_reference_origin_to_warehouse
```
The end-to-end table links existing forecast, sell/store, warehouse, and routing summaries by crop/model/horizon/scenario without retraining or rewriting upstream artifacts.

## SENSITIVITY ANALYSIS
These are configured scenarios, not probability distributions or observed rates.

### Transport rate multipliers
```text
  crop  scenario_multiplier  mean_cost_inr  mean_unserved_quintal
 Onion                  0.5      11.485646                    0.0
 Onion                  1.0      22.971292                    0.0
 Onion                  1.5      34.456938                    0.0
 Onion                  2.0      45.942584                    0.0
  Rice                  0.5      11.485646                    0.0
  Rice                  1.0      22.971292                    0.0
  Rice                  1.5      34.456938                    0.0
  Rice                  2.0      45.942584                    0.0
Tomato                  0.5       5.528626                    0.0
Tomato                  1.0      11.057253                    0.0
Tomato                  1.5      16.585879                    0.0
Tomato                  2.0      22.114505                    0.0
```

### Allocated quantity multipliers
```text
  crop  scenario_multiplier  mean_cost_inr  mean_unserved_quintal
 Onion                  0.5      11.485646                    0.0
 Onion                  1.0      22.971292                    0.0
 Onion                  1.5      34.456938                    0.0
  Rice                  0.5      11.485646                    0.0
  Rice                  1.0      22.971292                    0.0
  Rice                  1.5      34.456938                    0.0
Tomato                  0.5       5.528626                    0.0
Tomato                  1.0      11.057253                    0.0
Tomato                  1.5      16.585879                    0.0
```

## VALIDATION
- Saved warehouse allocation IDs and crop compatibility are checked.
- Haversine distances are independently recomputed from source coordinates and compared with the protected warehouse distances.
- Transport costs are independently recomputed and compared with the protected warehouse cost values.
- Route quantities are nonnegative and cannot exceed the selected warehouse capacity.
- Deterministic sensitivity outputs are independently recomputed in the verification script.
- Upstream forecasting, sell/store, and warehouse outputs are read-only inputs to this run.

## LIMITATIONS
- No genuine CVRP can be supported: origins, multiple demand nodes, vehicles, vehicle capacities, time windows, and observed routes are absent.
- The origin is synthetic, so Haversine distances are only reference proxies; no actual farmer route or road-distance claim is made.
- Supplied warehouse coordinates and capacities are not independently verified operational data.
- Transport rates are assumed and no carrier quotes, tolls, fuel surcharges, or driver costs are available.
- The evaluation only covers existing positive warehouse allocations and does not optimize route sequences or alter the allocation.

## REPRODUCIBILITY
Run the existing pipeline in isolated research mode with `--routing-research`, providing the saved warehouse-results CSV, warehouse dataset, and routing assumptions. Forecast, sell/store, and warehouse optimization artifacts remain unchanged.

## NO-OVERCLAIM STATEMENT
Results quantify transport costs under configured scenario assumptions only. They do not demonstrate real-world route optimality, farmer savings, warehouse efficiency, or causal income effects.


## Phase reports
## forecast_final_validation_report.md

# Phase 2 Final Forecast Validation

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


## Prediction Intervals and Coverage
- ARIMA and SARIMA intervals use each fitted statsmodels result's native `get_forecast().conf_int(alpha=0.05)` output; confidence level is 95%.
- Bounds are not clipped or modified. Interval coverage and width use only valid folds with finite ordered native bounds.
- Seasonal naive and LSTM intervals are unavailable; no heuristic or fabricated interval is supplied.
- Empirical coverage is the percentage of actual validation prices inside the corresponding bounds. Width and coverage are in INR per quintal; coverage is also reported separately by horizon.

```text
  crop  model horizon  empirical_coverage_percentage  mean_interval_width  number_of_intervals  confidence_level      price_unit
 Onion  arima       1                      66.666667          2162.977740                    3              0.95 INR per quintal
 Onion  arima       2                      66.666667          3264.812188                    3              0.95 INR per quintal
 Onion  arima       3                     100.000000          3859.090584                    3              0.95 INR per quintal
 Onion  arima       4                      66.666667          4407.017195                    3              0.95 INR per quintal
 Onion sarima       1                      66.666667          2018.593498                    3              0.95 INR per quintal
 Onion sarima       2                      66.666667          2822.715597                    3              0.95 INR per quintal
 Onion sarima       3                      66.666667          3442.774014                    3              0.95 INR per quintal
 Onion sarima       4                      33.333333          3967.175001                    3              0.95 INR per quintal
  Rice  arima       1                     100.000000           297.077323                    3              0.95 INR per quintal
  Rice  arima       2                     100.000000           429.814875                    3              0.95 INR per quintal
  Rice  arima       3                      66.666667           538.885562                    3              0.95 INR per quintal
  Rice  arima       4                      66.666667           636.133231                    3              0.95 INR per quintal
  Rice sarima       1                     100.000000           320.635631                    3              0.95 INR per quintal
  Rice sarima       2                     100.000000           478.567815                    3              0.95 INR per quintal
  Rice sarima       3                     100.000000           594.956041                    3              0.95 INR per quintal
  Rice sarima       4                      66.666667           691.814311                    3              0.95 INR per quintal
Tomato  arima       1                      33.333333          1596.996661                    3              0.95 INR per quintal
Tomato  arima       2                      66.666667          1643.437763                    3              0.95 INR per quintal
Tomato  arima       3                     100.000000          1652.853692                    3              0.95 INR per quintal
Tomato  arima       4                     100.000000          1654.327206                    3              0.95 INR per quintal
Tomato sarima       1                      66.666667          1682.240844                    3              0.95 INR per quintal
Tomato sarima       2                      66.666667          1693.024901                    3              0.95 INR per quintal
Tomato sarima       3                     100.000000          1702.549018                    3              0.95 INR per quintal
Tomato sarima       4                     100.000000          1716.198207                    3              0.95 INR per quintal
 Onion  arima     all                      75.000000          3423.474427                   12              0.95 INR per quintal
 Onion sarima     all                      58.333333          3062.814528                   12              0.95 INR per quintal
  Rice  arima     all                      83.333333           475.477748                   12              0.95 INR per quintal
  Rice sarima     all                      91.666667           521.493449                   12              0.95 INR per quintal
Tomato  arima     all                      75.000000          1636.903831                   12              0.95 INR per quintal
Tomato sarima     all                      83.333333          1698.503242                   12              0.95 INR per quintal
```

## ARIMA/SARIMA Diagnostics
Residual mean and sample standard deviation are calculated from fitted residuals. Lag-1 residual autocorrelation is reported. Ljung-Box is reported only when the residual sample size exceeds the chosen lag plus estimated model degrees of freedom; it is diagnostic, not a model acceptance rule. Seasonal small-sample flags remain explicit.

```text
  crop          model  fold status  train_observations  parameter_count converged        aic        bic  residual_mean  residual_std  ljung_box_lag  ljung_box_p_value  residual_acf_lag1  interval_generated                                                               small_sample_warning                                                                                                                           warning
  Rice seasonal_naive     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
  Rice seasonal_naive     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
  Rice seasonal_naive     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
  Rice          arima     1  VALID                  12              3.0      True 132.312550 133.506235     150.977859    441.267243            2.0                NaN          -0.269350                True                                                                                                                                                                                                                     
  Rice          arima     2  VALID                  16              3.0      True 180.904994 183.029145     121.554177    384.560156            3.0           0.788834          -0.188239                True                                                                                                                                                                                                                     
  Rice          arima     3  VALID                  20              3.0      True 223.129604 225.962921      98.058259    345.166445            4.0           0.831750          -0.173744                True                                                                                                                                                                                                                     
  Rice         sarima     1  VALID                  12              3.0      True  87.662803  87.500533      60.545357    494.088025            2.0                NaN          -0.007166                True SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
  Rice         sarima     2  VALID                  16              3.0      True 137.329005 138.522691      68.376511    424.510500            3.0           0.658505          -0.035667                True SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
  Rice         sarima     3  VALID                  20              3.0      True 180.518428 182.642579      51.149947    378.900081            4.0           0.332667          -0.036710                True                                                                                                                                  Non-invertible starting seasonal moving average Using zeros as starting parameters.
  Rice           lstm     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
  Rice           lstm     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
  Rice           lstm     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion seasonal_naive     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion seasonal_naive     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion seasonal_naive     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion          arima     1  VALID                  12              3.0      True 175.879331 177.073017     213.289921    633.090870            2.0                NaN          -0.111275                True                                                                                                                                                                                                                     
 Onion          arima     2  VALID                  16              3.0      True 234.516228 236.640378      85.215178    595.052567            3.0           0.037849          -0.324426                True                                                                                                                                                                                                                     
 Onion          arima     3  VALID                  20              3.0      True 307.465099 310.298416     175.664067    717.216887            4.0           0.184481          -0.233278                True                                                                                                                                                                                                                     
 Onion         sarima     1  VALID                  12              3.0      True 113.750072 113.587803     -11.463671    687.810435            2.0                NaN          -0.308851                True SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
 Onion         sarima     2  VALID                  16              3.0      True 173.348835 174.542521      -0.609305    623.972428            3.0           0.105220          -0.232272                True SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
 Onion         sarima     3  VALID                  20              3.0      True 243.031196 245.155346     123.643809    695.215504            4.0           0.326416          -0.175035                True                                                                                                                                  Non-invertible starting seasonal moving average Using zeros as starting parameters.
 Onion           lstm     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion           lstm     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
 Onion           lstm     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato seasonal_naive     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato seasonal_naive     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato seasonal_naive     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato          arima     1  VALID                  12              3.0      True 166.282866 167.476552      74.821623    704.607992            2.0                NaN          -0.384003                True                                                                                                                                     Non-invertible starting MA parameters found. Using zeros as starting parameters.
Tomato          arima     2  VALID                  16              3.0      True 225.940231 228.064381     105.047160    632.498172            3.0           0.163876          -0.340959                True                                                                                                                                     Non-invertible starting MA parameters found. Using zeros as starting parameters.
Tomato          arima     3  VALID                  20              3.0      True 298.699040 301.532357     151.218260    684.547584            4.0           0.106146          -0.146688                True                                                                                                                                     Non-invertible starting MA parameters found. Using zeros as starting parameters.
Tomato         sarima     1  VALID                  12              3.0      True 111.590905 111.428635      37.197783    748.128829            2.0                NaN          -0.535547                True SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
Tomato         sarima     2  VALID                  16              3.0      True 169.050162 170.243848      63.860481    660.438741            3.0           0.230553          -0.448664                True SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros.
Tomato         sarima     3  VALID                  20              3.0      True 237.862977 239.987127      74.514157    681.507406            4.0           0.671288          -0.083682                True                                                                                                                                  Non-invertible starting seasonal moving average Using zeros as starting parameters.
Tomato           lstm     1  VALID                  12              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato           lstm     2  VALID                  16              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
Tomato           lstm     3  VALID                  20              NaN      None        NaN        NaN            NaN           NaN            NaN                NaN                NaN               False                                                                                                                                                                                                                     
```

## Diebold-Mariano Comparisons
The DM test uses paired rolling-origin squared forecast errors, Bartlett HAC variance, and the Harvey-Leybourne-Newbold finite-sample correction. A test is reported only when the number of paired origins is at least max(5, horizon + 2). Current comparisons have only three paired origins per horizon, so they are explicitly marked insufficient and no statistical superiority is claimed.

```text
  crop model_a        model_b  horizon loss_function  DM_statistic  p_value  paired_origins                                                                    interpretation
  Rice  sarima seasonal_naive        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima seasonal_naive        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima seasonal_naive        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima seasonal_naive        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
  Rice  sarima          arima        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima          arima        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima          arima        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima          arima        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
  Rice  sarima           lstm        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima           lstm        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima           lstm        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
  Rice  sarima           lstm        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
 Onion    lstm seasonal_naive        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm seasonal_naive        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm seasonal_naive        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm seasonal_naive        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
 Onion    lstm          arima        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm          arima        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm          arima        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm          arima        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
 Onion    lstm         sarima        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm         sarima        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm         sarima        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
 Onion    lstm         sarima        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
Tomato  sarima seasonal_naive        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima seasonal_naive        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima seasonal_naive        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima seasonal_naive        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
Tomato  sarima          arima        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima          arima        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima          arima        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima          arima        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
Tomato  sarima           lstm        1 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima           lstm        2 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima           lstm        3 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 5); no significance conclusion.
Tomato  sarima           lstm        4 squared_error           NaN      NaN               3 Insufficient paired origins (3; requires at least 6); no significance conclusion.
```

`model_a` is the RMSE-selected model and `model_b` is each comparator, including seasonal naive, ARIMA, SARIMA, and LSTM when distinct. `Insufficient paired origins` means no alpha=0.05 inference is made.

## Paper-Reporting Forecast Table
The table contains the requested paper-reporting metrics. Selection uses only mean validation RMSE among valid folds.

```text
  crop          model  valid_folds  failed_folds    mean_MAE    std_MAE   mean_RMSE   std_RMSE  mean_MAPE  std_MAPE     mean_R2     std_R2     h1_RMSE     h2_RMSE     h3_RMSE     h4_RMSE      price_unit
 Onion          arima            3             0 1221.262175 727.149008 1366.133589 759.302576  64.016085 42.299065  -13.182963  16.975910 1366.779223 1466.716385 1530.036167 1846.914310 INR per quintal
 Onion           lstm            3             0  766.780489 661.391847  889.593869 786.346775  31.860920 15.956805   -1.076260   1.031200  530.811495  414.297106 1454.051660 1752.485334 INR per quintal
 Onion         sarima            3             0 1491.961384 886.468901 1583.277308 908.289684  76.885885 46.435080  -18.198517  23.342177 1536.420832 1398.398936 1995.426962 2242.585877 INR per quintal
 Onion seasonal_naive            3             0 1040.333742 543.544673 1273.652590 526.669834  50.607409  6.386635   -7.076359   4.194772  949.131137  449.833014 1659.409542 1934.282412 INR per quintal
  Rice          arima            3             0  101.078636  66.770267  123.250779  86.692352   4.545225  3.324620   -1.887292   1.854708   21.640491   63.046827  161.017725  245.876702 INR per quintal
  Rice           lstm            3             0  564.735782  94.672131  578.757972  83.368279  24.276782  2.167670 -200.745494 224.852965  446.277090  512.193071  629.957257  713.647750 INR per quintal
  Rice         sarima            3             0   85.325470  40.932253  104.562327  47.178286   3.800495  2.129472   -2.806736   4.023463   56.564276   24.612821  116.126101  188.004533 INR per quintal
  Rice seasonal_naive            3             0  238.910744  78.746715  259.213939  77.358601  10.414172  3.468313  -19.746753  12.713219  279.505542  267.468358  262.244641  272.525145 INR per quintal
Tomato          arima            3             0  572.923957 177.329615  782.193410 258.572373  24.396017  5.063904   -0.578832   0.115778 1362.753365  867.026014  202.945657  254.415064 INR per quintal
Tomato           lstm            3             0  653.788586  93.731697  875.586482 178.114433  27.890688  2.201118   -1.280569   0.750704 1402.366600  999.359018  143.937075  455.452899 INR per quintal
Tomato         sarima            3             0  412.557024 156.996084  513.175766 201.480439  19.019306  4.882193    0.281651   0.255561  612.473227  822.556076  105.252694  391.120001 INR per quintal
Tomato seasonal_naive            3             0  491.768097 178.469245  592.567329 209.854361  23.665164  6.831925    0.071205   0.213478  624.346412 1010.575070  224.517220  345.284193 INR per quintal
```

### Selected-model assessment
`beats seasonal naive RMSE` is descriptive, not a significance claim. Interval coverage is unavailable for models without native intervals.

- Rice: sarima; lower mean RMSE than seasonal naive = True; interval coverage = 91.67%; convergence = all converged; warnings = Non-invertible starting seasonal moving average Using zeros as starting parameters. | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. | SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters | SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters; DM vs seasonal naive: Insufficient paired origins (3; requires at least 5); no significance conclusion.; Insufficient paired origins (3; requires at least 6); no significance conclusion.
- Onion: lstm; lower mean RMSE than seasonal naive = True; interval coverage = unavailable; convergence = not applicable; warnings = ; DM vs seasonal naive: Insufficient paired origins (3; requires at least 5); no significance conclusion.; Insufficient paired origins (3; requires at least 6); no significance conclusion.
- Tomato: sarima; lower mean RMSE than seasonal naive = True; interval coverage = 83.33%; convergence = all converged; warnings = Non-invertible starting seasonal moving average Using zeros as starting parameters. | Too few observations to estimate starting parameters for seasonal ARMA. All parameters except for variances will be set to zeros. | SARIMA training size 12 is small for seasonal period 4 with 3 estimated parameters | SARIMA training size 16 is small for seasonal period 4 with 3 estimated parameters; DM vs seasonal naive: Insufficient paired origins (3; requires at least 5); no significance conclusion.; Insufficient paired origins (3; requires at least 6); no significance conclusion.

## Figures
Generated `forecast_validation_rice.png`, `forecast_validation_onion.png`, and `forecast_validation_tomato.png`. Each chart uses INR per quintal throughout and shows historical actuals, rolling-origin validation predictions, validation actuals, and native 95% ARIMA/SARIMA bounds where available.

## sell_store_validation_report.md

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

## warehouse_validation_report.md

# Warehouse Allocation Validation Report

## OBSERVED DATA
- Warehouse file: `tamilnadu_full_warehouse_dataset (1).csv` with 103 unique facilities.
- These are values present in the supplied CSV; repository documentation does not establish whether facilities, capacities, rates, or support flags are verified operational observations. They are not represented here as independently validated real-world warehouse facts.
- Capacity is supplied as `Capacity_MT`; source values range 5.0 to 2000.0 metric tonnes.
- Storage rate column: `Storage_Cost_per_MT`, values 1.52 to 3.00. The source does not declare currency or billing period.
- Crop-support flags and facility coordinates are present. Support counts: {"Rice": 51, "Onion": 60, "Tomato": 47}.
- Sell/store input: `sell_store_decisions.csv`. The evaluator takes one scenario per row matching the RMSE-selected model. These are simulated one-quintal quantities and not observed concurrent farmer demand.
- No farmer origin coordinates or acreage are available in this input.

## ASSUMPTIONS
```json
{
  "capacity_source_unit": "metric_tonne",
  "capacity_target_unit": "quintal",
  "quintals_per_metric_tonne": 10.0,
  "storage_rate_currency": "INR",
  "storage_rate_source_unit": "per_metric_tonne",
  "storage_rate_time_unit": "month",
  "storage_rate_interpretation": "Configurable assumption: Storage_Cost_per_MT is treated as INR per metric tonne per month because the source file does not state currency or billing period.",
  "transport_rate_inr_per_km_per_metric_tonne": 5.0,
  "transport_rate_interpretation": "Scenario assumption retained from routing.compute_transport_cost default; not an observed carrier quote.",
  "transport_distance_method": "haversine_straight_line_from_warehouse_coordinate_centroid",
  "origin_override_latitude": null,
  "origin_override_longitude": null,
  "origin_interpretation": "No farmer origins are available. Unless both overrides are set, use the arithmetic centroid of warehouse coordinates as a synthetic reference origin; resulting distances are straight-line proxies, not road distances or farmer routes.",
  "unallocated_penalty_inr_per_quintal": 1000000.0,
  "unallocated_penalty_interpretation": "Computational feasibility penalty only, not included in reported storage-plus-transport total cost and not an observed economic loss.",
  "sensitivity": {
    "storage_cost_multipliers": [
      0.5,
      1.0,
      1.5,
      2.0
    ],
    "transport_cost_multipliers": [
      0.5,
      1.0,
      1.5,
      2.0
    ],
    "available_quantity_multipliers": [
      0.5,
      1.0,
      1.5
    ]
  }
}
```
- Explicit conversion: 1 metric tonne = 10 quintals; therefore capacity_quintal = Capacity_MT x 10 and rate INR/quintal/month = Storage_Cost_per_MT / 10.
- Storage rate is assumed to mean INR/metric-tonne/month for calculation, although the source column does not specify currency/time. Sell/store `storage_duration` supplies months.
- Transport rate uses the existing routing default 5.0 per km per metric tonne, interpreted as INR/km/MT as a configurable scenario assumption.
- Origin is arithmetic centroid of warehouse coordinates; synthetic reference origin, not a farmer location; reference coordinate = (10.872450, 77.896333). Distances are haversine straight-line proxies and are not road distances or farmer routes.
- A 1,000,000 INR/quintal shortage penalty is used only to keep the optimization feasible when supply cannot be assigned. It is not included in reported storage-plus-transport cost and is not an observed economic cost.

## SIMULATED VALUES
Each sell/store row is an independent what-if allocation case. A row's quantity is treated as available to store for warehouse analysis regardless of its sell/store action; this isolates warehouse allocation from the upstream economic decision. Aggregated tables average across independent historical cases and do not represent simultaneous network occupancy.

## MILP Formulation
For crop c and compatible warehouse j, continuous decision variable x[c,j] >= 0 is allocated quintals; u[c] >= 0 is unallocated quantity.

Minimize:
`sum_j x[c,j] * (storage_rate[c,j] * duration + distance[c,j] * transport_rate / 10) + shortage_penalty * u[c]`

Subject to:
- `sum_j x[c,j] + u[c] = available_quantity[c]`
- `x[c,j] <= capacity_quintal[j]`
- `x[c,j] = 0` for unsupported crop/warehouse pairs (implemented by omitting those variables)
- `x[c,j] >= 0`, `u[c] >= 0`

Transport rate is divided by 10 because the rate is per metric tonne and quantities are quintals. Solver: PuLP CBC. All 36 base scenario solves returned statuses {"Optimal": 36}. CBC reported `Optimal`; a separate numeric optimality gap is not exposed by this PuLP command. Independently recomputed cost/objective checks pass for zero-unallocated cases; the reported objective additionally includes the explicit shortage penalty when unallocated quantity is positive. Total cost columns report storage plus transport only.

## Metrics and Results
- Base selected-model allocation scenarios: 36; crop/scenario summaries: 36.
- MILP constraint violation count across base scenarios: 0.
- Metrics include allocation, unallocated quantity, capacity utilization, storage and transport cost, total cost, average cost per allocated quintal, weighted straight-line distance, and warehouses used.
- Warehouse capacity constraints use per-scenario allocation, not sums across independent scenarios.

## OPTIMIZED VALUES
The following are solver-produced scenario means under the assumptions above, not observed costs or operational outcomes:

```text
  crop  scenarios  mean_allocated_quintal  mean_unallocated_quintal  mean_storage_cost_inr  mean_transport_cost_inr  mean_total_cost_inr  max_constraint_violations
 Onion         12                     1.0                       0.0                1.28625                22.971292            24.257542                          0
  Rice         12                     1.0                       0.0                1.28625                22.971292            24.257542                          0
Tomato         12                     1.0                       0.0                1.99500                11.057253            13.052253                          0
```

### Baseline comparison (mean per scenario)
```text
  crop              method  mean_cost_inr  mean_storage_cost_inr  mean_transport_cost_inr  mean_allocated_quintal  mean_unallocated_quintal  mean_warehouses_used
 Onion     Existing Method     119.831389                1.56750               118.263889                     1.0                       0.0                   1.0
 Onion Lowest Storage Cost      92.298628                1.14000                91.158628                     1.0                       0.0                   1.0
 Onion                MILP      24.257542                1.28625                22.971292                     1.0                       0.0                   1.0
 Onion    Nearest Feasible      24.494584                1.86000                22.634584                     1.0                       0.0                   1.0
  Rice     Existing Method     119.831389                1.56750               118.263889                     1.0                       0.0                   1.0
  Rice Lowest Storage Cost      31.838908                1.15500                30.683908                     1.0                       0.0                   1.0
  Rice                MILP      24.257542                1.28625                22.971292                     1.0                       0.0                   1.0
  Rice    Nearest Feasible      24.494584                1.86000                22.634584                     1.0                       0.0                   1.0
Tomato     Existing Method     120.815846                1.29000               119.525846                     1.0                       0.0                   1.0
Tomato Lowest Storage Cost      72.781005                1.18500                71.596005                     1.0                       0.0                   1.0
Tomato                MILP      13.052253                1.99500                11.057253                     1.0                       0.0                   1.0
Tomato    Nearest Feasible      13.052253                1.99500                11.057253                     1.0                       0.0                   1.0
```

## Baselines
- `Nearest Feasible`: greedily fill compatible warehouses in ascending straight-line distance.
- `Lowest Storage Cost`: greedily fill compatible warehouses by source storage rate; transport remains in reported cost but is not used to order this baseline.
- `Existing Method`: existing max-fill `allocate_storage` objective with crop-compatible warehouses prefiltered; it does not minimize economic cost.
- `MILP`: explicit storage-plus-transport cost minimization with the same scenario assumptions.

Methods are reported numerically without rank or winner labels.

## Sensitivity Analysis
These are scenario multipliers, not real-world probabilities.

### Storage cost multiplier
```text
  crop  scenario_multiplier  mean_cost_inr  mean_unallocated_quintal
 Onion                  0.5      23.549320                       0.0
 Onion                  1.0      24.257542                       0.0
 Onion                  1.5      24.900667                       0.0
 Onion                  2.0      25.528528                       0.0
  Rice                  0.5      23.549320                       0.0
  Rice                  1.0      24.257542                       0.0
  Rice                  1.5      24.900667                       0.0
  Rice                  2.0      25.528528                       0.0
Tomato                  0.5      12.054753                       0.0
Tomato                  1.0      13.052253                       0.0
Tomato                  1.5      14.049753                       0.0
Tomato                  2.0      15.047253                       0.0
```

### Transport cost multiplier
```text
  crop  scenario_multiplier  mean_cost_inr  mean_unallocated_quintal
 Onion                  0.5      12.764264                       0.0
 Onion                  1.0      24.257542                       0.0
 Onion                  1.5      35.702334                       0.0
 Onion                  2.0      47.098640                       0.0
  Rice                  0.5      12.764264                       0.0
  Rice                  1.0      24.257542                       0.0
  Rice                  1.5      35.702334                       0.0
  Rice                  2.0      47.098640                       0.0
Tomato                  0.5       7.523626                       0.0
Tomato                  1.0      13.052253                       0.0
Tomato                  1.5      18.580879                       0.0
Tomato                  2.0      24.109505                       0.0
```

### Available quantity multiplier
```text
  crop  scenario_multiplier  mean_cost_inr  mean_unallocated_quintal
 Onion                  0.5      12.128771                       0.0
 Onion                  1.0      24.257542                       0.0
 Onion                  1.5      36.386313                       0.0
  Rice                  0.5      12.128771                       0.0
  Rice                  1.0      24.257542                       0.0
  Rice                  1.5      36.386313                       0.0
Tomato                  0.5       6.526126                       0.0
Tomato                  1.0      13.052253                       0.0
Tomato                  1.5      19.578379                       0.0
```

## Paper Tables
### Table Z. Warehouse allocation outcomes (mean per independent scenario)
```text
  Crop              Method  Allocated Quantity (quintal)  Unallocated Quantity (quintal)  Storage Cost (INR)  Transport Cost (INR)  Total Cost (INR)  Average Cost (INR/quintal)  Warehouses Used
 Onion     Existing Method                           1.0                             0.0             1.56750            118.263889        119.831389                  119.831389              1.0
 Onion Lowest Storage Cost                           1.0                             0.0             1.14000             91.158628         92.298628                   92.298628              1.0
 Onion                MILP                           1.0                             0.0             1.28625             22.971292         24.257542                   24.257542              1.0
 Onion    Nearest Feasible                           1.0                             0.0             1.86000             22.634584         24.494584                   24.494584              1.0
  Rice     Existing Method                           1.0                             0.0             1.56750            118.263889        119.831389                  119.831389              1.0
  Rice Lowest Storage Cost                           1.0                             0.0             1.15500             30.683908         31.838908                   31.838908              1.0
  Rice                MILP                           1.0                             0.0             1.28625             22.971292         24.257542                   24.257542              1.0
  Rice    Nearest Feasible                           1.0                             0.0             1.86000             22.634584         24.494584                   24.494584              1.0
Tomato     Existing Method                           1.0                             0.0             1.29000            119.525846        120.815846                  120.815846              1.0
Tomato Lowest Storage Cost                           1.0                             0.0             1.18500             71.596005         72.781005                   72.781005              1.0
Tomato                MILP                           1.0                             0.0             1.99500             11.057253         13.052253                   13.052253              1.0
Tomato    Nearest Feasible                           1.0                             0.0             1.99500             11.057253         13.052253                   13.052253              1.0
```

### Table W. Warehouse utilization (mean per independent scenario)
```text
Warehouse  Capacity (quintal)  Allocated (quintal)  Utilization (%)  Storage Cost (INR)  Transport Cost (INR)
    WH001               250.0             0.000000         0.000000              0.0000              0.000000
    WH002               250.0             0.000000         0.000000              0.0000              0.000000
    WH003               250.0             0.000000         0.000000              0.0000              0.000000
    WH004               250.0             0.000000         0.000000              0.0000              0.000000
    WH005               250.0             0.000000         0.000000              0.0000              0.000000
    WH006               500.0             0.000000         0.000000              0.0000              0.000000
    WH007              5000.0             0.000000         0.000000              0.0000              0.000000
    WH008              5000.0             0.000000         0.000000              0.0000              0.000000
    WH009               250.0             0.000000         0.000000              0.0000              0.000000
    WH010               150.0             0.000000         0.000000              0.0000              0.000000
    WH011              3150.0             0.000000         0.000000              0.0000              0.000000
    WH012               400.0             0.000000         0.000000              0.0000              0.000000
    WH013               400.0             0.000000         0.000000              0.0000              0.000000
    WH014               400.0             0.000000         0.000000              0.0000              0.000000
    WH015               400.0             0.000000         0.000000              0.0000              0.000000
    WH016               250.0             0.000000         0.000000              0.0000              0.000000
    WH017               250.0             0.000000         0.000000              0.0000              0.000000
    WH018               250.0             0.000000         0.000000              0.0000              0.000000
    WH019             10000.0             0.000000         0.000000              0.0000              0.000000
    WH020               250.0             0.000000         0.000000              0.0000              0.000000
    WH021               250.0             0.000000         0.000000              0.0000              0.000000
    WH022               500.0             0.000000         0.000000              0.0000              0.000000
    WH023              1000.0             0.000000         0.000000              0.0000              0.000000
    WH024              1100.0             0.000000         0.000000              0.0000              0.000000
    WH025               250.0             0.000000         0.000000              0.0000              0.000000
    WH026               300.0             0.000000         0.000000              0.0000              0.000000
    WH027               300.0             0.000000         0.000000              0.0000              0.000000
    WH028                50.0             0.000000         0.000000              0.0000              0.000000
    WH029               250.0             0.000000         0.000000              0.0000              0.000000
    WH030              5000.0             0.000000         0.000000              0.0000              0.000000
    WH031              5000.0             0.000000         0.000000              0.0000              0.000000
    WH032               250.0             0.000000         0.000000              0.0000              0.000000
    WH033               250.0             0.000000         0.000000              0.0000              0.000000
    WH034               250.0             0.000000         0.000000              0.0000              0.000000
    WH035               250.0             0.000000         0.000000              0.0000              0.000000
    WH036               250.0             0.000000         0.000000              0.0000              0.000000
    WH037              1000.0             0.000000         0.000000              0.0000              0.000000
    WH038             10000.0             0.000000         0.000000              0.0000              0.000000
    WH039               250.0             0.000000         0.000000              0.0000              0.000000
    WH040               250.0             0.333333         0.133333              0.6650              3.685751
    WH041               750.0             0.000000         0.000000              0.0000              0.000000
    WH042               250.0             0.000000         0.000000              0.0000              0.000000
    WH043               250.0             0.000000         0.000000              0.0000              0.000000
    WH044               750.0             0.000000         0.000000              0.0000              0.000000
    WH045              3750.0             0.000000         0.000000              0.0000              0.000000
    WH046               250.0             0.000000         0.000000              0.0000              0.000000
    WH047               250.0             0.000000         0.000000              0.0000              0.000000
    WH048               250.0             0.000000         0.000000              0.0000              0.000000
    WH049              2200.0             0.000000         0.000000              0.0000              0.000000
    WH050               500.0             0.000000         0.000000              0.0000              0.000000
    WH051              6000.0             0.000000         0.000000              0.0000              0.000000
    WH052               250.0             0.000000         0.000000              0.0000              0.000000
    WH053               250.0             0.000000         0.000000              0.0000              0.000000
    WH054               250.0             0.000000         0.000000              0.0000              0.000000
    WH055               250.0             0.000000         0.000000              0.0000              0.000000
    WH056               250.0             0.500000         0.200000              0.7335             11.541764
    WH057                50.0             0.166667         0.333333              0.1240              3.772431
    WH058               100.0             0.000000         0.000000              0.0000              0.000000
    WH059               100.0             0.000000         0.000000              0.0000              0.000000
    WH060               250.0             0.000000         0.000000              0.0000              0.000000
    WH061              5000.0             0.000000         0.000000              0.0000              0.000000
    WH062               100.0             0.000000         0.000000              0.0000              0.000000
    WH063               100.0             0.000000         0.000000              0.0000              0.000000
    WH064                70.0             0.000000         0.000000              0.0000              0.000000
    WH065               100.0             0.000000         0.000000              0.0000              0.000000
    WH066               100.0             0.000000         0.000000              0.0000              0.000000
    WH067               500.0             0.000000         0.000000              0.0000              0.000000
    WH068               250.0             0.000000         0.000000              0.0000              0.000000
    WH069               250.0             0.000000         0.000000              0.0000              0.000000
    WH070              1000.0             0.000000         0.000000              0.0000              0.000000
    WH071               250.0             0.000000         0.000000              0.0000              0.000000
    WH072              1000.0             0.000000         0.000000              0.0000              0.000000
    WH073               250.0             0.000000         0.000000              0.0000              0.000000
    WH074             20000.0             0.000000         0.000000              0.0000              0.000000
    WH075               100.0             0.000000         0.000000              0.0000              0.000000
    WH076               100.0             0.000000         0.000000              0.0000              0.000000
    WH077               100.0             0.000000         0.000000              0.0000              0.000000
    WH078               250.0             0.000000         0.000000              0.0000              0.000000
    WH079               250.0             0.000000         0.000000              0.0000              0.000000
    WH080               500.0             0.000000         0.000000              0.0000              0.000000
    WH081               250.0             0.000000         0.000000              0.0000              0.000000
    WH082              1250.0             0.000000         0.000000              0.0000              0.000000
    WH083               250.0             0.000000         0.000000              0.0000              0.000000
    WH084              1000.0             0.000000         0.000000              0.0000              0.000000
    WH085               250.0             0.000000         0.000000              0.0000              0.000000
    WH086               250.0             0.000000         0.000000              0.0000              0.000000
    WH087               250.0             0.000000         0.000000              0.0000              0.000000
    WH088               500.0             0.000000         0.000000              0.0000              0.000000
    WH089                50.0             0.000000         0.000000              0.0000              0.000000
    WH090              5000.0             0.000000         0.000000              0.0000              0.000000
    WH091               250.0             0.000000         0.000000              0.0000              0.000000
    WH092               380.0             0.000000         0.000000              0.0000              0.000000
    WH093               500.0             0.000000         0.000000              0.0000              0.000000
    WH094               250.0             0.000000         0.000000              0.0000              0.000000
    WH095               250.0             0.000000         0.000000              0.0000              0.000000
    WH096               250.0             0.000000         0.000000              0.0000              0.000000
    WH097               250.0             0.000000         0.000000              0.0000              0.000000
    WH098                50.0             0.000000         0.000000              0.0000              0.000000
    WH099              1000.0             0.000000         0.000000              0.0000              0.000000
    WH100               250.0             0.000000         0.000000              0.0000              0.000000
    WH101               250.0             0.000000         0.000000              0.0000              0.000000
    WH102               100.0             0.000000         0.000000              0.0000              0.000000
    WH103               100.0             0.000000         0.000000              0.0000              0.000000
```

## Limitations
- Warehouse costs, units, and billing periods are incompletely documented. The assumed INR/MT/month interpretation must be validated before operational use.
- The upstream sell/store quantity is a synthetic 1-quintal scenario, not observed farmer demand; scenario totals are not concurrent loads.
- Farmer origins are unavailable. Centroid-origin haversine distances are reference proxies only; no road-routing optimization is claimed.
- Transport rate is a configurable assumed value, not a carrier quote. Permits, fuel surcharges, spoilage, and route fixed costs are not included.
- Compatible capacity is much larger than the simulated lots, so utilization values are very small and should not be interpreted as observed warehouse fill rates.
- The result is a feasible mathematical allocation under the stated assumptions, not evidence of real-world cost savings or warehouse efficiency improvement.


## Limitations and no-overclaim statement
Forecast, sell/store, and warehouse outputs are treated as supplied research artifacts and are not rewritten. Warehouse and origin provenance, cost assumptions, and transport rate limitations remain as stated in those phase reports. No real-world farmer savings, actual road-route optimality, or causal income claims are made.
