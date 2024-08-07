from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Schedule, DataClassEncoder, Goal, ExamResult, ScheduleType, ExamType
import datetime
import json
import itertools

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/dashboard/get_schedules', methods=['GET'])
@login_required
def get_schedules():
    today = datetime.date.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    next_month = first + datetime.timedelta(days=32)

    query = db.session.query(Schedule) \
            .filter(Schedule.start.between(last_month, next_month)) \
            .filter(Schedule.end.between(last_month, next_month)) \
            .filter_by(user_id=current_user.id) \
            .order_by(Schedule.start).all()

    return json.dumps(query, cls=DataClassEncoder)

@dashboard.route('/dashboard', methods=['GET'])
@login_required
def main():
    now = datetime.datetime.now()
    
    week_goals = db.session.query(Goal) \
        .filter(Goal.deadline > now) \
        .filter_by(user_id=current_user.id).all()
    
    schedule_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()

    return render_template('dashboard/main.html', week_goals=week_goals, schedule_types=schedule_types)

@dashboard.route('/dashboard/edit', methods=['GET'])
@login_required
def edit_today():
    schedule_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()

    return render_template('dashboard/edit.html', schedule_types=schedule_types)

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
            .filter_by(user_id=current_user.id) \
            .order_by(Schedule.type_id, Schedule.start).all()
    
    user_types = db.session.query(ScheduleType) \
        .filter_by(user_id=current_user.id).all()
    
    data = {}

    for type_id, group in itertools.groupby(schedules, lambda x: x.type_id):
        if not type_id in data:
            data[type_id] = []
        
        type = None
        for i in user_types:
            if i.id == type_id:
                type = i

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
    results = db.session.query(ExamResult) \
        .filter_by(user_id=current_user.id) \
        .order_by(ExamResult.type_id, ExamResult.date).all()
    
    exam_types = db.session.query(ExamType) \
        .filter_by(user_id=current_user.id).all()
    
    data = {}

    for type_id, group in itertools.groupby(results, lambda x: x.type_id):
        if not type_id in data:
            data[type_id] = []
        
        type = None
        for i in exam_types:
            if i.id == type_id:
                type = i

        data[type_id].append({
            'type': type,
            'result': list(group)
        })

    return render_template('dashboard/exam-results.html', data=json.dumps(data, cls=DataClassEncoder), exam_types=exam_types)


@dashboard.route('/dashboard/add_exam_result', methods=['POST'])
@login_required
def add_exam_result():
    type = db.session.query(ExamType) \
        .filter(ExamType.id == int(request.form.get('result-type', 0))) \
        .filter_by(user_id=current_user.id).one()

    date = datetime.datetime.strptime(request.form.get('date'), '%Y/%m/%d')
    value = request.form.get('result-value')
    description = request.form.get('result-description')

    result = ExamResult(date=date, type_id=type.id, value=value, user_id=current_user.id, description=description)
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


import requests
import icalendar
import datetime

@dashboard.route('/dashboard/import_ics', methods=['POST', 'GET'])
@login_required
def import_ics():
    url = request.form.get('url')
    if not url:
        url = request.args.get('url')
    
    print(url)

    try:
        text = requests.get(url).text
    except requests.exceptions.RequestException as e:
        return { 'ok': False, 'error': e.strerror }
    
    calendar = icalendar.Calendar.from_ical(text)

    events = []
    for event in calendar.walk('VEVENT'):
        start = icalendar.vDDDTypes.from_ical(event.get('DTSTART'), timezone='Asia/Tehran')
        end = icalendar.vDDDTypes.from_ical(event.get('DTEND'), timezone='Asia/Tehran')
        if not isinstance(start, datetime.datetime) or not isinstance(end, datetime.datetime):
            continue
        text = event.get('SUMMARY') or "NO DESC"
        events.append(Schedule(start=start, end=end, description=text, type_id=1, user_id=current_user.id))

    db.session.bulk_save_objects(events)
    db.session.commit()
    
    return {'ok': True}
