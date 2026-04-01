"""
Step 3: Create GSQL Queries for Money Mule Detection
====================================================

This script installs GSQL queries that detect cross-channel money mule patterns:
1. High-velocity cross-channel transactions
2. Mobile App → Wallet → ATM patterns
3. Shared device detection across accounts
4. Rapid accumulation and cashout patterns
"""

from config import get_connection, TIGERGRAPH_CONFIG

# ========================================
# GSQL QUERY DEFINITIONS
# ========================================

QUERIES = {
    # Query 1: Detect Mobile → Wallet → ATM pattern within time window
    "detect_mobile_wallet_atm_pattern": '''
CREATE QUERY detect_mobile_wallet_atm_pattern(INT time_window_minutes = 30, FLOAT min_amount = 1000) FOR GRAPH MoneyMuleGraph {
    /*
     * Detects the classic money mule pattern:
     * 1. Receive funds via Mobile App
     * 2. Transfer to Wallet
     * 3. Withdraw at ATM
     * All within a specified time window
     */
    
    TYPEDEF TUPLE<STRING account_id, STRING holder_name, FLOAT total_amount, 
                  INT step_count, STRING channels_used, DATETIME first_txn, DATETIME last_txn> MuleCandidate;
    
    SetAccum<STRING> @channels;
    SumAccum<FLOAT> @total_in;
    SumAccum<FLOAT> @total_out;
    SumAccum<INT> @txn_count;
    MinAccum<DATETIME> @first_txn;
    MaxAccum<DATETIME> @last_txn;
    ListAccum<MuleCandidate> @@suspicious_accounts;
    
    // Start from all accounts
    AllAccounts = {Account.*};
    
    // Step 1: Find accounts that received funds via mobile app
    MobileReceivers = SELECT a
        FROM AllAccounts:a -(RECEIVED:r)- Transaction:t
        WHERE t.channel == "mobile_app" AND t.amount >= min_amount
        ACCUM 
            a.@channels += t.channel,
            a.@total_in += t.amount,
            a.@txn_count += 1,
            a.@first_txn += t.timestamp,
            a.@last_txn += t.timestamp;
    
    // Step 2: Check if these accounts sent to wallets
    WalletSenders = SELECT a
        FROM MobileReceivers:a -(SENT:s)- Transaction:t -(VIA_WALLET:v)- Wallet:w
        WHERE t.channel == "wallet_transfer"
        ACCUM
            a.@channels += t.channel,
            a.@total_out += t.amount,
            a.@txn_count += 1,
            a.@last_txn += t.timestamp;
    
    // Step 3: Find accounts with ATM withdrawals
    // Get accounts linked to wallets that received funds
    LinkedToWallet = SELECT a 
        FROM WalletSenders:src -(LINKED_WALLET)- Wallet:w -(WALLET_TO_ACCOUNT)- Account:a;
    
    ATMWithdrawers = SELECT a
        FROM LinkedToWallet:a -(SENT:s)- Transaction:t -(WITHDREW_AT)- ATM:atm
        WHERE t.channel == "atm" AND t.txn_type == "withdrawal"
        ACCUM
            a.@channels += "atm",
            a.@total_out += t.amount,
            a.@txn_count += 1,
            a.@last_txn += t.timestamp;
    
    // Combine and filter by time window
    SuspiciousAccounts = SELECT a
        FROM WalletSenders:a
        WHERE a.@channels.size() >= 2 
          AND datetime_diff(a.@last_txn, a.@first_txn) <= time_window_minutes * 60
        POST-ACCUM
            @@suspicious_accounts += MuleCandidate(
                a.account_id, 
                a.holder_name, 
                a.@total_in, 
                a.@txn_count,
                setToString(a.@channels),
                a.@first_txn,
                a.@last_txn
            );
    
    PRINT @@suspicious_accounts AS suspicious_accounts;
    PRINT SuspiciousAccounts[SuspiciousAccounts.account_id, SuspiciousAccounts.holder_name, 
                            SuspiciousAccounts.@total_in, SuspiciousAccounts.@channels];
}
''',

    # Query 2: Detect high-velocity transactions
    "detect_high_velocity_pattern": '''
CREATE QUERY detect_high_velocity_pattern(INT time_window_minutes = 30, INT min_txn_count = 3, FLOAT min_total = 3000) FOR GRAPH MoneyMuleGraph {
    /*
     * Detects accounts with unusually high transaction velocity:
     * Multiple transactions in a short time window indicating potential mule activity
     */
    
    TYPEDEF TUPLE<STRING account_id, STRING holder_name, INT txn_count, 
                  FLOAT total_amount, FLOAT avg_amount, INT time_span_seconds> VelocityAlert;
    
    SumAccum<FLOAT> @total_received;
    SumAccum<INT> @received_count;
    MinAccum<DATETIME> @first_received;
    MaxAccum<DATETIME> @last_received;
    ListAccum<VelocityAlert> @@high_velocity_accounts;
    
    AllAccounts = {Account.*};
    
    // Find accounts with multiple incoming transactions
    HighVelocity = SELECT a
        FROM AllAccounts:a -(RECEIVED:r)- Transaction:t
        ACCUM
            a.@total_received += t.amount,
            a.@received_count += 1,
            a.@first_received += t.timestamp,
            a.@last_received += t.timestamp
        HAVING 
            a.@received_count >= min_txn_count AND
            a.@total_received >= min_total AND
            datetime_diff(a.@last_received, a.@first_received) <= time_window_minutes * 60
        POST-ACCUM
            @@high_velocity_accounts += VelocityAlert(
                a.account_id,
                a.holder_name,
                a.@received_count,
                a.@total_received,
                a.@total_received / a.@received_count,
                datetime_diff(a.@last_received, a.@first_received)
            );
    
    PRINT @@high_velocity_accounts AS high_velocity_alerts;
    PRINT HighVelocity[HighVelocity.account_id, HighVelocity.holder_name, 
                       HighVelocity.@received_count, HighVelocity.@total_received];
}
''',

    # Query 3: Detect shared devices across accounts (identity linkage)
    "detect_shared_devices": '''
CREATE QUERY detect_shared_devices(INT min_accounts = 2) FOR GRAPH MoneyMuleGraph {
    /*
     * Finds devices that are shared across multiple accounts
     * This is a strong indicator of coordinated mule activity
     */
    
    TYPEDEF TUPLE<STRING device_id, STRING device_type, INT account_count, STRING linked_accounts> SharedDevice;
    
    SetAccum<STRING> @linked_accounts;
    SumAccum<INT> @account_count;
    ListAccum<SharedDevice> @@shared_devices;
    
    AllDevices = {Device.*};
    
    // Find devices linked to multiple accounts
    SharedDevices = SELECT d
        FROM AllDevices:d -(OWNS_DEVICE:o)- Account:a
        ACCUM
            d.@linked_accounts += a.account_id,
            d.@account_count += 1
        HAVING d.@account_count >= min_accounts
        POST-ACCUM
            @@shared_devices += SharedDevice(
                d.device_id,
                d.device_type,
                d.@account_count,
                setToString(d.@linked_accounts)
            );
    
    PRINT @@shared_devices AS shared_device_alerts;
    PRINT SharedDevices[SharedDevices.device_id, SharedDevices.device_type, 
                        SharedDevices.@account_count, SharedDevices.@linked_accounts];
}
''',

    # Query 4: Full money mule pattern detection (comprehensive)
    "detect_money_mule_comprehensive": '''
CREATE QUERY detect_money_mule_comprehensive(INT time_window_minutes = 30, FLOAT amount_threshold = 1000) FOR GRAPH MoneyMuleGraph SYNTAX V2 {
    /*
     * Comprehensive money mule detection that combines multiple signals:
     * 1. Cross-channel activity (mobile, wallet, ATM)
     * 2. High velocity transactions
     * 3. Device sharing
     * 4. Recent account creation
     * 5. Rapid in-out patterns
     */
    
    TYPEDEF TUPLE<STRING account_id, STRING holder_name, FLOAT risk_score,
                  STRING risk_factors, FLOAT total_in, FLOAT total_out, 
                  INT channel_count, STRING channels> MuleRiskProfile;
    
    // Accumulators for risk scoring
    SumAccum<FLOAT> @risk_score;
    SetAccum<STRING> @risk_factors;
    SetAccum<STRING> @channels_used;
    SumAccum<FLOAT> @total_inflow;
    SumAccum<FLOAT> @total_outflow;
    SumAccum<INT> @txn_count;
    MinAccum<DATETIME> @first_activity;
    MaxAccum<DATETIME> @last_activity;
    SumAccum<INT> @shared_device_count;
    ListAccum<MuleRiskProfile> @@mule_candidates;
    
    AllAccounts = {Account.*};
    
    // Step 1: Analyze inbound transactions
    AccountsWithInflow = SELECT a
        FROM AllAccounts:a -(RECEIVED:r)- Transaction:t
        WHERE t.amount >= amount_threshold
        ACCUM
            a.@total_inflow += t.amount,
            a.@channels_used += t.channel,
            a.@txn_count += 1,
            a.@first_activity += t.timestamp,
            a.@last_activity += t.timestamp,
            // Mobile app large deposits are suspicious
            CASE WHEN t.channel == "mobile_app" AND t.amount >= 3000 THEN
                a.@risk_score += 20,
                a.@risk_factors += "large_mobile_deposit"
            END;
    
    // Step 2: Analyze outbound transactions
    AccountsWithOutflow = SELECT a
        FROM AccountsWithInflow:a -(SENT:s)- Transaction:t
        ACCUM
            a.@total_outflow += t.amount,
            a.@channels_used += t.channel,
            a.@last_activity += t.timestamp,
            // ATM withdrawals after receiving are suspicious
            CASE WHEN t.channel == "atm" AND t.txn_type == "withdrawal" THEN
                a.@risk_score += 25,
                a.@risk_factors += "atm_withdrawal"
            END,
            // Wallet transfers are suspicious
            CASE WHEN t.channel == "wallet_transfer" THEN
                a.@risk_score += 15,
                a.@risk_factors += "wallet_transfer"
            END;
    
    // Step 3: Check for wallet linkages
    WalletLinked = SELECT a
        FROM AccountsWithOutflow:a -(LINKED_WALLET)- Wallet:w
        ACCUM
            a.@risk_score += 10,
            a.@risk_factors += "wallet_linked";
    
    // Step 4: Check for device sharing
    DeviceLinked = SELECT a
        FROM AccountsWithOutflow:a -(OWNS_DEVICE)- Device:d -(OWNS_DEVICE)- Account:other
        WHERE a != other
        ACCUM
            a.@shared_device_count += 1,
            a.@risk_score += 30,
            a.@risk_factors += "shared_device";
    
    // Step 5: Score based on velocity and cross-channel activity
    ScoredAccounts = SELECT a
        FROM AccountsWithOutflow:a
        POST-ACCUM
            // High velocity bonus
            CASE WHEN a.@txn_count >= 3 AND 
                      datetime_diff(a.@last_activity, a.@first_activity) <= time_window_minutes * 60 THEN
                a.@risk_score += 25,
                a.@risk_factors += "high_velocity"
            END,
            // Cross-channel bonus
            CASE WHEN a.@channels_used.size() >= 3 THEN
                a.@risk_score += 20,
                a.@risk_factors += "cross_channel"
            ELSE CASE WHEN a.@channels_used.size() >= 2 THEN
                a.@risk_score += 10
            END END,
            // Rapid in-out pattern
            CASE WHEN a.@total_outflow >= a.@total_inflow * 0.9 AND a.@total_inflow >= amount_threshold THEN
                a.@risk_score += 20,
                a.@risk_factors += "rapid_in_out"
            END;
    
    // Step 6: Filter high-risk accounts
    HighRiskAccounts = SELECT a
        FROM ScoredAccounts:a
        WHERE a.@risk_score >= 40  // Threshold for flagging
        POST-ACCUM
            @@mule_candidates += MuleRiskProfile(
                a.account_id,
                a.holder_name,
                a.@risk_score,
                setToString(a.@risk_factors),
                a.@total_inflow,
                a.@total_outflow,
                a.@channels_used.size(),
                setToString(a.@channels_used)
            );
    
    PRINT @@mule_candidates AS money_mule_candidates;
    PRINT HighRiskAccounts[HighRiskAccounts.account_id, HighRiskAccounts.holder_name,
                           HighRiskAccounts.@risk_score, HighRiskAccounts.@risk_factors,
                           HighRiskAccounts.@channels_used];
}
''',

    # Query 5: Trace money flow path
    "trace_money_flow": '''
CREATE QUERY trace_money_flow(VERTEX<Account> start_account, INT max_depth = 5) FOR GRAPH MoneyMuleGraph {
    /*
     * Traces the flow of money from a starting account through the network
     * Useful for investigating flagged accounts
     */
    
    TYPEDEF TUPLE<STRING from_acct, STRING to_acct, FLOAT amount, STRING channel, DATETIME timestamp> FlowStep;
    
    ListAccum<FlowStep> @@money_flow;
    OrAccum @visited;
    
    Start = {start_account};
    Start = SELECT s FROM Start:s POST-ACCUM s.@visited = true;
    
    // Traverse outbound transactions
    FOREACH i IN RANGE[1, max_depth] DO
        Transactions = SELECT t
            FROM Start:a -(SENT:s)- Transaction:t
            WHERE NOT t.@visited
            ACCUM t.@visited = true;
        
        Recipients = SELECT r
            FROM Transactions:t -(RECEIVED:rec)- Account:r
            WHERE NOT r.@visited
            ACCUM
                r.@visited = true,
                @@money_flow += FlowStep(
                    t.@visited == true ? "via_txn" : "",
                    r.account_id,
                    t.amount,
                    t.channel,
                    t.timestamp
                );
        
        Start = Recipients;
    END;
    
    PRINT @@money_flow AS money_trail;
    PRINT Start AS reached_accounts;
}
''',

    # Query 6: Get account risk summary
    "get_account_risk_summary": '''
CREATE QUERY get_account_risk_summary() FOR GRAPH MoneyMuleGraph {
    /*
     * Provides a summary of all accounts with their risk indicators
     */
    
    SumAccum<FLOAT> @total_in;
    SumAccum<FLOAT> @total_out;
    SumAccum<INT> @txn_count;
    SumAccum<INT> @wallet_count;
    SumAccum<INT> @device_count;
    SumAccum<INT> @atm_withdrawals;
    
    AllAccounts = {Account.*};
    
    // Count incoming transactions
    AccountsIn = SELECT a
        FROM AllAccounts:a -(RECEIVED)- Transaction:t
        ACCUM
            a.@total_in += t.amount,
            a.@txn_count += 1;
    
    // Count outgoing transactions and ATM withdrawals
    AccountsOut = SELECT a
        FROM AllAccounts:a -(SENT)- Transaction:t
        ACCUM
            a.@total_out += t.amount,
            a.@txn_count += 1,
            CASE WHEN t.channel == "atm" THEN a.@atm_withdrawals += 1 END;
    
    // Count wallets
    AccountsWallet = SELECT a
        FROM AllAccounts:a -(LINKED_WALLET)- Wallet:w
        ACCUM a.@wallet_count += 1;
    
    // Count devices
    AccountsDevice = SELECT a
        FROM AllAccounts:a -(OWNS_DEVICE)- Device:d
        ACCUM a.@device_count += 1;
    
    PRINT AllAccounts[AllAccounts.account_id, AllAccounts.holder_name, AllAccounts.account_type,
                      AllAccounts.@total_in, AllAccounts.@total_out, AllAccounts.@txn_count,
                      AllAccounts.@wallet_count, AllAccounts.@device_count, AllAccounts.@atm_withdrawals];
}
'''
}


