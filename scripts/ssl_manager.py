#!/usr/bin/env python3
"""
SSL Certificate Manager for FOK Bot
Handles automatic SSL certificate renewal using Let's Encrypt
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


class SSLManager:
    """Manages SSL certificates using Let's Encrypt."""
    
    def __init__(self, domain: str, email: str, webroot_path: str = "/var/www/html"):
        self.domain = domain
        self.email = email
        self.webroot_path = webroot_path
        self.cert_path = f"/etc/letsencrypt/live/{domain}"
        self.cert_file = f"{self.cert_path}/fullchain.pem"
        self.key_file = f"{self.cert_path}/privkey.pem"
        
    def check_certificate_exists(self) -> bool:
        """Check if certificate already exists."""
        return os.path.exists(self.cert_file) and os.path.exists(self.key_file)
    
    def check_certificate_expiry(self) -> Optional[datetime]:
        """Check when certificate expires."""
        if not self.check_certificate_exists():
            return None
            
        try:
            result = subprocess.run([
                "openssl", "x509", "-in", self.cert_file, 
                "-noout", "-dates"
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.split('\n'):
                if line.startswith('notAfter='):
                    expiry_str = line.split('=', 1)[1]
                    return datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking certificate expiry: {e}")
            return None
        
        return None
    
    def is_certificate_expiring_soon(self, days: int = 30) -> bool:
        """Check if certificate expires within specified days."""
        expiry = self.check_certificate_expiry()
        if not expiry:
            return True  # No certificate, needs renewal
            
        return expiry <= datetime.now() + timedelta(days=days)
    
    def create_webroot_directory(self) -> bool:
        """Create webroot directory for ACME challenge."""
        try:
            os.makedirs(self.webroot_path, exist_ok=True)
            os.makedirs(f"{self.webroot_path}/.well-known/acme-challenge", exist_ok=True)
            return True
        except OSError as e:
            logger.error(f"Error creating webroot directory: {e}")
            return False
    
    def obtain_certificate(self, staging: bool = False) -> bool:
        """Obtain new SSL certificate."""
        if not self.create_webroot_directory():
            return False
            
        cmd = [
            "certbot", "certonly",
            "--webroot",
            "--webroot-path", self.webroot_path,
            "--email", self.email,
            "--agree-tos",
            "--no-eff-email",
            "--domains", self.domain
        ]
        
        if staging:
            cmd.append("--staging")
            
        try:
            logger.info(f"Obtaining SSL certificate for {self.domain}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Certificate obtained successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error obtaining certificate: {e}")
            logger.error(f"stderr: {e.stderr}")
            return False
    
    def renew_certificate(self) -> bool:
        """Renew existing SSL certificate."""
        try:
            logger.info(f"Renewing SSL certificate for {self.domain}")
            result = subprocess.run([
                "certbot", "renew", "--quiet"
            ], check=True, capture_output=True, text=True)
            logger.info("Certificate renewed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error renewing certificate: {e}")
            logger.error(f"stderr: e.stderr")
            return False
    
    def reload_nginx(self) -> bool:
        """Reload nginx configuration."""
        try:
            subprocess.run(["nginx", "-t"], check=True, capture_output=True)
            subprocess.run(["systemctl", "reload", "nginx"], check=True)
            logger.info("Nginx reloaded successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error reloading nginx: {e}")
            return False
    
    def update_nginx_config(self) -> bool:
        """Update nginx configuration with SSL certificates."""
        nginx_config = f"""
server {{
    listen 80;
    server_name {self.domain};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain};
    
    # SSL Configuration
    ssl_certificate {self.cert_file};
    ssl_certificate_key {self.key_file};
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Bot webhook endpoint
    location /webhook {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Health check endpoint
    location /health {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {{
        root {self.webroot_path};
    }}
    
    # Default location
    location / {{
        return 404;
    }}
}}
"""
        
        try:
            config_path = f"/etc/nginx/sites-available/{self.domain}"
            with open(config_path, 'w') as f:
                f.write(nginx_config)
            
            # Enable site
            subprocess.run([
                "ln", "-sf", config_path, f"/etc/nginx/sites-enabled/{self.domain}"
            ], check=True)
            
            logger.info(f"Nginx configuration updated for {self.domain}")
            return True
        except Exception as e:
            logger.error(f"Error updating nginx config: {e}")
            return False
    
    def setup_automatic_renewal(self) -> bool:
        """Setup automatic certificate renewal via cron."""
        cron_job = f"0 2 * * * /usr/bin/python3 {__file__} --renew --domain {self.domain} --email {self.email} >> /var/log/ssl-renewal.log 2>&1"
        
        try:
            # Add to crontab
            subprocess.run([
                "crontab", "-l"
            ], capture_output=True, text=True)
            
            # Check if job already exists
            result = subprocess.run([
                "crontab", "-l"
            ], capture_output=True, text=True)
            
            if cron_job not in result.stdout:
                # Add new cron job
                current_crontab = result.stdout if result.returncode == 0 else ""
                new_crontab = current_crontab + "\n" + cron_job + "\n"
                
                subprocess.run([
                    "crontab", "-"
                ], input=new_crontab, text=True, check=True)
                
                logger.info("Automatic renewal cron job added")
                return True
            else:
                logger.info("Automatic renewal cron job already exists")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error setting up automatic renewal: {e}")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="SSL Certificate Manager")
    parser.add_argument("--domain", required=True, help="Domain name for SSL certificate")
    parser.add_argument("--email", required=True, help="Email for Let's Encrypt registration")
    parser.add_argument("--webroot", default="/var/www/html", help="Webroot path for ACME challenge")
    parser.add_argument("--staging", action="store_true", help="Use Let's Encrypt staging environment")
    parser.add_argument("--renew", action="store_true", help="Renew existing certificate")
    parser.add_argument("--setup-auto", action="store_true", help="Setup automatic renewal")
    parser.add_argument("--check", action="store_true", help="Check certificate status")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    ssl_manager = SSLManager(
        domain=args.domain,
        email=args.email,
        webroot_path=args.webroot
    )
    
    if args.check:
        # Check certificate status
        if ssl_manager.check_certificate_exists():
            expiry = ssl_manager.check_certificate_expiry()
            if expiry:
                days_until_expiry = (expiry - datetime.now()).days
                logger.info(f"Certificate expires in {days_until_expiry} days")
                if ssl_manager.is_certificate_expiring_soon():
                    logger.warning("Certificate is expiring soon!")
                else:
                    logger.info("Certificate is valid")
            else:
                logger.error("Could not determine certificate expiry")
        else:
            logger.warning("No certificate found")
    
    elif args.renew:
        # Renew certificate
        if ssl_manager.renew_certificate():
            ssl_manager.reload_nginx()
        else:
            logger.error("Certificate renewal failed")
            sys.exit(1)
    
    elif args.setup_auto:
        # Setup automatic renewal
        if ssl_manager.setup_automatic_renewal():
            logger.info("Automatic renewal setup completed")
        else:
            logger.error("Failed to setup automatic renewal")
            sys.exit(1)
    
    else:
        # Obtain new certificate
        if ssl_manager.obtain_certificate(staging=args.staging):
            if ssl_manager.update_nginx_config():
                ssl_manager.reload_nginx()
                logger.info("SSL setup completed successfully")
            else:
                logger.error("Failed to update nginx configuration")
                sys.exit(1)
        else:
            logger.error("Failed to obtain SSL certificate")
            sys.exit(1)


if __name__ == "__main__":
    main()