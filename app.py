from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
import requests
import json
import logging
import sys
from untappd import UNTAPPD_CLIENT_ID, UNTAPPD_CLIENT_SECRET, UNTAPPD_REDIRECT_URL

# Init Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'I Like big beers'
app.debug = True
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.config.from_object('config')
db = SQLAlchemy(app)

# Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    untappd_id = db.Column(db.Integer, index=True)
    username = db.Column(db.String, index=True)
    user_avatar = db.Column(db.String)
    checkins = db.relationship('CheckIn', backref = 'author', lazy = 'dynamic')
    updated = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<User %r>' % self.username

    def get_min(self):
        return min([checkin.checkin_id for checkin in self.checkins])

    def get_max(self):
        return max([checkin.checkin_id for checkin in self.checkins])

    def get_checkins(self):
        checkins = []
        for checkin in self.checkins:
            checkins.append(dict((col, getattr(checkin, col)) for col in checkin.__table__.columns.keys()))
        return checkins

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checkin_id = db.Column(db.Integer, index=True)
    name = db.Column(db.String)
    brewery = db.Column(db.String)
    style = db.Column(db.String)
    abv = db.Column(db.Float)
    brewer_country = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<CheckIn - %r>' % self.name

# Views

@app.before_request
def load_access_token():
    if 'access_token' in session:
        access_token = session['access_token']
    else:
        access_token = None

    g.access_token = access_token

@app.route('/')
def index():
    if g.access_token:
        return render_template("index.html", access = g.access_token)
    else:
        return render_template("login.html")

@app.route('/beers')
def beers():
    # If their access token is not present then return an error
    if not g.access_token:
        error = {
          "success": False,
          "error": {
            "code": 100,
            "message": "No access token is present."
          }
        }
        return json.dumps(error)

    # Get User info, check if they are in DB, add them if not
    params = {'access_token': g.access_token}
    UNTAPPD_URL = "https://api.untappd.com/v4/user/info/"
    r = requests.get(UNTAPPD_URL, params = params)

    if r.json()[u'meta'][u'code'] != 200:
        error = {
          "success": False,
          "error": {
            "code": 500,
            "message": "Could not successfully call Untappd's API."
          }
        }
        return json.dumps(error)

    untappd_id, username, user_avatar = r.json()[u'response'][u'user'][u'uid'], r.json()[u'response'][u'user'][u'user_name'], r.json()[u'response'][u'user'][u'user_avatar']

    # Check if user is in database
    if not User.query.filter_by(untappd_id=untappd_id).all():
        print "User didn't exist"
        # Add user to database
        user = User(untappd_id=untappd_id, username=username, user_avatar=user_avatar)
        db.session.add(user)
        params = {'access_token': g.access_token, 'limit': 50, 'max_id': None}
        UNTAPPD_URL = "https://api.untappd.com/v4/user/checkins/"
        # Get as many checkins as possible
        get_the_beers(user, params)
    # If user is in database, check if we finished adding their beers
    else:
        print "User did exist"
        user = User.query.filter_by(untappd_id=untappd_id).first()
        if not user.updated:
            print "User was not updated"
            # Get the last checkin that was added to DB for that user
            max_id = user.get_min()
            params = {'access_token': g.access_token, 'limit': 50, 'max_id': max_id}
            get_the_beers(user, params)
        # Get most recent checkin added for that user
        since_id = user.get_max()
        params = {'access_token': g.access_token, 'limit': 50, 'since_id': since_id}
        get_the_beers(user, params)
    # Commit all DB changes
    db.session.commit()

    return json.dumps(user.get_checkins())

@app.route('/login-beers')
def test_beers():
    return send_from_directory('./static', 'checkins.json')

@app.route('/login')
def login():
    return redirect('https://untappd.com/oauth/authenticate/?client_id={0}&response_type=code&redirect_url={1}'.format(UNTAPPD_CLIENT_ID,UNTAPPD_REDIRECT_URL))

@app.route('/auth')
def authorize():
    try:
        code = request.args.get('code')
    except KeyError:
        return redirect(url_for('index'))

    params = {
        'client_id': UNTAPPD_CLIENT_ID,
        'client_secret': UNTAPPD_CLIENT_SECRET,
        'response_type': 'code',
        'redirect_url': UNTAPPD_REDIRECT_URL,
        'code': code 
    }

    UNTAPPD_URL = 'https://untappd.com/oauth/authorize/'

    r = requests.get(UNTAPPD_URL, params = params)

    if r.json()[u'meta'][u'http_code'] == 200:
        access_token = r.json()[u'response'][u'access_token']
        session['access_token'] = access_token
    return redirect(url_for('index'))


def get_the_beers(user, params):
    UNTAPPD_URL = "https://api.untappd.com/v4/user/checkins/"
    while True:
        r = requests.get(UNTAPPD_URL, params = params)
        
        if r.json()[u'meta'][u'code'] != 200:
            break

        if r.json()[u'response'][u'checkins'][u'count'] > 0:
            beer_list = r.json()[u'response'][u'checkins'][u'items']
            params['max_id'] = r.json()[u'response'][u'pagination'][u'max_id']
            for beer in beer_list:
                checkin = CheckIn(checkin_id=beer[u'checkin_id'],
                                    name=beer[u'beer'][u'beer_name'],
                                    brewery=beer[u'brewery'][u'brewery_name'],
                                    style=beer[u'beer'][u'beer_style'],
                                    abv=beer[u'beer'][u'beer_abv'],
                                    brewer_country=beer[u'brewery'][u'country_name'],
                                    author=user)
                db.session.add(checkin)

        if r.json()[u'response'][u'checkins'][u'count'] < 50:
            user.updated = True
            db.session.add(user)
            break

    return None

if __name__ == '__main__':
    app.run()