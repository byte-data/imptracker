# Production Deployment Guide

This guide provides step-by-step instructions for deploying ImpTracker to production, including SSL certificate setup, security hardening, and operational considerations.

## Prerequisites

- ✅ Docker and Docker Compose installed
- ✅ Domain name (`imptracker.znphi.co.zm`) pointing to your server's public IP
- ✅ Server firewall configured to allow inbound traffic on ports 80 and 443
- ✅ Router/gateway port forwarding configured (if behind NAT)
- ✅ SSH access to the server
- ✅ All containers currently running and tested locally

## Current Status

**Network Issue:** External traffic cannot reach the server at `102.23.123.177`
- Server private IP: `10.51.75.85`
- Public DNS: `imptracker.znphi.co.zm` → `102.23.123.177`
- **Action Required:** Configure router/gateway port forwarding and verify network connectivity before proceeding

---

## Phase 1: Network Verification (Prerequisites)

### Step 1.1: Test Network Connectivity
Once the network issue is resolved, verify connectivity:

```bash
# From an external machine, test if ports are open
curl -v https://imptracker.znphi.co.zm
# Expected: Should connect (may have SSL certificate warning initially)
```

### Step 1.2: Verify DNS Resolution
```bash
nslookup imptracker.znphi.co.zm
# Expected: Should resolve to public IP
```

### Step 1.3: Verify Port Forwarding
```bash
# From server, test connection from router/gateway
# Contact your network administrator to confirm:
# - Port 80 (HTTP) → 10.51.75.85:80
# - Port 443 (HTTPS) → 10.51.75.85:443
```

---

## Phase 2: SSL Certificate Setup

### Step 2.1: Stop Nginx (Temporary)
```bash
cd /home/znphi/imptracker
docker-compose stop nginx
```

### Step 2.2: Obtain Let's Encrypt Certificates
```bash
# Request a new certificate using standalone mode
docker-compose run --rm certbot certonly \
  --standalone \
  --preferred-challenges http \
  -d imptracker.znphi.co.zm \
  --email mashkaponde@gmail.com \
  --agree-tos \
  --no-eff-email
```

**What this does:**
- Requests an SSL certificate for `imptracker.znphi.co.zm`
- Validates domain ownership
- Saves certificates to `./certbot/conf/live/imptracker.znphi.co.zm/`

**Expected files created:**
- `fullchain.pem` - Certificate chain
- `privkey.pem` - Private key
- `chain.pem` - Chain certificate

### Step 2.3: Verify Certificate Files
```bash
ls -la ./certbot/conf/live/imptracker.znphi.co.zm/

# Expected output:
# fullchain.pem  (certificate)
# privkey.pem    (private key)
# chain.pem      (chain)
```

### Step 2.4: Start All Containers
```bash
docker-compose up -d
```

### Step 2.5: Test HTTPS Access
```bash
# Test with curl (should NOT have SSL warnings)
curl https://imptracker.znphi.co.zm

# Or open in browser: https://imptracker.znphi.co.zm
# Should show login page without certificate warnings
```

---

## Phase 3: Security Hardening

### Step 3.1: Re-enable Security Settings
Once SSL certificates are valid, enable these security settings in `production.env`:

```env
# Security toggles (change these back to True)
SECURE_SSL_REDIRECT=True      # Redirect HTTP → HTTPS
SESSION_COOKIE_SECURE=True    # Only send cookies over HTTPS
CSRF_COOKIE_SECURE=True       # CSRF token only over HTTPS
```

### Step 3.2: Update ALLOWED_HOSTS (Optional)
For production, you may want to restrict to domain only:

```env
# Remove IP addresses for security
ALLOWED_HOSTS=imptracker.znphi.co.zm
CSRF_TRUSTED_ORIGINS=https://imptracker.znphi.co.zm
```

### Step 3.3: Apply Security Settings
```bash
# Restart containers to apply changes
docker-compose down
docker-compose up -d
```

### Step 3.4: Verify Security
```bash
# Check HTTP → HTTPS redirect works
curl -I http://imptracker.znphi.co.zm
# Expected: HTTP/1.1 301 Moved Permanently
#          Location: https://imptracker.znphi.co.zm

# Verify HTTPS works
curl https://imptracker.znphi.co.zm
# Expected: Login page HTML (no certificate warnings)
```

