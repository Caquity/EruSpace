#!/bin/bash
set -e

echo "🚀 Starting OpenAgents Network..."

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Shutting down services..."
    kill $NETWORK_PID 2>/dev/null || true
    wait $NETWORK_PID 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start the OpenAgents Network
echo "🌐 Starting OpenAgents Network on port 8700..."
echo "   - Studio will be available at /studio"
echo "   - MCP will be available at /mcp"
echo "   - gRPC transport on port 8600"

# Use custom network config from environment variable or default
NETWORK_CONFIG=${NETWORK_CONFIG:-/network}
echo "📝 Using network configuration: $NETWORK_CONFIG"
openagents network start "$NETWORK_CONFIG" &
NETWORK_PID=$!

# Wait for network to be ready
echo "⏳ Waiting for network to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8700/api/health > /dev/null 2>&1; then
        echo "✅ Network is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Network failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Auto-start agents if AGENTS_DIR is set and exists
if [ -n "$AGENTS_DIR" ] && [ -d "$AGENTS_DIR" ]; then
    echo "🤖 Auto-starting agents from: $AGENTS_DIR"
    
    # Start Python agents (*.py files)
    for agent_file in "$AGENTS_DIR"/*.py; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file" .py)
            echo "   ▶️  Starting Python agent: $agent_name"
            python "$agent_file" &
            sleep 2  # Small delay between agent starts
        fi
    done
    
    # Start YAML agents (*.yaml files)
    for agent_file in "$AGENTS_DIR"/*.yaml; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file" .yaml)
            echo "   ▶️  Starting YAML agent: $agent_name"
            openagents agent start "$agent_file" &
            sleep 2  # Small delay between agent starts
        fi
    done
    
    echo "✅ All agents started!"
fi

echo ""
echo "✅ OpenAgents is running!"
echo ""
echo "📍 Access points:"
echo "   - Studio Web UI: http://localhost:8700/studio/"
echo "   - MCP Protocol:  http://localhost:8700/mcp"
echo "   - HTTP API:      http://localhost:8700/api/"
echo "   - gRPC:          localhost:8600"
echo ""
echo "Press Ctrl+C to stop"

# Wait for network process
wait $NETWORK_PID

# Exit with status of process
exit $?
