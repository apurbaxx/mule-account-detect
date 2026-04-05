# Money Mule Detection System using TigerGraph

## Problem Statement

Money mules operate across channels to hide their tracks—e.g., receiving money via Mobile App, moving it to a Linked Wallet, and withdrawing cash at an ATM in minutes. **Siloed fraud rules miss this high-velocity cross-channel pattern.**

## Solution

This system uses **TigerGraph's graph database** to detect money mule patterns by:

1. **Modeling transactions as a graph** - Accounts, Transactions, Wallets, Devices, and ATMs as vertices with edges representing money flow and relationships
2. **Cross-channel traversal** - Following money across Mobile App → Wallet → ATM in a single query
3. **Pattern matching** - Identifying suspicious patterns like:
   - High-velocity transactions (many transactions in short time)
   - Rapid accumulation and cashout
   - Shared devices across multiple accounts
   - Cross-channel activity within minutes

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the visual dashboard (RECOMMENDED for demo)
streamlit run dashboard.py

# Or run console detection
python demo.py
```

## 📊 Visual Dashboard

The Streamlit dashboard provides:

![Dashboard Preview](https://via.placeholder.com/800x400?text=Money+Mule+Detection+Dashboard)

- **Dashboard Overview** - Real-time metrics and alerts
- **Detection Results** - Detailed risk scores and factors
- **Network Visualization** - Interactive graph of money flow
- **Cross-Channel Analysis** - Sankey diagrams showing fund movements
- **Device Analysis** - Identity linkage through shared devices

### Run the Dashboard

```bash
streamlit run dashboard.py
```

Then open http://localhost:8501 in your browser.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TigerGraph Money Mule Detection             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌─────────────┐    ┌──────────┐             │
│   │  Mobile  │───▶│ Transaction │───▶│  Wallet  │             │
│   │   App    │    │             │    │          │             │
│   └──────────┘    └─────────────┘    └────┬─────┘             │
│                                           │                    │
│                                           ▼                    │
│   ┌──────────┐    ┌─────────────┐    ┌──────────┐             │
│   │  Device  │◀───│   Account   │───▶│   ATM    │             │
│   │          │    │   (Mule)    │    │          │             │
│   └──────────┘    └─────────────┘    └──────────┘             │
│                                                                 │
│   Graph Query: Traverse all paths in <30 minutes               │
│                Detect: Mobile → Wallet → ATM pattern           │
└─────────────────────────────────────────────────────────────────┘
```

## Graph Schema

### Vertices
| Vertex | Description |
|--------|-------------|
| **Account** | Bank accounts, wallets, user profiles |
| **Transaction** | Individual financial transactions |
| **Device** | Phones, computers, ATM terminals |
| **Wallet** | Digital wallets (PayPal, Venmo, Crypto) |
| **ATM** | Physical ATM locations |

### Edges
| Edge | From → To | Description |
|------|-----------|-------------|
| **SENT** | Account → Transaction | Account initiated transaction |
| **RECEIVED** | Transaction → Account | Account received funds |
| **LINKED_WALLET** | Account → Wallet | Account has linked wallet |
| **VIA_WALLET** | Transaction → Wallet | Transfer went through wallet |
| **WITHDREW_AT** | Transaction → ATM | Cash withdrawal location |
| **OWNS_DEVICE** | Account → Device | Account uses this device |
| **WALLET_TO_ACCOUNT** | Wallet → Account | Wallet transferred to account |

## Detection Queries

### 1. `detect_money_mule_comprehensive`
**Purpose:** Comprehensive detection combining multiple signals

**Risk Factors Detected:**
- Large mobile deposits (+20 risk score)
- ATM withdrawals (+25 risk score)
- Wallet transfers (+15 risk score)
- Shared devices (+30 risk score)
- High velocity (+25 risk score)
- Cross-channel activity (+10-20 risk score)
- Rapid in-out pattern (+20 risk score)

**Threshold:** Accounts with risk score ≥40 are flagged

### 2. `detect_high_velocity_pattern`
Finds accounts with multiple transactions in a short time window

