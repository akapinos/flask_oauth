import datetime
import inspect
import json
import os
import requests
import sys
import sqlite3

from dotenv import load_dotenv
from flask import (Flask, redirect, render_template, Response, request,
                   url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from oauthlib.oauth2 import WebApplicationClient
from typing import Optional

from db import init_db_command
from user import User

APP_ENDPOINTS = [
    'login', 'logout', 'index', 'list_city', 'city_date', 'about', 'useragent'
]

load_dotenv()

OWM_API_KEY = os.environ.get('OWM_API_KEY')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', None)
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', None)
GOOGLE_DISCOVERY_URL = (
    'https://accounts.google.com/.well-known/openid-configuration')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)

try:
    init_db_command()
except sqlite3.OperationalError:
    pass  # Assume it's already been created

client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def get_endpoints(endp_name: str) -> dict:
    excluded_endpoints = [endp_name]
    endpoints_dict = {}
    mod = sys.modules[__name__]

    if current_user.is_authenticated:
        excluded_endpoints.append('login')
    else:
        excluded_endpoints.append('logout')

    endpoints = [e for e in APP_ENDPOINTS if e not in excluded_endpoints]

    for e in endpoints:
        func = getattr(mod, e)
        args = inspect.getfullargspec(func).args
        if not args:
            endpoints_dict[e] = url_for(e)
        else:
            values = dict(zip(args, args))
            endpoints_dict[e] = url_for(e, **values)

    return endpoints_dict


def get_city_location(city: str) -> Optional[dict]:
    geo_api_url = 'https://api.openweathermap.org/geo/1.0/direct'
    query = {'q': city, 'appid': OWM_API_KEY}

    try:
        r = requests.get(geo_api_url, params=query).json()
        r = r[0]
        geo_loc = {'lat': r['lat'], 'lon': r['lon']}
        return geo_loc
    except:
        return None


def get_weather_data(city: str) -> Optional[dict]:
    owm_api_url = 'https://api.openweathermap.org/data/2.5/onecall?'

    city_loc = get_city_location(city)
    if not city_loc:
        return None

    weather_data = []
    query = dict(city_loc, **{'units': 'metric', 'appid': OWM_API_KEY})
    json_data = requests.get(owm_api_url, params=query).json()['daily']

    for w in json_data:
        weather = {
            'date': datetime.datetime.fromtimestamp(w['dt']).strftime('%d.%m'),
            'temperature': str(round(w['temp']['day'])) + ' \u00B0C',
            'description': w['weather'][0]['description'].capitalize(),
            'wind speed': str(round(w['wind_speed'])) + ' m/s',
            'pressure': str(w['pressure']) + ' hPa',
            'humidity': str(w['humidity']) + ' %',
            'icon': str(w['weather'][0]['icon'])
        }
        weather_data.append(weather)

    return weather_data


@app.route('/')
@app.route('/index')
def index() -> str:
    endpoints = get_endpoints(index.__name__)
    return render_template('index.html', endpoints=endpoints)


def get_google_provider_cfg() -> Response:
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/login')
def login() -> Response:
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + '/callback',
        scope=['openid', 'email', 'profile'],
    )
    return redirect(request_uri)


@app.route('/login/callback')
def callback():
    code = request.args.get('code')

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg['token_endpoint']

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get('email_verified'):
        unique_id = userinfo_response.json()['sub']
        users_email = userinfo_response.json()['email']
        picture = userinfo_response.json()['picture']
        users_name = userinfo_response.json()['given_name']
    else:
        return 'User email not available or not verified by Google.', 400

    user = User(id_=unique_id,
                name=users_name,
                email=users_email,
                profile_pic=picture)

    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    login_user(user)

    return redirect(url_for('index'))


@app.route('/logout')
def logout() -> Response:
    logout_user()
    return redirect(url_for('index'))


@app.route('/list/<city>')
def list_city(city=None) -> str:
    if city == 'city':
        return render_template('7day_city.html')

    weather_data = get_weather_data(city)
    if weather_data:
        return render_template('7day_city.html',
                               city=city,
                               weather_data=weather_data)
    else:
        return render_template('7day_city.html')


def get_date(date: str) -> datetime.datetime:
    patterns = ['%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d']

    for p in patterns:
        try:
            return datetime.datetime.strptime(date, p).date()
        except:
            pass

    return None


def get_weather_on_date(city: str, date: str) -> Optional[dict]:
    owm_api_url = 'https://api.openweathermap.org/data/2.5/onecall?'

    city_loc = get_city_location(city)
    if not city_loc:
        return None

    today = datetime.date.today()
    date = get_date(date)
    date_dt = (datetime.datetime.combine(date, datetime.time.min).timestamp())
    if not date:
        return None

    dt_days = (date - today).days
    if dt_days < -5 or dt_days > 7:
        return None

    query = dict(city_loc, **{'units': 'metric', 'appid': OWM_API_KEY})

    if dt_days < 0:
        owm_api_url = owm_api_url.strip('?') + '/timemachine?'
        query = dict(query, **{'dt': int(date_dt)})
        json_data = requests.get(owm_api_url, params=query).json()['current']
        temp = str(round(json_data['temp'])) + ' \u00B0C'
    else:
        json_data = requests.get(owm_api_url,
                                 params=query).json()['daily'][dt_days]
        temp = str(round(json_data['temp']['day'])) + ' \u00B0C'

    weather = {
        'temperature': temp,
        'description': json_data['weather'][0]['description'].capitalize(),
        'wind speed': str(round(json_data['wind_speed'])) + ' m/s',
        'pressure': str(json_data['pressure']) + ' hPa',
        'humidity': str(json_data['humidity']) + ' %',
        'icon': str(json_data['weather'][0]['icon'])
    }

    return weather


@app.route('/<city>/<date>')
def city_date(city=None, date=None) -> str:
    if city == 'city' or date == 'date':
        return render_template('city_date.html')

    weather_data = get_weather_on_date(city, date)
    if weather_data:
        return render_template('city_date.html',
                               city=city,
                               date=date,
                               weather=weather_data)
    else:
        return render_template('city_date.html')


@app.route('/about')
def about() -> str:
    if current_user.is_authenticated:
        return ('<p>Hello, {}! You\'re logged in! Email: {}</p>'
                '<div><p>Google Profile Picture:</p>'
                '<img src="{}" alt="Google profile pic"></img></div>'
                '<a class="button" href="/logout">Logout</a>'.format(
                    current_user.name, current_user.email,
                    current_user.profile_pic))
    else:
        return '<a class="button" href="/login">Google Login</a>'


@app.route('/useragent')
def useragent() -> str:
    browser = request.user_agent.browser.capitalize()
    os = request.user_agent.platform.capitalize()

    return (f'<p>OS name: {os}</p>'
            f'<p>Browser: {browser}</p>')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context='adhoc')
