from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import (
    db,
    Schedule,
    DataClassEncoder,
    Goal,
    ExamResult,
    ScheduleType,
    ExamType,
    Plan,
    PlanType,
)
import datetime
import json
import itertools

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard/get_schedules", methods=["GET"])
@login_required
def get_schedules():
    start = request.args.get('start', type=datetime.datetime.fromisoformat)
    end = request.args.get('end', type=datetime.datetime.fromisoformat)

    schedules = (
        db.session.query(Schedule)
        .filter(Schedule.start.between(start, end))
        .filter(Schedule.end.between(start, end))
        .filter_by(user_id=current_user.id)
        .order_by(Schedule.start)
        .all()
    )

    data = [
        {
            'start': schedule.start.timestamp() * 1000,
            'end': schedule.end.timestamp() * 1000,
            'title': schedule.description,
            'id': schedule.id,
            'className': f'item-{schedule.type_id}',
        }
        for schedule in schedules
    ]

    return data


@dashboard.route("/dashboard", methods=["GET"])
@login_required
def main():
    now = datetime.datetime.now()

    week_goals = (
        db.session.query(Goal)
        .filter(Goal.deadline > now)
        .filter_by(user_id=current_user.id)
        .all()
    )

    schedule_types = (
        db.session.query(ScheduleType).filter_by(user_id=current_user.id).all()
    )

    return render_template(
        "dashboard/main.html.jinja",
        week_goals=week_goals,
        schedule_types=schedule_types,
    )


@dashboard.route("/dashboard/edit_schedule", methods=["GET"])
@login_required
def edit_schedule():
    schedule_types = (
        db.session.query(ScheduleType).filter_by(user_id=current_user.id).all()
    )

    return render_template(
        "dashboard/edit_schedule.html.jinja", schedule_types=schedule_types
    )


@dashboard.route("/dashboard/edit_schedule/add", methods=["POST"])
@login_required
def add_schedule():
    start = datetime.datetime.fromtimestamp(int(request.form.get("start")) / 1000.0)
    end = datetime.datetime.fromtimestamp(int(request.form.get("end")) / 1000.0)
    description = request.form.get("description")
    type_id = int(request.form.get("type", 0))

    schedule = Schedule(
        start=start,
        end=end,
        description=description,
        type_id=type_id,
        user_id=current_user.id,
    )

    db.session.add(schedule)
    db.session.commit()

    return {"ok": True, "id": schedule.id}


@dashboard.route("/dashboard/edit_schedule/update", methods=["POST"])
@login_required
def update_schedule():
    id = int(request.form.get("id"))
    start = datetime.datetime.fromtimestamp(int(request.form.get("start")) / 1000.0)
    end = datetime.datetime.fromtimestamp(int(request.form.get("end")) / 1000.0)
    description = request.form.get("description")
    type_id = int(request.form.get("type", 0))

    db.session.query(Schedule).filter_by(user_id=current_user.id, id=id).update(
        {"start": start, "end": end, "description": description, "type_id": type_id}
    )

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_schedule/delete", methods=["POST"])
@login_required
def delete_schedule():
    id = int(request.form.get("id"))

    db.session.query(Schedule).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/goals", methods=["GET"])
@login_required
def goals():
    now = datetime.datetime.now()

    query = (
        db.session.query(Goal)
        .filter(Goal.deadline > now)
        .filter_by(user_id=current_user.id)
        .all()
    )

    return render_template("dashboard/goals.html.jinja", week_goals=query)


@dashboard.route("/dashboard/edit_goals/update", methods=["POST"])
@login_required
def update_goal():
    id = request.form.get("id").strip()
    description = request.form.get("description").strip()
    date = datetime.datetime.strptime(request.form.get("date"), "%Y/%m/%d %H:%M:%S")

    if id:
        db.session.query(Goal).filter_by(user_id=current_user.id, id=int(id)).update(
            {
                "deadline": date,
                "description": description,
            }
        )
    else:
        goal = Goal(deadline=date, description=description, user_id=current_user.id)
        db.session.add(goal)

    db.session.commit()
    return redirect(url_for("dashboard.goals"))


@dashboard.route("/dashboard/edit_goals/delete", methods=["POST"])
@login_required
def delete_goal():
    id = request.form.get("id", type=int)

    db.session.query(Goal).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return {'ok': True}


@dashboard.route("/dashboard/grade_calculator", methods=["GET"])
@login_required
def grade_calculator():
    return render_template("dashboard/grade_calculator.html.jinja")


