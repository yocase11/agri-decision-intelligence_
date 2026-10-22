import requests
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_road_distance_and_time(farmer_location, warehouse_location):
    lat1, lon1 = farmer_location
    lat2, lon2 = warehouse_location
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 'Ok' and data.get('routes'):
            distance_km = data['routes'][0]['distance'] / 1000.0
            duration_min = data['routes'][0]['duration'] / 60.0
            return distance_km, duration_min
    except Exception:
        pass
    return None, None


def compute_transport_cost(distance_km, quantity_kg, cost_per_km_per_tonne=5.0, fuel_rate=0.0, permit_cost=0.0, tolls=0.0, driver_wage_per_km=0.0):
    quantity_tonnes = quantity_kg / 1000.0
    base_cost = distance_km * quantity_tonnes * cost_per_km_per_tonne
    fuel_surcharge = distance_km * fuel_rate
    driver_pay = distance_km * driver_wage_per_km
    return round(base_cost + fuel_surcharge + permit_cost + tolls + driver_pay, 2)


def get_distance_matrix(farmer_location, warehouses):
    coordinates = [f"{farmer_location[1]},{farmer_location[0]}"]
    for w in warehouses:
        coordinates.append(f"{w['Longitude']},{w['Latitude']}")

    coord_str = ";".join(coordinates)
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_str}?annotations=distance,duration"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('code') == 'Ok':
            distances = data.get('distances')
            durations = data.get('durations')
            return distances, durations
    except Exception:
        pass

    return None, None


def optimize_warehouse(farmer_location, warehouses, quantity_kg, cost_per_km_per_tonne=5.0, fuel_rate=0.0, permit_cost=0.0, tolls=0.0, driver_wage_per_km=0.0, offline_mode=False):
    if not warehouses:
        return None

    distances, durations = get_distance_matrix(farmer_location, warehouses)

    candidate_info = []
    for i, w in enumerate(warehouses):
        if distances and durations and distances[0][i + 1] is not None:
            distance_km = distances[0][i + 1] / 1000.0
            travel_time_min = durations[0][i + 1] / 60.0
            used_osrm = True
        else:
            distance_km = haversine_distance(farmer_location[0], farmer_location[1], w['Latitude'], w['Longitude'])
            travel_time_min = max(1.0, distance_km * 2.0)
            used_osrm = False

        storage_cost_mt = float(w.get('Storage_Cost_per_MT', 0.0))
        storage_cost = storage_cost_mt * (quantity_kg / 1000.0)
        transport_cost = compute_transport_cost(distance_km, quantity_kg, cost_per_km_per_tonne=cost_per_km_per_tonne, fuel_rate=fuel_rate, permit_cost=permit_cost, tolls=tolls, driver_wage_per_km=driver_wage_per_km)

        # enforce capacity
        capacity_ok = float(w.get('Capacity_MT', 0.0)) >= (quantity_kg / 1000.0)
        if not capacity_ok:
            continue

        total_cost = transport_cost + storage_cost

        candidate_info.append({
            'warehouse': w,
            'distance_km': round(distance_km, 2),
            'travel_time_min': round(travel_time_min, 2),
            'transport_cost': round(transport_cost, 2),
            'storage_cost': round(storage_cost, 2),
            'total_cost': round(total_cost, 2),
            'used_osrm': used_osrm,
        })

    if not candidate_info:
        return None

    best_option = min(candidate_info, key=lambda x: x['total_cost'])
    return best_option


def best_route(farmer_lat, farmer_lon, warehouse_lat, warehouse_lon, quantity_kg, offline_mode=False, cost_per_km_per_tonne=5.0, fuel_rate=0.0, permit_cost=0.0, tolls=0.0, driver_wage_per_km=0.0):
    farmer_location = (farmer_lat, farmer_lon)
    warehouse_location = (warehouse_lat, warehouse_lon)

    distance_km = None
    duration_min = None

    if not offline_mode:
        distance_km, duration_min = get_road_distance_and_time(farmer_location, warehouse_location)

    if distance_km is None:
        distance_km = haversine_distance(farmer_lat, farmer_lon, warehouse_lat, warehouse_lon)
        duration_min = max(1.0, distance_km * 2.0)  # fallback approx

    estimated_cost = compute_transport_cost(
        distance_km,
        quantity_kg,
        cost_per_km_per_tonne=cost_per_km_per_tonne,
        fuel_rate=fuel_rate,
        permit_cost=permit_cost,
        tolls=tolls,
        driver_wage_per_km=driver_wage_per_km
    )

    return {
        'distance_km': round(distance_km, 2),
        'travel_time_min': round(duration_min, 2),
        'estimated_cost': estimated_cost,
        'route': [(farmer_lat, farmer_lon), (warehouse_lat, warehouse_lon)],
        'is_offline': offline_mode,
        'used_osrm': (not offline_mode and distance_km is not None),
    }