---

## Phase 4: Database Management

### Step 4.1: Set Strong Database Password
Update `production.env`:

```env
DB_PASSWORD=<generate-a-strong-random-password>
```

Generate a strong password:
```bash
openssl rand -base64 32
```

### Step 4.2: Backup Database Configuration
```bash
# Backup the entire production.env file
cp production.env production.env.backup

# Store in secure location (off-server)
```

### Step 4.3: Test Database Connection
```bash
# Connect to PostgreSQL using pgAdmin
# URL: http://10.51.75.85:5050
# Email: admin@znphi.gov.zm
# Password: AdminPassword2026!

# Or via command line:
docker exec postgres_db psql -U imptracker -d imptracker -c "SELECT 1;"
```

---

## Phase 5: Automated Certificate Renewal

### Step 5.1: Understand Auto-Renewal
The `certbot` container is already configured to:
- Check for expiring certificates every 12 hours
- Automatically renew certificates 30 days before expiration
- Restart nginx to load new certificates

### Step 5.2: Monitor Certificate Status
```bash
# Check certificate expiration date
docker exec certbot certbot certificates

# Expected output should show certificate valid for ~90 days
```

### Step 5.3: Manual Renewal (if needed)
```bash
# Force certificate renewal
docker-compose run --rm certbot renew --force-renewal
```

---

## Phase 6: Production Configuration

### Step 6.1: Disable DEBUG Mode (Already Done)
Verify in `production.env`:

```env
DEBUG=False
```

### Step 6.2: Set Production-Grade Gunicorn Workers
Current settings in `docker-compose.yml`:

```yaml
command: ["gunicorn", "config.wsgi:application", 
          "--bind", "0.0.0.0:8000", 
          "--workers", "3",           # Adjust based on CPU cores
          "--timeout", "120",
          "--access-logfile", "-"]
```

**Worker calculation:** `2 * CPU_CORES + 1`
- For a 2-core server: 5 workers
- For a 4-core server: 9 workers

Update if needed:
```bash
# Check CPU cores
nproc

# Update docker-compose.yml workers parameter
```

### Step 6.3: Configure Logging
```bash
# View application logs
docker-compose logs -f django_web

# View nginx logs
docker-compose logs -f nginx

# View database logs
docker-compose logs -f db
```

### Step 6.4: Set Email Configuration
Update `production.env` for production email sending:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<your-email@gmail.com>
EMAIL_HOST_PASSWORD=<app-specific-password>
DEFAULT_FROM_EMAIL=<your-email@gmail.com>

# For Gmail, generate an App Password:
# 1. Enable 2-Factor Authentication on Google Account
# 2. Go to myaccount.google.com/app-passwords
# 3. Generate app password for "Mail" and "Windows"
# 4. Use the 16-character password above
```

---

## Phase 7: Data Backup & Recovery

### Step 7.1: Set Up Regular Backups
```bash
# Create backup script: backup.sh
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/imptracker"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker exec postgres_db pg_dump -U imptracker imptracker > $BACKUP_DIR/db_$DATE.sql

# Backup uploaded files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Backup environment file
cp production.env $BACKUP_DIR/production.env_$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh
```

### Step 7.2: Schedule Daily Backups (Cron)
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /home/znphi/imptracker/backup.sh >> /var/log/imptracker_backup.log 2>&1
```

### Step 7.3: Database Recovery Procedure
```bash
# If database is corrupted:
docker-compose down

# Restore from backup
docker-compose up -d db
docker exec -i postgres_db psql -U imptracker imptracker < backups/imptracker/db_TIMESTAMP.sql

# Restart all services
docker-compose up -d
```

---

## Phase 8: Monitoring & Health Checks

### Step 8.1: Check Application Status
```bash
# View all containers
docker-compose ps

# All should show "Up" status
```

### Step 8.2: Monitor System Resources
```bash
# CPU and memory usage
docker stats

# Expected baseline (small Django app):
# - Web: 50-100MB memory
# - PostgreSQL: 100-200MB memory
# - Nginx: 10-20MB memory
```

### Step 8.3: View Application Logs
```bash
# Follow logs in real-time
docker-compose logs -f --tail 100

# View specific service logs
docker-compose logs -f django_web
docker-compose logs -f nginx
docker-compose logs -f postgres_db
```

