#!/bin/bash
# Push current project to GitHub as subfolder
REPO="https://github.com/AlexCHONG8/CC.git"
TEMP="/tmp/cc_repo"
PROJECT="$(basename "$(pwd)")"

git clone "$REPO" "$TEMP" && \
rsync -av --exclude='.git' --exclude='.venv' --exclude='__pycache__' "$(pwd)/" "$TEMP/$PROJECT/" && \
cd "$TEMP" && \
git add "$PROJECT/" && \
git commit -m "Add $PROJECT project" && \
git push origin main && \
cd - && \
rm -rf "$TEMP" && \
echo "✅ Pushed to: https://github.com/AlexCHONG8/CC/tree/main/$PROJECT"