@dashboard.route("/dashboard/graphs", methods=["GET"])
@login_required
def graphs():
    now = datetime.datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (
        start.replace(month=start.month + 1, day=1) - datetime.timedelta(seconds=1)
    ).replace(hour=23, minute=59, second=59)

    schedules = (
        db.session.query(Schedule)
        .filter(Schedule.start.between(start, end))
        .filter(Schedule.end.between(start, end))
        .filter_by(user_id=current_user.id)
        .order_by(Schedule.type_id, Schedule.start)
        .all()
    )

    user_types = db.session.query(ScheduleType).filter_by(user_id=current_user.id).all()

    data = {}

    for type_id, group in itertools.groupby(schedules, lambda x: x.type_id):
        if not type_id in data:
            data[type_id] = []

        type = None
        for i in user_types:
            if i.id == type_id:
                type = i

        per_day_total = {}

        for day, day_schedules in itertools.groupby(
            group, lambda x: x.start.strftime("%Y/%m/%d")
        ):
            total = 0
            for schedule in day_schedules:
                duration: datetime.timedelta = schedule.end - schedule.start
                total += duration.total_seconds() / 3600
            per_day_total[day] = total

        data[type_id].append({"type": type, "per_day_total": per_day_total})

    return render_template(
        "dashboard/graphs.html.jinja", data=json.dumps(data, cls=DataClassEncoder)
    )


@dashboard.route("/dashboard/exam_results", methods=["GET"])
@login_required
def exam_results():
    results = (
        db.session.query(ExamResult)
        .filter_by(user_id=current_user.id)
        .order_by(ExamResult.type_id, ExamResult.date)
        .all()
    )

    exam_types = db.session.query(ExamType).filter_by(user_id=current_user.id).all()

    data = {}

    for type_id, group in itertools.groupby(results, lambda x: x.type_id):
        if not type_id in data:
            data[type_id] = []

        type = None
        for i in exam_types:
            if i.id == type_id:
                type = i

        data[type_id].append({"type": type, "result": list(group)})

    return render_template(
        "dashboard/exam_results.html.jinja",
        data=json.dumps(data, cls=DataClassEncoder),
        exam_types=exam_types,
    )


@dashboard.route("/dashboard/edit_exam_results/add", methods=["POST"])
@login_required
def add_exam_result():
    type_id = int(request.form.get("result-type", 0))

    date = datetime.datetime.strptime(request.form.get("date"), "%Y/%m/%d")
    value = request.form.get("result-value")
    description = request.form.get("result-description")

    result = ExamResult(
        date=date,
        type_id=type_id,
        value=value,
        user_id=current_user.id,
        description=description,
    )
    db.session.add(result)

    db.session.commit()

    return redirect(url_for("dashboard.exam_results"))


@dashboard.route("/dashboard/edit_exam_results/delete", methods=["GET"])
@login_required
def delete_exam_result():
    id = request.args.get("id").strip()

    db.session.query(ExamResult).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return redirect(url_for("dashboard.exam_results"))


@dashboard.route("/dashboard/settings", methods=["GET"])
@login_required
def settings():
    return render_template("dashboard/settings.html.jinja")


import requests
import datetime
from ics import Calendar, Timezone
from ics.timespan import NormalizationAction


@dashboard.route("/dashboard/import_ics", methods=["POST", "GET"])
@login_required
def import_ics():
    url = request.form.get("url")
    if not url:
        url = request.args.get("url")

    try:
        text = requests.get(url).text
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": e.strerror}

    calendar = Calendar(text)

    calendar.normalize(
        Timezone.from_tzinfo(datetime.datetime.now().astimezone().tzinfo),
        normalize_floating=NormalizationAction.REPLACE,
        normalize_with_tz=NormalizationAction.CONVERT,
    )

    default_type = db.session.query(ScheduleType).filter_by(user_id=current_user.id, description="unknown").one()

    events = []
    for event in calendar.events:
        desc = event.summary or "NO DESC"
        events.append(
            Schedule(
                start=event.begin,
                end=event.end,
                description=desc,
                type_id=default_type.id,
                user_id=current_user.id,
            )
        )

    db.session.bulk_save_objects(events)
    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/weekly_plans", methods=["GET"])
