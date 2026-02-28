# SSL Certificates

Place your TLS certificate files here before starting the production stack:

```
nginx/ssl/fullchain.pem   ← full certificate chain (cert + intermediate)
nginx/ssl/privkey.pem     ← private key
```

## Option 1 – Let's Encrypt (recommended)

```bash
# Install certbot and obtain a certificate
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy the certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem  nginx/ssl/
```

## Option 2 – Self-signed (development / staging only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

> **Note:** These files are gitignored. Never commit private keys.
