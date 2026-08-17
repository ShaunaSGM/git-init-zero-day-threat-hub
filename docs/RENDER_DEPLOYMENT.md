# Render.com Integration Guide

## Overview

Render.com is a modern cloud platform that simplifies deployment. This guide walks you through deploying the Zero-Day Threat Hub to Render.com.

## Prerequisites

- Render.com account (free tier available)
- GitHub account
- Repository pushed to GitHub
- Docker image ready (provided in repo)

## Step 1: Connect GitHub to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Click **Connect a repository**
4. Authorize Render to access your GitHub account
5. Select `git-init-zero-day-threat-hub` repository
6. Click **Connect**

## Step 2: Configure Web Service

### Basic Settings
- **Name**: `zero-day-threat-hub`
- **Region**: Choose closest to your users
- **Branch**: `setup/phase-1-foundation`
- **Runtime**: `Docker`

### Build Settings
- **Docker Context**: `.`
- **Dockerfile Path**: `./Dockerfile`

### Plan
- **Free Tier** (for staging)
  - 0.5 GB RAM
  - Auto sleep after 15 mins inactivity
  - Good for testing

- **Starter Tier** (for production)
  - 0.5 GB RAM, $7/month
  - Always on
  - Auto-deploy on push

## Step 3: Configure PostgreSQL Database

### Option A: Render PostgreSQL (Recommended)

1. Click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `threat-hub-postgres`
   - **Region**: Same as web service
   - **PostgreSQL Version**: 15
   - **Database**: `threat_hub`
   - **User**: `threat_admin`
   - **Plan**: Free tier (0.5 GB)

3. Note the connection string, format:
   ```
   postgresql://threat_admin:PASSWORD@HOST:5432/threat_hub
   ```

### Option B: External Database
- Use AWS RDS, DigitalOcean, or other providers
- Update DATABASE_URL in environment variables

## Step 4: Set Environment Variables

1. In Render Dashboard, go to your Web Service
2. Click **Environment**
3. Add these variables:

```
DATABASE_URL=postgresql://threat_admin:YOUR_PASSWORD@HOST:5432/threat_hub
DEBUG=False
SECRET_KEY=your_random_secret_key_here
APP_NAME=Zero-Day Threat Hub
APP_VERSION=1.0.0
LOG_LEVEL=INFO
```

To generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 5: Configure Health Checks

1. **Health Check Path**: `/health`
2. **Health Check Protocol**: `HTTP`
3. **Startup Duration**: 300 seconds
4. **Check Interval**: 30 seconds

## Step 6: Deploy

### Auto-Deploy (Recommended)
1. In Web Service settings, enable **Auto-Deploy**
2. Each push to `setup/phase-1-foundation` automatically deploys
3. View deployment status in **Logs**

### Manual Deploy
1. Click **Manual Deploy** → **Deploy**
2. Monitor progress in **Logs** tab

## Step 7: Verify Deployment

Once deployment completes, access your application:

```bash
# Get your Render service URL (e.g., https://zero-day-threat-hub.onrender.com)

# Test health check
curl https://zero-day-threat-hub.onrender.com/health

# Access API docs
https://zero-day-threat-hub.onrender.com/docs
```

## Common Issues & Solutions

### Issue 1: Database Connection Failed

**Error**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Verify DATABASE_URL format
# Should be: postgresql://user:password@host:5432/database

# Check Render PostgreSQL service is running
# Allow Web Service IP in PostgreSQL firewall (if applicable)

