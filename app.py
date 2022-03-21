import inspect
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for
from typing import Optional


APP_ENDPOINTS = [
    'login', 'logout', 'index', 'list_city', 'city_date', 'about', 'useragent'
]

load_dotenv()

OWM_API_KEY = os.environ.get('OWM_API_KEY')

app = Flask(__name__)


def get_endpoints(endp_name: str) -> dict:
    endpoints = [e for e in APP_ENDPOINTS if e != endp_name]
    endpoints_dict = {}
    mod = sys.modules[__name__]

    for e in endpoints:
        func = getattr(mod, e)
        args = inspect.getfullargspec(func).args
        if not args:
            endpoints_dict[e] = url_for(e)
        else:
            values = dict(zip(args, '*'))
            endpoints_dict[e] = url_for(e, **values)

    return endpoints_dict


def get_city_location(city: str) -> Optional[dict]:
    geo_api_url = 'https://api.openweathermap.org/geo/1.0/direct'
    query = {'q': city, 'appid': OWM_API_KEY}

    r = requests.get(geo_api_url, params=query).json()
    if r:
        r = r[0]
        geo_loc = {'lat': r['lat'], 'lon': r['lon']}
        return geo_loc
    else:
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
            'date': datetime.fromtimestamp(w['dt']).strftime('%d.%m'),
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


@app.route('/login')
def login() -> str:
    return 'login'


@app.route('/logout')
def logout() -> str:
    return 'logout'


@app.route('/list/<city>')
def list_city(city=None) -> str:
    weather_data = get_weather_data(city)
    if weather_data:
        return render_template('7day_city.html',
                               city=city,
                               weather_data=weather_data)
    else:
        return render_template('7day_city.html')


@app.route('/city/date')
def city_date() -> str:
    return 'city/date'


@app.route('/about')
def about() -> str:
    return 'about'


@app.route('/useragent')
def useragent() -> str:
    browser = request.user_agent.browser.capitalize()
    os = request.user_agent.platform.capitalize()

    return (f'<p>OS name: {os}</p>'
            f'<p>Browser: {browser}</p>')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
