from flask import Blueprint, url_for, redirect, flash
from flask_login import LoginManager, login_required, logout_user

logout = Blueprint('logout', __name__)
login_manager = LoginManager()
login_manager.init_app(logout)

@logout.route('/logout')
@login_required
def process():
    logout_user()
    flash('شما با موفقیت خارج شدید', 'success')
    return redirect(url_for('login.show'))