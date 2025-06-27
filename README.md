# WBee Universal Company Manager

This repository contains a collection of Django applications for managing many aspects of a company.  The project was built on **Django 5.2** and expects **Python 3.11** or later.

## Prerequisites

- Python 3.11+
- Django 5.2
- Additional packages listed in `wbee/settings/base.py` (e.g. `django-extensions`, `djangorestframework`, `django-filter`, `django-import-export`, `django-crispy-forms`, `crispy-bootstrap5`, `django-cors-headers`, `dj-database-url`, `python-decouple`, `Pillow`, `easy-thumbnails`, `django-mptt`, `bleach`, `pytest-django`, `django-grappelli`, `django-filer`, `whitenoise`, `redis`, `qrcode`, `pytz`, `psycopg2-binary`, `sentry-sdk`, `django-storages[boto3]`, `django-debug-toolbar`, `weasyprint`).
- A database supported by Django (SQLite is fine for development).

## Environment Setup

```bash
# Clone the repository
$ git clone <repo-url>
$ cd WBee-appware

# Create a virtual environment
$ python -m venv .venv
$ source .venv/bin/activate

# Install dependencies
(venv)$ pip install -r requirements.txt
```

Create a `.env` file (or set environment variables) for secrets and database configuration.  A minimal example:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=America/Phoenix
```

Apply migrations and create a superuser:

```bash
(venv)$ python manage.py migrate
(venv)$ python manage.py createsuperuser
(venv)$ python manage.py collectstatic --noinput
```

## Running the Project

Start the development server with:

```bash
(venv)$ python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to access the application.

### Calendar Feeds

The schedule app exposes iCalendar (ICS) feeds for each calendar.  These feeds
allow integration with external calendaring clients such as Google Calendar or
Outlook.  Access a feed at:

```
/schedule/<calendar_id>/ical/
```

where `calendar_id` is the numeric ID of the calendar you want to subscribe to.

## Running Tests

Tests can be executed with Django's test runner.  The example below uses an in-memory SQLite database:

```bash
(venv)$ DATABASE_URL=sqlite:///:memory: python manage.py test
```

## Application Overview

Major apps included in this project are:

- **asset** – Manage company assets and categories.
- **client** – Customer records, addresses and contacts.
- **company** – Core company/organization information.
- **business** – Manage business types, configurations and templates.
- **helpdesk** – Ticket tracking and knowledge base.
- **hr** – Human resources: workers and positions.
- **location** – Business locations and configurable choices.
- **material** – Inventory and materials management.
- **project** – Project and scope tracking.
- **receipts** – Receipt and expense uploads.
- **schedule** – Calendar and event scheduling.
- **timecard** – Worker time tracking.
- **todo** – Simple task lists with comments and notifications.
- **wip** – Prototype work‑in‑progress features.

Each app lives in its own directory with `models`, `views`, templates and tests where applicable.

## Business Templates

The `business` app includes predefined templates for rapid deployment.  These
templates outline common configurations so you can get started quickly.  See
`business/templates.py` for examples such as the *beer_distribution* network.

