#!/bin/bash
set -e

echo "==== BensBot Codebase Cleanup ===="
echo "This script will consolidate and clean up the project structure."
echo "Make sure you have committed your changes before running this script!"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Create directories if they don't exist
mkdir -p trading-dashboard
mkdir -p dev_tools
mkdir -p docs

# Step 1: Consolidate frontend
echo "Step 1: Consolidating frontend code..."
if [ -d "new-trading-dashboard" ] && [ -d "trading-dashboard" ]; then
    # Check which is more up-to-date based on last commit date
    NEW_COMMIT=$(git log -1 --format="%ct" -- new-trading-dashboard)
    OLD_COMMIT=$(git log -1 --format="%ct" -- trading-dashboard)
    
    if [ "$NEW_COMMIT" -gt "$OLD_COMMIT" ]; then
        echo "Using new-trading-dashboard as the main frontend (more recent)"
        TARGET_DIR="trading-dashboard"
        SOURCE_DIR="new-trading-dashboard"
    else
        echo "Using trading-dashboard as the main frontend (more recent)"
        TARGET_DIR="new-trading-dashboard"
        SOURCE_DIR="trading-dashboard"
    fi
    
    # Copy important files from SOURCE to TARGET
    cp -r $SOURCE_DIR/src/* trading-dashboard/src/ 2>/dev/null || mkdir -p trading-dashboard/src
    cp -r $SOURCE_DIR/public/* trading-dashboard/public/ 2>/dev/null || mkdir -p trading-dashboard/public
    cp $SOURCE_DIR/package.json trading-dashboard/ 2>/dev/null || echo "No package.json found"
    cp $SOURCE_DIR/vite.config.ts trading-dashboard/ 2>/dev/null || echo "No vite.config.ts found"
    cp $SOURCE_DIR/tsconfig.json trading-dashboard/ 2>/dev/null || echo "No tsconfig.json found"
    cp $SOURCE_DIR/.env.local trading-dashboard/ 2>/dev/null || echo "No .env.local found"
    cp $SOURCE_DIR/tailwind.config.js trading-dashboard/ 2>/dev/null || echo "No tailwind.config.js found"
    
    # Delete the outdated frontend directory
    echo "Removing $TARGET_DIR directory..."
    rm -rf $TARGET_DIR
fi

# Step 2: Move mock API to dev_tools
echo "Step 2: Moving mock_api.py to dev_tools directory..."
if [ -f "mock_api.py" ]; then
    mv mock_api.py dev_tools/
fi

# Step 3: Consolidate documentation
echo "Step 3: Consolidating documentation..."
if [ -f "README-PRODUCTION.md" ]; then
    mv README-PRODUCTION.md docs/production-guide.md
fi
if [ -f "UNIFIED_SYSTEM_GUIDE.md" ]; then
    mv UNIFIED_SYSTEM_GUIDE.md docs/system-guide.md
fi
if [ -f "launch_checklist.md" ]; then
    mv launch_checklist.md docs/launch-checklist.md
fi

# Update main README.md to reference moved docs
echo "Updating README.md to reference moved documentation..."
cat << 'EOF' >> README.md

## Documentation
For more detailed information, see the following guides:
- [Production Guide](docs/production-guide.md)
- [System Guide](docs/system-guide.md)
- [Launch Checklist](docs/launch-checklist.md)
EOF

# Step 4: Clean up script duplication
echo "Step 4: Cleaning up script duplication..."
mkdir -p scripts/archive

# Archive redundant scripts and launch files
for file in scripts/test_framework.py scripts/test_monte_carlo.py scripts/validate_enhancements.py verify_config.py; do
    if [ -f "$file" ]; then
        echo "Archiving $file..."
        mv "$file" scripts/archive/
    fi
done

# Step 5: Standardize Docker setup
echo "Step 5: Standardizing Docker setup..."
mkdir -p docker
if [ -f "Dockerfile.api" ] && [ -f "Dockerfile.frontend" ]; then
    mv Dockerfile.api docker/
    mv Dockerfile.frontend docker/
    echo "Moved Dockerfiles to docker/ directory"
fi

# Archive redundant launch scripts
mkdir -p scripts/launch
for file in launch_*.sh; do
    if [ -f "$file" ] && [ "$file" != "launch_checklist.md" ]; then
        echo "Moving $file to scripts/launch/"
        mv "$file" scripts/launch/
    fi
done

echo "==== Cleanup Complete ===="
echo "Next steps:"
echo "1. Review the changes and ensure everything still works"
echo "2. Update references to moved files in your codebase"
echo "3. Commit the cleanup changes"
echo "4. Run 'npm install' in the trading-dashboard directory" 