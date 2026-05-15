release: python manage.py migrate --noinput && python manage.py collectstatic --noinput -i src
web: gunicorn researchdoc.wsgi --log-file - --workers 2 --timeout 60
