"""
Main Runner: Money Mule Detection System
========================================

Run this script to execute all steps in sequence:
1. Setup schema
2. Load sample data
3. Install queries
4. Run detection

Usage: python main.py
"""

import sys

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           MONEY MULE DETECTION SYSTEM - TigerGraph              ║
║     Detecting Cross-Channel Fraud with Graph Analytics          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Test Connection
    print("\n[STEP 0] Testing TigerGraph Connection...")
    try:
        from config import get_connection
        conn, graph_name = get_connection()
        result = conn.gsql('SHOW USER')
        print("✓ Connection successful!")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease ensure TigerGraph is running:")
        print("  - REST API: http://localhost:9000")
        print("  - GraphStudio: http://localhost:14240")
        sys.exit(1)
    
    # Step 1: Setup Schema
    print("\n" + "─" * 60)
    print("[STEP 1] Setting up Graph Schema...")
    print("─" * 60)
    try:
        from importlib import import_module
        setup = import_module("01_setup_schema")
        setup.setup_schema()
    except Exception as e:
        print(f"Schema setup error: {e}")
        print("Continuing anyway (schema may already exist)...")
    
    # Step 2: Load Data
    print("\n" + "─" * 60)
    print("[STEP 2] Loading Sample Data...")
    print("─" * 60)
    try:
        load_data = import_module("02_load_sample_data")
        load_data.load_data_to_tigergraph()
    except Exception as e:
        print(f"Data loading error: {e}")
        print("Please check the error and try running 02_load_sample_data.py directly")
        sys.exit(1)
    
    # Step 3: Install Queries
    print("\n" + "─" * 60)
    print("[STEP 3] Installing Detection Queries...")
    print("─" * 60)
    try:
        queries = import_module("03_create_queries")
        queries.install_queries()
    except Exception as e:
        print(f"Query installation error: {e}")
        print("Please check the error and try running 03_create_queries.py directly")
        sys.exit(1)
    
    # Step 4: Run Detection
    print("\n" + "─" * 60)
    print("[STEP 4] Running Money Mule Detection...")
    print("─" * 60)
    try:
        detection = import_module("04_run_detection")
        detection.run_detection()
    except Exception as e:
        print(f"Detection error: {e}")
        print("Please check the error and try running 04_run_detection.py directly")
        sys.exit(1)
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    ALL STEPS COMPLETED!                          ║
╠══════════════════════════════════════════════════════════════════╣
║  View your graph at: http://localhost:14240                      ║
║  Graph name: MoneyMuleGraph                                      ║
╚══════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
