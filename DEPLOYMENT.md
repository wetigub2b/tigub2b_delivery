# Tigu B2B Delivery Platform - Deployment Guide

## Nginx Configuration Setup

### 1. Copy Configuration File

```bash
# Copy the nginx configuration to sites-available
sudo cp /home/mli/tigub2b/tigub2b_delivery/nginx-delivery.conf /etc/nginx/sites-available/stgdelivery

# Create symbolic link to sites-enabled (if not exists)
sudo ln -sf /etc/nginx/sites-available/stgdelivery /etc/nginx/sites-enabled/stgdelivery
```

### 2. Deploy Frontend

```bash
# Navigate to frontend directory
cd /home/mli/tigub2b/tigub2b_delivery/frontend

# Build production bundle
npm run build

# Copy built files to nginx root
sudo rm -rf /var/www/html/delivery/*
sudo cp -r dist/* /var/www/html/delivery/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html/delivery
sudo chmod -R 755 /var/www/html/delivery
```

### 3. Verify Backend is Running

```bash
# Check if backend is running on port 9000
sudo netstat -tlnp | grep :9000

# If not running, start the backend
cd /home/mli/tigub2b/tigub2b_delivery/bff
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

### 4. Test Nginx Configuration

```bash
# Test nginx configuration syntax
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx

# Or restart nginx
sudo systemctl restart nginx
```

### 5. Verify Deployment

```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx error logs
sudo tail -f /var/log/nginx/delivery_error.log

# Test frontend access
curl -I https://stgdelivery.wetigu.com

