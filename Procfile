release: . /opt/venv/bin/activate && python manage.py migrate --noinput
web: . /opt/venv/bin/activate && gunicorn researchdoc.wsgi --log-file - --workers 2 --timeout 60