# Test connection from service logs
docker-compose exec api psql $DATABASE_URL
```

### Issue 2: Build Timeout

**Error**: `Build timeout after 20 minutes`

**Solution**:
1. Optimize `requirements.txt` - remove unused dependencies
2. Use lighter base image (already using `python:3.11-slim`)
3. Cache Docker layers by using `.dockerignore`

### Issue 3: Out of Memory

**Error**: `Service crashed: Out of memory`

**Solution**:
1. Upgrade to Starter plan (more RAM)
2. Optimize application startup
3. Set memory limits in Dockerfile

### Issue 4: Cold Start on Free Tier

**Error**: First request takes 30+ seconds

**Solution**:
- Expected on free tier (auto-sleep feature)
- Use Starter tier for production ($7/month)
- Configure health checks to keep service warm

## Render.com vs Docker Compose

| Feature | Render.com | Docker Compose |
|---------|-----------|-----------------|
| Cost | Free/Paid | Free (host costs) |
| Setup Time | 5 minutes | 10 minutes |
| Scaling | 1-click | Manual |
| SSL/TLS | Automatic | Self-signed |
| Monitoring | Built-in | External tool |
| Backup | Automated | Manual |
| Use Case | Production/Staging | Development |

## Deployment Checklist

- [ ] GitHub repository is public or authorized
- [ ] `setup/phase-1-foundation` branch exists
- [ ] Dockerfile is present and valid
- [ ] requirements.txt is up to date
- [ ] Environment variables configured
- [ ] PostgreSQL database created
- [ ] Health check path verified
- [ ] First deployment successful
- [ ] API documentation loads at `/docs`
- [ ] Database connection working

## Monitoring & Logs

### View Logs in Render

1. Go to Web Service → **Logs**
2. Filter by:
   - **Type**: All/Build/Runtime
   - **Service**: Web/Database
   - **Time Range**: Last hour/day

### Common Log Messages

```
✓ Build succeeded
✓ Deployment started
✓ Container running
✓ Health check passed
```

## Updating Deployment

### Auto-Deploy (Recommended)
```bash
# Push to setup/phase-1-foundation
git push origin setup/phase-1-foundation
# Render automatically rebuilds and deploys
```

### Manual Deploy
1. Click **Manual Deploy** → **Deploy latest**
2. Monitor in **Logs**

## Scaling

### Free Tier
- Single instance
- Limited resources (0.5 GB RAM)
- Auto-sleep after 15 mins

### Starter Tier ($7/month)
- Single instance
- Always-on
- Better performance

### Growth Tier ($25/month)
- 2 instances
- Load balancing
- More resources

## Custom Domain (Optional)

1. Go to Web Service → **Settings**
2. Click **Add Custom Domain**
3. Follow DNS configuration steps
4. Point your domain to Render
5. SSL certificate auto-generated

## Security Considerations

### Before Production
- [ ] Change default PostgreSQL credentials
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS (automatic on Render)
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Enable database encryption
- [ ] Review environment variables
- [ ] Test API authentication

### Recommended Settings
```
DEBUG=False                    # Disable debug mode
LOG_LEVEL=INFO                # Log important events only
ALLOWED_ORIGINS=yourdomain    # CORS restrictions
DB_SSL_MODE=require           # Enforce SSL for DB
```

## Cost Estimation

### Free Tier
- Web Service: Free (with limitations)
- PostgreSQL: Free (500 MB)
- **Total**: $0/month

### Starter Tier (Production)
- Web Service: $7/month
- PostgreSQL: $15/month (upgraded)
- **Total**: ~$22/month

## Backup Strategy

### PostgreSQL Backups
1. Render auto-backs up free tier daily
2. Starter tier: Backup every 6 hours
3. Download backups from Render Dashboard

### Application Data
- Store audit logs in database
- Export matches regularly
- Use Render's managed backups

## Performance Tips

1. **Use Starter tier for production** (free tier auto-sleeps)
2. **Add indexes to frequently queried columns**
3. **Cache threat advisory responses**
4. **Use connection pooling** (SQLAlchemy does this)
5. **Monitor database query performance**

## Support & Documentation

- [Render Documentation](https://render.com/docs)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Docker on Render](https://render.com/docs/docker)
- [Render Support](https://render.com/support)

## Next Steps

1. ✅ Push repository to GitHub
2. ✅ Create Render account
3. ✅ Connect GitHub repository
4. ✅ Configure PostgreSQL database
5. ✅ Set environment variables
6. ✅ Deploy
7. ✅ Test API endpoints
8. ✅ Set up monitoring
9. ✅ Configure custom domain
10. ✅ Set up backups

---

**Integration Date**: 2026-08-17  
**Platform**: Render.com  
**Status**: Ready for Deployment  
**Documentation Version**: 1.0
