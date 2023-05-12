from flask import Blueprint, render_template, request, redirect, url_for, flash
from captcha import captcha_handle
from werkzeug.security import generate_password_hash
from models import User, db
import sqlalchemy

register = Blueprint('register', __name__)


@register.route("/register", methods=['GET'])
def show():
    captcha = captcha_handle.create(length=4)
    return render_template('register.html', captcha=captcha)


REGISTER_FIELDS = {'username', 'password', 'email', 'name', 'captcha-hash', 'captcha-text'}

@register.route("/register", methods=['POST'])
def process():
    response_validation = tuple(filter(lambda x: x in REGISTER_FIELDS, request.form.keys()))
    if len(response_validation) < len(REGISTER_FIELDS):
        flash('برخی ورودی ها پر نشده اند', 'danger')
        return redirect(url_for('register.show')) 

    c_hash = request.form.get('captcha-hash')
    c_text = request.form.get('captcha-text')
    
    if not captcha_handle.verify(c_text, c_hash):
        flash('کد امنیتی به درستی وارد نشده است', 'danger')
        return redirect(url_for('register.show')) 

    hashed_password = generate_password_hash(request.form['password'], method='sha256')
    
    try: 
        user = User(username=request.form['username'], 
                        email=request.form['email'],
                        password=hashed_password,
                        name=request.form['name'])
        
        db.session.add(user)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        flash('نام کاربری یا ایمیل تکراری است', 'danger')
        return redirect(url_for('register.show')) 

    flash('ثبت نام با موفقیت انجام شد', 'success')
    return redirect(url_for('register.show'))
