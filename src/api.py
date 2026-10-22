import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Agri Price Forecasting API", version="1.0")


class DataPaths(BaseModel):
    model_dir: str = r"C:\Users\yoges\agrii\models"


def _load_json(path):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health_check():
    return {"status": "OK", "service": "agri-forecast-api"}


@app.get("/forecast_summary")
def forecast_summary(model_dir: str = DataPaths().model_dir):
    path = os.path.join(model_dir, "forecast_summary.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="forecast_summary.csv not found")
    # return as JSON list
    import pandas as pd
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


@app.get("/decision_report")
def decision_report(model_dir: str = DataPaths().model_dir):
    path = os.path.join(model_dir, "decision_report.json")
    return _load_json(path)


@app.get("/models")
def model_list(model_dir: str = DataPaths().model_dir):
    if not os.path.exists(model_dir):
        raise HTTPException(status_code=404, detail="Model directory not found")
    files = [f for f in os.listdir(model_dir) if f.endswith(".pkl")]
    return {"models": files}


@app.post("/decide")
def decide_crop_action(data: dict):
    """Make decision for crop sell/store based on current conditions"""
    try:
        crop = data.get('crop', 'Onion')
        quantity_kg = float(data.get('quantity_kg', 1000))
        lat = float(data.get('lat', 11.0))
        lon = float(data.get('lon', 77.0))
        
        # Import here to avoid circular imports
        from decision_support import run_single_farmer_decision
        
        result = run_single_farmer_decision(
            crop=crop,
            quantity_kg=quantity_kg,
            farmer_lat=lat,
            farmer_lon=lon,
            price_path=r"C:\Users\yoges\agrii\price dataset (1).csv",
            model_dir=r"C:\Users\yoges\agrii\models"
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chatbot endpoints
from chatbot import AgriChatbot

chatbot_instance = AgriChatbot()

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
def chat_with_bot(chat_message: ChatMessage):
    """Send a message to the AgriChat chatbot"""
    try:
        response = chatbot_instance.chat(chat_message.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/reset")
def reset_chat():
    """Reset the chatbot conversation history"""
    try:
        chatbot_instance.reset_conversation()
        return {"status": "Conversation reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
