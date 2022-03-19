from flask import Flask, request

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return 'index'


@app.route('/login')
def login():
    return 'login'


@app.route('/logout')
def logout():
    return 'logout'


@app.route('/list/city')
def list_city():
    return 'list/city'


@app.route('/about')
def about():
    return 'about'


@app.route('/useragent')
def useragent():
    browser = request.user_agent.browser.capitalize()
    os = request.user_agent.platform.capitalize()

    return (f'<p>OS name: {os}</p>'
            f'<p>Browser: {browser}</p>')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
