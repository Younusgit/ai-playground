#!/data/data/com.termux/files/usr/bin/bash
# Deploy to Render via GitHub
# Usage: bash scripts/deploy.sh "commit message"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

cd "$(dirname "$0")/.."

MSG="${1:-Deploy update $(date '+%Y-%m-%d %H:%M')}"

echo -e "${YELLOW}Deploying: $MSG${NC}"

git add .
git commit -m "$MSG"
git push origin main

echo -e "\n${GREEN}Pushed to GitHub!${NC}"
echo "Render will auto-deploy in 1-2 minutes."
echo "Check: https://dashboard.render.com"