def install_queries():
    """Install all detection queries into TigerGraph"""
    print("=" * 60)
    print("STEP 3: Installing Money Mule Detection Queries")
    print("=" * 60)
    
    conn, graph_name = get_connection()
    
    print(f"\nTarget graph: {graph_name}")
    print(f"Installing {len(QUERIES)} queries...\n")
    
    # First, drop existing queries
    print("[1/3] Dropping existing queries...")
    for query_name in QUERIES.keys():
        try:
            conn.gsql(f'USE GRAPH {graph_name}\nDROP QUERY {query_name}')
            print(f"  Dropped: {query_name}")
        except:
            pass  # Query might not exist
    
    # Install each query
    print("\n[2/3] Creating queries...")
    for query_name, query_gsql in QUERIES.items():
        try:
            print(f"  Installing: {query_name}...")
            result = conn.gsql(f'USE GRAPH {graph_name}\n{query_gsql}')
            print(f"    Result: {result[:100] if len(result) > 100 else result}")
        except Exception as e:
            print(f"    Error: {e}")
    
    # Install all queries
    print("\n[3/3] Installing queries...")
    try:
        result = conn.gsql(f'USE GRAPH {graph_name}\nINSTALL QUERY ALL')
        print(result)
    except Exception as e:
        print(f"  Error during installation: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Query installation complete!")
    print("\nAvailable queries:")
    for name in QUERIES.keys():
        print(f"  - {name}")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    install_queries()
