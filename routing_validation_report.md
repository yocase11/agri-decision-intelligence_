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
