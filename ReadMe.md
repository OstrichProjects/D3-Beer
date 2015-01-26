# D3-Beer

This is a Flask app that uses Untappd's API and D3.js to visualize your Untappd history.

## Running a local instance

To run a local instance of D3-Beer you'll need Python 2.7, pip, and virtualenv.  Once you have those, clone this repository:

```
git clone https://github.com/OstrichProjects/D3-Beer.git
cd D3-Beer
```

Create and activate a virtualenv:

```
virtualenv flask
source flask/bin/activate # Linux/OS X
"flask/Scripts/activate" # Windows
```

Install the requirements:

```
pip install -r requirements.txt
```

If you're using Windows, you may get an error psycopg2.  You don't need it because it's for Heroku which uses PostgreSQL instead of SQLite which is used when the app is deployed locally.  If you're really annoyed by the error, then run this and it should install it without errors (If you get a 404, then visit http://www.stickpeople.com/projects/python/win-psycopg and get the url for the latest python2.7 release):

```
easy_install http://www.stickpeople.com/projects/python/win-psycopg/2.5.4/psycopg2-2.5.4.win32-py2.7-pg9.3.5-release.exe
```

You will need to register an new app with Untappd and copy your client id and client secret in __init__.py of the Untappd directory.

Once everything is installed initiate a local db and run the app:

```
python db_create.py
python app.py
```

## Deploying to Heroku

Login to Heroku in your console and create a new app:

```
heroku login
heroku create APP-NAME
```

Change the redirect url in your Untappd App's menu and in __init__.py in the Untappd directory.

Push to Heroku, change the environment variable for HEROKU to 1, and create a new PostgreSQL DB:

```
git add -A
git commit -m "COMMIT MESSAGE"
git push heroku master
```

Start a free PostgreSQL db on Heroku and initiate your db:

```
heroku addons:add heroku-postgresql:dev
heroku run createdb
```

And you should be good to go!

Note: The free postgresql database will probably fill up pretty quick since it's only 10000 rows, but it should be fine if you don't plan on having more than 10 people use the app.