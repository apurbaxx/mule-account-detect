"""
Money Mule Detection System using TigerGraph
=============================================

This system detects cross-channel money mule patterns where criminals:
1. Receive money via Mobile App
2. Move funds to Linked Wallet
3. Withdraw cash at ATM within minutes

Run these scripts in order:
1. python 01_setup_schema.py     - Create the graph schema
2. python 02_load_sample_data.py - Load sample transaction data
3. python 03_create_queries.py   - Install detection queries
4. python 04_run_detection.py    - Execute money mule detection
"""

import pyTigerGraph as tg
import os

# TigerGraph Configuration - supports environment variables for cloud deployment
# For Streamlit Community Cloud, set these in secrets.toml or environment
TIGERGRAPH_CONFIG = {
    "host": os.environ.get("TIGERGRAPH_HOST", "https://1e27-139-167-143-182.ngrok-free.app"),
    "restppPort": os.environ.get("TIGERGRAPH_REST_PORT", "443"),
    "gsPort": os.environ.get("TIGERGRAPH_GS_PORT", "443"),
    "username": os.environ.get("TIGERGRAPH_USERNAME", "tigergraph"),
    "password": os.environ.get("TIGERGRAPH_PASSWORD", "tigergraph"),
    "graphName": os.environ.get("TIGERGRAPH_GRAPH", "MoneyMuleGraph")
}

def get_connection(use_graph=False):
    """Create TigerGraph connection"""
    config = TIGERGRAPH_CONFIG.copy()
    graph_name = config.pop("graphName")
    
    if use_graph:
        conn = tg.TigerGraphConnection(
            **config,
            graphname=graph_name
        )
    else:
        conn = tg.TigerGraphConnection(**config)
    
    return conn, graph_name

if __name__ == "__main__":
    print("Testing TigerGraph Connection...")
    print("=" * 50)
    print(f"Host: {TIGERGRAPH_CONFIG['host']}")
    print(f"REST Port: {TIGERGRAPH_CONFIG['restppPort']}")
    print(f"GS Port: {TIGERGRAPH_CONFIG['gsPort']}")
    print("=" * 50)
    
    try:
        conn, graph_name = get_connection()
        result = conn.gsql('SHOW USER')
        print("✓ Connection successful!")
        print(f"Target graph: {graph_name}")
        print("\nUser info:")
        print(result)
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease verify:")
        print("  1. TigerGraph is running and accessible")
        print(f"  2. REST API is available at {TIGERGRAPH_CONFIG['host']}")
        print("  3. Credentials are correct")
        print("\nFor remote TigerGraph, set environment variables:")
        print("  TIGERGRAPH_HOST, TIGERGRAPH_REST_PORT, TIGERGRAPH_GS_PORT")
        print("  TIGERGRAPH_USERNAME, TIGERGRAPH_PASSWORD, TIGERGRAPH_GRAPH")
