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
        
from sqlalchemy.orm import Mapped, mapped_column, relationship

@dataclass
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()

'''
class ScheduleEnum(enum.Enum): 
    SLEEP = 'خواب'
    STUDY = 'درس خواندن'
    WORK = 'کار کردن'
    BREAK = 'استراحت'
    EXERCISE = 'ورزش'
    OTHER = 'سایر'
'''

@dataclass
class ScheduleType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column()
    background_color_hex: Mapped[str] = mapped_column()
    text_color_hex: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    
    user = db.relationship(User)

@dataclass
class Schedule(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[datetime] = mapped_column()
    end: Mapped[datetime] = mapped_column()
    description: Mapped[str] = mapped_column()
    type: Mapped[ScheduleType] = db.relationship(ScheduleType)
    type_id: Mapped[int] = mapped_column(db.ForeignKey(ScheduleType.id))
    
    user_id = mapped_column(db.ForeignKey(User.id))
    user = db.relationship(User)


@dataclass
class Goal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    deadline: Mapped[datetime] = mapped_column()
    description: Mapped[str] = mapped_column()

    user_id = mapped_column(db.ForeignKey(User.id))
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