#!/usr/bin/env bash
# oracle-setup.sh — One-time setup for GDriveGenie on an Oracle Cloud Ubuntu VM
# Run as: bash oracle-setup.sh
# Tested on Ubuntu 22.04 (ARM Ampere A1 — Always Free tier)
set -euo pipefail

REPO_URL="https://github.com/mdtahmidurrahmanuae/GDriveGenie.git"
APP_DIR="$HOME/GDriveGenie"

echo "========================================"
echo "  GDriveGenie — Oracle Cloud Setup"
echo "========================================"

# ── 1. System packages ────────────────────────────────────────────────────────
echo ""
echo "[1/6] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y curl git ca-certificates gnupg

# ── 2. Install Docker ─────────────────────────────────────────────────────────
echo ""
echo "[2/6] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "Docker installed. NOTE: log out and back in for group membership to take effect,"
    echo "or run: newgrp docker"
else
    echo "Docker already installed: $(docker --version)"
fi

# Docker Compose v2 (plugin)
if ! docker compose version &>/dev/null 2>&1; then
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4)
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL \
        "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    echo "Docker Compose installed: $(docker compose version)"
else
    echo "Docker Compose already installed: $(docker compose version)"
fi

# ── 3. Open firewall ports ────────────────────────────────────────────────────
# Oracle Cloud Ubuntu VMs block all incoming traffic via iptables by default.
# You ALSO need to open port 80 in the Oracle Console:
#   Networking → Virtual Cloud Networks → your VCN → Security Lists → Ingress Rules
#   Add: TCP, Source 0.0.0.0/0, Destination Port 80
echo ""
echo "[3/6] Opening firewall ports..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80   -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443  -j ACCEPT
# Persist rules across reboots
if ! dpkg -l iptables-persistent &>/dev/null; then
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | sudo debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | sudo debconf-set-selections
    sudo apt-get install -y iptables-persistent
else
    sudo netfilter-persistent save
fi
echo "Ports 80 and 443 opened."

# ── 4. Clone the repository ───────────────────────────────────────────────────
echo ""
echo "[4/6] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "Repo already exists at $APP_DIR, pulling latest..."
    git -C "$APP_DIR" pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
fi

# ── 5. Create .env from template ─────────────────────────────────────────────
echo ""
echo "[5/6] Setting up environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo "  .env created from .env.example"
    echo "  !! Edit $APP_DIR/.env and fill in:"
    echo "     SERVER_IP        — your VM's public IP (from Oracle Console)"
    echo "     CF_ACCOUNT_ID    — Cloudflare account ID"
    echo "     CF_D1_DATABASE_ID — Cloudflare D1 database ID"
    echo "     CF_API_TOKEN     — Cloudflare API token"
else
    echo ".env already exists, skipping."
fi

# ── 6. Install systemd service for auto-start ─────────────────────────────────
echo ""
echo "[6/6] Installing systemd service..."
sudo tee /etc/systemd/system/gdrivegenie.service > /dev/null <<EOF
[Unit]
Description=GDriveGenie
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d --build
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=300
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gdrivegenie
echo "systemd service installed and enabled."

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Open port 80 in the Oracle Console security list (if not done yet):"
echo "     Networking → VCN → Security Lists → Add Ingress Rule"
echo "     Protocol: TCP | Source: 0.0.0.0/0 | Dest Port: 80"
echo ""
echo "  2. Place your Google OAuth credentials file:"
echo "     $APP_DIR/config/credentials.json"
echo ""
echo "  3. Fill in your .env file:"
echo "     nano $APP_DIR/.env"
echo ""
echo "  4. (First run only) Generate secrets and set your dashboard PIN:"
echo "     cd $APP_DIR && docker compose -f docker-compose.prod.yml run --rm backend \\"
echo "       python scripts/generate_secrets.py"
echo ""
echo "  5. Start the app:"
echo "     sudo systemctl start gdrivegenie"
echo "     # or manually:"
echo "     cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "  Your app will be at: http://\$(curl -s ifconfig.me)"
echo ""
