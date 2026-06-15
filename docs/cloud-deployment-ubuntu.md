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

## 1. Install System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

Optional, for HTTPS:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## 2. Clone the Repository

```bash
sudo mkdir -p /opt/draf
sudo chown "$USER":"$USER" /opt/draf
git clone https://github.com/Miyazak1/DRAF.git /opt/draf
cd /opt/draf
```

---

## 3. Create Python Environment

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

## 4. Start Viewer Manually

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

## 5. systemd Service

Create:

```bash
sudo nano /etc/systemd/system/draf-viewer.service
```

Use:

```ini
[Unit]
Description=DRAF RPF Web Workbench
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/draf
ExecStart=/opt/draf/.venv/bin/python -m rpf viewer /opt/draf/out/experience/yellow_sign_cold_case --host 127.0.0.1 --port 8765
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
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

## 6. Nginx Reverse Proxy

Create:

```bash
sudo nano /etc/nginx/sites-available/draf
```

Use:

```nginx
server {
    listen 80;
    server_name your-domain.example;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/draf /etc/nginx/sites-enabled/draf
sudo nginx -t
sudo systemctl reload nginx
```

If using a domain, enable HTTPS:

```bash
sudo certbot --nginx -d your-domain.example
```

---

## 7. API Key Boundary

The web workbench currently stores LLM API keys in the user's browser local storage and sends them to the local backend only when rendering.

For a public deployment:

- do not hard-code your DeepSeek key in the repository
- prefer letting testers enter their own key
- if you later store a server-side key, add authentication before exposing the site

---

## 8. Output Storage

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

## 9. Updating the Server

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

