from flask import Blueprint, render_template, request, redirect, url_for, flash
from captcha import captcha_handle
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db, ScheduleType, ExamType, PlanType
from flask_login import login_required, logout_user, login_user, current_user
import sqlalchemy

import re
import string

auth = Blueprint('auth', __name__)

def password_check(password: str):
    ascii_error = not password.isascii()
    space_error = any([x in password for x in string.whitespace])
    length_error = len(password) < 8
    digit_error = re.search(r"\d", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    lowercase_error = re.search(r"[a-z]", password) is None
    symbol_error = re.search(r"[!#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) is None
    password_ok = not ( ascii_error or space_error or length_error or digit_error or uppercase_error or lowercase_error or symbol_error )

    return password_ok

@auth.route("/register", methods=['GET'])
def register_show():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))

    captcha = captcha_handle.create(length=5)
    return render_template('auth/register.html.jinja', captcha=captcha)

REGISTER_FIELDS = {'username', 'password', 'passwordRep', 'name', 'captcha-hash', 'captcha-text'}

@auth.route("/register", methods=['POST'])
def register_process():
    response_validation = tuple(filter(lambda x: x in REGISTER_FIELDS and x, request.form.keys()))
    if len(response_validation) < len(REGISTER_FIELDS):
        flash('برخی ورودی ها پر نشده اند.', 'danger')
        return redirect(url_for('auth.register_show')) 
 
    c_hash = request.form.get('captcha-hash')
    c_text = request.form.get('captcha-text')
    
    if not captcha_handle.verify(c_text, c_hash):
        flash('کد امنیتی به درستی وارد نشده است', 'danger')
        return redirect(url_for('auth.register_show')) 
    if request.form.get('password') != request.form.get('passwordRep'):
        flash('رمز عبور به درستی تکرار نشده است.', 'danger')
        return redirect(url_for('auth.register_show')) 
    
    if not password_check(request.form.get('password')):
        flash('رمز عبور باید شرایط ذکر شده را داشته باشد.', 'danger')
        return redirect(url_for('auth.register_show')) 
    

    hashed_password = generate_password_hash(request.form['password'], method='scrypt')
    
    try: 
        user = User(username=request.form['username'], 
                        password=hashed_password,
                        name=request.form['name'])
        
        db.session.add(user)
        db.session.commit()

        schedule_types = [
            ScheduleType(description='unknown', background_color_hex='#222', text_color_hex='#fff', user_id=user.id),
            ScheduleType(description='sleep', background_color_hex='#666DCB', text_color_hex='#fff', user_id=user.id),
            ScheduleType(description='study', background_color_hex='#3ABBC9', text_color_hex='#222', user_id=user.id),
            ScheduleType(description='work', background_color_hex='#9BCA3E', text_color_hex='#222', user_id=user.id),
            ScheduleType(description='break', background_color_hex='#FEEB51', text_color_hex='#fff', user_id=user.id),
            ScheduleType(description='exercise', background_color_hex='#FF8C00', text_color_hex='#222', user_id=user.id),
            ScheduleType(description='other', background_color_hex='#D2042D', text_color_hex='#fff', user_id=user.id)
        ]

        plan_types = [
            PlanType(description='unknown', background_color_hex='#222', text_color_hex='#fff', user_id=user.id),
            PlanType(description='sleep', background_color_hex='#666DCB', text_color_hex='#fff', user_id=user.id),
            PlanType(description='study', background_color_hex='#3ABBC9', text_color_hex='#222', user_id=user.id),
            PlanType(description='work', background_color_hex='#9BCA3E', text_color_hex='#222', user_id=user.id),
            PlanType(description='break', background_color_hex='#FEEB51', text_color_hex='#fff', user_id=user.id),
            PlanType(description='exercise', background_color_hex='#FF8C00', text_color_hex='#222', user_id=user.id),
            PlanType(description='other', background_color_hex='#D2042D', text_color_hex='#fff', user_id=user.id)
        ]

        exam_types = [
            ExamType(description='test', color_hex='#666DCB', user_id=user.id),
            ExamType(description='quiz', color_hex='#3ABBC9', user_id=user.id),
            ExamType(description='essay', color_hex='#9BCA3E', user_id=user.id)
        ]

        db.session.bulk_save_objects(schedule_types)
        db.session.bulk_save_objects(exam_types)
        db.session.bulk_save_objects(plan_types)

        db.session.commit()

    except sqlalchemy.exc.IntegrityError:
        flash('نام کاربری تکراری است.', 'danger')
        return redirect(url_for('auth.register_show')) 

    flash('ثبت نام با موفقیت انجام شد.', 'success')
    return redirect(url_for('auth.login_show'))

