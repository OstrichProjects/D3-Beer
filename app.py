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
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.config.from_object('config')
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    untappd_id = db.Column(db.Integer, index=True)
    username = db.Column(db.String, index=True)
    user_avatar = db.Column(db.String)
    checkins = db.relationship('CheckIn', backref = 'author', lazy = 'dynamic')

    def __repr__(self):
        return '<User %r>' % self.username

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

    untappd_id, username, user_avatar = r.json()[u'response'][u'user'][u'uid'], r.json()[u'response'][u'user'][u'user_name'], r.json()[u'response'][u'user'][u'user_avatar']

    if not User.query.filter(User.untappd_id == untappd_id):
        # Add user to database
        user = User(untappd_id=untappd_id, username=username, user_avatar=user_avatar)
        db.session.add(user)

    params = {'access_token': g.access_token, 'limit': 50}
    UNTAPPD_URL = "https://api.untappd.com/v4/user/checkins/"
    beer_list_untappd = []
    a = 0
    while True:
        if a > 49:
            break
        r = requests.get(UNTAPPD_URL, params = params)
        if r.json()[u'response'][u'checkins'][u'count'] > 0:
            beer_list_untappd += r.json()[u'response'][u'checkins'][u'items']
        if r.json()[u'response'][u'checkins'][u'count'] < 50:
            break
        params['max_id'] = r.json()[u'response'][u'pagination'][u'max_id']
        a += 1
    beer_list = []
    for beer_untappd in beer_list_untappd:
        beer = {
            'name': beer_untappd[u'beer'][u'beer_name'],
            'brewery': beer_untappd[u'brewery'][u'brewery_name'],
            'style': beer_untappd[u'beer'][u'beer_style'],
            # 'ibu': beer_untappd[u'beer'][u'beer_ibu'],
            'abv': beer_untappd[u'beer'][u'beer_abv'],
            'brewer-country': beer_untappd[u'brewery'][u'country_name'], 
        }
        if beer_untappd[u'venue'] != []:
            beer['venue-country'] = beer_untappd[u'venue'][u'location'][u'venue_country']
            beer['venue-city'] = beer_untappd[u'venue'][u'location'][u'venue_city']
        else:
            beer['venue-country'] = None
            beer['venue-city'] = None
        beer_list.append(beer)
    return json.dumps(beer_list)

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



if __name__ == '__main__':
    app.run()