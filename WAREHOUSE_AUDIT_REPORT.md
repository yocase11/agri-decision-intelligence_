# Warehouse Allocation Audit

## Scope and timing
This report records the existing warehouse allocation, TOPSIS, routing, and direct caller behavior before any warehouse optimization logic was changed. No changes have been made to `storage_opt.py`, `mcdm.py`, `routing.py`, warehouse data, or the sell/store artifacts for this phase.

## Observed data
`tamilnadu_full_warehouse_dataset (1).csv` contains 103 unique warehouse IDs and no nulls in the inspected fields. It has:
- `Capacity_MT` (5 to 2,000), assumed by the column name to be metric tonnes; 1 MT = 10 quintals.
- `Storage_Cost_per_MT` (1.52 to 3.00), but the file/schema does not state currency, whether this is per metric tonne or a total charge, or its time period.
- Latitude and longitude for each warehouse.
- Binary crop compatibility flags: 51 Rice-supported, 60 Onion-supported, 47 Tomato-supported. Thirteen records support none of the three crops.
- `Spoilage_Rate`, which is not used by the current allocation MILP or routing optimizer.

The upstream `sell_store_decisions.csv` contains simulated 1-quintal decision quantities, not observed farmer lot sizes. It contains no farmer location. The farmer dataset contains `Crop_Yield_tonnes_per_acre`, but no acreage or latitude/longitude, so summing yield-per-acre rows does not provide a justified available quantity or origin.

## Existing allocation MILP: `src/storage_opt.py`
Decision variable: continuous nonnegative `allocation[(warehouse, crop)]`.

Objective: maximize total allocated quantity, not minimize storage or transport cost.

Constraints:
- For each warehouse, sum allocated quantities across crops is at most its supplied capacity.
- For each crop, sum allocated quantities across warehouses is at most its supplied quantity.
- Variables have lower bound zero.

Missing formulation elements:
- No crop compatibility constraints.
- No requirement that requested quantity be allocated, no unallocated variable, and no shortage penalty.
- No storage duration, storage cost, distance, transport cost, spoilage, solver status, or objective diagnostics are returned.
- The function accepts numeric units without validation; its direct caller supplies MT, while its generic API does not declare a unit.
- The returned solution is not checked for capacity/quantity residuals.

In `decision_support.build_storage_plan`, the input warehouse list is filtered to crop-compatible rows before calling this MILP, so that particular caller enforces compatibility indirectly. It passes capacity and demand in MT. The quantity upstream is derived by summing tonnes-per-acre values without acreage, then converting to kg and MT; it is not a defensible farm total.

## Existing TOPSIS: `src/mcdm.py`
`load_warehouses` filters by the crop support flag and attaches a synthetic facility score (Cold Storage=1, other=0.5). `topsis_selection` scores one warehouse at a time using straight-line haversine distance, the `Storage_Cost_per_MT` value, capacity, and facility score. Default weights are 0.3, 0.3, 0.2, and 0.2. The `quantity_mt` argument is unused, so feasibility against lot size is not tested. TOPSIS does not allocate or split quantities and does not include monetary transport cost in an economic objective.

## Existing routing and greedy warehouse selection: `src/routing.py`
`optimize_warehouse` obtains OSRM road distances when available, otherwise falls back to haversine straight-line distance. It filters a candidate if `Capacity_MT < quantity_kg / 1000`, then chooses one warehouse minimizing its locally computed storage plus transport cost. It does not split allocation across facilities. Crop compatibility is left to the caller's warehouse list.

`compute_transport_cost` calculates:
- distance (km) x quantity (metric tonnes) x configured rate (default 5.0 per km per tonne),
- plus configured fuel and driver rates per km and fixed permit/toll amounts.
The currency and time units for these rates are not encoded in the warehouse dataset. The calculation returns a total amount but not a per-quintal rate. OSRM distance is road distance; haversine is not road distance.

`decision_support.estimate_transport_cost` instead calls `transport_opt.simple_vrp_distance`, which measures Euclidean degrees through a route beginning at (0,0), then multiplies that number by quantity and a separate default 0.05 rate. Its distance is not km and is not suitable as a transport-cost estimate.

## Other optimization and fallback paths
- `src/advanced_decision_system.optimize_warehouse_vrp` is a greedy one-facility selector. Its `vrp_milp` uses binary warehouse selection and distance x 5 x tonnes as objective, constrains each selected facility's capacity in the input's unspecified `capacity`/`quantity_kg` units, and omits storage cost and crop compatibility.
- The advanced MILP is a single-origin selection, not a multi-crop quantity allocation.
- `custom_ui.load_warehouses_for_crop` falls back to the first five rows if a crop has no supported facilities, and creates a fabricated fallback warehouse if the dataset fails to load. That path is excluded from research results.
- `generate_performance_report.py` has hard-coded synthetic warehouse defaults; those are excluded.
- `src/app.py` displays TOPSIS facility recommendations; the integrated and API callers use the legacy paths above.

## Callers
- `decision_support.build_storage_plan` calls the max-fill MILP with crop-filtered warehouses.
- `decision_support.run_decision_support` calls TOPSIS only for route/warehouse recommendation; its transport estimate is a separate degree-based stub.
- `decision_support.run_single_farmer_decision` calls `routing.optimize_warehouse` with a UI/API quantity in kg.
- `custom_ui.py` has its own warehouse loader and fallback facilities.
- `src/app.py` loads compatible facilities and displays a TOPSIS selection.
- `src/advanced_decision_system.py` contains greedy and single-facility binary selectors.
- `tests/test_integrated_pipeline.py` exercises TOPSIS and route calculation but not the storage MILP's capacity, compatibility, or objective.
- The warehouse research CLI will be added to `src/run_full_pipeline.py` as an isolated mode consuming existing sell/store outputs; default forecasting and sell/store modes remain unchanged.

## Unit and objective conclusions
- Source capacity is labeled MT. Research calculations will convert 1 MT = 10 quintals explicitly.
- Source storage-rate timing/currency is underspecified. A configurable scenario assumption is required to compute economic cost; it must be marked as an assumption, not observed invoice data.
- Upstream quantity is a simulated quintal value and will be treated as such; no kg/tonne inference will be made from the farmer yield-per-acre file.
- No farmer-origin location exists in sell/store results or farmer data. A transparent configurable reference-origin scenario derived from the warehouse coordinate centroid is technically needed for distance baselines; resulting haversine distances will be labeled straight-line proxy distances, not road distances or farmer routes.
- The current max-fill MILP maximizes quantity and does not optimize cost. TOPSIS is a weighted ranking, and `routing.optimize_warehouse` is a greedy one-facility cost comparison; neither is the requested allocation-cost MILP.

## Falsifiable local hypothesis
The existing `allocate_storage` solution can change when warehouse insertion order changes because all feasible quantity assignments have the same max-quantity objective, and it cannot enforce crop compatibility unless callers prefilter. A small two-warehouse fixture with unequal costs should therefore be allocated differently by an explicit cost-minimizing MILP than by the current max-fill objective, while satisfying capacity and demand balance.

## Planned research boundary
The proposed evaluator will operate independently of the legacy UI/routing functions. It will use only crop-compatible warehouses, per-scenario sell/store quantity rows, explicit capacity and storage-rate conversions, and a clearly labeled origin/transport assumption. It will separately report allocation, storage cost, transport cost, solver status, and constraint residuals; it will not modify forecasting results, sell/store calculations, routing, or dashboard code.
