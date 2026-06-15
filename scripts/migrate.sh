#!/data/data/com.termux/files/usr/bin/bash
# Run database migrations
# Usage: bash scripts/migrate.sh

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'

cd "$(dirname "$0")/.."

set -a
[ -f backend/.env ] && source backend/.env
set +a

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not set in backend/.env${NC}"
    exit 1
fi

echo -e "${GREEN}Running database migrations...${NC}"

for sql_file in migrations/*.sql; do
    echo "Running: $sql_file"
    psql "$DATABASE_URL" -f "$sql_file"
    echo -e "${GREEN}Done: $sql_file${NC}"
done

echo -e "\n${GREEN}All migrations completed!${NC}"
