#!/bin/bash
# Ubuntu 24.04 Worker Bee Server Setup Script
# Run as: bash setup_workerbee_server.sh

echo "🐝 Setting up Worker Bee server on Ubuntu 24.04..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    vim \
    htop \
    tree \
    nginx \
    supervisor \
    redis-server \
    memcached \
    imagemagick \
    libmagickwand-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxslt-dev \
    libgeos-dev \
    libproj-dev \
    gdal-bin \
    libgdal-dev

# Install PostgreSQL 16 (latest)
echo "🐘 Installing PostgreSQL 16..."
sudo apt install -y postgresql postgresql-contrib postgresql-client
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install PostGIS for geographic features
sudo apt install -y postgresql-16-postgis-3

# Install Python 3.12 (latest in Ubuntu 24.04)
echo "🐍 Installing Python 3.12..."
sudo apt install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    python3-setuptools \
    python3-wheel

# Make python3.12 the default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Install Node.js 20 LTS (for modern frontend tools)
echo "📦 Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker (for containerization)
echo "🐳 Installing Docker..."
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null || true
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Create worker bee user
echo "👤 Creating workerbee user..."
sudo useradd -m -s /bin/bash workerbee
sudo usermod -aG sudo workerbee
sudo mkdir -p /home/workerbee/.ssh
sudo chown workerbee:workerbee /home/workerbee/.ssh

# Setup application directory
echo "📁 Setting up application directories..."
sudo mkdir -p /var/www/workerbee
sudo chown workerbee:workerbee /var/www/workerbee
sudo mkdir -p /var/log/workerbee
sudo chown workerbee:workerbee /var/log/workerbee

# Create Python virtual environment
echo "🏠 Creating Python virtual environment..."
sudo -u workerbee python3 -m venv /var/www/workerbee/venv
sudo -u workerbee /var/www/workerbee/venv/bin/pip install --upgrade pip setuptools wheel

# Install Python packages
echo "📚 Installing Python packages..."
sudo -u workerbee /var/www/workerbee/venv/bin/pip install \
    django==5.0.* \
    djangorestframework==3.15.* \
    django-extensions \
    django-debug-toolbar \
    django-cors-headers \
    django-environ \
    django-filter \
    django-crispy-forms \
    crispy-bootstrap5 \
    django-channels \
    channels-redis \
    psycopg2-binary \
    redis \
    celery \
    gunicorn \
    whitenoise \
    pillow \
    python-decouple \
    django-storages \
    boto3 \
    sentry-sdk \
    newrelic \
    uvicorn \
    daphne \
    pytest \
    pytest-django \
    coverage \
    black \
    flake8 \
    mypy \
    pre-commit

# Setup PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE USER workerbee WITH PASSWORD 'workerbee_secure_password_2025';"
sudo -u postgres psql -c "CREATE DATABASE workerbee_db OWNER workerbee;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE workerbee_db TO workerbee;"
sudo -u postgres psql -c "ALTER USER workerbee CREATEDB;"
sudo -u postgres psql -d workerbee_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Configure Redis
echo "📦 Configuring Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Setup Nginx configuration
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/workerbee > /dev/null <<EOF
server {
    listen 80;
    server_name wbee.app www.wbee.app;
    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /var/www/workerbee/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/workerbee/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/workerbee /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Setup Supervisor for Django/Celery
echo "👨‍💼 Configuring Supervisor..."
sudo tee /etc/supervisor/conf.d/workerbee.conf > /dev/null <<EOF
[program:workerbee_django]
command=/var/www/workerbee/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 workerbee.wsgi:application
directory=/var/www/workerbee
user=workerbee
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/workerbee/django.log
environment=PATH="/var/www/workerbee/venv/bin"

[program:workerbee_celery]
command=/var/www/workerbee/venv/bin/celery -A workerbee worker -l info
directory=/var/www/workerbee
user=workerbee
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/workerbee/celery.log
environment=PATH="/var/www/workerbee/venv/bin"

[program:workerbee_celery_beat]
command=/var/www/workerbee/venv/bin/celery -A workerbee beat -l info
directory=/var/www/workerbee
user=workerbee
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/workerbee/celery_beat.log
environment=PATH="/var/www/workerbee/venv/bin"
EOF

# Create environment file template
echo "⚙️ Creating environment configuration..."
sudo -u workerbee tee /var/www/workerbee/.env.template > /dev/null <<EOF
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=wbee.app,www.wbee.app,localhost,127.0.0.1

# Database
DATABASE_URL=postgres://workerbee:workerbee_secure_password_2025@localhost:5432/workerbee_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (configure with your SMTP settings)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for file storage - optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1

# Sentry (for error tracking - optional)
SENTRY_DSN=

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EOF

# Setup SSL with Let's Encrypt (commented out - run manually)
echo "🔒 SSL setup commands (run manually after DNS is configured):"
echo "sudo apt install certbot python3-certbot-nginx"
echo "sudo certbot --nginx -d wbee.app -d www.wbee.app"

# Setup firewall
echo "🔥 Configuring UFW firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Final system configuration
echo "🔧 Final system configuration..."
sudo systemctl restart nginx
sudo systemctl enable nginx
sudo systemctl restart supervisor
sudo systemctl enable supervisor

# Create deployment script
sudo tee /home/workerbee/deploy.sh > /dev/null <<'EOF'
#!/bin/bash
# Worker Bee Deployment Script

echo "🚀 Deploying Worker Bee..."

cd /var/www/workerbee

# Pull latest code (when using git)
# git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update Python dependencies
pip install -r requirements.txt

# Run Django management commands
python manage.py collectstatic --noinput
python manage.py migrate

# Restart services
sudo supervisorctl restart workerbee_django
sudo supervisorctl restart workerbee_celery
sudo supervisorctl restart workerbee_celery_beat
sudo systemctl reload nginx

echo "✅ Deployment complete!"
EOF

sudo chmod +x /home/workerbee/deploy.sh
sudo chown workerbee:workerbee /home/workerbee/deploy.sh

# Display summary
echo ""
echo "🎉 Worker Bee server setup complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ Ubuntu 24.04 updated"
echo "  ✅ Python 3.12 installed"
echo "  ✅ PostgreSQL 16 with PostGIS"
echo "  ✅ Redis server"
echo "  ✅ Nginx web server"
echo "  ✅ Docker & Docker Compose"
echo "  ✅ Node.js 20 LTS"
echo "  ✅ Django 5.0 + modern packages"
echo "  ✅ Supervisor process management"
echo "  ✅ UFW firewall configured"
echo ""
echo "📍 Next steps:"
echo "  1. Copy your Django project to /var/www/workerbee/"
echo "  2. Copy .env.template to .env and configure"
echo "  3. Run: sudo -u workerbee /home/workerbee/deploy.sh"
echo "  4. Configure DNS to point to this server"
echo "  5. Run SSL setup: sudo certbot --nginx -d wbee.app -d www.wbee.app"
echo ""
echo "🔑 Database credentials:"
echo "  Database: workerbee_db"
echo "  Username: workerbee"
echo "  Password: workerbee_secure_password_2025"
echo ""
echo "🏠 Project directory: /var/www/workerbee/"
echo "📁 Logs directory: /var/log/workerbee/"
echo ""

# Show status of services
echo "🔍 Service status:"
systemctl is-active postgresql nginx redis-server supervisor docker
