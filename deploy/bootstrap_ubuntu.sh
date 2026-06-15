#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/draf}"
REPO_URL="${REPO_URL:-https://github.com/Miyazak1/DRAF.git}"
SCENARIO="${SCENARIO:-examples/yellow_sign_cold_case.yaml}"

sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx

if [ ! -d "$APP_DIR/.git" ]; then
  sudo mkdir -p "$APP_DIR"
  sudo chown "$USER":"$USER" "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git pull

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python -m rpf run "$SCENARIO" --steps 12 --seed 42 --out out/experience

sudo cp deploy/draf-viewer.service /etc/systemd/system/draf-viewer.service
sudo systemctl daemon-reload
sudo systemctl enable draf-viewer
sudo systemctl restart draf-viewer

sudo cp deploy/nginx-draf.conf /etc/nginx/sites-available/draf
if [ ! -e /etc/nginx/sites-enabled/draf ]; then
  sudo ln -s /etc/nginx/sites-available/draf /etc/nginx/sites-enabled/draf
fi
sudo nginx -t
sudo systemctl reload nginx

echo "DRAF viewer is running behind Nginx."
echo "Open http://YOUR_SERVER_IP/ or configure a domain and HTTPS with certbot."
