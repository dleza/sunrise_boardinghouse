#!/usr/bin/env bash
#!/usr/bin/env bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings

python -m django --version
python -m django check

python -m django collectstatic --noinput
python -m django migrate
