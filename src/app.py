import os
import io
import datetime
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from decision_support import run_single_farmer_decision
from mcdm import load_warehouses
from forecast import load_price_data
from price_pipeline import clean_price_data, prepare_crop_timeseries, run_crop_pipeline
from chatbot import AgriChatbot

# App configuration
st.set_page_config(page_title='Agri Decision Intelligence', layout='wide', page_icon='🌾')

PRICE_PATH = r"C:\Users\yoges\agrii\price dataset (1).csv"
MODEL_DIR = r"C:\Users\yoges\agrii\models"
FARMER_PATH = r"C:\Users\yoges\agrii\farmer_crop_dataset (1).csv"
WAREHOUSE_PATH = r"C:\Users\yoges\agrii\tamilnadu_full_warehouse_dataset (1).csv"
HISTORY_CSV = os.path.join(os.getcwd(), 'farmer_decision_history.csv')

DISTRICT_COORD_MAPPING = {
    'Chennai': (13.0827, 80.2707),
    'Coimbatore': (11.0168, 76.9558),
    'Madurai': (9.9252, 78.1198),
    'Salem': (11.6643, 78.1460),
    'Tiruchirappalli': (10.7905, 78.7047),
    'Tirunelveli': (8.7268, 77.6951),
}

VALID_USERS = {
    'farmer': 'agri123',
    'admin': 'admin123',
}

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = ''
if 'history' not in st.session_state:
    st.session_state.history = []
if 'latest_result' not in st.session_state:
    st.session_state.latest_result = None
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = AgriChatbot()
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []


def authenticate(username, password):
    return VALID_USERS.get(username) == password


@st.cache_data(ttl=1800)
def load_full_price_data():
    df = pd.read_csv(PRICE_PATH)
    if 'Quarter' in df.columns:
        df['quarter_date'] = pd.PeriodIndex(df['Quarter'].astype(str), freq='Q').to_timestamp('Q')
    elif 'Year' in df.columns and 'Quarter' in df.columns:
        df['quarter_date'] = pd.PeriodIndex(df['Quarter'].astype(str), freq='Q').to_timestamp('Q')
    else:
        df['quarter_date'] = pd.to_datetime(df.get('Date', pd.NaT), errors='coerce')

    df = df.dropna(subset=['quarter_date'])
    if 'Final_Price' in df.columns and 'Crop' in df.columns:
        df['price_per_kg'] = df.apply(lambda r: r['Final_Price'] / 144.0 if str(r['Crop']).lower() == 'rice' else r['Final_Price'], axis=1)
    elif 'Rice' in df.columns:
        df['price_per_kg'] = df.apply(lambda r: r['Rice'] / 144.0 if 'Rice' in r else np.nan, axis=1)
    else:
        df['price_per_kg'] = np.nan

    df = df.sort_values('quarter_date').reset_index(drop=True)
    return df


def save_history_to_disk():
    if not st.session_state.history:
        return
    summary_df = pd.DataFrame(st.session_state.history)
    try:
        summary_df.to_csv(HISTORY_CSV, index=False)
    except Exception:
        pass


def load_history_from_disk():
    if os.path.exists(HISTORY_CSV):
        try:
            return pd.read_csv(HISTORY_CSV).to_dict('records')
        except Exception:
            return []
    return []


