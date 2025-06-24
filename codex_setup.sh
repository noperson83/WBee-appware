#!/bin/bash
echo "Codex Setup Starting..."
pip install -r requirements.txt

# Create a minimal .env for local testing when one does not exist
if [ ! -f .env ]; then
    cat <<EOF > .env
SECRET_KEY=dummysecret
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EOF
fi

# Load environment variables and run migrations
export $(grep -v '^#' .env | xargs)
python manage.py migrate --noinput
