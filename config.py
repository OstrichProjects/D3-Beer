CSRF_ENABLED = True
SECRET_KEY = 'SECRET_KEY'

import os
basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('HEROKU') is not None:
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
else:
	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')