### Step 8.4: Check Database Health
```bash
# Connect to database and run checks
docker exec postgres_db psql -U imptracker -d imptracker << EOF
-- Check database size
SELECT pg_database.datname, 
       pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'imptracker';

-- Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

---

## Phase 9: Post-Deployment Verification

### Step 9.1: Test Core Functionality
```bash
# 1. Login page loads
curl https://imptracker.znphi.co.zm/accounts/login/

# 2. API endpoints accessible
curl https://imptracker.znphi.co.zm/api/

# 3. Static files served
curl https://imptracker.znphi.co.zm/static/css/style.css

# 4. Database connection working
curl -X POST https://imptracker.znphi.co.zm/api/activities/ \
  -H "Content-Type: application/json"
# Should return 403 or 401 (auth required), not 500
```

### Step 9.2: Performance Baseline
```bash
# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 https://imptracker.znphi.co.zm/

# Should handle requests without errors
# Look for "Requests per second" metric
```

### Step 9.3: SSL Security Check
```bash
# Test SSL configuration
openssl s_client -connect imptracker.znphi.co.zm:443 \
  -showcerts | grep -A2 "Issuer"

# Should show Let's Encrypt as issuer
```

---

## Phase 10: Operational Procedures

### Step 10.1: Restarting Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart django_web
docker-compose restart nginx
docker-compose restart postgres_db
```

### Step 10.2: Updating Application Code
```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild containers if dependencies changed
docker-compose up -d --build

# 3. Run migrations
docker-compose exec django_web python manage.py migrate

# 4. Verify application
curl https://imptracker.znphi.co.zm/
```

### Step 10.3: Viewing Real-Time Logs
```bash
# All service logs
docker-compose logs -f

# Filter by service
docker-compose logs -f django_web
docker-compose logs -f nginx
docker-compose logs -f postgres_db

# Search in logs
docker-compose logs django_web | grep ERROR
```

### Step 10.4: Emergency Recovery
```bash
# If something goes wrong, full restart:
docker-compose down
docker-compose up -d

# If database is corrupted:
docker-compose down
docker-compose up -d db  # Start database only
# Restore backup from backup.sh

# Check application health
docker-compose ps
docker-compose logs
```

---

## Troubleshooting

### SSL Certificate Issues
```bash
# Certificate expired?
docker exec certbot certbot certificates

# Manually renew:
docker-compose stop nginx
docker-compose run --rm certbot renew --force-renewal
docker-compose up -d nginx
```

### Database Connection Issues
```bash
# Check if database is running
docker-compose ps postgres_db

# Check database logs
docker-compose logs postgres_db

# Test connection
docker exec postgres_db pg_isready -U imptracker
```

### Application Not Starting
```bash
# Check for errors
docker-compose logs django_web

# Common issues:
# - Database not ready: Wait and retry
# - Missing migrations: docker-compose exec django_web python manage.py migrate
# - Static files: docker-compose exec django_web python manage.py collectstatic
```

### High Memory Usage
```bash
# Check resource usage
docker stats

# Restart to free memory
docker-compose restart

# If persistent, increase server RAM or optimize queries
```

---

## Security Checklist

- [ ] SSL certificate obtained and valid
- [ ] `SECURE_SSL_REDIRECT=True` enabled
- [ ] `DEBUG=False` set
- [ ] Strong database password configured
- [ ] `SECRET_KEY` is unique and strong (not default)
- [ ] Email credentials secured (not in git)
- [ ] Regular backups scheduled
- [ ] Firewall rules configured properly
- [ ] SSH key-based authentication enabled (disable password auth)
- [ ] Let's Encrypt auto-renewal configured
- [ ] Database backups stored off-server
- [ ] Log files monitored for errors

---

## Quick Reference Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec django_web python manage.py <command>

# Backup database
docker exec postgres_db pg_dump -U imptracker imptracker > backup.sql

# Restore database
docker exec -i postgres_db psql -U imptracker imptracker < backup.sql

# Restart service
docker-compose restart <service>

# View container stats
docker stats

# Check certificate expiration
docker exec certbot certbot certificates
```

---

## Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- Docker Documentation: https://docs.docker.com/
- Let's Encrypt: https://letsencrypt.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Gunicorn: https://gunicorn.org/

---

**Last Updated:** January 24, 2026  
**Next Review:** After production deployment
