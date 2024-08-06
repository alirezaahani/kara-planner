from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Schedule, DataClassEncoder, Goal, ExamResult, ExamEnum, ScheduleType
import datetime
import json
import itertools

from sqlalchemy.sql import functions

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard', methods=['GET'])
@login_required
def main():
    now = datetime.datetime.now()
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    next_month = first + datetime.timedelta(days=32)

    query = db.session.query(Schedule) \
            .filter(Schedule.start.between(last_month, next_month)) \
            .filter(Schedule.end.between(last_month, next_month)) \
            .filter_by(user_id=current_user.id).all()
    
    week_goals = db.session.query(Goal) \
        .filter(Goal.deadline > now) \
        .filter_by(user_id=current_user.id).all()
    
    schedule_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()

    return render_template('dashboard/main.html', today_schedules=json.dumps(query, cls=DataClassEncoder), week_goals=week_goals, schedule_types=schedule_types)

@dashboard.route('/dashboard/edit', methods=['GET'])
@login_required
def edit_today():
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    next_month = first + datetime.timedelta(days=32)

    query = db.session.query(Schedule) \
            .filter(Schedule.start.between(last_month, next_month)) \
            .filter(Schedule.end.between(last_month, next_month)) \
            .filter_by(user_id=current_user.id).all()
    
    schedule_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()

    return render_template('dashboard/edit.html', today_schedules=json.dumps(query, cls=DataClassEncoder), schedule_types=schedule_types)

@dashboard.route('/dashboard/edit/add', methods=['POST'])
@login_required
def add_schedule():
    start = datetime.datetime.fromtimestamp(int(request.form.get('start')) / 1000.0)
    end =  datetime.datetime.fromtimestamp(int(request.form.get('end')) / 1000.0)
    description = request.form.get('description')

    type = db.session.query(ScheduleType) \
            .filter(ScheduleType.id == int(request.form.get('type', 0))) \
            .filter_by(user_id=current_user.id).one()
    
    schedule = Schedule(start=start, 
                        end=end, 
                        description=description,
                        type_id=type.id,
                        user_id=current_user.id)
    
    db.session.add(schedule)
    db.session.commit()
    
    return {'id': schedule.id}

@dashboard.route('/dashboard/edit/update', methods=['POST'])
@login_required
def update_schedule():
    id = int(request.form.get('id'))
    start = datetime.datetime.fromtimestamp(int(request.form.get('start')) / 1000.0)
    end =  datetime.datetime.fromtimestamp(int(request.form.get('end')) / 1000.0)
    description = request.form.get('description')

    type = db.session.query(ScheduleType) \
        .filter(ScheduleType.id == int(request.form.get('type', 0))) \
        .filter_by(user_id=current_user.id).one()

    db.session.query(Schedule).filter_by(user_id=current_user.id, id=id).update({
        'start': start,
        'end': end,
        'description': description,
        'type_id': type.id    
    })

    db.session.commit()
    
    return {'ok': True}


@dashboard.route('/dashboard/edit/delete', methods=['POST'])
@login_required
def delete_schedule():
    id = int(request.form.get('id'))

    db.session.query(Schedule).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()
    
    return {'ok': True}


@dashboard.route('/dashboard/goal', methods=['GET'])
@login_required
def edit_goal():
    now = datetime.datetime.now()

    query = db.session.query(Goal) \
            .filter(Goal.deadline > now) \
            .filter_by(user_id=current_user.id).all()

    return render_template('dashboard/goal.html', week_goals=query)

@dashboard.route('/dashboard/update_add_goal', methods=['POST'])
@login_required
def update_add_goal():
    id = (request.form.get('id').strip())
    description = request.form.get('description').strip()
    date = datetime.datetime.strptime(request.form.get('date'), '%Y/%m/%d %H:%M:%S')

    if id:
        db.session.query(Goal).filter_by(user_id=current_user.id, id=int(id)).update({
            'deadline': date,
            'description': description,
        })
    else:
        goal = Goal(deadline=date, description=description, user_id=current_user.id)
        db.session.add(goal)

    db.session.commit()
    return redirect(url_for('dashboard.edit_goal'))

@dashboard.route('/dashboard/delete_goal', methods=['GET'])
@login_required
def delete_goal():
    id = (request.args.get('id').strip())

    db.session.query(Goal).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return redirect(url_for('dashboard.edit_goal'))


@dashboard.route('/dashboard/percentage', methods=['GET'])
@login_required
def percentage():
    return render_template('dashboard/percentage.html')

@dashboard.route('/dashboard/graphs', methods=['GET'])
@login_required
def graphs():
    now = datetime.datetime.now()
    
    start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = (start + datetime.timedelta(days=6)).replace(hour=23, minute=59, second=59)

    schedules = db.session.query(Schedule) \
            .filter(Schedule.start.between(start, end)) \
            .filter(Schedule.end.between(start, end)) \
            .filter_by(user_id=current_user.id).all()
    
    user_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()
    
    data = {}

    for type_id, group in itertools.groupby(schedules, lambda x: x.type_id):
        if not type_id in data:
            data[type_id] = []
        
        type = user_types[type_id]

        per_day_total = {}
        
        for day, day_schedules in itertools.groupby(group, lambda x: x.start.strftime('%Y/%m/%d')):
            total = 0
            for schedule in day_schedules:
                duration: datetime.timedelta = schedule.end - schedule.start
                total += (duration.total_seconds() / 3600)
            per_day_total[day] = total

        data[type_id].append({
            'type': type,
            'per_day_total': per_day_total
        })
        
    return render_template('dashboard/graphs.html', data=json.dumps(data, cls=DataClassEncoder))



@dashboard.route('/dashboard/exam_results', methods=['GET'])
@login_required
def exam_results():
    query = db.session.query(ExamResult).filter_by(user_id=current_user.id).order_by(ExamResult.type, ExamResult.date).all()

    grouped_results = {}
    grouped_labels = {}
    grouped_values = {}
    grouped_descriptions = {}

    for k, g in itertools.groupby(query, lambda x: x.type):
        grouped_results[k] = []
        grouped_labels[k] = []
        grouped_values[k] = []
        grouped_descriptions[k] = []

        for i in g:
            grouped_results[k].append(i)
            grouped_labels[k].append(datetime.datetime.combine(i.date, datetime.datetime.min.time()).timestamp() * 1000)
            grouped_values[k].append(i.value)
            grouped_descriptions[k].append(i.description)
            

    return render_template('dashboard/exam-results.html', grouped_results=grouped_results, grouped_values=grouped_values, grouped_labels=grouped_labels, grouped_descriptions=grouped_descriptions)


@dashboard.route('/dashboard/add_exam_result', methods=['POST'])
@login_required
def add_exam_result():

    type = ExamEnum[request.form.get('result-type')]
    date = datetime.datetime.strptime(request.form.get('date'), '%Y/%m/%d')
    value = request.form.get('result-value')
    description = request.form.get('result-description')

    result = ExamResult(date=date, type=type, value=value, user_id=current_user.id, description=description)
    db.session.add(result)

    db.session.commit()

    return redirect(url_for('dashboard.exam_results'))

@dashboard.route('/dashboard/delete_exam_result', methods=['GET'])
@login_required
def delete_exam_result():
    id = (request.args.get('id').strip())

    db.session.query(ExamResult).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return redirect(url_for('dashboard.exam_results'))


@dashboard.route('/dashboard/change_info', methods=['GET'])
@login_required
def change_info():

    return render_template('dashboard/change-info.html')