@login_required
def weekly_plans():
    weekday_order = {
        5: 0,  # Saturday -> 0
        6: 1,  # Sunday -> 1
        0: 2,  # Monday -> 2
        1: 3,  # Tuesday -> 3
        2: 4,  # Wednesday -> 4
        3: 5,  # Thursday -> 5
        4: 6,  # Friday -> 6
    }

    now = datetime.datetime.now()

    last_saturday = now - datetime.timedelta(days=weekday_order[now.weekday()])
    last_saturday = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)

    next_friday = last_saturday + datetime.timedelta(days=6)
    next_friday = next_friday.replace(hour=23, minute=59, second=59)

    week_plans = (
        db.session.query(Plan)
        .filter(Plan.date >= last_saturday)
        .filter(Plan.date <= next_friday)
        .filter_by(user_id=current_user.id)
        .all()
    )

    plan_types = db.session.query(PlanType).filter_by(user_id=current_user.id).all()

    type_id_to_index = {ptype.id: index for index, ptype in enumerate(plan_types)}
    index_to_type_id = {index: ptype.id for index, ptype in enumerate(plan_types)}

    num_plan_types = len(plan_types)
    week_matrix = [
        [
            (last_saturday + datetime.timedelta(days=i)).strftime("%Y/%m/%d"),
            [
                [index_to_type_id[plan_type], None]
                for plan_type in range(num_plan_types)
            ],
        ]
        for i in range(7)
    ]

    for plan in week_plans:
        day_of_week = plan.date.weekday()
        day_index = weekday_order[day_of_week]
        type_index = type_id_to_index[plan.type_id]
        week_matrix[day_index][1][type_index][1] = plan

    return render_template(
        "dashboard/weekly_plans.html.jinja",
        week_matrix=week_matrix,
        plan_types=plan_types,
    )


@dashboard.route("/dashboard/edit_plan/update", methods=["POST"])
@login_required
def update_plan():
    id = int(request.form.get("id"))
    description = request.form.get("description")

    db.session.query(Plan).filter_by(user_id=current_user.id, id=id).update(
        {
            "description": description,
        }
    )

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_plan/add", methods=["POST"])
@login_required
def add_plan():
    description = request.form.get("description")
    date = datetime.datetime.strptime(request.form.get("date"), "%Y/%m/%d")
    type_id = int(request.form.get("type_id"))

    plan = Plan(
        description=description, date=date, type_id=type_id, user_id=current_user.id
    )

    db.session.add(plan)
    db.session.commit()

    return {"ok": True, "id": plan.id}


@dashboard.route("/dashboard/types", methods=["GET"])
@login_required
def types():
    schedule_types = (
        db.session.query(ScheduleType)
        .filter_by(user_id=current_user.id)
        .filter(ScheduleType.description != "unknown")
        .all()
    )

    exam_types = (
        db.session.query(ExamType)
        .filter_by(user_id=current_user.id)
        .all()
    )

    plan_types = (
        db.session.query(PlanType)
        .filter_by(user_id=current_user.id)
        .all()
    )

    return render_template(
        "dashboard/types.html.jinja",
        schedule_types=schedule_types,
        exam_types=exam_types,
        plan_types=plan_types,
    )


@dashboard.route("/dashboard/edit_schedule_type/update", methods=["POST"])
@login_required
def update_schedule_type():
    id = int(request.form.get("id"))
    description = request.form.get("description")
    background_color_hex = request.form.get("background_color_hex")
    text_color_hex = request.form.get("text_color_hex")

    db.session.query(ScheduleType).filter_by(user_id=current_user.id, id=id).update(
        {
            "description": description,
            "background_color_hex": background_color_hex,
            "text_color_hex": text_color_hex,
        }
    )

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_schedule_type/delete", methods=["POST"])
@login_required
def delete_schedule_type():
    id = int(request.form.get("id"))

    default_type = db.session.query(ScheduleType).filter_by(user_id=current_user.id, description="unknown").one()

    db.session.query(Schedule).filter_by(type_id=id).update(
        {"type_id": default_type.id}
    )

    db.session.query(ScheduleType).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_schedule_type/add", methods=["POST"])
@login_required
def add_schedule_type():
    description = request.form.get("description")
    background_color_hex = request.form.get("background_color_hex")
    text_color_hex = request.form.get("text_color_hex")

    schedule_type = ScheduleType(
        description=description,
        background_color_hex=background_color_hex,
        text_color_hex=text_color_hex,
        user_id=current_user.id,
    )

    db.session.add(schedule_type)
    db.session.commit()

    return {"ok": True, "id": schedule_type.id}


