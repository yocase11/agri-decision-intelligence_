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
