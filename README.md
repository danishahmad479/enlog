## HOW TO RUN

1. Create a virtual env
python3 -m venv venv

2. Acitvate virtual env
. venv/bin/activate

3. Run migrations and collectstatic
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic

4. Run Server
daphne ecommerce.asgi:application
