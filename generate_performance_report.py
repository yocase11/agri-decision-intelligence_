#!/usr/bin/env python
"""
Standalone script to generate performance metrics HTML report
without running the Flask dashboard.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from complete_system import run_full_system


def load_crop_price_series(crop):
    """Load and adjust historical prices for a crop."""
    try:
        price_file = 'price dataset (1).csv'
        if not os.path.exists(price_file):
            print(f"Warning: {price_file} not found. Using synthetic data.")
            return np.array([50, 52, 51, 53, 55, 54, 56, 58, 57, 59, 
                           60, 62, 61, 63, 65, 64, 66, 68, 67, 69] * 2)
        
        df = pd.read_csv(price_file)
        
        # Find price column (could be named differently)
        price_columns = [col for col in df.columns if 'price' in col.lower() or 'cost' in col.lower()]
        if not price_columns:
            # Try first numeric column after commodity
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            price_columns = numeric_cols if numeric_cols else []
        
        if not price_columns:
            print(f"Warning: No price column found. Using synthetic data.")
            return np.array([50, 52, 51, 53, 55, 54, 56, 58, 57, 59, 
                           60, 62, 61, 63, 65, 64, 66, 68, 67, 69] * 2)
        
        price_col = price_columns[0]
        
        # Filter by crop if Commodity column exists
        if 'Commodity' in df.columns:
            crop_data = df[df['Commodity'].str.strip().str.lower() == crop.lower()]
            if crop_data.empty:
                print(f"Warning: {crop} not found in price data. Using first available crop.")
                crop_data = df
        else:
            crop_data = df
        
        prices = crop_data[price_col].dropna().values.astype(float)
        
        # Apply adjustments
        if crop.lower() == 'onion':
            prices = np.maximum(prices, 15)
        elif crop.lower() == 'tomato':
            prices = prices * 6
        elif crop.lower() == 'rice':
            prices = prices / 100
        
        return prices if len(prices) > 0 else np.array([50] * 40)
    
    except Exception as e:
        print(f"Warning: Error loading price data: {e}. Using synthetic data.")
        return np.array([50] * 40)


def load_warehouses_for_crop(crop, quantity_kg, farmer_location):
    """Load warehouse data for a crop."""
    try:
        warehouse_file = 'tamilnadu_full_warehouse_dataset (1).csv'
        if not os.path.exists(warehouse_file):
            print(f"Warning: {warehouse_file} not found. Using synthetic warehouses.")
            return [
                {'name': 'Chennai Hub', 'capacity': 10000, 'cost_per_kg': 2.5, 'spoilage_rate': 0.05,
                 'lat': 13.0827, 'lon': 80.2707, 'distance_km': 5},
                {'name': 'Madras Storage', 'capacity': 5000, 'cost_per_kg': 3.0, 'spoilage_rate': 0.08,
                 'lat': 13.1939, 'lon': 80.1829, 'distance_km': 15}
            ]
        
        df = pd.read_csv(warehouse_file)
        
        # Filter by crop if applicable
        warehouses = []
        for idx, row in df.head(10).iterrows():  # Use first 10 warehouses
            try:
                warehouse = {
                    'name': str(row.get('warehouse_name', f'Warehouse {idx}')).strip(),
                    'capacity': float(row.get('capacity', 5000)),
                    'cost_per_kg': float(row.get('cost_per_kg', 2.5)),
                    'spoilage_rate': float(row.get('spoilage_rate', 0.05)),
                    'lat': float(row.get('latitude', 13.0)),
                    'lon': float(row.get('longitude', 80.0))
                }
                warehouses.append(warehouse)
            except Exception as e:
                continue
        
        return warehouses if warehouses else load_warehouses_for_crop(crop, quantity_kg, farmer_location)
    
    except Exception as e:
        print(f"Error loading warehouse data: {e}")
        return load_warehouses_for_crop(crop, quantity_kg, farmer_location)


def generate_report(crop='Onion', quantity_kg=1000, 
                   lat=13.0827, lon=80.2707,
                   demand_index=1.0, rainfall=50, temperature=28, humidity=70):
    """Generate performance metrics report."""
    
    print(f"\n{'='*60}")
    print(f"Generating Performance Report")
    print(f"{'='*60}")
    print(f"Configuration:")
    print(f"  Crop: {crop}")
    print(f"  Quantity: {quantity_kg} kg")
    print(f"  Location: ({lat}, {lon})")
    print(f"  Demand Index: {demand_index}")
    print(f"{'='*60}\n")
    
    try:
        # Load data
        print("Loading price data...", end=" ")
        price_series = load_crop_price_series(crop)
        print(f"[OK] ({len(price_series)} data points)")
        
        print("Loading warehouse data...", end=" ")
        warehouses = load_warehouses_for_crop(crop, quantity_kg, (lat, lon))
        print(f"[OK] ({len(warehouses)} warehouses)")
        
        # Prepare inputs
        weather_data = {
            'rainfall': rainfall,
            'temperature': temperature,
            'humidity': humidity
        }
        
        farmer_location = (lat, lon)
        
        current_price = float(price_series[-1]) if len(price_series) > 0 else 50
        
        cost_params = {
            'unit_cost': 30 if crop.lower() == 'onion' else 40,
            'holding_cost': 2 if crop.lower() == 'onion' else 3,
            'stockout_cost': 50 if crop.lower() == 'onion' else 60,
            'transport_cost': 5,
            'storage_cost': 3,
            'current_price': current_price
        }
        
        # Run the complete system
        print("Running complete forecasting & decision system...", end=" ")
        result = run_full_system(
            price_series=price_series,
            weather_data=weather_data,
            demand_index=demand_index,
            warehouses=warehouses,
            farmer_location=farmer_location,
            quantity_kg=quantity_kg,
            cost_params=cost_params
        )
        print("[OK]")
        
        # Render template
        print("Rendering HTML template...", end=" ")
        template_dir = os.path.dirname(os.path.abspath(__file__))
        env = Environment(loader=FileSystemLoader(os.path.join(template_dir, 'templates')))
        template = env.get_template('performance_metrics_simple.html')
        
        html_content = template.render(
            result=result,
            selected_crop=crop,
            quantity_kg=quantity_kg,
            farmer_location=f"({lat:.4f}, {lon:.4f})",
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            error=None
        )
        print("[OK]")
        
        # Save to file
        output_dir = os.path.join(template_dir, 'models')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'performance_metrics_report.html')
        
        print(f"Saving to file...", end=" ")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[OK]\n")
        
        print(f"{'='*60}")
        print(f"[SUCCESS] Report generated successfully!")
        print(f"{'='*60}")
        print(f"\nOutput file: {output_file}")
        print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")
        print(f"\nYou can now:")
        print(f"  1. Open the file in a browser: {output_file}")
        print(f"  2. Share the HTML file with others")
        print(f"  3. View performance metrics without the server running")
        print(f"{'='*60}\n")
        
        return output_file
    
    except Exception as e:
        print(f"\n[ERROR] Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate performance metrics HTML report')
    parser.add_argument('--crop', default='Onion', help='Crop name (default: Onion)')
    parser.add_argument('--quantity', type=float, default=1000, help='Quantity in kg (default: 1000)')
    parser.add_argument('--lat', type=float, default=13.0827, help='Latitude (default: 13.0827)')
    parser.add_argument('--lon', type=float, default=80.2707, help='Longitude (default: 80.2707)')
    parser.add_argument('--demand', type=float, default=1.0, help='Demand index (default: 1.0)')
    parser.add_argument('--rainfall', type=float, default=50, help='Rainfall in mm (default: 50)')
    parser.add_argument('--temperature', type=float, default=28, help='Temperature in °C (default: 28)')
    parser.add_argument('--humidity', type=float, default=70, help='Humidity % (default: 70)')
    parser.add_argument('--open', action='store_true', help='Open report in browser after generation')
    
    args = parser.parse_args()
    
    output_file = generate_report(
        crop=args.crop,
        quantity_kg=args.quantity,
        lat=args.lat,
        lon=args.lon,
        demand_index=args.demand,
        rainfall=args.rainfall,
        temperature=args.temperature,
        humidity=args.humidity
    )
    
    if output_file and args.open:
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(output_file)}')
