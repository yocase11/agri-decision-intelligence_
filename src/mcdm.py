import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points."""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def load_warehouses(warehouse_path, crop):
    """Load warehouses that support the crop."""
    df = pd.read_csv(warehouse_path)
    crop_col = f"{crop}_Supported"
    if crop_col not in df.columns:
        return []
    supported = df[df[crop_col] == 1].copy()
    supported['facility_score'] = supported.apply(lambda row: 1 if row['Storage_Type'] == 'Cold Storage' else 0.5, axis=1)  # simple score
    return supported.to_dict('records')


def topsis_selection(warehouses, farmer_lat, farmer_lon, quantity_mt, weights=None):
    """Select best warehouse using TOPSIS."""
    if not warehouses:
        return None

    if weights is None:
        weights = {"distance": 0.3, "cost": 0.3, "capacity": 0.2, "facility": 0.2}

    # Criteria: distance (min), cost (min), capacity (max), facility (max)
    criteria = []
    for wh in warehouses:
        dist = haversine(farmer_lat, farmer_lon, wh['Latitude'], wh['Longitude'])
        cost = wh['Storage_Cost_per_MT']  # per MT
        cap = wh['Capacity_MT']
        fac = wh['facility_score']
        criteria.append([dist, cost, cap, fac])

    criteria = np.array(criteria)
    n = len(criteria)
    if n == 0:
        return None

    # Normalize
    norms = np.sqrt((criteria ** 2).sum(axis=0))
    normalized = criteria / norms

    # Weighted
    weighted = normalized * np.array([weights["distance"], weights["cost"], weights["capacity"], weights["facility"]])

    # Ideal best and worst
    ideal_best = np.array([weighted[:, 0].min(), weighted[:, 1].min(), weighted[:, 2].max(), weighted[:, 3].max()])
    ideal_worst = np.array([weighted[:, 0].max(), weighted[:, 1].max(), weighted[:, 2].min(), weighted[:, 3].min()])

    # Distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Scores
    scores = dist_worst / (dist_best + dist_worst)

    # Best index
    best_idx = np.argmax(scores)
    best_wh = warehouses[best_idx]
    best_wh['topsis_score'] = scores[best_idx]
    best_wh['distance_km'] = haversine(farmer_lat, farmer_lon, best_wh['Latitude'], best_wh['Longitude'])

    return best_wh