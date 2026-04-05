import pyTigerGraph as tg
import os

# Get TigerGraph config from environment or use defaults
host = os.environ.get("TIGERGRAPH_HOST", "https://cd6d-139-167-143-182.ngrok-free.app")
rest_port = os.environ.get("TIGERGRAPH_REST_PORT", "443")
gs_port = os.environ.get("TIGERGRAPH_GS_PORT", "443")
username = os.environ.get("TIGERGRAPH_USERNAME", "tigergraph")
password = os.environ.get("TIGERGRAPH_PASSWORD", "tigergraph")

# Connect to TigerGraph
conn = tg.TigerGraphConnection(
    host=host,
    restppPort=rest_port,
    gsPort=gs_port,
    userName=username,
    password=password
)

print("Testing TigerGraph Connection...")
print("=" * 50)
print(f"Host: {host}")
print(f"REST Port: {rest_port}")
print(f"GS Port: {gs_port}")
print("=" * 50)

# Check available graphs
try:
    result = conn.gsql('SHOW GRAPH *')
    print("Available Graphs:")
    print(result)
except Exception as e:
    print(f"Error checking graphs: {e}")

print("\nConnection test complete!")
