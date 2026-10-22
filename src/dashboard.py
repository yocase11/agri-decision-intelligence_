from flask import Flask, jsonify, render_template
import os
import pandas as pd
import json

app = Flask(__name__)
MODEL_DIR = r"C:\Users\yoges\agrii\models"


@app.route("/")
def home():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agri Price Forecast & Decision Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f4f7fb; }
    h1 { text-align: center; margin-bottom: 20px; }
    .card { background: #ffffff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; padding: 20px; }
    .row { display: flex; flex-wrap: wrap; gap: 20px; }
    .col { flex: 1; min-width: 300px; }
    .metric { margin: 12px 0; padding: 16px; background: #eef3fb; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    table th, table td { border: 1px solid #dbe2ef; padding: 8px; text-align: center; }
    table th { background: #e5edff; }
    .decision-badge { padding: 4px 8px; border-radius: 8px; color: white; font-weight: bold; }
    .sell { background: #2d86ff; }
    .store { background: #2e946d; }
  </style>
</head>
<body>
  <h1>Agri Price Forecast & Decision Dashboard</h1>

  <div class="card" id="loading-status"><strong>Loading data...</strong></div>

  <div class="card">
    <h2>Forecast Metrics</h2>
    <div id="forecast_table"></div>
    <div id="forecast_chart" style="height: 440px;"></div>
  </div>

  <div class="card">
    <h2>Farmer Decision Support</h2>
    <form id="decision_form">
      <label>Crop: 
        <select name="crop" required>
          <option value="Onion">Onion</option>
          <option value="Tomato">Tomato</option>
          <option value="Rice">Rice</option>
        </select>
      </label><br><br>
      <label>Quantity (kg): <input type="number" name="quantity_kg" required></label><br><br>
      <label>Latitude: <input type="number" step="0.01" name="lat" required></label><br><br>
      <label>Longitude: <input type="number" step="0.01" name="lon" required></label><br><br>
      <button type="submit">Get Recommendation</button>
    </form>
    <div id="decision_result" style="margin-top: 20px;"></div>
  </div>

  <script>
    async function loadData() {
      const statusEl = document.getElementById('status');
      if (!statusEl) {
        console.error('Status element not found');
        return;
      }
      try {
        const [forecastResp, decisionResp] = await Promise.all([
          fetch('/forecast_summary'),
          fetch('/decision_report')
        ]);

        if (!forecastResp.ok || !decisionResp.ok) {
          statusEl.innerHTML = '<strong style="color:red">Error loading data</strong>';
          return;
        }

        const forecastData = await forecastResp.json();
        const decisionData = await decisionResp.json();

        statusEl.innerHTML = '<strong>Data loaded</strong>: ' + forecastData.length + ' crops, ' + decisionData.decision_report.length + ' decisions.';

        renderForecastTable(forecastData);
        renderForecastChart(forecastData);
        renderDecisionCards(decisionData.decision_report);
        renderProfitChart(decisionData.decision_report);
        renderCostChart(decisionData.decision_report);

      } catch (err) {
        statusEl.innerHTML = '<strong style="color:red">Load failed: ' + err.message + '</strong>';
      }
    }

    function renderForecastTable(data) {
      const container = document.getElementById('forecast_table');
      let html = '<table><thead><tr><th>Crop</th><th>Best Model</th><th>ARIMA RMSE</th><th>SARIMA RMSE</th><th>LSTM RMSE</th><th>Future1</th><th>Future2</th><th>Future3</th><th>Future4</th></tr></thead><tbody>';
      data.forEach(d => {
        html += '<tr><td>' + d.crop + '</td><td>' + d.best_model + '</td><td>' + d.arima_rmse.toFixed(2) + '</td><td>' + d.sarima_rmse.toFixed(2) + '</td><td>' + d.lstm_rmse.toFixed(2) + '</td><td>' + d.future_1.toFixed(2) + '</td><td>' + d.future_2.toFixed(2) + '</td><td>' + d.future_3.toFixed(2) + '</td><td>' + d.future_4.toFixed(2) + '</td></tr>';
      });
      html += '</tbody></table>';
      container.innerHTML = html;
    }

    function renderForecastChart(data) {
      const x = ['t+1','t+2','t+3','t+4'];
      const traces = data.map(d => ({
        x,
        y: [d.future_1, d.future_2, d.future_3, d.future_4],
        mode: 'lines+markers',
        name: d.crop,
        hovertemplate: '%{x}: %{y:.2f}<extra>' + d.crop + '</extra>'
      }));
      Plotly.newPlot('forecast_chart', traces, { title: 'Forecast Price Trajectory', legend: {orientation: 'h', x:0, y:-0.25}, margin: {t: 40}});
    }

    function renderDecisionCards(reports) {
      const container = document.getElementById('decision_cards');
      container.innerHTML = '';
      reports.forEach(r => {
        const decisionClass = r.decision.decision === 'sell' ? 'sell' : 'store';
        const card = document.createElement('div');
        card.className = 'col metric';
        card.innerHTML = '
          <h3>' + r.crop + '</h3>
          <div class="decision-badge ' + decisionClass + '">' + r.decision.decision.toUpperCase() + '</div>
          <p>Current: ' + r.decision.current_price + '</p>
          <p>Forecast 1: ' + r.decision.forecast_price.toFixed(2) + '</p>
          <p>Profit now: ' + r.decision.profit_now.toFixed(2) + '</p>
          <p>Profit store: ' + r.decision.profit_store.toFixed(2) + '</p>
          <p>Spoilage: ' + r.decision.spoilage_loss.toFixed(2) + '</p>
          <p>Storage: ' + r.decision.storage_cost.toFixed(2) + ' | Transport: ' + r.decision.transport_cost.toFixed(2) + '</p>
        ';
        container.appendChild(card);
      });
    }

    function renderProfitChart(reports) {
      const crops = reports.map(r => r.crop);
      const now = reports.map(r => r.decision.profit_now);
      const store = reports.map(r => r.decision.profit_store);
      Plotly.newPlot('profit_chart', [
        { x: crops, y: now, type: 'bar', name: 'Profit Now', marker: {color: '#2d86ff'} },
        { x: crops, y: store, type: 'bar', name: 'Profit Store', marker: {color: '#2e946d'} }
      ], { title: 'Profit Comparison (Now vs Store)', barmode: 'group'});
    }

    function renderCostChart(reports) {
      const crops = reports.map(r => r.crop);
      const spoilage = reports.map(r => r.decision.spoilage_loss);
      const storage = reports.map(r => r.decision.storage_cost);
      const transport = reports.map(r => r.decision.transport_cost);
      Plotly.newPlot('cost_chart', [
        { x: crops, y: spoilage, type: 'bar', name: 'Spoilage', marker: {color: '#e94560'} },
        { x: crops, y: storage, type: 'bar', name: 'Storage', marker: {color: '#ff9f1c'} },
        { x: crops, y: transport, type: 'bar', name: 'Transport', marker: {color: '#3a86ff'} }
      ], { title: 'Cost Components', barmode: 'stack'});
    }

    document.getElementById('decision_form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const data = Object.fromEntries(formData);
      const resultEl = document.getElementById('decision_result');
      resultEl.innerHTML = 'Processing...';
      try {
        const resp = await fetch('http://127.0.0.1:8503/decide', {
          method: 'POST',
          body: formData
        });
        if (resp.ok) {
          const html = await resp.text();
          resultEl.innerHTML = html;
        } else {
          resultEl.innerHTML = 'Error: ' + resp.status;
        }
      } catch (err) {
        resultEl.innerHTML = 'Error: ' + err.message;
      }
    });

    window.addEventListener('load', () => {
      loadData();
    });
  </script>
</body>
</html>
'''


@app.route('/performance_metrics')
def performance_metrics():
    return render_template('performance_metrics.html')


@app.route('/forecast_summary')
def forecast_summary():
    path = os.path.join(MODEL_DIR, 'forecast_summary.csv')
    if not os.path.exists(path):
        return jsonify({'error': 'forecast_summary.csv not found'}), 404
    df = pd.read_csv(path)
    return jsonify(df.to_dict(orient='records'))


@app.route('/decision_report')
def decision_report():
    path = os.path.join(MODEL_DIR, 'decision_report.json')
    if not os.path.exists(path):
        return jsonify({'error': 'decision_report.json not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/models')
def models():
    if not os.path.exists(MODEL_DIR):
        return jsonify({'error': 'model dir not found'}), 404
    files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
    return jsonify({'models': files})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8502, debug=True)

