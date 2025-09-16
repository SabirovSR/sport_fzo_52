# FOK Bot Deployment Guide

This guide covers the deployment of the FOK Bot with SSL support, monitoring, and CI/CD.

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS pointing to your server
- Email address for Let's Encrypt certificates
- Sentry account (optional, for error monitoring)

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd fok-bot
cp .env.example .env
# Edit .env with your configuration
```

### 2. Basic Deployment (HTTP only)

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 3. SSL Deployment (Recommended)

```bash
# Set SSL environment variables
export SSL_DOMAIN=your-domain.com
export SSL_EMAIL=admin@your-domain.com

# Run with SSL support
docker-compose -f docker-compose.ssl.yml up -d

# Check SSL setup
docker-compose -f docker-compose.ssl.yml logs -f fok-bot-ssl
```

## SSL Certificate Management

### Automatic Setup

The SSL-enabled Docker container automatically:
1. Obtains Let's Encrypt certificates
2. Configures Nginx with SSL
3. Sets up automatic renewal

### Manual SSL Management

```bash
# Check certificate status
python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --check

# Renew certificate
python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --renew

# Setup automatic renewal
python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --setup-auto
```

## Environment Variables

### Required Variables

- `BOT_TOKEN`: Telegram bot token
- `WEBHOOK_URL`: Full webhook URL (e.g., https://your-domain.com/webhook)
- `WEBHOOK_SECRET`: Secret token for webhook validation

### Database Variables

- `MONGO_HOST`: MongoDB host (default: mongodb)
- `MONGO_PORT`: MongoDB port (default: 27017)
- `MONGO_DB_NAME`: Database name (default: fok_bot)
- `MONGO_USERNAME`: MongoDB username
- `MONGO_PASSWORD`: MongoDB password

### Redis Variables

- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password

### SSL Variables

- `SSL_DOMAIN`: Domain name for SSL certificate
- `SSL_EMAIL`: Email for Let's Encrypt registration

### Monitoring Variables

- `SENTRY_DSN`: Sentry DSN for error monitoring (optional)
- `APP_VERSION`: Application version (default: 1.0.0)

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Domain Configuration

```bash
# Point your domain to your server IP
# A record: your-domain.com -> YOUR_SERVER_IP
# CNAME record: www.your-domain.com -> your-domain.com
```

### 3. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd fok-bot

# Configure environment
cp .env.example .env
nano .env  # Edit with your values

# Deploy with SSL
docker-compose -f docker-compose.ssl.yml up -d

# Verify deployment
curl -I https://your-domain.com/health
```

### 4. Setup Monitoring

```bash
# Configure Sentry (optional)
# Add SENTRY_DSN to .env file

# Setup log rotation
sudo nano /etc/logrotate.d/fok-bot
```

Log rotation configuration:
```
/var/lib/docker/containers/*/fok-bot-ssl-*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

## CI/CD Pipeline

### GitHub Actions Setup

1. **Repository Secrets**: Add the following secrets to your GitHub repository:
   - `BOT_TOKEN`: Telegram bot token
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password
   - `SLACK_WEBHOOK`: Slack webhook URL (optional)

2. **Environment Variables**: Set up environment-specific variables:
   - `STAGING_DOMAIN`: Staging domain
   - `PRODUCTION_DOMAIN`: Production domain
   - `SSL_EMAIL`: Email for SSL certificates

### Pipeline Features

- **Automated Testing**: Runs on every push and PR
- **Security Scanning**: Weekly security vulnerability scans
- **Docker Build**: Builds and pushes Docker images
- **SSL Renewal**: Automatic SSL certificate renewal
- **Deployment**: Automated deployment to staging/production

## Monitoring and Maintenance

### Health Checks

```bash
# Check application health
curl https://your-domain.com/health

# Check SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check logs
docker-compose -f docker-compose.ssl.yml logs -f
```

### Backup

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.ssl.yml down
docker-compose -f docker-compose.ssl.yml build --no-cache
docker-compose -f docker-compose.ssl.yml up -d
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --check
   
   # Renew if needed
   python scripts/ssl_manager.py --domain your-domain.com --email admin@your-domain.com --renew
   ```

2. **Bot Not Responding**
   ```bash
   # Check webhook status
   curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
   
   # Check application logs
   docker-compose -f docker-compose.ssl.yml logs fok-bot-ssl
   ```

3. **Database Connection Issues**
   ```bash
   # Check MongoDB status
   docker-compose -f docker-compose.ssl.yml exec mongodb mongosh --eval "db.adminCommand('ping')"
   
   # Check Redis status
   docker-compose -f docker-compose.ssl.yml exec redis redis-cli ping
   ```

### Log Locations

- Application logs: `docker-compose logs fok-bot-ssl`
- Nginx logs: `/var/lib/docker/volumes/fok-bot-ssl_nginx_logs/_data/`
- SSL renewal logs: `/var/lib/docker/volumes/fok-bot-ssl_ssl_logs/_data/`

## Security Considerations

1. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **SSL Security**
   - Certificates are automatically renewed
   - Strong SSL ciphers are configured
   - HSTS headers are enabled

3. **Application Security**
   - Rate limiting is enabled
   - Input validation is implemented
   - Error monitoring with Sentry

## Support

For issues and questions:
1. Check the logs first
2. Review this documentation
3. Create an issue in the repository
4. Contact the development team