### 3. `detect_shared_devices`
Identifies devices used by multiple accounts (coordinated fraud indicator)

### 4. `detect_mobile_wallet_atm_pattern`
Specific detection of the Mobile→Wallet→ATM sequence within 30 minutes

### 5. `trace_money_flow`
Investigative query to trace money movement from a suspicious account

### 6. `get_account_risk_summary`
Dashboard query showing all accounts with their risk indicators

## Installation & Usage

### Prerequisites
- TigerGraph Enterprise (local or cloud)
- Python 3.8+
- pyTigerGraph library

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run all steps at once
python main.py

# OR run individual steps:
python config.py              # Test connection
python 01_setup_schema.py     # Create graph schema
python 02_load_sample_data.py # Load sample data
python 03_create_queries.py   # Install GSQL queries
python 04_run_detection.py    # Run detection
```

### Configuration

The system supports multiple configuration methods:

#### Option 1: Environment Variables
```bash
export TIGERGRAPH_HOST="https://your-ngrok-url.ngrok-free.app"
export TIGERGRAPH_REST_PORT="443"
export TIGERGRAPH_GS_PORT="443"
export TIGERGRAPH_USERNAME="tigergraph"
export TIGERGRAPH_PASSWORD="tigergraph"
export TIGERGRAPH_GRAPH="MoneyMuleGraph"
```

#### Option 2: Edit config.py
The default configuration connects to the ngrok-exposed TigerGraph instance.

### Streamlit Community Cloud Deployment

To deploy the dashboard on Streamlit Community Cloud:

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your GitHub repo
4. In App Settings → Secrets, add:

```toml
[tigergraph]
host = "https://your-ngrok-url.ngrok-free.app"
restppPort = "443"
gsPort = "443"
username = "tigergraph"
password = "tigergraph"
graphname = "MoneyMuleGraph"
```

**Important:** Your ngrok URL must be running and accessible for the dashboard to work.

## Sample Data

The system includes realistic sample data with:
- **20 legitimate accounts** with normal transaction patterns
- **3 money mule patterns:**
  - **Pattern 1 (MULE_A1_*):** Classic Mobile → Wallet → ATM in 25 minutes
  - **Pattern 2 (MULE_B1_*):** 5 rapid transfers + ATM cashout in 28 minutes
  - **Pattern 3 (MULE_C1_*):** Multi-hop wallet chain + ATM in 32 minutes
- **Shared suspicious devices** (DEV_SUS_001, DEV_SUS_002)
- **6 ATM locations** across US cities
- **23 wallets** including 3 mule-associated wallets

## Viewing Results

1. **Console Output:** Run `python 04_run_detection.py` for detection alerts
2. **GraphStudio:** Open http://localhost:14240 to visualize the graph
3. **REST API:** Query via http://localhost:9000

## Why Graph Databases?

Traditional fraud detection uses **siloed rules** that check individual channels:
- ❌ Mobile rule: "Flag deposits > $5000"
- ❌ Wallet rule: "Flag transfers > $4000"  
- ❌ ATM rule: "Flag withdrawals > $3000"

**Problem:** A mule depositing $5000 via mobile, transferring $4900 to wallet, and withdrawing $4800 at ATM passes ALL individual rules.

**Graph Solution:**
```gsql
// Single query traverses ALL channels
Account -[RECEIVED]-> Transaction (mobile_app, $5000)
        -[SENT]-> Transaction -[VIA_WALLET]-> Wallet
                              -[WALLET_TO_ACCOUNT]-> Account
                              -[SENT]-> Transaction -[WITHDREW_AT]-> ATM

// Time constraint: < 30 minutes end-to-end
// Result: FLAGGED as money mule pattern
```

## Files

| File | Description |
|------|-------------|
| `config.py` | Connection configuration and test |
| `01_setup_schema.py` | Creates TigerGraph schema |
| `02_load_sample_data.py` | Generates and loads sample data |
| `03_create_queries.py` | Installs GSQL detection queries |
| `04_run_detection.py` | Runs detection and displays results |
| `main.py` | Runs all steps in sequence |