def init_sqlite_db(db_path='farmer_history.db'):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            timestamp TEXT,
            crop TEXT,
            quantity_kg REAL,
            district TEXT,
            decision TEXT,
            current_price REAL,
            forecast_price REAL,
            profit_now REAL,
            profit_store REAL,
            storage_cost REAL,
            transport_cost REAL,
            recommended_warehouse TEXT
        )
    ''')
    conn.commit()
    return conn


# database connection for history
DB_CONN = init_sqlite_db()

# Load persisted history at app start
if not st.session_state.history:
    st.session_state.history = load_history_from_disk()


def append_history(result):
    row = {
        'timestamp': datetime.datetime.now().isoformat(),
        'crop': result.get('crop'),
        'quantity_kg': float(result.get('quantity_kg', 0)),
        'district': result.get('district'),
        'decision': result.get('decision'),
        'current_price': float(result.get('current_price', 0) or 0),
        'forecast_price': float(result.get('forecast_price', 0) or 0),
        'profit_now': float(result.get('profit_now', 0) or 0),
        'profit_store': float(result.get('profit_store', 0) or 0),
        'storage_cost': float(result.get('storage_cost', 0) or 0),
        'transport_cost': float(result.get('transport_cost', 0) or 0),
        'recommended_warehouse': result.get('recommended_warehouse', {}).get('name') if result.get('recommended_warehouse') else None,
    }
    st.session_state.history.append(row)
    save_history_to_disk()

    try:
        cursor = DB_CONN.cursor()
        cursor.execute('''
            INSERT INTO history (
                timestamp, crop, quantity_kg, district, decision,
                current_price, forecast_price, profit_now, profit_store,
                storage_cost, transport_cost, recommended_warehouse
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['timestamp'], row['crop'], row['quantity_kg'], row['district'], row['decision'],
            row['current_price'], row['forecast_price'], row['profit_now'], row['profit_store'],
            row['storage_cost'], row['transport_cost'], row['recommended_warehouse']
        ))
        DB_CONN.commit()
    except Exception:
        pass


# Custom CSS for modern SaaS styling
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #e8f5e9, #e3f2fd);
}

.main {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(8px);
}

.card, .input-panel, .output-panel, .price-card, .profit-card, .warehouse-card, .decision-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.45);
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(14, 78, 94, 0.16);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.card:hover, .input-panel:hover, .output-panel:hover, .price-card:hover, .profit-card:hover, .warehouse-card:hover, .decision-card:hover {
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 14px 40px rgba(14, 78, 94, 0.24);
}

.title {
    font-size: 36px;
    font-weight: 800;
    color: #2e7d32;
    text-align: center;
    margin-bottom: 0;
}

.subtitle {
    font-size: 18px;
    color: #2e7d32;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 25px;
}

.input-panel, .output-panel {
    margin-bottom: 20px;
}

.decision-card {
    text-align: center;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 15px;
}

.sell-decision {
    background-color: rgba(244, 67, 54, 0.12);
    border: 2px solid rgba(244, 67, 54, 0.4);
    color: #c62828;
}

.store-decision {
    background-color: rgba(76, 175, 80, 0.12);
    border: 2px solid rgba(76, 175, 80, 0.45);
    color: #2e7d32;
}

.price-card, .profit-card, .warehouse-card {
    background: rgba(255,255,255,0.70);
    border-left: 4px solid #2e7d32;
}

.stButton>button {
    background-color: #2e7d32;
    color: white;
    border: none;
    border-radius: 25px;
    padding: 12px 35px;
    font-size: 17px;
    font-weight: bold;
    width: 100%;
}

.stButton>button:hover {
    background-color: #1b5e20;
}

.charts-section {
    margin-top: 30px;
}

.blurred-header {
    transition: all 0.4s ease;
}

