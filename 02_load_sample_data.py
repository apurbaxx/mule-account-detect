"""
Step 2: Load Sample Data for Money Mule Detection
=================================================

This script generates and loads realistic sample data including:
- Normal customer accounts with regular transactions
- Money mule patterns with cross-channel rapid movements
- Various devices, ATMs, and wallets

The data includes several embedded money mule patterns for detection testing.
"""

from config import get_connection, TIGERGRAPH_CONFIG
import random
from datetime import datetime, timedelta
import json

# Sample data generation
def generate_sample_data():
    """Generate comprehensive sample data with embedded mule patterns"""
    
    data = {
        "accounts": [],
        "transactions": [],
        "devices": [],
        "atms": [],
        "wallets": [],
        "edges": {
            "sent": [],
            "received": [],
            "linked_wallet": [],
            "owns_device": [],
            "used_device": [],
            "withdrew_at": [],
            "via_wallet": [],
            "wallet_to_account": []
        }
    }
    
    base_time = datetime(2024, 3, 15, 10, 0, 0)
    
    # ========================================
    # CREATE LEGITIMATE ACCOUNTS (20 accounts)
    # ========================================
    legitimate_names = [
        "John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis",
        "David Wilson", "Jessica Taylor", "Chris Anderson", "Amanda Thomas",
        "Matthew Jackson", "Ashley White", "Daniel Harris", "Jennifer Martin",
        "Andrew Garcia", "Stephanie Martinez", "Joshua Robinson", "Nicole Clark",
        "Ryan Lewis", "Samantha Lee", "Kevin Walker", "Lauren Hall"
    ]
    
    for i, name in enumerate(legitimate_names):
        data["accounts"].append({
            "account_id": f"ACCT_LEGIT_{i+1:03d}",
            "account_type": "bank_account",
            "holder_name": name,
            "created_date": (base_time - timedelta(days=random.randint(365, 1000))).isoformat(),
            "risk_score": random.uniform(0.0, 0.2),
            "is_flagged": False,
            "kyc_verified": True
        })
    
    # ========================================
    # CREATE MULE ACCOUNTS (Pattern accounts)
    # ========================================
    
    # PATTERN 1: Classic Mobile -> Wallet -> ATM mule ring
    mule_ring_1 = [
        {"id": "MULE_A1_SOURCE", "name": "Alex Recruiter", "type": "bank_account"},
        {"id": "MULE_A1_001", "name": "Tom Runner", "type": "bank_account"},
        {"id": "MULE_A1_002", "name": "Lisa Cashout", "type": "bank_account"},
        {"id": "MULE_A1_003", "name": "Mark Transfer", "type": "bank_account"},
    ]
    
    # PATTERN 2: Rapid velocity mule (many small transactions)
    mule_ring_2 = [
        {"id": "MULE_B1_SOURCE", "name": "Cyber Fraud LLC", "type": "bank_account"},
        {"id": "MULE_B1_001", "name": "Quick Cash Mike", "type": "bank_account"},
        {"id": "MULE_B1_002", "name": "Speedy Sara", "type": "bank_account"},
    ]
    
    # PATTERN 3: Cross-border mule pattern
    mule_ring_3 = [
        {"id": "MULE_C1_SOURCE", "name": "Overseas Scam Op", "type": "bank_account"},
        {"id": "MULE_C1_001", "name": "Border Bob", "type": "bank_account"},
        {"id": "MULE_C1_002", "name": "Transit Tina", "type": "bank_account"},
    ]
    
    for ring in [mule_ring_1, mule_ring_2, mule_ring_3]:
        for mule in ring:
            data["accounts"].append({
                "account_id": mule["id"],
                "account_type": mule["type"],
                "holder_name": mule["name"],
                "created_date": (base_time - timedelta(days=random.randint(30, 90))).isoformat(),
                "risk_score": 0.0,  # Not flagged yet
                "is_flagged": False,
                "kyc_verified": random.choice([True, False])
            })
    
    # ========================================
    # CREATE DEVICES
    # ========================================
    device_types = ["mobile", "desktop", "tablet"]
    os_types = ["iOS", "Android", "Windows", "MacOS"]
    
    for i in range(30):
        data["devices"].append({
            "device_id": f"DEV_{i+1:04d}",
            "device_type": random.choice(device_types),
            "os_type": random.choice(os_types),
            "first_seen": (base_time - timedelta(days=random.randint(1, 365))).isoformat(),
            "last_seen": base_time.isoformat(),
            "is_trusted": random.choice([True, False])
        })
    
    # Suspicious devices (used across multiple mule accounts)
    suspicious_devices = [
        {"device_id": "DEV_SUS_001", "device_type": "mobile", "os_type": "Android", 
         "first_seen": (base_time - timedelta(days=5)).isoformat(), "last_seen": base_time.isoformat(), "is_trusted": False},
        {"device_id": "DEV_SUS_002", "device_type": "mobile", "os_type": "Android",
         "first_seen": (base_time - timedelta(days=3)).isoformat(), "last_seen": base_time.isoformat(), "is_trusted": False},
    ]
    data["devices"].extend(suspicious_devices)
    
    # ========================================
    # CREATE ATMS
    # ========================================
    atm_locations = [
        ("ATM_NYC_001", "Chase", "Times Square", "New York", "USA", 40.758, -73.985),
        ("ATM_NYC_002", "BOA", "Wall Street", "New York", "USA", 40.707, -74.011),
        ("ATM_LA_001", "Wells Fargo", "Hollywood", "Los Angeles", "USA", 34.092, -118.328),
        ("ATM_CHI_001", "Chase", "Loop", "Chicago", "USA", 41.882, -87.627),
        ("ATM_MIA_001", "Citibank", "Downtown", "Miami", "USA", 25.761, -80.191),
        ("ATM_MIA_002", "BOA", "South Beach", "Miami", "USA", 25.790, -80.130),
    ]
    
    for atm in atm_locations:
        data["atms"].append({
            "atm_id": atm[0],
            "bank_name": atm[1],
            "location": atm[2],
            "city": atm[3],
            "country": atm[4],
            "latitude": atm[5],
            "longitude": atm[6]
        })
    
    # ========================================
    # CREATE WALLETS
    # ========================================
    wallet_types = ["paypal", "venmo", "cashapp", "crypto", "mobile_wallet"]
    
    for i in range(20):
        data["wallets"].append({
            "wallet_id": f"WALLET_{i+1:04d}",
            "wallet_type": random.choice(wallet_types),
            "provider": random.choice(["PayPal", "Venmo", "CashApp", "Coinbase", "ApplePay"]),
            "linked_date": (base_time - timedelta(days=random.randint(30, 365))).isoformat(),
            "is_verified": random.choice([True, False])
        })
    
    # Mule-associated wallets
    mule_wallets = [
        {"wallet_id": "WALLET_MULE_001", "wallet_type": "crypto", "provider": "Unknown Exchange",
         "linked_date": (base_time - timedelta(days=7)).isoformat(), "is_verified": False},
        {"wallet_id": "WALLET_MULE_002", "wallet_type": "mobile_wallet", "provider": "CashApp",
         "linked_date": (base_time - timedelta(days=5)).isoformat(), "is_verified": False},
        {"wallet_id": "WALLET_MULE_003", "wallet_type": "paypal", "provider": "PayPal",
         "linked_date": (base_time - timedelta(days=3)).isoformat(), "is_verified": False},
    ]
    data["wallets"].extend(mule_wallets)
    
    # ========================================
    # CREATE TRANSACTIONS - LEGITIMATE
    # ========================================
    txn_counter = 1
    
    # Normal transactions for legitimate accounts
    for i in range(50):
        acct = f"ACCT_LEGIT_{random.randint(1, 20):03d}"
        txn_time = base_time - timedelta(hours=random.randint(1, 720))
        
        data["transactions"].append({
            "txn_id": f"TXN_{txn_counter:06d}",
            "amount": round(random.uniform(20, 500), 2),
            "currency": "USD",
            "timestamp": txn_time.isoformat(),
            "channel": random.choice(["mobile_app", "web", "branch"]),
            "txn_type": random.choice(["deposit", "transfer", "payment"]),
            "status": "completed",
            "device_fingerprint": f"DEV_{random.randint(1, 30):04d}",
            "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "geo_location": random.choice(["New York", "Los Angeles", "Chicago"])
        })
        
        # Add edges
        data["edges"]["sent"].append({
            "from": acct,
            "to": f"TXN_{txn_counter:06d}",
            "sent_at": txn_time.isoformat()
        })
        data["edges"]["received"].append({
            "from": f"TXN_{txn_counter:06d}",
            "to": f"ACCT_LEGIT_{random.randint(1, 20):03d}",
            "received_at": txn_time.isoformat()
        })
        
        txn_counter += 1
    
    # ========================================
    # CREATE MULE PATTERN 1: Mobile -> Wallet -> ATM (within 30 mins)
    # ========================================
    pattern1_start = base_time
    
    # Step 1: Large deposit via mobile app to mule account
    data["transactions"].append({
        "txn_id": "TXN_MULE1_STEP1",
        "amount": 5000.00,
        "currency": "USD",
        "timestamp": pattern1_start.isoformat(),
        "channel": "mobile_app",
        "txn_type": "deposit",
        "status": "completed",
        "device_fingerprint": "DEV_SUS_001",
        "ip_address": "45.33.32.156",
        "geo_location": "Miami"
    })
    data["edges"]["sent"].append({"from": "MULE_A1_SOURCE", "to": "TXN_MULE1_STEP1", "sent_at": pattern1_start.isoformat()})
    data["edges"]["received"].append({"from": "TXN_MULE1_STEP1", "to": "MULE_A1_001", "received_at": pattern1_start.isoformat()})
    data["edges"]["used_device"].append({"from": "TXN_MULE1_STEP1", "to": "DEV_SUS_001"})
    
    # Step 2: Transfer to wallet (8 minutes later)
    step2_time = pattern1_start + timedelta(minutes=8)
    data["transactions"].append({
        "txn_id": "TXN_MULE1_STEP2",
        "amount": 4950.00,
        "currency": "USD",
        "timestamp": step2_time.isoformat(),
        "channel": "wallet_transfer",
        "txn_type": "transfer",
        "status": "completed",
        "device_fingerprint": "DEV_SUS_001",
        "ip_address": "45.33.32.156",
        "geo_location": "Miami"
    })
    data["edges"]["sent"].append({"from": "MULE_A1_001", "to": "TXN_MULE1_STEP2", "sent_at": step2_time.isoformat()})
    data["edges"]["via_wallet"].append({"from": "TXN_MULE1_STEP2", "to": "WALLET_MULE_001"})
    data["edges"]["linked_wallet"].append({"from": "MULE_A1_001", "to": "WALLET_MULE_001", "linked_date": (pattern1_start - timedelta(days=2)).isoformat(), "is_primary": True})
    
    # Step 3: Move from wallet to second mule account (5 minutes later)
    step3_time = step2_time + timedelta(minutes=5)
    data["edges"]["wallet_to_account"].append({
        "from": "WALLET_MULE_001",
        "to": "MULE_A1_002",
        "transfer_date": step3_time.isoformat(),
        "amount": 4900.00
    })
    
    # Step 4: ATM withdrawal (12 minutes later)
    step4_time = step3_time + timedelta(minutes=12)
    data["transactions"].append({
        "txn_id": "TXN_MULE1_STEP4",
        "amount": 4800.00,
        "currency": "USD",
        "timestamp": step4_time.isoformat(),
        "channel": "atm",
        "txn_type": "withdrawal",
        "status": "completed",
        "device_fingerprint": "ATM_TERMINAL",
        "ip_address": "",
        "geo_location": "Miami"
    })
    data["edges"]["sent"].append({"from": "MULE_A1_002", "to": "TXN_MULE1_STEP4", "sent_at": step4_time.isoformat()})
    data["edges"]["withdrew_at"].append({"from": "TXN_MULE1_STEP4", "to": "ATM_MIA_001", "withdrawal_time": step4_time.isoformat()})
    
    # ========================================
    # CREATE MULE PATTERN 2: Rapid velocity (many small txns)
    # ========================================
    pattern2_start = base_time + timedelta(hours=2)
    
    for i in range(5):
        txn_time = pattern2_start + timedelta(minutes=i*5)
        txn_id = f"TXN_MULE2_RAPID_{i+1}"
        
        data["transactions"].append({
            "txn_id": txn_id,
            "amount": round(random.uniform(800, 1200), 2),
            "currency": "USD",
            "timestamp": txn_time.isoformat(),
            "channel": random.choice(["mobile_app", "wallet_transfer"]),
            "txn_type": "transfer",
            "status": "completed",
            "device_fingerprint": "DEV_SUS_002",
            "ip_address": "103.45.67.89",
            "geo_location": "New York"
        })
        data["edges"]["sent"].append({"from": "MULE_B1_SOURCE", "to": txn_id, "sent_at": txn_time.isoformat()})
        data["edges"]["received"].append({"from": txn_id, "to": "MULE_B1_001", "received_at": txn_time.isoformat()})
    
    # ATM cashout for pattern 2
    cashout_time = pattern2_start + timedelta(minutes=28)
    data["transactions"].append({
        "txn_id": "TXN_MULE2_CASHOUT",
        "amount": 5500.00,
        "currency": "USD",
        "timestamp": cashout_time.isoformat(),
        "channel": "atm",
        "txn_type": "withdrawal",
        "status": "completed",
        "device_fingerprint": "ATM_TERMINAL",
        "ip_address": "",
        "geo_location": "New York"
    })
    data["edges"]["sent"].append({"from": "MULE_B1_001", "to": "TXN_MULE2_CASHOUT", "sent_at": cashout_time.isoformat()})
    data["edges"]["withdrew_at"].append({"from": "TXN_MULE2_CASHOUT", "to": "ATM_NYC_001", "withdrawal_time": cashout_time.isoformat()})
    
    # ========================================
    # CREATE MULE PATTERN 3: Multi-hop with wallet chains
    # ========================================
    pattern3_start = base_time + timedelta(hours=5)
    
    # Initial large transfer via mobile
    data["transactions"].append({
        "txn_id": "TXN_MULE3_INIT",
        "amount": 8500.00,
        "currency": "USD",
        "timestamp": pattern3_start.isoformat(),
        "channel": "mobile_app",
        "txn_type": "deposit",
        "status": "completed",
        "device_fingerprint": "DEV_SUS_001",
        "ip_address": "89.123.45.67",
        "geo_location": "Chicago"
    })
    data["edges"]["sent"].append({"from": "MULE_C1_SOURCE", "to": "TXN_MULE3_INIT", "sent_at": pattern3_start.isoformat()})
    data["edges"]["received"].append({"from": "TXN_MULE3_INIT", "to": "MULE_C1_001", "received_at": pattern3_start.isoformat()})
    
    # First wallet hop
    hop1_time = pattern3_start + timedelta(minutes=10)
    data["transactions"].append({
        "txn_id": "TXN_MULE3_HOP1",
        "amount": 8400.00,
        "currency": "USD",
        "timestamp": hop1_time.isoformat(),
        "channel": "wallet_transfer",
        "txn_type": "transfer",
        "status": "completed",
        "device_fingerprint": "DEV_SUS_001",
        "ip_address": "89.123.45.67",
        "geo_location": "Chicago"
    })
    data["edges"]["sent"].append({"from": "MULE_C1_001", "to": "TXN_MULE3_HOP1", "sent_at": hop1_time.isoformat()})
    data["edges"]["via_wallet"].append({"from": "TXN_MULE3_HOP1", "to": "WALLET_MULE_002"})
    data["edges"]["linked_wallet"].append({"from": "MULE_C1_001", "to": "WALLET_MULE_002", "linked_date": (pattern3_start - timedelta(days=1)).isoformat(), "is_primary": True})
    
    # Second wallet hop
    hop2_time = hop1_time + timedelta(minutes=7)
    data["edges"]["wallet_to_account"].append({
        "from": "WALLET_MULE_002",
        "to": "MULE_C1_002",
        "transfer_date": hop2_time.isoformat(),
        "amount": 8300.00
    })
    data["edges"]["linked_wallet"].append({"from": "MULE_C1_002", "to": "WALLET_MULE_003", "linked_date": (pattern3_start - timedelta(days=1)).isoformat(), "is_primary": False})
    
    # Final ATM withdrawal
    final_time = hop2_time + timedelta(minutes=15)
    data["transactions"].append({
        "txn_id": "TXN_MULE3_FINAL",
        "amount": 8000.00,
        "currency": "USD",
        "timestamp": final_time.isoformat(),
        "channel": "atm",
        "txn_type": "withdrawal",
        "status": "completed",
        "device_fingerprint": "ATM_TERMINAL",
        "ip_address": "",
        "geo_location": "Chicago"
    })
    data["edges"]["sent"].append({"from": "MULE_C1_002", "to": "TXN_MULE3_FINAL", "sent_at": final_time.isoformat()})
    data["edges"]["withdrew_at"].append({"from": "TXN_MULE3_FINAL", "to": "ATM_CHI_001", "withdrawal_time": final_time.isoformat()})
    
    # ========================================
    # LINK ACCOUNTS TO DEVICES
    # ========================================
    # Legitimate accounts to random devices
    for i in range(1, 21):
        data["edges"]["owns_device"].append({
            "from": f"ACCT_LEGIT_{i:03d}",
            "to": f"DEV_{random.randint(1, 30):04d}",
            "first_used": (base_time - timedelta(days=random.randint(30, 365))).isoformat()
        })
    
    # Mule accounts sharing suspicious devices (red flag!)
    mule_device_links = [
        ("MULE_A1_001", "DEV_SUS_001"),
        ("MULE_A1_002", "DEV_SUS_001"),  # Same device = suspicious
        ("MULE_B1_001", "DEV_SUS_002"),
        ("MULE_C1_001", "DEV_SUS_001"),  # Same device across rings!
        ("MULE_C1_002", "DEV_SUS_001"),
    ]
    
    for acct, dev in mule_device_links:
        data["edges"]["owns_device"].append({
            "from": acct,
            "to": dev,
            "first_used": (base_time - timedelta(days=random.randint(1, 7))).isoformat()
        })
    
    return data


