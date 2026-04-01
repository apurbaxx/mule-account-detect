import pyTigerGraph as tg

# Connect to TigerGraph
conn = tg.TigerGraphConnection(
    host='http://localhost',
    restppPort='9000',
    gsPort='14240',
    userName='tigergraph',
    password='tigergraph'
)

print("Testing TigerGraph Connection...")
print("=" * 50)

# Check available graphs
try:
    result = conn.gsql('SHOW GRAPH *')
    print("Available Graphs:")
    print(result)
except Exception as e:
    print(f"Error checking graphs: {e}")

print("\nConnection test complete!")
