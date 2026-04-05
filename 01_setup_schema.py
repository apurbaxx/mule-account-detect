"""
Step 1: Create TigerGraph Schema for Money Mule Detection
=========================================================

This script creates the graph schema with vertices and edges
to model cross-channel financial transactions.

Graph Model:
- Account: Bank accounts, wallets, user profiles
- Transaction: Individual financial transactions
- Device: Phones, computers used for transactions
- Channel: Mobile App, Web, ATM, Branch, Wallet
- Location: Geographic locations (for ATMs, etc.)

Edges capture relationships:
- SENT/RECEIVED: Money flow between accounts
- USED_CHANNEL: Which channel was used for transaction
- USED_DEVICE: Device used for transaction
- AT_LOCATION: Where transaction occurred
"""

from config import get_connection, TIGERGRAPH_CONFIG

def setup_schema():
    """Create the TigerGraph schema"""
    print("=" * 60)
    print("STEP 1: Setting up TigerGraph Schema for Money Mule Detection")
    print("=" * 60)
    
    conn, graph_name = get_connection()
    
    # Step 1: Try to drop existing graph (ignore errors if it doesn't exist)
    print("\n[1/5] Dropping existing graph if present...")
    try:
        result = conn.gsql(f'DROP GRAPH {graph_name}')
        print(result)
    except Exception as e:
        print(f"  Note: Graph may not exist yet - {str(e)[:50]}")
    
    # Step 2: Drop existing vertex/edge types (clean slate)
    print("\n[2/5] Cleaning up existing types...")
    types_to_drop = [
        "DROP EDGE SUSPICIOUS_LINK",
        "DROP EDGE SAME_OWNER", 
        "DROP EDGE WALLET_TO_ACCOUNT",
        "DROP EDGE VIA_WALLET",
        "DROP EDGE WITHDREW_AT",
        "DROP EDGE USED_DEVICE",
        "DROP EDGE OWNS_DEVICE",
        "DROP EDGE LINKED_WALLET",
        "DROP EDGE RECEIVED",
        "DROP EDGE SENT",
        "DROP VERTEX Wallet",
        "DROP VERTEX ATM",
        "DROP VERTEX Device",
        "DROP VERTEX Transaction",
        "DROP VERTEX Account",
    ]
    for cmd in types_to_drop:
        try:
            conn.gsql(cmd)
        except:
            pass  # Ignore errors - types may not exist
    print("  Cleanup complete")
    
    # Step 3: Create vertex types
    print("\n[3/5] Creating vertex types...")
    
    vertex_gsql = '''
CREATE VERTEX Account (
    PRIMARY_ID account_id STRING,
    account_type STRING,
    holder_name STRING,
    created_date DATETIME,
    risk_score FLOAT DEFAULT 0.0,
    is_flagged BOOL,
    kyc_verified BOOL
) WITH primary_id_as_attribute="true"

CREATE VERTEX Transaction (
    PRIMARY_ID txn_id STRING,
    amount FLOAT,
    currency STRING DEFAULT "USD",
    timestamp DATETIME,
    channel STRING,
    txn_type STRING,
    status STRING DEFAULT "completed",
    device_fingerprint STRING,
    ip_address STRING,
    geo_location STRING
) WITH primary_id_as_attribute="true"

CREATE VERTEX Device (
    PRIMARY_ID device_id STRING,
    device_type STRING,
    os_type STRING,
    first_seen DATETIME,
    last_seen DATETIME,
    is_trusted BOOL
) WITH primary_id_as_attribute="true"

CREATE VERTEX ATM (
    PRIMARY_ID atm_id STRING,
    bank_name STRING,
    location STRING,
    city STRING,
    country STRING,
    latitude FLOAT,
    longitude FLOAT
) WITH primary_id_as_attribute="true"

CREATE VERTEX Wallet (
    PRIMARY_ID wallet_id STRING,
    wallet_type STRING,
    provider STRING,
    linked_date DATETIME,
    is_verified BOOL
) WITH primary_id_as_attribute="true"
'''
    
    try:
        result = conn.gsql(vertex_gsql)
        print(result if result else "  Vertices created")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Step 4: Create edge types
    print("\n[4/5] Creating edge types...")
    
    edge_gsql = '''
CREATE DIRECTED EDGE SENT (
    FROM Account, 
    TO Transaction,
    sent_at DATETIME
)

CREATE DIRECTED EDGE RECEIVED (
    FROM Transaction, 
    TO Account,
    received_at DATETIME
)

CREATE DIRECTED EDGE LINKED_WALLET (
    FROM Account,
    TO Wallet,
    linked_date DATETIME,
    is_primary BOOL
)

CREATE DIRECTED EDGE OWNS_DEVICE (
    FROM Account,
    TO Device,
    first_used DATETIME
)

CREATE DIRECTED EDGE USED_DEVICE (
    FROM Transaction,
    TO Device
)

CREATE DIRECTED EDGE WITHDREW_AT (
    FROM Transaction,
    TO ATM,
    withdrawal_time DATETIME
)

CREATE DIRECTED EDGE VIA_WALLET (
    FROM Transaction,
    TO Wallet
)

CREATE DIRECTED EDGE WALLET_TO_ACCOUNT (
    FROM Wallet,
    TO Account,
    transfer_date DATETIME,
    amount FLOAT
)

CREATE UNDIRECTED EDGE SAME_OWNER (
    FROM Account,
    TO Account,
    confidence FLOAT,
    link_type STRING
)

CREATE DIRECTED EDGE SUSPICIOUS_LINK (
    FROM Account,
    TO Account,
    detected_at DATETIME,
    pattern_type STRING,
    risk_score FLOAT,
    evidence STRING
)
'''
    
    try:
        result = conn.gsql(edge_gsql)
        print(result if result else "  Edges created")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Step 5: Create the graph with all types
    print("\n[5/5] Creating graph...")
    
    graph_gsql = '''
CREATE GRAPH MoneyMuleGraph(
    Account, Transaction, Device, ATM, Wallet,
    SENT, RECEIVED, LINKED_WALLET, OWNS_DEVICE,
    USED_DEVICE, WITHDREW_AT, VIA_WALLET, WALLET_TO_ACCOUNT,
    SAME_OWNER, SUSPICIOUS_LINK
)
'''
    
    try:
        result = conn.gsql(graph_gsql)
        print(result if result else "  Graph created")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Verify
    print("\n[Verification] Checking schema...")
    try:
        result = conn.gsql(f'USE GRAPH {graph_name}\nLS')
        print(result)
    except Exception as e:
        print(f"  Note: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Schema setup complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    setup_schema()
