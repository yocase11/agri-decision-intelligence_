import pandas as pd
import json
import random
from typing import List, Dict

def create_agricultural_qa_dataset():
    """Create a comprehensive Q&A dataset for agricultural chatbot training"""

    # Load existing data
    try:
        farmer_data = pd.read_csv('farmer_crop_dataset (1).csv')
        price_data = pd.read_csv('price dataset (1).csv')
        warehouse_data = pd.read_csv('tamilnadu_full_warehouse_dataset (1).csv')
        decision_history = pd.read_csv('farmer_decision_history.csv')
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return []

    qa_pairs = []

    # Crop information Q&A
    crops = ['Rice', 'Onion', 'Tomato']
    seasons = ['Kharif', 'Rabi', 'Summer', 'Winter']

    for crop in crops:
        # Basic crop info
        qa_pairs.extend([
            {
                "instruction": f"What is {crop.lower()}?",
                "input": "",
                "output": f"{crop} is a major agricultural crop grown in India. It has different varieties and is cultivated in various seasons depending on the region and climate."
            },
            {
                "instruction": f"What are the best seasons to grow {crop.lower()}?",
                "input": "",
                "output": f"{crop} can be grown in multiple seasons including Kharif, Rabi, and Summer seasons, depending on the variety and regional climate conditions."
            }
        ])

        # Price related questions
        crop_prices = price_data[price_data['Crop'] == crop]
        if not crop_prices.empty:
            avg_price = crop_prices['Final_Price'].mean()
            qa_pairs.append({
                "instruction": f"What is the average market price of {crop.lower()}?",
                "input": "",
                "output": f"The average market price of {crop} is approximately ₹{avg_price:.2f} per kg, though prices can vary significantly based on season, location, and market conditions."
            })

    # Seasonal advice
    for season in seasons:
        qa_pairs.extend([
            {
                "instruction": f"What crops should I grow in {season.lower()} season?",
                "input": "",
                "output": f"In {season} season, you can grow various crops like Rice, Onion, Tomato, and other seasonal vegetables. The choice depends on your location, soil type, and water availability."
            },
            {
                "instruction": f"What are the challenges in {season.lower()} season farming?",
                "input": "",
                "output": f"{season} season farming presents unique challenges including weather conditions, pest management, and market fluctuations. Proper planning and crop selection are essential."
            }
        ])

    # Warehouse and storage advice
    districts = warehouse_data['District'].unique()
    for district in districts[:5]:  # Limit to first 5 districts
        district_warehouses = warehouse_data[warehouse_data['District'] == district]
        cold_storage_count = len(district_warehouses[district_warehouses['Storage_Type'] == 'Cold Storage'])

        qa_pairs.append({
            "instruction": f"What storage facilities are available in {district} district?",
            "input": "",
            "output": f"{district} district has {len(district_warehouses)} warehouse facilities, including {cold_storage_count} cold storage units. These facilities help in proper storage of crops like rice, onion, and tomato to prevent spoilage and maintain quality."
        })

    # Decision making advice
    qa_pairs.extend([
        {
            "instruction": "When should I sell my crops immediately?",
            "input": "",
            "output": "You should sell crops immediately when current market prices are high and expected future prices are lower. Consider factors like storage costs, spoilage risks, and your immediate cash flow needs."
        },
        {
            "instruction": "When should I store crops for later selling?",
            "input": "",
            "output": "Store crops when current prices are low but future prices are expected to rise. Ensure you have proper storage facilities, calculate storage costs, and consider transportation costs to warehouses."
        },
        {
            "instruction": "How do I calculate profit from farming?",
            "input": "",
            "output": "Profit calculation involves subtracting all costs (seeds, fertilizers, labor, irrigation, transportation) from total revenue. Consider both immediate selling and storage options to maximize returns."
        }
    ])

    # Pest and disease management
    qa_pairs.extend([
        {
            "instruction": "How can I protect my crops from pests?",
            "input": "",
            "output": "Use integrated pest management including crop rotation, natural predators, organic pesticides, and regular field monitoring. Early detection and preventive measures are key to pest control."
        },
        {
            "instruction": "What are common diseases affecting rice crops?",
            "input": "",
            "output": "Common rice diseases include blast, bacterial blight, and sheath blight. Prevention involves using disease-resistant varieties, proper field sanitation, and appropriate fungicide application."
        },
        {
            "instruction": "How can I improve soil fertility?",
            "input": "",
            "output": "Improve soil fertility through organic matter addition, crop rotation, green manuring, and balanced fertilizer application. Regular soil testing helps determine nutrient requirements."
        }
    ])

    # Sustainable farming
    qa_pairs.extend([
        {
            "instruction": "What is sustainable farming?",
            "input": "",
            "output": "Sustainable farming maintains soil health, conserves water, reduces chemical inputs, and preserves biodiversity while ensuring profitable crop production for future generations."
        },
        {
            "instruction": "How can I reduce water usage in farming?",
            "input": "",
            "output": "Implement drip irrigation, rainwater harvesting, mulching, and drought-resistant crop varieties. Efficient water management is crucial for sustainable agriculture."
        }
    ])

    # Market and economic advice
    qa_pairs.extend([
        {
            "instruction": "How do I get better prices for my crops?",
            "input": "",
            "output": "Get better prices by understanding market trends, selling at peak seasons, improving crop quality, direct marketing to consumers, and joining farmer producer organizations."
        },
        {
            "instruction": "What government schemes are available for farmers?",
            "input": "",
            "output": "Various government schemes include PM-KISAN, soil health cards, crop insurance (PMFBY), KCC loans, and subsidies for equipment and seeds. Check local agricultural offices for eligibility."
        }
    ])

    return qa_pairs

def save_dataset(qa_pairs: List[Dict], filename: str = "agricultural_qa_dataset.json"):
    """Save the Q&A dataset to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    print(f"Dataset saved to {filename} with {len(qa_pairs)} Q&A pairs")

def create_training_split(dataset, train_ratio=0.8):
    """Split dataset into training and validation sets"""
    random.shuffle(dataset)
    split_idx = int(len(dataset) * train_ratio)

    train_data = dataset[:split_idx]
    val_data = dataset[split_idx:]

    return train_data, val_data

if __name__ == "__main__":
    # Create the dataset
    qa_dataset = create_agricultural_qa_dataset()

    # Split into train/val
    train_data, val_data = create_training_split(qa_dataset)

    # Save datasets
    save_dataset(train_data, "agricultural_train.json")
    save_dataset(val_data, "agricultural_val.json")

    print(f"Training set: {len(train_data)} samples")
    print(f"Validation set: {len(val_data)} samples")
    print("Dataset creation completed!")