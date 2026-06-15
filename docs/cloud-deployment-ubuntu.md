# RPF Cloud Deployment on Ubuntu

This document describes a simple production-style deployment for letting other people access the RPF web workbench.

Recommended baseline:

```text
Ubuntu 22.04 or 24.04 x64
2 CPU cores
4 GB RAM
50 GB disk
Nginx
Python 3.11+
systemd
```

The viewer backend should run on localhost and be exposed through Nginx.

```text
Browser
-> HTTPS / domain
-> Nginx
-> http://127.0.0.1:8765
-> python -m rpf viewer
```

Do not expose port `8765` directly to the public internet.

---

## 1. Fast Path

On a fresh Ubuntu server, this repository includes a bootstrap script:

```bash
curl -L https://github.com/Miyazak1/DRAF/archive/refs/heads/main.tar.gz -o draf-main.tar.gz
tar -xzf draf-main.tar.gz
cd DRAF-main
bash deploy/bootstrap_ubuntu.sh
```

The script:

- installs Python, Git, and Nginx
- clones or updates `/opt/draf`
- creates `.venv`
- installs `requirements.txt`
- generates an initial `yellow_sign_cold_case` run
- installs `draf-viewer.service`
- installs the Nginx reverse proxy config
- starts the viewer behind Nginx

After it finishes, open:

```text
http://YOUR_SERVER_IP/
```

For a custom install location:

```bash
APP_DIR=/opt/draf bash deploy/bootstrap_ubuntu.sh
```

---

## 2. Manual Install

### 2.1 Install System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

Optional, for HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

### 2.2 Clone the Repository

```bash
sudo mkdir -p /opt/draf
sudo chown "$USER":"$USER" /opt/draf
git clone https://github.com/Miyazak1/DRAF.git /opt/draf
cd /opt/draf
```

---

### 2.3 Create Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Quick check:

```bash
python -m rpf run examples/yellow_sign_cold_case.yaml --steps 10 --seed 42 --out out/smoke
```

Expected output directory:

```text
out/smoke/yellow_sign_cold_case/
```

---

### 2.4 Start Viewer Manually

First create or reuse an initial run:

```bash
python -m rpf run examples/yellow_sign_cold_case.yaml --steps 12 --seed 42 --out out/experience
```

Then start the web workbench:

```bash
python -m rpf viewer out/experience/yellow_sign_cold_case --host 127.0.0.1 --port 8765
```

Open locally on the server:

```text
http://127.0.0.1:8765/
```

---

## 3. systemd Service

The repository includes:

```text
deploy/draf-viewer.service
```

Install it:

```bash
sudo cp deploy/draf-viewer.service /etc/systemd/system/draf-viewer.service
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable draf-viewer
sudo systemctl start draf-viewer
sudo systemctl status draf-viewer
```

Logs:

```bash
journalctl -u draf-viewer -f
```

---

## 4. Nginx Reverse Proxy

The repository includes:

```text
deploy/nginx-draf.conf
```

Install it:

```bash
sudo cp deploy/nginx-draf.conf /etc/nginx/sites-available/draf
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/draf /etc/nginx/sites-enabled/draf
sudo nginx -t
sudo systemctl reload nginx
```

If using a domain, enable HTTPS:

```bash
sudo sed -i 's/server_name _;/server_name your-domain.example;/' /etc/nginx/sites-available/draf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.example
```

---

## 5. API Key Boundary

The web workbench currently stores LLM API keys in the user's browser local storage and sends them to the local backend only when rendering.

For a public deployment:

- do not hard-code your DeepSeek key in the repository
- prefer letting testers enter their own key
- if you later store a server-side key, add authentication before exposing the site

---

## 6. Output Storage

Simulation output grows under:

```text
out/experience/
```

Clean old runs periodically:

```bash
du -sh /opt/draf/out/experience
```

Archive or delete old run folders when disk pressure rises.

---

## 7. Updating the Server

```bash
cd /opt/draf
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart draf-viewer
```

Smoke test after update:

```bash
python -m rpf run examples/yellow_sign_cold_case.yaml --steps 5 --seed 42 --out out/smoke_update
```
