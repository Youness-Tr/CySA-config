#!/bin/bash
set -e

# Path to configs
CONFIG_DIR="/velociraptor/config"
SERVER_CONFIG="$CONFIG_DIR/server.config.yaml"

# Download binary if not present
if [ ! -f /usr/local/bin/velociraptor ]; then
  echo "Installing curl and ca-certificates..."
  apt-get update && apt-get install -y curl ca-certificates
  echo "Downloading Velociraptor binary..."
  VERSION="0.77.1"
  curl -L -o /usr/local/bin/velociraptor https://github.com/Velocidex/velociraptor/releases/download/v${VERSION}/velociraptor-v${VERSION}-linux-amd64
  chmod +x /usr/local/bin/velociraptor
fi

# Generate configuration if not present
if [ ! -f "$SERVER_CONFIG" ]; then
  echo "Generating new server config..."
  mkdir -p "$CONFIG_DIR"
  /usr/local/bin/velociraptor config generate > "$SERVER_CONFIG"
  
  # Update bind address for GUI to allow external connections
  sed -i 's/bind_address: 127.0.0.1/bind_address: 0.0.0.0/g' "$SERVER_CONFIG"
  
  # Update server URLs to use public IP
  sed -i 's/https:\/\/localhost:8000\//https:\/\/20.91.141.211:8001\//g' "$SERVER_CONFIG"
  
  echo "Adding admin user..."
  /usr/local/bin/velociraptor --config "$SERVER_CONFIG" user add admin cysa-atlas-forensics --role administrator
fi

echo "Starting Velociraptor Server..."
exec /usr/local/bin/velociraptor --config "$SERVER_CONFIG" frontend
