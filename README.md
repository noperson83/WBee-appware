# WBee-appware
Work Connection Convenience

WBee new install
Create a Database:

sudo -u postgres psql

CREATE DATABASE newapp;
CREATE USER newappuser WITH PASSWORD 'password';
ALTER ROLE newappuser SET client_encoding TO 'utf8';
ALTER ROLE newappuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE newappuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE  newapp TO  newappuser;
\q
mkdir ~/newapp.wbee.app
sudo chown -R nope:www-data newapp.wbee.app
cd ~/newapp.wbee.app
virtualenv wbeenv
source wbeenv/bin/activate
pip install django gunicorn psycopg2-binary

Creating and Configuring a New Django Project
django-admin.py startproject wbeeapp /var/www/wbeeapp.wbee.app
nano /var/www/wbeeapp.wbee.app/wbeeapp/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'nope',
        'NAME': 'wbeeapp',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}
ALLOWED_HOSTS = ['wbeeapp.wbee.app']

python /var/www/j2.wbee.app/manage.py showmigrations
python /var/www/j2.wbee.app/manage.py migrate hr
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

pip install django-extensions
pip install python-dateutil
sudo ufw allow 9000
sudo certbot --nginx -d j2.wbee.app
sudo nano /etc/nginx/sites-available/wbee.app
upstream wbeeapp_app_server {
    server 127.0.0.1:9000 fail_timeout=0;
}
location / {
proxy_pass http://wbeeapp_app_server;
} 
python manage.py runserver 127.0.0.1:9000
gunicorn --bind 127.0.0.1:9000 wbeeapp.wsgi
deactivate
sudo nano /etc/systemd/system/wbeeapp.socket
sudo nano /etc/systemd/system/wbeeapp.service
sudo systemctl start wbeeapp.socket
sudo systemctl enable wbeeapp.socket
sudo systemctl status wbeeapp.socket
file /run/wbeeapp.sock
sudo systemctl status wbeeapp
curl --unix-socket /run/wbeeapp.sock localhost
sudo systemctl daemon-reload
sudo systemctl restart wbeeapp
sudo nano /etc/nginx/sites-available/wbee.app
sudo nginx -t
sudo systemctl restart nginx
pip install xhtml2pdf
pip install bleach
