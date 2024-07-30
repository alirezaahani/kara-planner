from flask import Flask
from index import index, support
from login import login
from register import register
from dashboard import dashboard
from logout import logout
from captcha import captcha_handle
from flask_login import LoginManager

from flask import Flask
from models import db, User
from flask_minify import Minify


app = Flask(__name__)
Minify(app=app, html=True, js=True, cssless=True)

app.config.from_mapping(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI='sqlite:///kara.sqlite',
)

app.config["TEMPLATES_AUTO_RELOAD"] = True

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()

app = captcha_handle.init_app(app)
app.register_blueprint(index)
app.register_blueprint(login)
app.register_blueprint(register)
app.register_blueprint(support)
app.register_blueprint(dashboard)
app.register_blueprint(logout)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))