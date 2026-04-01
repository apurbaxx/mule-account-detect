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

SCHEMA_GSQL = '''
// Drop existing graph if exists (comment out if you want to keep data)
DROP GRAPH IF EXISTS MoneyMuleGraph

// Create the graph
CREATE GRAPH MoneyMuleGraph()

// Use the graph
USE GRAPH MoneyMuleGraph

// ===================
// VERTEX DEFINITIONS
// ===================

// Account vertex - represents bank accounts, wallets, etc.
CREATE VERTEX Account (
    PRIMARY_ID account_id STRING,
    account_type STRING,        // "bank_account", "wallet", "crypto_wallet"
    holder_name STRING,
    created_date DATETIME,
    risk_score FLOAT DEFAULT 0.0,
    is_flagged BOOL DEFAULT FALSE,
    kyc_verified BOOL DEFAULT TRUE
) WITH primary_id_as_attribute="true"

// Transaction vertex - individual financial transactions
CREATE VERTEX Transaction (
    PRIMARY_ID txn_id STRING,
    amount FLOAT,
    currency STRING DEFAULT "USD",
    timestamp DATETIME,
    channel STRING,             // "mobile_app", "web", "atm", "branch", "wallet_transfer"
    txn_type STRING,            // "deposit", "withdrawal", "transfer", "payment"
    status STRING DEFAULT "completed",
    device_fingerprint STRING,
    ip_address STRING,
    geo_location STRING
) WITH primary_id_as_attribute="true"

// Device vertex - devices used for transactions
CREATE VERTEX Device (
    PRIMARY_ID device_id STRING,
    device_type STRING,         // "mobile", "desktop", "tablet", "atm_terminal"
    os_type STRING,
    first_seen DATETIME,
    last_seen DATETIME,
    is_trusted BOOL DEFAULT FALSE
) WITH primary_id_as_attribute="true"

// ATM vertex - physical ATM locations
CREATE VERTEX ATM (
    PRIMARY_ID atm_id STRING,
    bank_name STRING,
    location STRING,
    city STRING,
    country STRING,
    latitude FLOAT,
    longitude FLOAT
) WITH primary_id_as_attribute="true"

// Wallet vertex - digital wallets (PayPal, Venmo, crypto, etc.)
CREATE VERTEX Wallet (
    PRIMARY_ID wallet_id STRING,
    wallet_type STRING,         // "paypal", "venmo", "crypto", "mobile_wallet"
    provider STRING,
    linked_date DATETIME,
    is_verified BOOL DEFAULT FALSE
) WITH primary_id_as_attribute="true"

// ===================
// EDGE DEFINITIONS
// ===================

// Money flow edges
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

// Account relationships
CREATE DIRECTED EDGE LINKED_WALLET (
    FROM Account,
    TO Wallet,
    linked_date DATETIME,
    is_primary BOOL DEFAULT FALSE
)

CREATE DIRECTED EDGE OWNS_DEVICE (
    FROM Account,
    TO Device,
    first_used DATETIME
)

// Transaction context edges
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

// Wallet to Account edge (for tracing wallet transfers)
CREATE DIRECTED EDGE WALLET_TO_ACCOUNT (
    FROM Wallet,
    TO Account,
    transfer_date DATETIME,
    amount FLOAT
)

// Same-person/entity links (for identity resolution)
CREATE UNDIRECTED EDGE SAME_OWNER (
    FROM Account,
    TO Account,
    confidence FLOAT,
    link_type STRING  // "phone_match", "email_match", "device_match", "behavior_match"
)

// Suspicious activity edge (created by detection algorithms)
CREATE DIRECTED EDGE SUSPICIOUS_LINK (
    FROM Account,
    TO Account,
    detected_at DATETIME,
    pattern_type STRING,
    risk_score FLOAT,
    evidence STRING
)

// ===================
// CREATE GRAPH WITH ALL TYPES
// ===================

CREATE GRAPH MoneyMuleGraph(
    Account, Transaction, Device, ATM, Wallet,
    SENT, RECEIVED, LINKED_WALLET, OWNS_DEVICE,
    USED_DEVICE, WITHDREW_AT, VIA_WALLET, WALLET_TO_ACCOUNT,
    SAME_OWNER, SUSPICIOUS_LINK
)
'''

def setup_schema():
    """Create the TigerGraph schema"""
    print("=" * 60)
    print("STEP 1: Setting up TigerGraph Schema for Money Mule Detection")
    print("=" * 60)
    
    conn, graph_name = get_connection()
    
    # Split and execute GSQL commands
    print("\n[1/3] Dropping existing graph if present...")
    try:
        result = conn.gsql(f'DROP GRAPH IF EXISTS {graph_name}')
        print(result)
    except Exception as e:
        print(f"Note: {e}")
    
    print("\n[2/3] Creating schema...")
    try:
        # Execute the full schema creation
        result = conn.gsql(SCHEMA_GSQL)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    print("\n[3/3] Verifying schema...")
    try:
        result = conn.gsql(f'USE GRAPH {graph_name}\nLS')
        print(result)
    except Exception as e:
        print(f"Note: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Schema setup complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    setup_schema()