@dashboard.route("/dashboard/edit_plan_type/update", methods=["POST"])
@login_required
def update_plan_type():
    id = int(request.form.get("id"))
    description = request.form.get("description")
    background_color_hex = request.form.get("background_color_hex")
    text_color_hex = request.form.get("text_color_hex")

    db.session.query(PlanType).filter_by(user_id=current_user.id, id=id).update(
        {
            "description": description,
            "background_color_hex": background_color_hex,
            "text_color_hex": text_color_hex,
        }
    )

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_plan_type/delete", methods=["POST"])
@login_required
def delete_plan_type():
    id = int(request.form.get("id"))

    # We can't merge plans now
    db.session.query(Plan).filter_by(user_id=current_user.id, type_id=id).delete()
    db.session.query(PlanType).filter_by(user_id=current_user.id, id=id).delete()

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_plan_type/add", methods=["POST"])
@login_required
def add_plan_type():
    description = request.form.get("description")
    background_color_hex = request.form.get("background_color_hex")
    text_color_hex = request.form.get("text_color_hex")

    plan_type = PlanType(
        description=description,
        background_color_hex=background_color_hex,
        text_color_hex=text_color_hex,
        user_id=current_user.id,
    )

    db.session.add(plan_type)
    db.session.commit()

    return {"ok": True, "id": plan_type.id}


@dashboard.route("/dashboard/edit_exam_type/update", methods=["POST"])
@login_required
def update_exam_type():
    id = int(request.form.get("id"))
    description = request.form.get("description")
    color_hex = request.form.get("color_hex")

    db.session.query(ExamType).filter_by(user_id=current_user.id, id=id).update(
        {
            "description": description,
            "color_hex": color_hex,
        }
    )

    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_exam_type/delete", methods=["POST"])
@login_required
def delete_exam_type():
    id = int(request.form.get("id"))

    db.session.query(ExamResult).filter_by(user_id=current_user.id, type_id=id).delete()
    db.session.query(ExamType).filter_by(user_id=current_user.id, id=id).delete()
    db.session.commit()

    return {"ok": True}


@dashboard.route("/dashboard/edit_exam_type/add", methods=["POST"])
@login_required
def add_exam_type():
    description = request.form.get("description")
    color_hex = request.form.get("color_hex")

    exam_type = ExamType(
        description=description,
        color_hex=color_hex,
        user_id=current_user.id,
    )

    db.session.add(exam_type)
    db.session.commit()

    return {"ok": True, "id": exam_type.id}

import io
import json
import os

import random
import random

def generate_random_color():
    temperature = random.choice(["warm", "neutral", "cool"])

    if temperature == "warm":
        # Warm colors (orange, red, yellow)
        r = random.randint(150, 255)
        g = random.randint(50, 150)
        b = random.randint(0, 50)
    elif temperature == "neutral":
        # Neutral colors (green, blue, purple)
        r = random.randint(50, 150)
        g = random.randint(50, 150)
        b = random.randint(50, 150)
    else:
        # Cool colors (blue, purple, pink)
        r = random.randint(0, 50)
        g = random.randint(50, 150)
        b = random.randint(150, 255)

    r = max(0, min(255, r + random.randint(-20, 20)))
    g = max(0, min(255, g + random.randint(-20, 20)))
    b = max(0, min(255, b + random.randint(-20, 20)))

    return f"#{r:02x}{g:02x}{b:02x}"

def calculate_contrast_color(color):
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255

    if luminance > 0.5:
        return "#0c0c0c"
    else:
        return "#ededed"

@dashboard.route("/dashboard/init_lessons", methods=["GET"])
@login_required
def init_lessons():
    grade = request.args.get('grade', type=str, default="10")
    major = request.args.get('major', type=str, default='math')

    data = {}
    with io.open(os.path.join(current_app.root_path, 'static', 'lessons.json'), encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for row in data[grade][major]:
        bg_color = generate_random_color()
        text_color = calculate_contrast_color(bg_color)

        rows.append(PlanType(
            description=row,
            background_color_hex=bg_color,
            text_color_hex=text_color,
            user_id=current_user.id,
        ))

        rows.append(ExamType(
            description=row,
            user_id=current_user.id,
            color_hex=bg_color
        ))

        rows.append(ScheduleType(
            description=row,
            background_color_hex=bg_color,
            text_color_hex=text_color,
            user_id=current_user.id,
        ))
    
    db.session.bulk_save_objects(rows)
    db.session.commit()

    return {"ok": True}