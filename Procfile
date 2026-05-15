release: python manage.py migrate --noinput
web: gunicorn researchdoc.wsgi --log-file - --workers 2 --timeout 60
