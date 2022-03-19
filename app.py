from flask import Flask, render_template, request, url_for

APP_ENDPOINTS = [
    'login', 'logout', 'index', 'list_city', 'city_date', 'about', 'useragent'
]

app = Flask(__name__)


def get_endpoints(endp_name: str) -> dict:
    endpoints = [e for e in APP_ENDPOINTS if e != endp_name]
    endpoints_dict = {}
    for e in endpoints:
        if e != endp_name:
            endpoints_dict[e] = url_for(e)
    return endpoints_dict


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


@app.route('/list/city')
def list_city() -> str:
    return 'list/city'


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
