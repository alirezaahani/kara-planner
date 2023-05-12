from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash
from models import User, db
from flask_login import LoginManager, login_user


login = Blueprint('login', __name__)
login_manager = LoginManager()
login_manager.init_app(login)

@login.route('/login', methods=['GET'])
def show():
    return render_template('login.html')

LOGIN_FIELDS = {'username', 'password'}

@login.route('/login', methods=['POST'])
def process():
    response_validation = tuple(filter(lambda x: x in LOGIN_FIELDS, request.form.keys()))
    if len(response_validation) < len(LOGIN_FIELDS):
        flash('برخی ورودی ها پر نشده اند', 'danger')
        return redirect(url_for('login.show')) 
    
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('رمز یا نام کاربری به درستی وارد نشده است.', 'danger')
        return redirect(url_for('login.show')) 
    
    if not check_password_hash(user.password, password):
        flash('رمز یا نام کاربری به درستی وارد نشده است.', 'danger')
        return redirect(url_for('login.show')) 

    login_user(user)
    flash(f'سلام {user.name}، شما با موفقیت وارد شدید!', 'success')
    return redirect(url_for('dashboard.main')) 

