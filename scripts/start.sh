#!/data/data/com.termux/files/usr/bin/bash
# Start all services
# Usage: bash scripts/start.sh [api|bot|all]

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true

# Load env
set -a
[ -f backend/.env ] && source backend/.env
set +a

MODE=${1:-all}

start_api() {
    echo -e "${GREEN}Starting API server on port 8000...${NC}"
    cd backend
    uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload &
    API_PID=$!
    cd ..
    echo "API PID: $API_PID"
}

start_bot() {
    echo -e "${GREEN}Starting Telegram Admin Bot...${NC}"
    cd backend
    python ../bot/admin_bot.py &
    BOT_PID=$!
    cd ..
    echo "Bot PID: $BOT_PID"
}

case "$MODE" in
    api)  start_api ;;
    bot)  start_bot ;;
    all)
        start_api
        sleep 2
        start_bot
        echo -e "\n${GREEN}All services started!${NC}"
        echo -e "${YELLOW}API:${NC} http://localhost:8000"
        echo -e "${YELLOW}Docs:${NC} http://localhost:8000/docs"
        wait
        ;;
    *)
        echo "Usage: bash scripts/start.sh [api|bot|all]"
        exit 1
        ;;
esac
