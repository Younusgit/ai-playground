#!/data/data/com.termux/files/usr/bin/bash
# Backup database
# Usage: bash scripts/backup.sh

GREEN='\033[0;32m'; NC='\033[0m'

cd "$(dirname "$0")/.."

set -a
[ -f backend/.env ] && source backend/.env
set +a

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

echo -e "${GREEN}Creating backup: $BACKUP_FILE${NC}"
pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"
echo -e "${GREEN}Backup saved: ${BACKUP_FILE}.gz${NC}"

# Keep only last 10 backups
ls -t backups/*.sql.gz | tail -n +11 | xargs rm -f 2>/dev/null || true

echo -e "${GREEN}Backup complete!${NC}"
ls -lh backups/*.sql.gz | tail -5
