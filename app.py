```python
import streamlit as st
import threading
import time
import requests
import random
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Hardcoded Service Pools
VIEWS_POOL = [
    {"id": 4480, "name": "Instagram Views [Cheapest]", "min": 100, "max": 100000000},
    {"id": 3508, "name": "Instagram Reel/Video Views [Best]", "min": 100, "max": 2147483647},
    {"id": 4322, "name": "Instagram Reel Views [Premium]", "min": 100, "max": 2147483647},
    {"id": 4894, "name": "Instagram Reel/Video Views [Instant]", "min": 100, "max": 100000000},
    {"id": 5026, "name": "Instagram Views [Per 5 Min 1k]", "min": 100, "max": 100000000},
    {"id": 5031, "name": "Instagram Views [Per 5 Min 500]", "min": 500, "max": 100000000}
]

LIKES_POOL = [
    {"id": 4731, "name": "Instagram Likes [WW New]", "min": 10, "max": 3000000},
    {"id": 4561, "name": "Instagram Likes [Emergency Instant]", "min": 10, "max": 300000},
    {"id": 4942, "name": "Instagram Likes [Mix Speed]", "min": 10, "max": 300000},
    {"id": 4489, "name": "Instagram Likes [Fast Refill]", "min": 10, "max": 1000000}
]

SHARES_POOL = [
    {"id": 4479, "name": "Instagram Shares + Reach", "min": 10, "max": 1000000},
    {"id": 4633, "name": "Instagram Profile Shares [Real]", "min": 10, "max": 100000},
    {"id": 4476, "name": "Instagram Shares [Indian]", "min": 10, "max": 100000}
]

SAVES_POOL = [
    {"id": 1693, "name": "Instagram Real Saves [Instant]", "min": 10, "max": 500000},
    {"id": 1691, "name": "Instagram Saves [Always Working]", "min": 10, "max": 1000000},
    {"id": 1692, "name": "Instagram Real Saves [10k/h]", "min": 10, "max": 100000}
]

# Session state initialization
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'dispatch_log' not in st.session_state:
    st.session_state.dispatch_log = []
if 'worker_running' not in st.session_state:
    st.session_state.worker_running = False
if 'ordered' not in st.session_state:
    st.session_state.ordered = {'views': 0, 'likes': 0, 'shares': 0, 'saves': 0}
if 'dispatched' not in st.session_state:
    st.session_state.dispatched = {'views': 0, 'likes': 0, 'shares': 0, 'saves': 0}
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'target_url' not in st.session_state:
    st.session_state.target_url = ''

# UI Layout
st.set_page_config(page_title="YoMo Traffic Engine", layout="wide")
st.title("🚀 YoMo Automated Traffic Distribution Engine")
st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("YoYoMedia API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    target_url = st.text_input("Target Link", value=st.session_state.target_url, placeholder="https://instagram.com/p/CxYzAbCdEfG/")
    st.session_state.target_url = target_url
    
    st.markdown("---")
    st.subheader("🎯 Primary Metric")
    target_views = st.number_input("Target Total Views", min_value=100, value=5000, step=100)
    
    # Auto-calculate secondary metrics (3.5% ratio)
    target_likes = int(target_views * 0.035)
    target_shares = int(target_views * 0.035)
    target_saves = int(target_views * 0.035)
    
    st.markdown("Auto-calculated:")
    st.markdown(f"- Likes: `{target_likes}`")
    st.markdown(f"- Shares: `{target_shares}`")
    st.markdown(f"- Saves: `{target_saves}`")
    
    st.markdown("---")
    st.subheader("⏱️ Timeline Settings")
    total_hours = st.slider("Distribution Duration (Hours)", 1.0, 24.0, 12.0, 0.5)
    num_chunks = st.slider("Number of Chunks", 5, 50, 20)
    
    st.markdown("---")
    if st.button("📊 Start Distribution"):
        if not api_key:
            st.error("❌ Please enter your API key")
        elif not target_url:
            st.error("❌ Please enter a target URL")
        else:
            st.session_state.worker_running = True
            start_distribution_engine(api_key, target_url, target_views, target_likes, target_shares, target_saves, total_hours, num_chunks)
    
    if st.button("🛑 Stop Distribution"):
        st.session_state.worker_running = False
        st.warning("Worker stopped. Current tasks will finish.")

# Main Dashboard
tab1, tab2, tab3 = st.tabs(["📈 Live Monitor", "🔍 Order Logs", "📤 Dispatch History"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ordered", f"{st.session_state.ordered['views']:,}", "Views")
    with col2:
        st.metric("Dispatched", f"{st.session_state.dispatched['views']:,}", "Views")
    with col3:
        st.metric("Ordered", f"{st.session_state.ordered['likes']:,}", "Likes")
    with col4:
        st.metric("Dispatched", f"{st.session_state.dispatched['likes']:,}", "Likes")
    
    # Live status table
    if st.session_state.dispatch_log:
        df = pd.DataFrame(st.session_state.dispatch_log)
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("📱 No dispatches yet. Start distribution to monitor.")

with tab2:
    log_container = st.empty()
    if st.session_state.logs:
        log_text = "\n".join(st.session_state.logs[-100:])  # Last 100 logs
        log_container.code(log_text, language="text")

with tab3:
    # Curve visualization
    st.subheader("Delivery Curve Preview")
    if target_views > 0:
        curve_data = generate_sigmoid_curve(target_views, num_chunks)
        time_points = list(range(1, num_chunks + 1))
        df_curve = pd.DataFrame({"Chunk": time_points, "Views": curve_data})
        fig = px.line(df_curve, x="Chunk", y="Views", title="Sigmoid Delivery Curve (with Poisson noise simulation)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Historical dispatch records
    if st.session_state.dispatch_log:
        hist_df = pd.DataFrame(st.session_state.dispatch_log)
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("No historical data yet.")

# Mathematical engine functions
def generate_sigmoid_curve(target_total, num_segments):
    """Generate S-curve using cumulative distribution function"""
    curve = []
    for i in range(num_segments):
        x = (i / (num_segments - 1)) * 10 - 5  # Scale from -5 to +5
        y = 1 / (1 + math.exp(-x))  # Sigmoid function
        curve.append(y)
    
    # Normalize to target total
    total = sum(curve)
    scaled_curve = [(val / total) * target_total for val in curve]
    
    # Apply Poisson distribution noise (±35% jitter)
    noisy_curve = []
    for val in scaled_curve:
        jitter = random.uniform(-0.35, 0.35)
        noisy_val = max(1, int(val * (1 + jitter)))
        noisy_curve.append(noisy_val)
    
    return noisy_curve

def check_status(api_key, order_id):
    """Check order status via API"""
    try:
        payload = {"key": api_key, "action": "status", "order": order_id}
        response = requests.post("https://yoyomedia.com/api/v2/index.php", data=payload, timeout=30)
        log_msg = f"Status Check | Order: {order_id} | Status: {response.status_code} | Response: {response.text}"
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        return response
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Error checking status for order {order_id}: {str(e)}"
        st.session_state.logs.append(error_msg)
        return None

def submit_order(api_key, service_id, target_link, quantity):
    """Submit order via API"""
    try:
        payload = {
            "key": api_key,
            "action": "add",
            "service": service_id,
            "link": target_link,
            "quantity": quantity
        }
        response = requests.post("https://yoyomedia.com/api/v2/index.php", data=payload, timeout=30)
        log_msg = f"Order Submit | Service: {service_id} | Qty: {quantity} | Status: {response.status_code} | Response: {response.text}"
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        
        # Extract order ID from response
        try:
            order_data = response.json()
            order_id = order_data.get("order", "UNKNOWN")
        except:
            order_id = "UNKNOWN"
            
        return response, order_id
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Error submitting order: {str(e)}"
        st.session_state.logs.append(error_msg)
        return None, None

def check_link_orders(api_key, target_link):
    """Check all orders for a specific link"""
    try:
        payload = {"key": api_key, "action": "orders", "link": target_link}
        response = requests.post("https://yoyomedia.com/api/v2/index.php", data=payload, timeout=30)
        log_msg = f"Link Orders Check | Link: {target_link} | Status: {response.status_code} | Response: {response.text}"
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        
        # Try to parse orders from response
        try:
            data = response.json()
            if isinstance(data, dict) and 'orders' in data:
                return data['orders']
            elif isinstance(data, list):
                return data
        except:
            pass
        
        return []
    except Exception as e:
        error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Error checking link orders: {str(e)}"
        st.session_state.logs.append(error_msg)
        return []

def is_service_busy(api_key, target_link, service_id):
    """Check if service ID has active orders for this URL"""
    # Get all orders for this link
    orders = check_link_orders(api_key, target_link)
    
    for order in orders:
        if order.get('service') == str(service_id):
            status = order.get('status', '').lower()
            if status in ['pending', 'processing', 'in progress']:
                st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Service {service_id} is busy with order {order.get('id', 'unknown')} in {status} status")
                return True
    
    return False

def select_available_service(pool, api_key, target_link):
    """Cascading selection of available service IDs"""
    for service in pool:
        if not is_service_busy(api_key, target_link, service["id"]):
            return service
    
    # If all are busy, sleep and retry (max 5 attempts = 5 minutes)
    for attempt in range(5):
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] All services busy. Waiting 60 seconds... (Attempt {attempt+1}/5)")
        time.sleep(60)
        
        # Retry selection
        for service in pool:
            if not is_service_busy(api_key, target_link, service["id"]):
                st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Found available service after waiting: {service['id']}")
                return service
    
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to find available service after 5 minutes")
    return None

def start_distribution_engine(api_key, target_url, views, likes, shares, saves, duration_hours, chunks):
    """Main worker thread function"""
    def worker():
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Worker thread started")
        
        # Update ordered stats
        st.session_state.ordered = {'views': views, 'likes': likes, 'shares': shares, 'saves': saves}
        
        # Create distributions
        views_curve = generate_sigmoid_curve(views, chunks)
        likes_curve = generate_sigmoid_curve(likes, len(views_curve))  # Match chunk count
        shares_curve = generate_sigmoid_curve(shares, len(views_curve))
        saves_curve = generate_sigmoid_curve(saves, len(views_curve))
        
        total_time = duration_hours * 3600  # Convert to seconds
        base_interval = total_time / chunks
        
        # Process each chunk
        for i in range(chunks):
            if not st.session_state.worker_running:
                break
                
            # Get quantities for this chunk
            v_qty = views_curve[i] if i < len(views_curve) else 0
            l_qty = likes_curve[i] if i < len(likes_curve) else 0
            s_qty = shares_curve[i] if i < len(shares_curve) else 0
            sv_qty = saves_curve[i] if i < len(saves_curve) else 0
            
            chunks_info = [
                ("Views", v_qty, VIEWS_POOL, "views"),
                ("Likes", l_qty, LIKES_POOL, "likes"),
                ("Shares", s_qty, SHARES_POOL, "shares"),
                ("Saves", sv_qty, SAVES_POOL, "saves")
            ]
            
            for category_name, qty, pool, category_key in chunks_info:
                if qty <= 0:
                    continue
                    
                # Select available service (anti-concurrency cascading logic)
                service = select_available_service(pool, api_key, target_url)
                if service is None:
                    continue
                    
                # Apply Poisson jitter to quantity (±35%)
                jitter_factor = random.uniform(-0.35, 0.35)
                adjusted_qty = max(service["min"], int(qty * (1 + jitter_factor)))
                adjusted_qty = min(adjusted_qty, service["max"])
                
                # Submit order
                response, order_id = submit_order(api_key, service["id"], target_url, adjusted_qty)
                
                # Record dispatch
                dispatch_record = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Target Link": target_url,
                    "Category": category_name,
                    "Service ID": service["id"],
                    "Quantity": adjusted_qty,
                    "Order ID": order_id
                }
                st.session_state.dispatch_log.append(dispatch_record)
                st.session_state.dispatched[category_key] += adjusted_qty
                
                # Log dispatch
                st.session_state.logs.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Dispatched {category_name}: "
                    f"ServiceID={service['id']}, Qty={adjusted_qty}, OrderID={order_id}"
                )
                
                # Check status of submitted order
                if order_id != "UNKNOWN":
                    check_response = check_status(api_key, order_id)
                    if check_response:
                        status_data = check_response.json()
                        status = status_data.get("status", "Unknown")
                        st.session_state.logs.append(
                            f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Order {order_id} status: {status}"
                        )
                
                # Random Poisson jitter on interval (±35%)
                jitter_interval = base_interval * random.uniform(0.65, 1.35)
                time.sleep(jitter_interval)
        
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Worker completed all chunks")
    
    # Start background thread
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()

# Footer
st.markdown("---")
st.markdown("*YoYoMedia Traffic Engine v2.1 | Running on Streamlit Cloud*")
```
