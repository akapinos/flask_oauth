from flask import Flask

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
    return 'useragent'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
