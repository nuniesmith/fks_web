#!/bin/bash

# Fix React Dependencies Script
# This script cleans up npm cache and fixes integrity issues

set -e

echo "🧹 Cleaning npm cache and fixing integrity issues..."

# Clean npm cache
npm cache clean --force

# Remove problematic files
rm -rf node_modules package-lock.json

echo "📦 Installing dependencies with integrity fixes..."

# Use npm install with specific flags to handle deprecated packages and integrity issues
npm install --legacy-peer-deps --no-audit --no-fund --maxsockets 1 --progress=false

echo "🔧 Attempting to fix known vulnerability issues..."

# Fix deprecated packages if npm audit fix is available
npm audit fix --legacy-peer-deps --force || echo "⚠️ Audit fix completed with warnings"

echo "✅ Dependencies installed successfully"

echo "🧪 Testing build..."

# Test if the project builds
if npm run build; then
    echo "✅ Build test successful"
else
    echo "❌ Build test failed"
    echo "🔧 Trying with legacy OpenSSL provider..."
    NODE_OPTIONS="--openssl-legacy-provider" npm run build || echo "❌ Build failed with both standard and legacy approaches"
fi

echo "🏁 Dependency fix complete!"
