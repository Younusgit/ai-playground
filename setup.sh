#!/data/data/com.termux/files/usr/bin/bash
# ============================================
# AI Playground - Termux Setup Script
# Run: bash setup.sh
# ============================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   AI Playground - Termux Setup            ${NC}"
echo -e "${BLUE}============================================${NC}\n"

step() { echo -e "\n${YELLOW}[STEP]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Update Termux packages
step "Updating Termux packages..."
pkg update -y && pkg upgrade -y
ok "Packages updated"

# Install system dependencies
step "Installing system dependencies..."
pkg install -y python python-pip nodejs git curl wget openssh nano
ok "System deps installed"

# Install PostgreSQL client (for migrations)
step "Installing PostgreSQL client..."
pkg install -y libpq
ok "PostgreSQL client installed"

# Setup project directory
step "Setting up project..."
cd ~

if [ ! -d "ai-playground" ]; then
    echo -e "${YELLOW}Clone from GitHub? (y/n):${NC} "
    read -r USE_GIT
    if [ "$USE_GIT" = "y" ]; then
        echo -e "${YELLOW}Enter GitHub repo URL:${NC} "
        read -r REPO_URL
        git clone "$REPO_URL" ai-playground
    else
        mkdir -p ai-playground
        echo "Manual setup - copy project files to ~/ai-playground"
    fi
fi

cd ai-playground

# Setup Python environment
step "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate
ok "Virtual env created"

# Install Python dependencies
step "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
ok "Python deps installed"

# Setup .env file
step "Setting up environment variables..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo -e "\n${YELLOW}Please edit backend/.env with your credentials:${NC}"
    echo -e "  nano backend/.env\n"
    echo -e "${YELLOW}Required values:${NC}"
    echo "  DATABASE_URL=postgresql://..."
    echo "  JWT_SECRET=your-secret"
    echo "  ADMIN_EMAILS=your@email.com"
    echo "  TELEGRAM_BOT_TOKEN=..."
    echo "  TELEGRAM_ADMIN_CHAT_ID=..."
else
    ok ".env already exists"
fi

# Setup frontend
step "Setting up frontend..."
if command -v npm &> /dev/null; then
    cd frontend
    npm install
    cd ..
    ok "Frontend deps installed"
else
    echo -e "${YELLOW}npm not found, skipping frontend setup${NC}"
fi

# Make scripts executable
step "Making scripts executable..."
chmod +x scripts/*.sh
ok "Scripts are executable"

# Create start shortcuts
step "Creating shortcuts..."
cat > ~/start-api.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/ai-playground
source venv/bin/activate
cd backend
source .env 2>/dev/null || export $(cat .env | grep -v '#' | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF

cat > ~/start-bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/ai-playground
source venv/bin/activate
cd backend
source .env 2>/dev/null || export $(cat .env | grep -v '#' | xargs)
python ../bot/admin_bot.py
EOF

chmod +x ~/start-api.sh ~/start-bot.sh
ok "Shortcuts created: ~/start-api.sh and ~/start-bot.sh"

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}   Setup Complete!                         ${NC}"
echo -e "${GREEN}============================================${NC}\n"
echo -e "Next steps:"
echo -e "  1. ${YELLOW}nano backend/.env${NC}          - Set your credentials"
echo -e "  2. ${YELLOW}bash scripts/migrate.sh${NC}    - Setup database"
echo -e "  3. ${YELLOW}bash scripts/start.sh${NC}      - Start everything"
echo ""
