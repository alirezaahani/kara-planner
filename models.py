from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from dataclasses import dataclass
from datetime import datetime, date
from datetime import timedelta
import enum

db = SQLAlchemy()

import dataclasses, json

class DataClassEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if isinstance(o, (datetime, date)):
                return o.timestamp()
            if isinstance(o, enum.Enum):
                return o.name
            return super().default(o)

@dataclass
class User(UserMixin, db.Model):
    id: int
    username: str
    password: str
    name: str

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)

class ScheduleEnum(enum.Enum): 
    SLEEP = 'خواب'
    STUDY = 'درس خواندن'
    WORK = 'کار کردن'
    BREAK = 'استراحت'
    EXERCISE = 'ورزش'
    OTHER = 'سایر'

@dataclass
class Schedule(db.Model):
    id: int
    start: datetime
    end: datetime
    description: str
    type: ScheduleEnum

    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    description = db.Column(db.String)
    type = db.Column(db.Enum(ScheduleEnum))
    
    user_id = db.Column(db.ForeignKey(User.id))
    user = db.relationship(User)

@dataclass
class Goal(db.Model):
    id: int
    deadline: datetime
    description: str

    id = db.Column(db.Integer, primary_key=True)
    deadline = db.Column(db.DateTime)
    description = db.Column(db.String)
    
    user_id = db.Column(db.ForeignKey(User.id))
    user = db.relationship(User)


class ExamEnum(enum.Enum): 
    TEST = 'چهار گزینه ای'
    QUIZ = 'آزمونک'
    ESSAY = 'تشریحی'
    OTHER = 'سایر'

@dataclass
class ExamResult(db.Model):
    id: int
    date: date
    type: ExamEnum
    value: float
    description: str

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    type = db.Column(db.Enum(ExamEnum))
    value = db.Column(db.Float)
    description = db.Column(db.String)
    
    user_id = db.Column(db.ForeignKey(User.id))
    user = db.relationship(User)


@dataclass
class ScheduleStructure(db.Model):
    id: int
    repeats: timedelta
    starting: datetime
    ending: datetime
    description: str
    type: ScheduleEnum

    id = db.Column(db.Integer, primary_key=True)
    repeats = db.Column(db.Interval)
    starting = db.Column(db.DateTime)
    ending = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String)
    type = db.Column(db.Enum(ScheduleEnum))
    
    user_id = db.Column(db.ForeignKey(User.id))
    user = db.relationship(User)