@auth.route('/login', methods=['GET'])
def login_show():
    if current_user.is_authenticated:
        return redirect(request.form.get('next', '') or url_for('dashboard.main'))

    return render_template('auth/login.html.jinja')

LOGIN_FIELDS = {'username', 'password'}

@auth.route('/login', methods=['POST'])
def login_process():
    response_validation = tuple(filter(lambda x: x in LOGIN_FIELDS and x, request.form.keys()))
    if len(response_validation) < len(LOGIN_FIELDS):
        flash('برخی ورودی ها پر نشده اند', 'danger')
        return redirect(url_for('auth.login_show')) 
    
    username = request.form.get('username')
    password = request.form.get('password')
    remember_me = request.form.get('remember', False) == "True"

    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('رمز یا نام کاربری به درستی وارد نشده است.', 'danger')
        return redirect(url_for('auth.login_show')) 
    
    if not check_password_hash(user.password, password):
        flash('رمز یا نام کاربری به درستی وارد نشده است.', 'danger')
        return redirect(url_for('auth.login_show')) 

    login_user(user, remember=remember_me)
    flash(f'سلام {user.name}، شما با موفقیت وارد شدید!', 'success')

    return redirect(request.form.get('next', '') or url_for('dashboard.main')) 

@auth.route('/logout')
@login_required
def logout_process():
    logout_user()
    flash('شما با موفقیت خارج شدید', 'success')
    return redirect(url_for('auth.login_show'))

CHANGE_AUTH_FIELDS = {'password', 'newPassword', 'newPasswordRep'}

@auth.route('/change_auth_process', methods=['POST'])
@login_required
def change_auth_process():
    response_validation = tuple(filter(lambda x: x in CHANGE_AUTH_FIELDS and x, request.form.keys()))
    
    if len(response_validation) < len(CHANGE_AUTH_FIELDS):
        flash('برخی ورودی ها پر نشده اند', 'danger')
        return redirect(url_for('dashboard.settings'))

    if not check_password_hash(current_user.password, request.form.get('password')):
        flash('رمز عبور فعلی به درستی وارد نشده است.', 'danger')
        return redirect(url_for('dashboard.settings'))

    if request.form.get('newPassword') != request.form.get('newPasswordRep'):
        flash('رمز عبور جدید به درستی تکرار نشده است.', 'danger')
        return redirect(url_for('dashboard.settings'))

    if not password_check(request.form.get('newPassword')):
        flash('رمز عبور باید شرایط ذکر شده را داشته باشد.', 'danger')
        return redirect(url_for('dashboard.settings')) 
    
    hashed_password = generate_password_hash(request.form['newPassword'], method='scrypt')

    db.session.query(User).filter_by(id=current_user.id).update({'password': hashed_password})
    db.session.commit()

    flash(f'رمز عبور با موفقیت تغییر یافت!', 'success')
    return redirect(url_for('dashboard.settings'))



CHANGE_NAME_FIELDS = {'password', 'name'}

@auth.route('/change_name_process', methods=['POST'])
@login_required
def change_name_process():
    response_validation = tuple(filter(lambda x: x in CHANGE_NAME_FIELDS and x, request.form.keys()))
    
    if len(response_validation) < len(CHANGE_NAME_FIELDS):
        flash('برخی ورودی ها پر نشده اند', 'danger')
        return redirect(url_for('dashboard.settings'))

    if not check_password_hash(current_user.password, request.form.get('password')):
        flash('رمز عبور فعلی به درستی وارد نشده است.', 'danger')
        return redirect(url_for('dashboard.settings'))
    
    db.session.query(User).filter_by(id=current_user.id).update({'name': request.form.get('name')})
    db.session.commit()

    flash(f'سلام {current_user.name}. نام نمایشی با موفقیت تغییر یافت!', 'success')
    return redirect(url_for('dashboard.settings'))