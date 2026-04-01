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

# TigerGraph Configuration
TIGERGRAPH_CONFIG = {
    "host": "http://localhost",
    "restppPort": "9000",
    "gsPort": "14240",
    "username": "tigergraph",
    "password": "tigergraph",
    "graphName": "MoneyMuleGraph"
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
        print("  1. TigerGraph is running")
        print("  2. REST API is available at http://localhost:9000")
        print("  3. Credentials are correct")
