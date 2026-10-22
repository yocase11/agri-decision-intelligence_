def simple_vrp_distance(locations, depot=(0,0)):
    """Very small stub: compute route distance from depot to each location and back."""
    import math
    dist = 0.0
    current = depot
    for loc in locations:
        dist += math.dist(current, loc)
        current = loc
    dist += math.dist(current, depot)
    return dist