def load_data_to_tigergraph():
    """Load generated data into TigerGraph"""
    print("=" * 60)
    print("STEP 2: Loading Sample Data into TigerGraph")
    print("=" * 60)
    
    conn, graph_name = get_connection(use_graph=True)
    
    print("\n[1/5] Generating sample data...")
    data = generate_sample_data()
    
    print(f"  - Accounts: {len(data['accounts'])}")
    print(f"  - Transactions: {len(data['transactions'])}")
    print(f"  - Devices: {len(data['devices'])}")
    print(f"  - ATMs: {len(data['atms'])}")
    print(f"  - Wallets: {len(data['wallets'])}")
    
    # Upsert vertices
    print("\n[2/5] Loading vertices...")
    
    try:
        # Load Accounts
        print("  Loading Accounts...")
        conn.upsertVertices("Account", [
            (a["account_id"], {
                "account_type": a["account_type"],
                "holder_name": a["holder_name"],
                "created_date": a["created_date"],
                "risk_score": a["risk_score"],
                "is_flagged": a["is_flagged"],
                "kyc_verified": a["kyc_verified"]
            }) for a in data["accounts"]
        ])
        
        # Load Transactions
        print("  Loading Transactions...")
        conn.upsertVertices("Transaction", [
            (t["txn_id"], {
                "amount": t["amount"],
                "currency": t["currency"],
                "timestamp": t["timestamp"],
                "channel": t["channel"],
                "txn_type": t["txn_type"],
                "status": t["status"],
                "device_fingerprint": t["device_fingerprint"],
                "ip_address": t["ip_address"],
                "geo_location": t["geo_location"]
            }) for t in data["transactions"]
        ])
        
        # Load Devices
        print("  Loading Devices...")
        conn.upsertVertices("Device", [
            (d["device_id"], {
                "device_type": d["device_type"],
                "os_type": d["os_type"],
                "first_seen": d["first_seen"],
                "last_seen": d["last_seen"],
                "is_trusted": d["is_trusted"]
            }) for d in data["devices"]
        ])
        
        # Load ATMs
        print("  Loading ATMs...")
        conn.upsertVertices("ATM", [
            (a["atm_id"], {
                "bank_name": a["bank_name"],
                "location": a["location"],
                "city": a["city"],
                "country": a["country"],
                "latitude": a["latitude"],
                "longitude": a["longitude"]
            }) for a in data["atms"]
        ])
        
        # Load Wallets
        print("  Loading Wallets...")
        conn.upsertVertices("Wallet", [
            (w["wallet_id"], {
                "wallet_type": w["wallet_type"],
                "provider": w["provider"],
                "linked_date": w["linked_date"],
                "is_verified": w["is_verified"]
            }) for w in data["wallets"]
        ])
        
    except Exception as e:
        print(f"  Error loading vertices: {e}")
        return False
    
    # Upsert edges
    print("\n[3/5] Loading edges...")
    
    try:
        # SENT edges
        print("  Loading SENT edges...")
        conn.upsertEdges("Account", "SENT", "Transaction", [
            (e["from"], e["to"], {"sent_at": e["sent_at"]}) 
            for e in data["edges"]["sent"]
        ])
        
        # RECEIVED edges
        print("  Loading RECEIVED edges...")
        conn.upsertEdges("Transaction", "RECEIVED", "Account", [
            (e["from"], e["to"], {"received_at": e["received_at"]}) 
            for e in data["edges"]["received"]
        ])
        
        # LINKED_WALLET edges
        print("  Loading LINKED_WALLET edges...")
        conn.upsertEdges("Account", "LINKED_WALLET", "Wallet", [
            (e["from"], e["to"], {"linked_date": e["linked_date"], "is_primary": e.get("is_primary", False)}) 
            for e in data["edges"]["linked_wallet"]
        ])
        
        # OWNS_DEVICE edges
        print("  Loading OWNS_DEVICE edges...")
        conn.upsertEdges("Account", "OWNS_DEVICE", "Device", [
            (e["from"], e["to"], {"first_used": e["first_used"]}) 
            for e in data["edges"]["owns_device"]
        ])
        
        # USED_DEVICE edges
        print("  Loading USED_DEVICE edges...")
        conn.upsertEdges("Transaction", "USED_DEVICE", "Device", [
            (e["from"], e["to"], {}) 
            for e in data["edges"]["used_device"]
        ])
        
        # WITHDREW_AT edges
        print("  Loading WITHDREW_AT edges...")
        conn.upsertEdges("Transaction", "WITHDREW_AT", "ATM", [
            (e["from"], e["to"], {"withdrawal_time": e["withdrawal_time"]}) 
            for e in data["edges"]["withdrew_at"]
        ])
        
        # VIA_WALLET edges
        print("  Loading VIA_WALLET edges...")
        conn.upsertEdges("Transaction", "VIA_WALLET", "Wallet", [
            (e["from"], e["to"], {}) 
            for e in data["edges"]["via_wallet"]
        ])
        
        # WALLET_TO_ACCOUNT edges
        print("  Loading WALLET_TO_ACCOUNT edges...")
        conn.upsertEdges("Wallet", "WALLET_TO_ACCOUNT", "Account", [
            (e["from"], e["to"], {"transfer_date": e["transfer_date"], "amount": e["amount"]}) 
            for e in data["edges"]["wallet_to_account"]
        ])
        
    except Exception as e:
        print(f"  Error loading edges: {e}")
        return False
    
    print("\n[4/5] Verifying data load...")
    try:
        stats = conn.getVertexCount("*")
        print(f"  Vertex counts: {stats}")
        
        edge_stats = conn.getEdgeCount("*")
        print(f"  Edge counts: {edge_stats}")
    except Exception as e:
        print(f"  Note: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Sample data loaded successfully!")
    print("\nEmbedded Money Mule Patterns:")
    print("  - Pattern 1: MULE_A1_* (Mobile → Wallet → ATM in 25 mins)")
    print("  - Pattern 2: MULE_B1_* (5 rapid transfers + ATM cashout)")
    print("  - Pattern 3: MULE_C1_* (Multi-hop wallet chain + ATM)")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    load_data_to_tigergraph()