</style>
""", unsafe_allow_html=True)


# Authentication
if not st.session_state.authenticated:
    st.markdown('<h1 class="title">🌾 Agri Decision Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-powered Farmer Decision Support</p>', unsafe_allow_html=True)

    st.markdown('## 🔐 Login')
    with st.form('login_form'):
        username = st.text_input('Username', value='farmer')
        password = st.text_input('Password', type='password')
        submit = st.form_submit_button('Login')

    if submit:
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.user = username
            st.success('Login successful. Welcome!')
            st.rerun()
        else:
            st.error('Invalid credentials. Use farmer/agri123 or admin/admin123')
    st.stop()


# Main application layout
st.markdown('<h1 class="title">🌾 Agri Decision Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered Farmer Decision Support</p>', unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    page = st.radio("Choose a page:", ["Dashboard", "AgriChat Assistant"], index=0)

    if page == "AgriChat Assistant":
        st.markdown("---")
        st.markdown("**🤖 AgriChat**")
        st.markdown("Your AI agricultural assistant")
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.session_state.chatbot.reset_conversation()
            st.rerun()

if page == "AgriChat Assistant":
    # Chatbot page
    st.markdown("## 🤖 AgriChat - Your AI Agricultural Assistant")
    st.markdown("Ask me anything about farming, crops, weather, pricing, and sustainable agriculture!")

    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me about agriculture..."):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.chat(prompt)
            st.markdown(response)

        # Add assistant response to chat history
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

    st.stop()  # Don't show dashboard content

# Dashboard page (existing content)

# Two-column layout
left_col, right_col = st.columns([1, 1])

# LEFT PANEL: Input
with left_col:
    st.markdown('<div class="input-panel">', unsafe_allow_html=True)
    st.markdown('### 🌾 Enter Farm Details')

    with st.form('farmer_input'):
        crop = st.selectbox('Crop', ['Onion', 'Tomato', 'Rice'])
        quantity_kg = st.number_input('Quantity (kg)', min_value=10.0, max_value=5000.0, value=2000.0, step=10.0)
        district = st.selectbox('District', list(DISTRICT_COORD_MAPPING.keys()))
        offline_mode = st.checkbox('Offline mode (use local route estimation, no OSRM requests)', value=False)
        cost_per_km_per_tonne = st.number_input('Transport cost per km per tonne (₹)', min_value=0.1, max_value=100.0, value=5.0, step=0.1)
        fuel_rate = st.number_input('Fuel surcharge per km (₹)', min_value=0.0, max_value=50.0, value=1.0, step=0.1)
        permit_cost = st.number_input('Permit/administrative cost (₹)', min_value=0.0, max_value=5000.0, value=0.0, step=10.0)
        tolls = st.number_input('Tolls (₹)', min_value=0.0, max_value=10000.0, value=0.0, step=10.0)
        driver_wage_per_km = st.number_input('Driver wage per km (₹)', min_value=0.0, max_value=100.0, value=2.0, step=0.1)
        run_button = st.form_submit_button('Get Recommendation')

    if run_button:
        try:
            farmer_lat, farmer_lon = DISTRICT_COORD_MAPPING.get(district, (11.0, 77.0))
            result = run_single_farmer_decision(
                crop,
                quantity_kg,
                farmer_lat,
                farmer_lon,
                PRICE_PATH,
                MODEL_DIR,
                FARMER_PATH,
                WAREHOUSE_PATH,
                offline_mode=offline_mode,
                cost_per_km_per_tonne=cost_per_km_per_tonne,
                fuel_rate=fuel_rate,
                permit_cost=permit_cost,
                tolls=tolls,
                driver_wage_per_km=driver_wage_per_km,
            )
            result['district'] = district
            result['timestamp'] = datetime.datetime.now().isoformat()
            result['location'] = (farmer_lat, farmer_lon)
            st.session_state.latest_result = result
            append_history(result)
            st.success('✅ Recommendation generated successfully!')
        except Exception as e:
            st.error('Something went wrong. Please try again.')
            st.session_state.latest_result = None

    st.markdown('</div>', unsafe_allow_html=True)

# RIGHT PANEL: Output
with right_col:
    st.markdown('<div class="output-panel">', unsafe_allow_html=True)

    if st.session_state.latest_result:
        res = st.session_state.latest_result

        # Decision Card
        decision_class = "sell-decision" if res['decision'].upper() == 'SELL' else "store-decision"
        st.markdown(f'<div class="decision-card {decision_class}">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="margin: 0; font-size: 36px;">{res["decision"].upper()}</h2>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Price Card
        st.markdown('<div class="price-card">', unsafe_allow_html=True)
        st.markdown('### 💰 Price Information')
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Current Price', f"₹{res['current_price']:.2f}/kg")
        with col2:
            st.metric('Forecast Price', f"₹{res['forecast_price']:.2f}/kg")
        st.markdown('</div>', unsafe_allow_html=True)

        # Profit Card
        st.markdown('<div class="profit-card">', unsafe_allow_html=True)
        st.markdown('### 📈 Profit Analysis')
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Profit Now', f"₹{res['profit_now']:.2f}")
        with col2:
            st.metric('Profit After Storage', f"₹{res['profit_store']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

        # Warehouse Card (only if STORE)
        if res.get('recommended_warehouse') and res['decision'].upper() == 'STORE':
            st.markdown('<div class="warehouse-card">', unsafe_allow_html=True)
            st.markdown('### 🏭 Recommended Warehouse')
            wh = res['recommended_warehouse']
            st.write(f"**Name:** {wh['name']}")
            st.write(f"**Distance:** {wh['distance_km']:.1f} km")
            st.write(f"**Storage Cost:** ₹{wh['storage_cost_per_mt']:.2f}/MT")
            st.write(f"**Capacity:** {wh['capacity_mt']:.0f} MT")
            if res.get('transport_cost') is not None:
                st.write(f"**Transport Cost:** ₹{res['transport_cost']:.2f}")
            if res.get('route'):
                st.write(f"**Road Distance:** {res.get('distance_km', 0):.2f} km")
                st.write(f"**Travel Time:** {res.get('travel_time_min', 0):.1f} min")
                if res['route'].get('is_offline'):
                    st.warning('Using offline route estimation (OSRM disabled).')
            st.markdown('</div>', unsafe_allow_html=True)

            # Map visualization section
            try:
                farmer_lat, farmer_lon = res.get('location', (None, None))
                wh_lat, wh_lon = wh.get('latitude'), wh.get('longitude')
                if farmer_lat is not None and farmer_lon is not None and wh_lat is not None and wh_lon is not None:
                    distance_km = float(wh.get('distance_km', 0) or 0)
                    transport_cost = float(res.get('transport_cost', 0) or 0)
                    speed_kmh = 40.0
                    eta_hours = distance_km / speed_kmh if distance_km > 0 else 0
                    eta_str = f"{int(eta_hours)}h {int((eta_hours % 1) * 60)}m"

                    if distance_km <= 10:
                        zoom_level = 11
                    elif distance_km <= 25:
                        zoom_level = 10
                    elif distance_km <= 50:
                        zoom_level = 9
                    elif distance_km <= 100:
                        zoom_level = 8
                    elif distance_km <= 200:
                        zoom_level = 7
                    else:
                        zoom_level = 6

                    map_df = pd.DataFrame({
                        'Name': ['Farmer', wh['name']],
                        'Latitude': [farmer_lat, wh_lat],
                        'Longitude': [farmer_lon, wh_lon],
                        'Type': ['Farmer', 'Warehouse'],
                        'Details': [
                            f"Farmer location\nLat: {farmer_lat:.4f}\nLon: {farmer_lon:.4f}",
                            f"Warehouse: {wh['name']}\nDistance: {distance_km:.1f} km\nCost: ₹{transport_cost:.2f}\nETA: {eta_str}"
                        ]
                    })

                    fig_map = px.scatter_mapbox(
                        map_df,
                        lat='Latitude',
                        lon='Longitude',
                        color='Type',
                        hover_name='Name',
                        hover_data={'Details': True, 'Latitude': False, 'Longitude': False, 'Type': False},
                        zoom=zoom_level,
                        height=450,
                        color_discrete_map={'Farmer': 'blue', 'Warehouse': 'green'}
                    )

                    fig_map.add_trace(go.Scattermapbox(
                        lat=[farmer_lat, wh_lat],
                        lon=[farmer_lon, wh_lon],
                        mode='lines',
                        line=dict(width=4, color='#1f77b4'),
                        name='Transport Route',
                        hoverinfo='text',
                        hovertext=[f"Route from farmer to warehouse ({distance_km:.1f} km, ETA {eta_str})"]
                    ))

                    fig_map.update_layout(
                        mapbox_style='open-street-map',
                        mapbox=dict(center=dict(lat=(farmer_lat + wh_lat) / 2, lon=(farmer_lon + wh_lon) / 2), zoom=zoom_level),
                        margin={'r':0,'t':0,'l':0,'b':0},
                        legend=dict(orientation='h', yanchor='bottom', y=0.01, xanchor='left', x=0.01)
                    )

                    st.markdown('### 🗺️ Transport & Warehouse Map')
                    st.plotly_chart(fig_map, use_container_width=True, key='warehouse_map')

                    st.info(f"🚚 Route distance: {distance_km:.1f} km | ETA: {eta_str} | Transport cost: ₹{transport_cost:.2f}")

                    gmap_url = f"https://www.google.com/maps/dir/{farmer_lat},{farmer_lon}/{wh_lat},{wh_lon}"
                    st.markdown(f"### 🧭 Navigation\n👉 [Open Route in Google Maps]({gmap_url})")
            except Exception:
                st.warning('Map visualization temporarily unavailable.')

    else:
        st.info('👈 Enter your farm details on the left and click "Get Recommendation" to see results here.')

    st.markdown('</div>', unsafe_allow_html=True)

# Charts Section (below both panels)
st.markdown('<div class="charts-section">', unsafe_allow_html=True)
st.markdown('## 📊 Analytics & Insights')

# Premium animation step
with st.spinner('Creating 3D intelligence charts...'):
    import time
    time.sleep(0.8)

if st.session_state.latest_result:
    res = st.session_state.latest_result

    # Price trajectory chart
    col1, col2 = st.columns(2)
    with col1:
        trajectory_df = pd.DataFrame({
            'Period': ['Current', 'Next Quarter'],
            'Price (₹/kg)': [res['current_price'], res['forecast_price']]
        })
        fig_traj = px.line(trajectory_df, x='Period', y='Price (₹/kg)', markers=True,
                     title='Price Forecast Trajectory')
        fig_traj.update_traces(line_color='#2e7d32', marker=dict(size=10))
        st.plotly_chart(fig_traj, use_container_width=True)

    with col2:
        profit_df = pd.DataFrame({
            'Option': ['Sell Now', 'Store & Sell Later'],
            'Profit (₹)': [res['profit_now'], res['profit_store']]
        })
        fig_profit = px.bar(profit_df, x='Option', y='Profit (₹)', color='Option',
                    title='Profit Comparison', color_discrete_map={'Sell Now': '#f44336', 'Store & Sell Later': '#4caf50'})
        fig_profit.update_traces(marker_line_width=1.5, opacity=0.85)
        st.plotly_chart(fig_profit, use_container_width=True)

    # 3D-like surface chart for premium SaaS feel
    z = np.array([[res['current_price'], (res['current_price'] + res['forecast_price'])/2, res['forecast_price']],
                  [res['current_price']*0.95, res['forecast_price']*1.05, res['forecast_price']*1.1],
                  [res['current_price']*0.9, res['forecast_price']*1.1, res['forecast_price']*1.3]])
    fig_surface = go.Figure(data=[go.Surface(z=z, x=[0,1,2], y=[0,1,2], colorscale='Viridis', opacity=0.88)])
    fig_surface.update_layout(title='3D Price Surface Projection', autosize=True,
                              scene=dict(xaxis_title='Time', yaxis_title='Scenario', zaxis_title='Price (₹/kg)'),
                              margin=dict(l=20, r=20, t=45, b=10))
    st.plotly_chart(fig_surface, use_container_width=True)

# Download history
if st.session_state.history:
    st.markdown('---')
    st.download_button('📥 Download History CSV',
                      data=pd.DataFrame(st.session_state.history).to_csv(index=False).encode('utf-8'),
                      file_name='agri_decision_history.csv',
                      mime='text/csv')

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('---')
st.caption('Data source: price dataset and warehouse dataset. Built with Streamlit, Plotly, and Agri Intelligence Pipeline.')
