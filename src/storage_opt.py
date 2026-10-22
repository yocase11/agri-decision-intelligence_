from pulp import LpProblem, LpVariable, lpSum, LpMaximize


def allocate_storage(warehouses, quantities):
    """Simple MILP to allocate quantities to warehouses by capacity to maximize use."""
    prob = LpProblem("storage_allocation", LpMaximize)

    allocation = {(w, c): LpVariable(f"alloc_{w}_{c}", lowBound=0) for w in warehouses for c in quantities}

    # objective maximize total assigned
    prob += lpSum(allocation[w, c] for w in warehouses for c in quantities)

    # capacity constraints
    for w, cap in warehouses.items():
        prob += lpSum(allocation[w, c] for c in quantities) <= cap

    # quantity constraints
    for c, qty in quantities.items():
        prob += lpSum(allocation[w, c] for w in warehouses) <= qty

    prob.solve()
    return { (w,c): allocation[w,c].value() for w in warehouses for c in quantities }
