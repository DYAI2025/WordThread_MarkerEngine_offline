#!/bin/bash

set -e

# Gemini CLI Quickstart Script
# This script installs Node.js 20 if needed, installs the Gemini CLI globally,
# and then starts the CLI.

MIN_NODE_MAJOR=20

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

need_node_install=false
if command_exists node; then
  NODE_MAJOR=$(node -v | sed 's/v\([0-9]*\).*/\1/')
  if [ "$NODE_MAJOR" -lt "$MIN_NODE_MAJOR" ]; then
    need_node_install=true
  fi
else
  need_node_install=true
fi

install_node() {
  echo "Installing Node.js 20..."
  if command_exists apt-get; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
  elif command_exists brew; then
    brew install node@20
    brew link --overwrite --force node@20
  else
    echo "Unsupported OS or missing package manager. Please install Node.js 20 manually." >&2
    exit 1
  fi
}

if [ "$need_node_install" = true ]; then
  install_node
else
  echo "Node.js is already installed."
fi

# Install Gemini CLI globally
if ! command_exists gemini; then
  echo "Installing Gemini CLI..."
  npm install -g @google/gemini-cli
else
  echo "Gemini CLI already installed."
fi

# Launch Gemini CLI
exec gemini "$@"

