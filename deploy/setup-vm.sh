#!/usr/bin/env bash
# Run this on a fresh Ubuntu GCP e2-micro VM (us-west1 / us-central1 / us-east1
# for the Always Free tier). Usage:
#   sudo JARVIS_DOMAIN=jarvis.yourdomain.com bash deploy/setup-vm.sh
#
# JARVIS_DOMAIN must be a real domain/subdomain whose DNS A record already
# points at this VM's external IP — Caddy needs that to issue a free TLS
# certificate. A free dynamic-DNS hostname (e.g. DuckDNS) works fine.
set -euo pipefail

if [[ -z "${JARVIS_DOMAIN:-}" ]]; then
  echo "Set JARVIS_DOMAIN to a hostname that already points at this VM's IP." >&2
  exit 1
fi

REPO_URL="${JARVIS_REPO_URL:-https://github.com/Joel-Trumpet-67/Jarvis.git}"
INSTALL_DIR=/opt/jarvis

apt-get update
apt-get install -y python3-venv python3-pip git ufw debian-keyring debian-archive-keyring apt-transport-https curl gnupg

# Caddy's official repo (for automatic HTTPS)
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

id -u jarvis &>/dev/null || useradd --system --create-home --shell /usr/sbin/nologin jarvis

if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" pull
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

if [[ ! -f "$INSTALL_DIR/.env" ]]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  echo "Created $INSTALL_DIR/.env from .env.example — edit it now with real secrets:"
  echo "  sudo nano $INSTALL_DIR/.env"
fi

chown -R jarvis:jarvis "$INSTALL_DIR"

cp "$INSTALL_DIR/deploy/jarvis.service" /etc/systemd/system/jarvis.service
systemctl daemon-reload
systemctl enable --now jarvis

sed "s/__DOMAIN__/${JARVIS_DOMAIN}/" "$INSTALL_DIR/deploy/Caddyfile" > /etc/caddy/Caddyfile
systemctl restart caddy

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo
echo "Done. Jarvis should be reachable at https://${JARVIS_DOMAIN}"
echo "If you just edited .env, restart the app with: sudo systemctl restart jarvis"
