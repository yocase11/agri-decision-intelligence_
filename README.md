# AI-Driven Agricultural Price Forecasting & Profit Optimization System

This repository contains modules for price forecasting, decision modeling, storage allocation, and transport optimization for farmer profitability.

## Features

- **Price Forecasting**: AI-powered crop price predictions
- **Decision Support**: Optimal sell/store recommendations for farmers
- **Warehouse Optimization**: Best storage facility recommendations
- **Transport Planning**: Route optimization and cost calculation
- **AgriChat**: AI chatbot for agricultural advice and queries (integrated in web dashboards)
- **Analytics Dashboard**: Interactive charts and insights
- **Decision History**: Track past recommendations and outcomes

## Structure

- `src/` - core modules
- `data/` - datasets
- `tests/` - unit tests

## Quickstart

1. Create & activate virtual environment:
   - `python -m venv .venv`
   - `.\.venv\Scripts\activate`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run tests:
   - `pytest`

## Running the Applications

### Custom Web Dashboard (Flask)
```bash
python custom_ui.py
```
- Access at: http://localhost:5000
- Features: Dashboard, Decision Support, Analytics, AgriChat Assistant
- Set `FLASK_SECRET_KEY`, `AGRI_FARMER_PASSWORD`, and `AGRI_ADMIN_PASSWORD` before starting the app. The login usernames are `farmer` and `admin`; passwords are supplied through those environment variables.

### Main Dashboard (Streamlit)
```bash
streamlit run src/app.py
```

### API Server
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Training Your Own Agricultural AI Model

The system includes tools to train a specialized agricultural chatbot using your data:

### 1. Prepare the Dataset
```bash
python src/create_agri_dataset.py
```
This creates `agricultural_train.json` and `agricultural_val.json` with Q&A pairs about:
- Crop information and cultivation
- Seasonal farming advice
- Price forecasting insights
- Storage and warehouse recommendations
- Pest management and soil health
- Sustainable farming practices

### 2. Train the Model
**Option A: Simple Training (Recommended)**
```bash
# Windows
train_agri_model.bat

# Or manually:
python src/train_simple_agri_model.py
```

**Option B: Advanced Training**
```bash
python src/train_agri_model.py --model_name "microsoft/DialoGPT-medium" --num_epochs 3
```

### 3. Use the Trained Model
The chatbot automatically detects and uses the trained model if available:
- Flask app: `python custom_ui.py` (will use trained model if available)
- Streamlit app: `streamlit run src/app.py`
- Standalone: `python src/chatbot.py`

### Model Features
- **Specialized Knowledge**: Trained on agricultural data from your datasets
- **Context Awareness**: Understands farming terminology and practices
- **Practical Advice**: Provides actionable recommendations
- **Fallback Support**: Falls back to external API if trained model unavailable

### Training Requirements
- Python 3.8+
- CUDA-compatible GPU (recommended for faster training)
- 4GB+ RAM
- Training time: ~30-60 minutes on modern hardware
3. Run tests:
   - `pytest`
