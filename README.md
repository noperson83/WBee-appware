# WBee-appware
Work Connection Convenience
Completing Initial Project Setup

Now, we can migrate the initial database schema to our PostgreSQL database using the management script:

~/myprojectdir/manage.py makemigrations
~/myprojectdir/manage.py migrate
Create an administrative user for the project by typing:

~/myprojectdir/manage.py createsuperuser
You will have to select a username, provide an email address, and choose and confirm a password.

We can collect all of the static content into the directory location we configured by typing:

~/myprojectdir/manage.py collectstatic
You will have to confirm the operation. The static files will then be placed in a directory called static within your project directory.

If you followed the initial server setup guide, you should have a UFW firewall protecting your server. In order to test the development server, we'll have to allow access to the port we'll be using.

Create an exception for port 8000 by typing:

sudo ufw allow 8000