# Test backend API
curl -I https://stgdelivery.wetigu.com/api/health
```

## Configuration Details

### Backend API Endpoints

The nginx configuration proxies the following backend routes:

- **API Routes**: `/api/*` → `http://localhost:9000/api/*`
- **WebSocket**: `/ws` → `http://localhost:9000/ws`
- **Health Check**: `/health` → `http://localhost:9000/health`
- **API Docs**: `/docs`, `/redoc`, `/openapi.json` → Backend docs

### Frontend Routes

- All other routes are handled by Vue.js SPA with HTML5 history mode
- Static assets are cached for 1 year
- HTML files have no caching for instant updates

### Security Features

✅ HTTPS enforcement (HTTP → HTTPS redirect)
✅ Security headers (X-Frame-Options, X-XSS-Protection, CSP)
✅ Gzip compression for text assets
✅ CORS headers for API access
✅ Client upload size limit: 20MB

### Performance Optimizations

✅ Static asset caching (1 year)
✅ Gzip compression (level 6)
✅ Proxy buffering disabled for streaming
✅ WebSocket support with long timeouts

## Backend Service Setup (Systemd)

Create a systemd service for automatic backend startup:

```bash
# Create service file
sudo nano /etc/systemd/system/tigu-delivery-bff.service
```

Paste the following content:

```ini
[Unit]
Description=Tigu B2B Delivery BFF (FastAPI)
After=network.target mysql.service redis.service

[Service]
Type=simple
User=mli
Group=mli
WorkingDirectory=/home/mli/tigub2b/tigub2b_delivery/bff
Environment="PATH=/home/mli/tigub2b/tigub2b_delivery/bff/.venv/bin"
ExecStart=/home/mli/tigub2b/tigub2b_delivery/bff/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tigu-delivery-bff

# Start the service
sudo systemctl start tigu-delivery-bff

# Check status
sudo systemctl status tigu-delivery-bff

# View logs
sudo journalctl -u tigu-delivery-bff -f
```

## Environment Configuration

### Backend (.env)

Ensure `/home/mli/tigub2b/tigub2b_delivery/bff/.env` contains:

```env
APP_NAME=Tigu Delivery BFF
API_V1_PREFIX=/api
BFF_PORT=9000
SECRET_KEY=<your-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=mysql+asyncmy://user:pass@localhost:3307/tigu_b2b
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=https://stgdelivery.wetigu.com,https://testdelivery.wetigu.com
GOOGLE_MAPS_API_KEY=<your-google-maps-key>
LOG_LEVEL=INFO
```

### Frontend (.env.production)

Create `/home/mli/tigub2b/tigub2b_delivery/frontend/.env.production`:

```env
VITE_API_URL=https://stgdelivery.wetigu.com/api
VITE_WS_URL=wss://stgdelivery.wetigu.com/ws
VITE_GOOGLE_MAPS_KEY=<your-google-maps-key>
```

## Troubleshooting

### Backend not accessible

```bash
# Check if backend is running
sudo netstat -tlnp | grep :9000

# Check backend logs
sudo journalctl -u tigu-delivery-bff -n 100

# Test backend directly
curl http://localhost:9000/health
```

### Frontend not loading

```bash
# Check nginx error logs
sudo tail -f /var/log/nginx/delivery_error.log

# Verify files exist
ls -la /var/www/html/delivery/

# Check nginx configuration
sudo nginx -t
```

### API requests failing

```bash
# Check CORS configuration in backend
# Verify ALLOWED_ORIGINS in .env includes your domain

# Check nginx proxy configuration
sudo nginx -t

# Test API endpoint directly
curl -v https://stgdelivery.wetigu.com/api/health
```

### WebSocket connection issues

```bash
# Check nginx websocket configuration
# Verify upgrade headers are set

# Test websocket connection
wscat -c wss://stgdelivery.wetigu.com/ws
```

## Quick Deployment Script

Create `/home/mli/tigub2b/tigub2b_delivery/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Tigu B2B Delivery Platform..."

# Build frontend
echo "📦 Building frontend..."
cd /home/mli/tigub2b/tigub2b_delivery/frontend
npm run build

# Deploy frontend
echo "📋 Deploying frontend files..."
sudo rm -rf /var/www/html/delivery/*
sudo cp -r dist/* /var/www/html/delivery/
sudo chown -R www-data:www-data /var/www/html/delivery

# Reload nginx
echo "🔄 Reloading nginx..."
sudo nginx -t && sudo systemctl reload nginx

# Restart backend
echo "🔄 Restarting backend service..."
sudo systemctl restart tigu-delivery-bff

echo "✅ Deployment complete!"
echo "🌐 Frontend: https://stgdelivery.wetigu.com"
echo "🔧 Backend: https://stgdelivery.wetigu.com/api/health"
```

Make it executable:

```bash
chmod +x /home/mli/tigub2b/tigub2b_delivery/deploy.sh
```

Run deployment:

```bash
./deploy.sh
```

## Monitoring

### Log Files

- **Nginx Access**: `/var/log/nginx/delivery_access.log`
- **Nginx Error**: `/var/log/nginx/delivery_error.log`
- **Backend Service**: `sudo journalctl -u tigu-delivery-bff -f`

### Health Checks

- **Frontend**: https://stgdelivery.wetigu.com
- **Backend Health**: https://stgdelivery.wetigu.com/health
- **API Docs**: https://stgdelivery.wetigu.com/docs

## SSL Certificate Renewal

If using Let's Encrypt:

```bash
# Renew certificates
sudo certbot renew

# Or for Cloudflare certificates, update:
# /etc/ssl/cloudflare/tigu.cert
# /etc/ssl/cloudflare/tigu.key
```

## Rollback Procedure

If deployment fails:

```bash
# Restore previous nginx config
sudo cp /etc/nginx/sites-available/stgdelivery.backup /etc/nginx/sites-available/stgdelivery
sudo nginx -t && sudo systemctl reload nginx

# Restore previous frontend build
sudo rm -rf /var/www/html/delivery/*
sudo cp -r /var/www/html/delivery.backup/* /var/www/html/delivery/

# Restart backend with previous code
cd /home/mli/tigub2b/tigub2b_delivery/bff
git checkout <previous-commit>
sudo systemctl restart tigu-delivery-bff
```
