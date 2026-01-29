#!/usr/bin/env bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings

python manage.py collectstatic --noinput
python manage.py migrate

