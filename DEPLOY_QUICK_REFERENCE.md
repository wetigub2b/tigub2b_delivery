# Quick Deployment Reference

## 🚀 One-Line Deployment Commands

### Step 1: Deploy Nginx Configuration
```bash
sudo cp /home/mli/tigub2b/tigub2b_delivery/nginx-delivery.conf /etc/nginx/sites-available/stgdelivery && sudo nginx -t && sudo systemctl reload nginx
```

### Step 2: Build & Deploy Frontend
```bash
cd /home/mli/tigub2b/tigub2b_delivery/frontend && npm run build && sudo rm -rf /var/www/html/delivery/* && sudo cp -r dist/* /var/www/html/delivery/ && sudo chown -R www-data:www-data /var/www/html/delivery
```

### Step 3: Start Backend (if not using systemd)
```bash
cd /home/mli/tigub2b/tigub2b_delivery/bff && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4 &
```

## 📋 Configuration Summary

| Component | Location | Port |
|-----------|----------|------|
| **Frontend** | /var/www/html/delivery | HTTPS 443 |
| **Backend** | localhost:9000 | 9000 |
| **Nginx Config** | /etc/nginx/sites-available/stgdelivery | - |
| **Domain** | stgdelivery.wetigu.com | - |

## 🔗 API Routing

| URL Pattern | Proxied To | Purpose |
|-------------|------------|---------|
| `/api/*` | `http://localhost:9000/api/*` | Backend API |
| `/ws` | `http://localhost:9000/ws` | WebSocket |
| `/health` | `http://localhost:9000/health` | Health check |
| `/docs` | `http://localhost:9000/docs` | Swagger UI |
| `/*` | Vue SPA (index.html) | Frontend routes |

## ✅ Verification Commands

```bash
# Test nginx config
sudo nginx -t

# Check backend running
curl http://localhost:9000/health

# Check frontend deployed
ls -la /var/www/html/delivery/

# Test full stack
curl -I https://stgdelivery.wetigu.com
curl https://stgdelivery.wetigu.com/api/health

# View logs
sudo tail -f /var/log/nginx/delivery_error.log
```

## 🐛 Quick Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| **502 Bad Gateway** | Backend not running | `sudo systemctl start tigu-delivery-bff` |
| **404 on refresh** | Wrong nginx config | Check `try_files` in location `/` |
| **CORS errors** | Backend ALLOWED_ORIGINS | Update `.env` with correct domain |
| **API not responding** | Backend port | Verify port 9000: `sudo netstat -tlnp \| grep :9000` |
| **SSL errors** | Certificate files | Check `/etc/ssl/cloudflare/tigu.cert` exists |

## 📝 Important File Locations

```
/home/mli/tigub2b/tigub2b_delivery/
├── nginx-delivery.conf          # Nginx config template
├── frontend/
│   ├── dist/                   # Built files (copy to /var/www/html/delivery/)
│   └── .env.production         # Production environment vars
└── bff/
    ├── .env                    # Backend environment vars (port 9000)
    └── app/main.py             # FastAPI application

/etc/nginx/
└── sites-enabled/
    └── stgdelivery             # Active nginx config

/var/www/html/
└── delivery/                   # Frontend files served by nginx

/var/log/nginx/
├── delivery_access.log         # Access logs
└── delivery_error.log          # Error logs
```

## 🔄 Update Workflow

```bash
# 1. Pull latest code
cd /home/mli/tigub2b/tigub2b_delivery
git pull

# 2. Update frontend
cd frontend
npm install
npm run build
sudo rm -rf /var/www/html/delivery/*
sudo cp -r dist/* /var/www/html/delivery/

# 3. Update backend
cd ../bff
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart tigu-delivery-bff

# 4. Reload nginx (if config changed)
sudo systemctl reload nginx
```

## 🎯 Key Environment Variables

### Backend (.env)
```bash
BFF_PORT=9000
API_V1_PREFIX=/api
DATABASE_URL=mysql+asyncmy://user:pass@localhost:3307/tigu_b2b
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=https://stgdelivery.wetigu.com
```

### Frontend (.env.production)
```bash
VITE_API_URL=https://stgdelivery.wetigu.com/api
VITE_WS_URL=wss://stgdelivery.wetigu.com/ws
```
