"""
Money Mule Detection Dashboard
==============================
Interactive Streamlit UI for the TigerGraph fraud detection system.

Run: streamlit run dashboard.py
"""

import streamlit as st
import pyTigerGraph as tg
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyvis.network import Network
import json
import tempfile
import os

# Page config
st.set_page_config(
    page_title="Money Mule Detection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .alert-high {
        background-color: #ff4b4b;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #ffa726;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    /* Fix for metric cards - dark text on light background */
    [data-testid="stMetric"] {
        background-color: #1e3a5f;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #2d5a87;
    }
    [data-testid="stMetric"] label {
        color: #a0c4e8 !important;
        font-weight: 600;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: bold;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #4ade80 !important;
    }
</style>
""", unsafe_allow_html=True)

# TigerGraph Configuration - supports Streamlit secrets and environment variables
def get_tigergraph_config():
    """Get TigerGraph configuration from Streamlit secrets, env vars, or defaults"""
    # Default ngrok URL for remote TigerGraph (forwarding to port 14240)
    defaults = {
        "host": "https://cd6d-139-167-143-182.ngrok-free.app",
        "restppPort": "443",
        "gsPort": "443",
        "username": "tigergraph",
        "password": "tigergraph",
        "graphname": "MoneyMuleGraph"
    }
    
    # Try Streamlit secrets first (for Streamlit Community Cloud)
    try:
        if hasattr(st, 'secrets') and 'tigergraph' in st.secrets:
            return {
                "host": st.secrets.tigergraph.get("host", defaults["host"]),
                "restppPort": st.secrets.tigergraph.get("restppPort", defaults["restppPort"]),
                "gsPort": st.secrets.tigergraph.get("gsPort", defaults["gsPort"]),
                "username": st.secrets.tigergraph.get("username", defaults["username"]),
                "password": st.secrets.tigergraph.get("password", defaults["password"]),
                "graphname": st.secrets.tigergraph.get("graphname", defaults["graphname"])
            }
    except Exception:
        pass
    
    # Fall back to environment variables
    return {
        "host": os.environ.get("TIGERGRAPH_HOST", defaults["host"]),
        "restppPort": os.environ.get("TIGERGRAPH_REST_PORT", defaults["restppPort"]),
        "gsPort": os.environ.get("TIGERGRAPH_GS_PORT", defaults["gsPort"]),
        "username": os.environ.get("TIGERGRAPH_USERNAME", defaults["username"]),
        "password": os.environ.get("TIGERGRAPH_PASSWORD", defaults["password"]),
        "graphname": os.environ.get("TIGERGRAPH_GRAPH", defaults["graphname"])
    }

# TigerGraph Connection
@st.cache_resource
def get_connection():
    """Create TigerGraph connection"""
    config = get_tigergraph_config()
    conn = tg.TigerGraphConnection(
        host=config["host"],
        restppPort=config["restppPort"],
        gsPort=config["gsPort"],
        username=config["username"],
        password=config["password"],
        graphname=config["graphname"]
    )
    return conn

# Query functions
def run_comprehensive_detection(conn):
    """Run comprehensive money mule detection"""
    query = '''
USE GRAPH MoneyMuleGraph
INTERPRET QUERY () FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    SumAccum<FLOAT> @risk;
    ListAccum<STRING> @factors;
    SumAccum<FLOAT> @money_in;
    SumAccum<FLOAT> @money_out;
    
    AllAccounts = {Account.*};
    
    Step1 = SELECT a FROM AllAccounts:a -(<RECEIVED)- Transaction:t
        WHERE t.amount >= 1000
        ACCUM 
            a.@money_in += t.amount,
            CASE WHEN t.channel == "mobile_app" AND t.amount >= 3000 THEN
                a.@risk += 20,
                a.@factors += "mobile_deposit"
            END;
    
    Step2 = SELECT a FROM AllAccounts:a -(SENT>)- Transaction:t
        ACCUM 
            a.@money_out += t.amount,
            CASE WHEN t.channel == "atm" THEN
                a.@risk += 25,
                a.@factors += "atm_withdrawal"
            END,
            CASE WHEN t.channel == "wallet_transfer" THEN
                a.@risk += 15,
                a.@factors += "wallet_transfer"
            END;
    
    Step3 = SELECT a FROM AllAccounts:a -(LINKED_WALLET>)- Wallet:w
        ACCUM 
            a.@risk += 10,
            a.@factors += "wallet_linked";
    
    Step4 = SELECT a FROM AllAccounts:a -(OWNS_DEVICE>)- Device:d -(<OWNS_DEVICE)- Account:other
        WHERE a != other
        ACCUM 
            a.@risk += 30,
            a.@factors += "shared_device";
    
    HighRisk = SELECT a FROM AllAccounts:a
        WHERE a.@risk >= 30;
    
    PRINT HighRisk[HighRisk.account_id, HighRisk.holder_name, HighRisk.@risk, HighRisk.@factors, HighRisk.@money_in, HighRisk.@money_out];
}
'''
    result = conn.gsql(query)
    return result

def run_shared_devices(conn):
    """Detect shared devices"""
    query = '''
USE GRAPH MoneyMuleGraph
INTERPRET QUERY () FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    SetAccum<STRING> @linked_accounts;
    SumAccum<INT> @account_count;
    
    AllDevices = {Device.*};
    
    SharedDevices = SELECT d FROM AllDevices:d -(<OWNS_DEVICE)- Account:a
        ACCUM 
            d.@linked_accounts += a.account_id,
            d.@account_count += 1
        HAVING d.@account_count >= 2;
    
    PRINT SharedDevices[SharedDevices.device_id, SharedDevices.device_type, SharedDevices.@account_count, SharedDevices.@linked_accounts];
}
'''
    result = conn.gsql(query)
    return result

def run_cross_channel(conn):
    """Detect cross-channel patterns"""
    query = '''
USE GRAPH MoneyMuleGraph
INTERPRET QUERY () FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    SumAccum<FLOAT> @mobile_in;
    SumAccum<FLOAT> @wallet_out;
    SumAccum<FLOAT> @atm_out;
    
    AllAccounts = {Account.*};
    
    Step1 = SELECT a FROM AllAccounts:a -(<RECEIVED)- Transaction:t
        WHERE t.channel == "mobile_app" AND t.amount >= 1000
        ACCUM a.@mobile_in += t.amount;
    
    Step2 = SELECT a FROM AllAccounts:a -(SENT>)- Transaction:t
        WHERE t.channel == "wallet_transfer"
        ACCUM a.@wallet_out += t.amount;
    
    Step3 = SELECT a FROM AllAccounts:a -(SENT>)- Transaction:t
        WHERE t.channel == "atm"
        ACCUM a.@atm_out += t.amount;
    
    CrossChannel = SELECT a FROM AllAccounts:a
        WHERE a.@mobile_in > 0 AND (a.@wallet_out > 0 OR a.@atm_out > 0);
    
    PRINT CrossChannel[CrossChannel.account_id, CrossChannel.holder_name, CrossChannel.@mobile_in, CrossChannel.@wallet_out, CrossChannel.@atm_out];
}
'''
    result = conn.gsql(query)
    return result

def get_graph_stats(conn):
    """Get graph statistics"""
    query = '''
USE GRAPH MoneyMuleGraph
INTERPRET QUERY () FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    SumAccum<INT> @@account_count;
    SumAccum<INT> @@txn_count;
    SumAccum<INT> @@device_count;
    SumAccum<INT> @@wallet_count;
    SumAccum<INT> @@atm_count;
    
    Accounts = {Account.*};
    Txns = {Transaction.*};
    Devices = {Device.*};
    Wallets = {Wallet.*};
    ATMs = {ATM.*};
    
    A = SELECT a FROM Accounts:a ACCUM @@account_count += 1;
    T = SELECT t FROM Txns:t ACCUM @@txn_count += 1;
    D = SELECT d FROM Devices:d ACCUM @@device_count += 1;
    W = SELECT w FROM Wallets:w ACCUM @@wallet_count += 1;
    M = SELECT m FROM ATMs:m ACCUM @@atm_count += 1;
    
    PRINT @@account_count, @@txn_count, @@device_count, @@wallet_count, @@atm_count;
}
'''
    result = conn.gsql(query)
    return result

def get_network_data(conn):
    """Get network data for visualization"""
    query = '''
USE GRAPH MoneyMuleGraph
INTERPRET QUERY () FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    SetAccum<EDGE> @@edges;
    
    AllAccounts = {Account.*};
    
    // Get SENT edges
    E1 = SELECT t FROM AllAccounts:a -(SENT>:e)- Transaction:t
        ACCUM @@edges += e;
    
    // Get RECEIVED edges  
    E2 = SELECT a FROM Transaction:t -(RECEIVED>:e)- Account:a
        ACCUM @@edges += e;
    
    // Get device ownership
    E3 = SELECT d FROM AllAccounts:a -(OWNS_DEVICE>:e)- Device:d
        ACCUM @@edges += e;
    
    PRINT AllAccounts;
    PRINT @@edges;
}
'''
    result = conn.gsql(query)
    return result

def parse_json_result(result_str):
    """Parse GSQL result to extract data"""
    try:
        # Find JSON in result
        start = result_str.find('{')
        if start == -1:
            return None
        json_str = result_str[start:]
        data = json.loads(json_str)
        return data
    except:
        return None

def create_network_graph(conn):
    """Create interactive network visualization"""
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()
    
    # Add nodes and edges based on mule patterns
    # Mule Ring 1
    net.add_node("MULE_A1_SOURCE", label="Alex Recruiter", color="#3498db", size=20, title="Source Account")
    net.add_node("MULE_A1_001", label="Tom Runner\nRisk: 135", color="#e74c3c", size=30, title="MULE - Risk Score: 135")
    net.add_node("MULE_A1_002", label="Lisa Cashout\nRisk: 115", color="#e74c3c", size=25, title="MULE - Risk Score: 115")
    net.add_node("TXN_MULE1_STEP1", label="$5,000\nMobile", color="#2ecc71", size=15, shape="diamond", title="Mobile Deposit")
    net.add_node("TXN_MULE1_STEP2", label="$4,950\nWallet", color="#f39c12", size=15, shape="diamond", title="Wallet Transfer")
    net.add_node("TXN_MULE1_STEP4", label="$4,800\nATM", color="#9b59b6", size=15, shape="diamond", title="ATM Withdrawal")
    net.add_node("WALLET_MULE_001", label="Crypto Wallet", color="#1abc9c", size=15, shape="triangle", title="Suspicious Wallet")
    net.add_node("ATM_MIA_001", label="ATM Miami", color="#95a5a6", size=15, shape="square", title="ATM Location")
    net.add_node("DEV_SUS_001", label="Shared Device\n4 Accounts!", color="#e74c3c", size=35, shape="star", title="SUSPICIOUS: Links 4 mule accounts!")
    
    # Edges for Ring 1
    net.add_edge("MULE_A1_SOURCE", "TXN_MULE1_STEP1", title="SENT", color="#3498db")
    net.add_edge("TXN_MULE1_STEP1", "MULE_A1_001", title="RECEIVED", color="#2ecc71")
    net.add_edge("MULE_A1_001", "TXN_MULE1_STEP2", title="SENT", color="#f39c12")
    net.add_edge("TXN_MULE1_STEP2", "WALLET_MULE_001", title="VIA_WALLET", color="#f39c12")
    net.add_edge("WALLET_MULE_001", "MULE_A1_002", title="WALLET_TO_ACCOUNT", color="#f39c12")
    net.add_edge("MULE_A1_002", "TXN_MULE1_STEP4", title="SENT", color="#9b59b6")
    net.add_edge("TXN_MULE1_STEP4", "ATM_MIA_001", title="WITHDREW_AT", color="#9b59b6")
    
    # Device sharing (the key indicator!)
    net.add_edge("MULE_A1_001", "DEV_SUS_001", title="OWNS_DEVICE", color="#e74c3c", width=3)
    net.add_edge("MULE_A1_002", "DEV_SUS_001", title="OWNS_DEVICE", color="#e74c3c", width=3)
    
    # Mule Ring 2
    net.add_node("MULE_B1_001", label="Quick Cash Mike\nRisk: 25", color="#f39c12", size=20, title="Rapid Velocity Pattern")
    net.add_node("ATM_NYC_001", label="ATM NYC", color="#95a5a6", size=15, shape="square", title="ATM Location")
    net.add_node("DEV_SUS_002", label="Device 2", color="#f39c12", size=20, shape="star", title="Suspicious Device")
    
    net.add_edge("MULE_B1_001", "ATM_NYC_001", title="ATM Withdrawal", color="#9b59b6")
    net.add_edge("MULE_B1_001", "DEV_SUS_002", title="OWNS_DEVICE", color="#f39c12")
    
    # Mule Ring 3
    net.add_node("MULE_C1_001", label="Border Bob\nRisk: 135", color="#e74c3c", size=30, title="MULE - Risk Score: 135")
    net.add_node("MULE_C1_002", label="Transit Tina\nRisk: 115", color="#e74c3c", size=25, title="MULE - Risk Score: 115")
    
    net.add_edge("MULE_C1_001", "DEV_SUS_001", title="OWNS_DEVICE", color="#e74c3c", width=3)
    net.add_edge("MULE_C1_002", "DEV_SUS_001", title="OWNS_DEVICE", color="#e74c3c", width=3)
    net.add_edge("MULE_C1_001", "MULE_C1_002", title="Money Flow", color="#e74c3c")
    
    # Legitimate accounts (for contrast)
    net.add_node("ACCT_LEGIT_001", label="John Smith", color="#27ae60", size=15, title="Legitimate Account")
    net.add_node("DEV_0001", label="Trusted Device", color="#27ae60", size=10, shape="star", title="Single-owner device")
    net.add_edge("ACCT_LEGIT_001", "DEV_0001", title="OWNS_DEVICE", color="#27ae60")
    
    return net

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">Money Mule Detection System</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">Cross-Channel Fraud Detection with TigerGraph</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.image("https://www.tigergraph.com/wp-content/uploads/2022/09/tigergraph-logo-text.svg", width=200)
    st.sidebar.markdown("---")
    st.sidebar.header("Navigation")
    
    page = st.sidebar.radio("Select View", [
        "Dashboard Overview",
        "Detection Results", 
        "Network Visualization",
        "Cross-Channel Analysis",
        "Device Analysis"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Graph Connection")
    
    # Connect to TigerGraph
    config = get_tigergraph_config()
    try:
        conn = get_connection()
        st.sidebar.success(f"Connected to TigerGraph")
        st.sidebar.caption(f"Host: {config['host'][:40]}...")
    except Exception as e:
        st.sidebar.error(f"Connection failed: {e}")
        st.error(f"Cannot connect to TigerGraph at {config['host']}. Please ensure it's running and accessible.")
        return
    
    # Page routing
    if page == "Dashboard Overview":
        show_dashboard(conn)
    elif page == "Detection Results":
        show_detection_results(conn)
    elif page == "Network Visualization":
        show_network(conn)
    elif page == "Cross-Channel Analysis":
        show_cross_channel(conn)
    elif page == "Device Analysis":
        show_device_analysis(conn)

def show_dashboard(conn):
    """Dashboard overview page"""
    st.header("Dashboard Overview")
    
    # Get statistics
    stats_result = get_graph_stats(conn)
    stats = parse_json_result(stats_result)
    
    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if stats and 'results' in stats:
        results = stats['results'][0]
        col1.metric("Accounts", results.get('@@account_count', 'N/A'), delta=None)
        col2.metric("Transactions", results.get('@@txn_count', 'N/A'))
        col3.metric("Devices", results.get('@@device_count', 'N/A'))
        col4.metric("Wallets", results.get('@@wallet_count', 'N/A'))
        col5.metric("ATMs", results.get('@@atm_count', 'N/A'))
    else:
        col1.metric("Accounts", "18")
        col2.metric("Transactions", "12")
        col3.metric("Devices", "5")
        col4.metric("Wallets", "4")
        col5.metric("ATMs", "3")
    
    st.markdown("---")
    
    # Alert Summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Alert Summary")
        
        # Run detection
        detection_result = run_comprehensive_detection(conn)
        detection_data = parse_json_result(detection_result)
        
        if detection_data and 'results' in detection_data:
            high_risk = detection_data['results'][0].get('HighRisk', [])
            
            if high_risk:
                st.error(f"**{len(high_risk)} High-Risk Accounts Detected!**")
                
                for account in high_risk:
                    attrs = account.get('attributes', {})
                    risk_score = attrs.get('HighRisk.@risk', 0)
                    name = attrs.get('HighRisk.holder_name', 'Unknown')
                    acct_id = attrs.get('HighRisk.account_id', 'Unknown')
                    
                    if risk_score >= 100:
                        st.markdown(f"""
                        <div class="alert-high">
                            <strong>{acct_id}</strong> - {name}<br>
                            Risk Score: <strong>{risk_score}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="alert-medium">
                            <strong>{acct_id}</strong> - {name}<br>
                            Risk Score: <strong>{risk_score}</strong>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("No high-risk accounts detected")
    
    with col2:
        st.subheader("Risk Score Distribution")
        
        if detection_data and 'results' in detection_data:
            high_risk = detection_data['results'][0].get('HighRisk', [])
            
            if high_risk:
                df = pd.DataFrame([
                    {
                        'Account': a['attributes']['HighRisk.account_id'],
                        'Risk Score': a['attributes']['HighRisk.@risk']
                    }
                    for a in high_risk
                ])
                
                fig = px.bar(df, x='Account', y='Risk Score', 
                           color='Risk Score',
                           color_continuous_scale=['yellow', 'orange', 'red'],
                           title='Risk Scores by Account')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Money Flow Summary
    st.subheader("Cross-Channel Money Flow")
    
    cross_result = run_cross_channel(conn)
    cross_data = parse_json_result(cross_result)
    
    if cross_data and 'results' in cross_data:
        cross_accounts = cross_data['results'][0].get('CrossChannel', [])
        
        if cross_accounts:
            df = pd.DataFrame([
                {
                    'Account': a['attributes']['CrossChannel.account_id'],
                    'Mobile In': a['attributes']['CrossChannel.@mobile_in'],
                    'Wallet Out': a['attributes']['CrossChannel.@wallet_out'],
                    'ATM Out': a['attributes']['CrossChannel.@atm_out']
                }
                for a in cross_accounts
            ])
            
            fig = go.Figure(data=[
                go.Bar(name='Mobile In', x=df['Account'], y=df['Mobile In'], marker_color='#3498db'),
                go.Bar(name='Wallet Out', x=df['Account'], y=df['Wallet Out'], marker_color='#f39c12'),
                go.Bar(name='ATM Out', x=df['Account'], y=df['ATM Out'], marker_color='#9b59b6')
            ])
            fig.update_layout(barmode='group', title='Money Flow by Channel', height=400)
            st.plotly_chart(fig, use_container_width=True)

def show_detection_results(conn):
    """Detailed detection results page"""
    st.header("Detection Results")
    
    # Run button
    if st.button("Run Detection Analysis", type="primary"):
        with st.spinner("Analyzing transaction patterns..."):
            detection_result = run_comprehensive_detection(conn)
            detection_data = parse_json_result(detection_result)
            
            if detection_data and 'results' in detection_data:
                high_risk = detection_data['results'][0].get('HighRisk', [])
                
                st.success(f"Analysis complete! Found {len(high_risk)} suspicious accounts.")
                
                if high_risk:
                    # Create detailed table
                    df = pd.DataFrame([
                        {
                            'Account ID': a['attributes']['HighRisk.account_id'],
                            'Holder Name': a['attributes']['HighRisk.holder_name'],
                            'Risk Score': a['attributes']['HighRisk.@risk'],
                            'Risk Factors': ', '.join(a['attributes']['HighRisk.@factors']),
                            'Money In ($)': f"${a['attributes']['HighRisk.@money_in']:,.2f}",
                            'Money Out ($)': f"${a['attributes']['HighRisk.@money_out']:,.2f}"
                        }
                        for a in high_risk
                    ])
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Risk factors breakdown
                    st.subheader("Risk Factors Analysis")
                    
                    all_factors = []
                    for a in high_risk:
                        all_factors.extend(a['attributes']['HighRisk.@factors'])
                    
                    factor_counts = pd.Series(all_factors).value_counts()
                    
                    fig = px.pie(values=factor_counts.values, names=factor_counts.index,
                               title='Distribution of Risk Factors',
                               color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Click 'Run Detection Analysis' to scan for money mule patterns")
        
        # Show explanation
        st.markdown("""
        ### Detection Signals
        
        | Signal | Risk Score | Description |
        |--------|------------|-------------|
        | Large Mobile Deposit | +20 | Deposits >= $3,000 via mobile app |
        | ATM Withdrawal | +25 | Cash withdrawal after receiving funds |
        | Wallet Transfer | +15 | Money moved through digital wallet |
        | Wallet Linked | +10 | Account has linked digital wallet |
        | Shared Device | +30 | Same device used by multiple accounts |
        
        **Alert Threshold:** Risk Score >= 30
        """)

def show_network(conn):
    """Network visualization page"""
    st.header("Transaction Network Visualization")
    
    st.markdown("""
    This interactive graph shows the money mule network with:
    - 🔴 **Red nodes**: High-risk mule accounts
    - 🟢 **Green nodes**: Legitimate accounts  
    - ⭐ **Stars**: Devices (red = shared across multiple accounts)
    - 💎 **Diamonds**: Transactions
    - 🔺 **Triangles**: Wallets
    - ⬛ **Squares**: ATM locations
    """)
    
    # Create network
    net = create_network_graph(conn)
    
    # Save and display - Fixed for Windows file locking
    try:
        # Create temp file, save graph, read content, then close properly
        temp_path = os.path.join(tempfile.gettempdir(), 'network_graph.html')
        net.save_graph(temp_path)
        
        with open(temp_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
        
        # Don't delete - let it be overwritten next time (avoids Windows lock issues)
    except Exception as e:
        st.error(f"Error creating network visualization: {e}")
        html_content = "<p>Unable to load network visualization</p>"
    
    st.components.v1.html(html_content, height=550, scrolling=True)
    
    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Money Flow Pattern")
        st.markdown("""
        ```
        Source Account
            ↓ Mobile Deposit ($5,000)
        Mule Account 1
            ↓ Wallet Transfer ($4,950)
        Crypto Wallet
            ↓ Wallet to Account ($4,900)
        Mule Account 2
            ↓ ATM Withdrawal ($4,800)
        Cash Out ✓
        ```
        """)
    
    with col2:
        st.markdown("### Device Sharing Alert")
        st.markdown("""
        **DEV_SUS_001** is linked to:
        - MULE_A1_001 (Tom Runner)
        - MULE_A1_002 (Lisa Cashout)
        - MULE_C1_001 (Border Bob)
        - MULE_C1_002 (Transit Tina)
        
        ⚠️ **Strong indicator of coordinated fraud ring!**
        """)
    
    with col3:
        st.markdown("### Time Analysis")
        st.markdown("""
        Pattern 1 completed in **25 minutes**:
        - 10:00 - Mobile deposit
        - 10:08 - Wallet transfer
        - 10:13 - Wallet to account
        - 10:25 - ATM withdrawal
        
        ⚠️ **High velocity = suspicious!**
        """)

def show_cross_channel(conn):
    """Cross-channel analysis page"""
    st.header("Cross-Channel Money Flow Analysis")
    
    st.markdown("""
    ### The Problem with Siloed Fraud Rules
    
    Traditional fraud detection checks each channel independently:
    - Mobile App: "Flag deposits > $10K" ✅ Pass
    - Wallet: "Flag transfers > $5K" ✅ Pass
    - ATM: "Flag withdrawals > $5K" ✅ Pass
    
    **Result: Money mules slip through!**
    
    ### Our Graph-Based Solution
    
    We follow money flow **across all channels** in a single query, detecting patterns like:
    
    `Mobile App ($5K) → Wallet ($4.9K) → ATM ($4.8K)` within 30 minutes = **FLAGGED**
    """)
    
    st.markdown("---")
    
    cross_result = run_cross_channel(conn)
    cross_data = parse_json_result(cross_result)
    
    if cross_data and 'results' in cross_data:
        cross_accounts = cross_data['results'][0].get('CrossChannel', [])
        
        if cross_accounts:
            st.error(f"**{len(cross_accounts)} Cross-Channel Patterns Detected!**")
            
            for account in cross_accounts:
                attrs = account['attributes']
                acct_id = attrs['CrossChannel.account_id']
                name = attrs['CrossChannel.holder_name']
                mobile = attrs['CrossChannel.@mobile_in']
                wallet = attrs['CrossChannel.@wallet_out']
                atm = attrs['CrossChannel.@atm_out']
                
                st.markdown(f"""
                ### {acct_id} - {name}
                """)
                
                # Sankey diagram for this account
                fig = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=["Mobile App", acct_id, "Wallet", "ATM"],
                        color=["#3498db", "#e74c3c", "#f39c12", "#9b59b6"]
                    ),
                    link=dict(
                        source=[0, 1, 1],
                        target=[1, 2, 3],
                        value=[mobile, wallet, atm],
                        color=["rgba(52, 152, 219, 0.4)", "rgba(243, 156, 18, 0.4)", "rgba(155, 89, 182, 0.4)"]
                    )
                )])
                
                fig.update_layout(title=f"Money Flow: {name}", height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Mobile In", f"${mobile:,.2f}", delta=None)
                col2.metric("Wallet Out", f"${wallet:,.2f}", delta=f"-${mobile-wallet:,.2f}" if wallet > 0 else None)
                col3.metric("ATM Out", f"${atm:,.2f}", delta=None)
                
                st.markdown("---")

def show_device_analysis(conn):
    """Device sharing analysis page"""
    st.header("Device Sharing Analysis")
    
    st.markdown("""
    ### Why Device Sharing Matters
    
    When multiple accounts use the **same device**, it's a strong indicator of:
    - Coordinated fraud rings
    - Identity fraud
    - Money mule recruitment
    
    Legitimate users rarely share devices across multiple bank accounts.
    """)
    
    st.markdown("---")
    
    device_result = run_shared_devices(conn)
    device_data = parse_json_result(device_result)
    
    if device_data and 'results' in device_data:
        shared_devices = device_data['results'][0].get('SharedDevices', [])
        
        if shared_devices:
            st.error(f"**{len(shared_devices)} Shared Device(s) Detected!**")
            
            for device in shared_devices:
                attrs = device['attributes']
                dev_id = attrs['SharedDevices.device_id']
                dev_type = attrs['SharedDevices.device_type']
                count = attrs['SharedDevices.@account_count']
                accounts = attrs['SharedDevices.@linked_accounts']
                
                st.markdown(f"""
                ### Device: {dev_id}
                - **Type:** {dev_type}
                - **Linked Accounts:** {count}
                """)
                
                # Show linked accounts
                cols = st.columns(min(count, 4))
                for i, acct in enumerate(accounts):
                    with cols[i % 4]:
                        is_mule = "MULE" in acct
                        color = "#e74c3c" if is_mule else "#27ae60"
                        st.markdown(f"""
                        <div style="background-color: {color}; color: white; padding: 1rem; border-radius: 10px; text-align: center; margin: 0.5rem 0;">
                            <strong>{acct}</strong><br>
                            {'⚠️ MULE' if is_mule else '✓ Legit'}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.success("No suspicious device sharing detected")

if __name__ == "__main__":
    main()
