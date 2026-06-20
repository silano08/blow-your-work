#!/usr/bin/env bash
# One-time server bootstrap script
# Run as: bash scripts/bootstrap.sh
set -e

REPO_URL="https://github.com/silano08/blow-your-work.git"
APP_DIR="$HOME/blow-your-work"
VENV_DIR="$APP_DIR/.venv"

echo "=== Blow Your Work — Server Bootstrap ==="

# 1. Clone repo
if [ ! -d "$APP_DIR" ]; then
  echo "▶ Cloning repository..."
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

# 2. Python venv
echo "▶ Setting up Python venv..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 3. .env file (must be set up manually with real secrets)
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Edit .env with real credentials:"
  echo "    GITHUB_TOKEN=..."
  echo "    AZURE_SPEECH_KEY=..."
  echo "    AZURE_SPEECH_REGION=koreacentral"
  echo ""
fi

# 4. systemd service
echo "▶ Installing systemd service..."
sudo cp deploy/blow-your-work.service /etc/systemd/system/
sudo sed -i "s|azureuser|$(whoami)|g" /etc/systemd/system/blow-your-work.service
sudo systemctl daemon-reload
sudo systemctl enable blow-your-work
sudo systemctl start blow-your-work

# 5. Nginx
echo "▶ Configuring nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/blow-your-work
sudo ln -sf /etc/nginx/sites-available/blow-your-work /etc/nginx/sites-enabled/blow-your-work
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "✅ Bootstrap complete!"
echo "   App: http://$(curl -s ifconfig.me)"
echo "   Logs: sudo journalctl -u blow-your-work -f"
