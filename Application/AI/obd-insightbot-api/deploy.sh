#!/bin/bash
# ===========================================
# OBD InsightBot API - VM Deployment Script
# ===========================================
# This script sets up the API on a fresh Ubuntu VM
#
# Usage: chmod +x deploy.sh && ./deploy.sh
# ===========================================

set -e  # Exit on error

echo "=========================================="
echo "OBD InsightBot API - Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warn "Running as root. Creating a non-root user is recommended for production."
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
fi

log_info "Detected OS: $OS $VER"

# ===========================================
# OPTION 1: Deploy with Docker (Recommended)
# ===========================================
deploy_with_docker() {
    log_info "Deploying with Docker..."
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        log_info "Docker installed. You may need to log out and back in."
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Build and run
    log_info "Building Docker image..."
    docker-compose build api
    
    log_info "Starting container..."
    docker-compose up -d api
    
    log_info "Waiting for service to be healthy..."
    sleep 5
    
    # Check health
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        log_info "✅ API is running and healthy!"
    else
        log_warn "API may still be starting up. Check with: docker-compose logs -f"
    fi
}

# ===========================================
# OPTION 2: Deploy directly with Python
# ===========================================
deploy_with_python() {
    log_info "Deploying with Python directly..."
    
    # Install Python 3.11+ if needed
    if ! command -v python3.11 &> /dev/null; then
        log_info "Installing Python 3.11..."
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        sudo apt install -y python3.11 python3.11-venv python3.11-dev
    fi
    
    # Create virtual environment
    log_info "Creating virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements-light.txt
    
    # Create systemd service
    log_info "Creating systemd service..."
    sudo tee /etc/systemd/system/obd-insightbot.service > /dev/null <<EOF
[Unit]
Description=OBD InsightBot API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable obd-insightbot
    sudo systemctl start obd-insightbot
    
    log_info "Service started. Check status with: sudo systemctl status obd-insightbot"
}

# ===========================================
# Setup Nginx reverse proxy (optional)
# ===========================================
setup_nginx() {
    log_info "Setting up Nginx reverse proxy..."
    
    sudo apt update
    sudo apt install -y nginx
    
    # Create Nginx config
    sudo tee /etc/nginx/sites-available/obd-insightbot > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/obd-insightbot /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload
    sudo nginx -t
    sudo systemctl reload nginx
    
    log_info "Nginx configured. API accessible on port 80."
}

# ===========================================
# Main menu
# ===========================================
echo ""
echo "Select deployment method:"
echo "1) Docker (Recommended)"
echo "2) Python + systemd"
echo "3) Setup Nginx reverse proxy"
echo "4) Full setup (Docker + Nginx)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        deploy_with_docker
        ;;
    2)
        deploy_with_python
        ;;
    3)
        setup_nginx
        ;;
    4)
        deploy_with_docker
        setup_nginx
        ;;
    *)
        log_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
log_info "Deployment complete!"
echo "=========================================="
echo ""
echo "API Endpoints:"
echo "  - Health check: http://localhost:8000/health"
echo "  - API docs:     http://localhost:8000/docs"
echo "  - Chat:         POST http://localhost:8000/chat"
echo ""
echo "Test with:"
echo '  curl -X POST http://localhost:8000/chat \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"message": "How is my car doing?"}'\'''
echo ""
