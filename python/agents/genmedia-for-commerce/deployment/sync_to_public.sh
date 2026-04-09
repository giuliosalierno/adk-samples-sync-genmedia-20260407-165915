#!/bin/bash
# Sync code (no binary assets) to the adk-samples fork for PR to google/adk-samples.
#
# Usage:
#   make sync-to-public
#   # or directly:
#   bash deployment/sync_to_public.sh [--dry-run]
#
# What it does:
#   1. Clones/updates the fork of google/adk-samples
#   2. Copies code files (excluding binary assets) into python/agents/genmedia-for-commerce/
#   3. Commits and pushes to the fork
#   4. Optionally opens a PR to google/adk-samples

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FORK_REPO="lspataroG/adk-samples"
UPSTREAM_REPO="google/adk-samples"
SYNC_DIR="/tmp/adk-samples-sync"
TARGET_DIR="python/agents/genmedia-for-commerce"
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
    esac
done

# Binary asset extensions to exclude
EXCLUDE_EXTENSIONS="*.png *.jpg *.jpeg *.webp *.mp4 *.mov *.npz *.npy *.wasm *.data *.h5"

echo "=== Syncing to public repo ==="

# 1. Clone or update the fork
if [ -d "$SYNC_DIR" ]; then
    echo "Updating existing clone..."
    cd "$SYNC_DIR"
    git fetch origin
    git checkout main
    git reset --hard origin/main
else
    echo "Cloning fork..."
    gh repo clone "$FORK_REPO" "$SYNC_DIR"
    cd "$SYNC_DIR"
    git remote add upstream "https://github.com/$UPSTREAM_REPO.git" 2>/dev/null || true
fi

# Sync with upstream
echo "Syncing fork with upstream..."
git fetch upstream
git merge upstream/main --no-edit 2>/dev/null || true

# 2. Create a sync branch
BRANCH="sync-genmedia-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BRANCH"

# 3. Clean the target directory
rm -rf "$SYNC_DIR/$TARGET_DIR"
mkdir -p "$SYNC_DIR/$TARGET_DIR"

# 4. Build rsync exclude list
EXCLUDE_ARGS=""
for ext in $EXCLUDE_EXTENSIONS; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$ext"
done

# Exclude directories that shouldn't go to public
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=frontend_dev/"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=catalogue/"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=__pycache__/"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=.venv/"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=*.pyc"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=.env"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=deployment_metadata.json"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude='Makefile copy'"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=/debug_*"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=/test_*"
EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=mcp_server.log"

# 5. Copy files (rsync exit code 23 = some files excluded, which is expected)
echo "Copying code files..."
_rsync() {
    rsync "$@" || { rc=$?; [ $rc -eq 23 ] && return 0 || return $rc; }
}

_rsync -av --delete \
    $EXCLUDE_ARGS \
    "$PROJECT_ROOT/genmedia4commerce/" \
    "$SYNC_DIR/$TARGET_DIR/genmedia4commerce/"

_rsync -av --delete \
    $EXCLUDE_ARGS \
    "$PROJECT_ROOT/tests/" \
    "$SYNC_DIR/$TARGET_DIR/tests/"

_rsync -av --delete \
    $EXCLUDE_ARGS \
    "$PROJECT_ROOT/deployment/" \
    "$SYNC_DIR/$TARGET_DIR/deployment/"

_rsync -av --delete \
    $EXCLUDE_ARGS \
    "$PROJECT_ROOT/frontend/" \
    "$SYNC_DIR/$TARGET_DIR/frontend/"

# Copy root files
for f in Makefile pyproject.toml config.env Dockerfile README.md DESIGN_SPEC.md CLAUDE.md GEMINI.md uv.lock; do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        cp "$PROJECT_ROOT/$f" "$SYNC_DIR/$TARGET_DIR/"
    fi
done

# 6. Show what changed
echo ""
echo "=== Changes ==="
cd "$SYNC_DIR"
git add "$TARGET_DIR"
git status --short "$TARGET_DIR"

FILE_COUNT=$(git diff --cached --name-only "$TARGET_DIR" | wc -l | tr -d ' ')
echo ""
echo "$FILE_COUNT files changed"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "[DRY RUN] Would commit and push branch '$BRANCH' to $FORK_REPO"
    echo "[DRY RUN] Cleaning up..."
    git checkout main
    git branch -D "$BRANCH"
    exit 0
fi

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "No changes to sync."
    git checkout main
    git branch -D "$BRANCH"
    exit 0
fi

# 7. Commit and push
git commit -m "Sync genmedia-for-commerce from internal repo"
git push origin "$BRANCH"

echo ""
echo "=== Pushed branch '$BRANCH' to $FORK_REPO ==="
echo ""

# 8. Ask about PR
read -p "Open a PR to $UPSTREAM_REPO? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh pr create \
        --repo "$UPSTREAM_REPO" \
        --head "$FORK_REPO:$BRANCH" \
        --title "Update genmedia-for-commerce agent" \
        --body "Sync latest changes from internal repo."
fi
