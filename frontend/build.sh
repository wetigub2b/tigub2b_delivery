#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Building with npx vite..."
echo "y" | npx --yes vite@5.4.21 build
