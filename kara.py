from flask import Flask
from index import index, support
from auth import auth
from dashboard import dashboard
from captcha import captcha_handle
from flask_login import LoginManager
from flask import Flask
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login_show"
login_manager.login_message = "لطفا ابتدا وارد شوید."
login_manager.login_message_category = 'danger'
login_manager.needs_refresh_message = "لطفا دوباره وارد شوید."
login_manager.needs_refresh_message_category = 'danger'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

app = captcha_handle.init_app(app)
app.register_blueprint(index)
app.register_blueprint(auth)
app.register_blueprint(support)
app.register_blueprint(dashboard)

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)