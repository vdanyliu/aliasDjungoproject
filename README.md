# django-project

## Setup
```bash
git clone https://github.com/vdanyliu/aliasDjungoproject.git
```

### Install requirements:
```bash
pip install -r requirements.txt
```

### Perform database migration:
```bash
manage.py makemigrations alias
manage.py migrate
manage.py createsuperuser
```

## Run Development Server

```bash
manage.py runserver
```
Admin endpoint is at http://127.0.0.1:8000/admin/

## Testing

### Run tests:
```bash
python manage.py test
```

