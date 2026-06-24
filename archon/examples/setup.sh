#!/bin/bash
# setup.sh — Bootstrap Archon examples into your project
#
# Usage:
#   cd /path/to/your/project
#   bash /path/to/archon-tutorial/examples/setup.sh
#
# This copies all example workflows, commands, and scripts
# into your project's .archon/ directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"

# Create directories
mkdir -p "$TARGET_DIR/.archon/workflows"
mkdir -p "$TARGET_DIR/.archon/commands"
mkdir -p "$TARGET_DIR/.archon/scripts"

echo "=== Archon Examples Setup ==="
echo "Source: $SCRIPT_DIR"
echo "Target: $TARGET_DIR"
echo ""

# Copy workflow examples
echo "Copying workflows..."
cp -v "$SCRIPT_DIR/workflows/"*.yaml "$TARGET_DIR/.archon/workflows/"
echo "  → $TARGET_DIR/.archon/workflows/"
echo ""

# Copy command examples
echo "Copying commands..."
cp -v "$SCRIPT_DIR/commands/"*.md "$TARGET_DIR/.archon/commands/"
echo "  → $TARGET_DIR/.archon/commands/"
echo ""

# Copy script examples
echo "Copying scripts..."
cp -v "$SCRIPT_DIR/scripts/"* "$TARGET_DIR/.archon/scripts/"
echo "  → $TARGET_DIR/.archon/scripts/"
echo ""

echo "=== Done! ==="
echo ""
echo "Available workflows:"
ls -1 "$TARGET_DIR/.archon/workflows/"
echo ""
echo "To use:"
echo "  cd $TARGET_DIR"
echo "  claude"
echo "  > What archon workflows do I have?"
echo "  > Use archon to run hello-world"
