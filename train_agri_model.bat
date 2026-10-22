@echo off
echo Starting Agricultural Model Training...
echo.

cd /d %~dp0

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Create dataset
echo Creating agricultural Q&A dataset...
python src\create_agri_dataset.py

REM Train the model
echo.
echo Starting model training...
python src\train_simple_agri_model.py

echo.
echo Training completed! Model saved to ./agri_model
echo You can now use the trained model in your chatbot.

pause