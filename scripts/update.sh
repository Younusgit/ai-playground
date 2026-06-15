#!/data/data/com.termux/files/usr/bin/bash
# Pull latest changes and restart
# Usage: bash scripts/update.sh

GREEN='\033[0;32m'; NC='\033[0m'

cd "$(dirname "$0")/.."

echo -e "${GREEN}Pulling latest changes...${NC}"
git pull origin main

source venv/bin/activate
pip install -r backend/requirements.txt -q

echo -e "${GREEN}Update complete! Restart with: bash scripts/start.sh${NC}"
