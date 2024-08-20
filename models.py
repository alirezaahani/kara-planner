from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from dataclasses import dataclass
import enum
import datetime

db = SQLAlchemy()

import dataclasses, json

class DataClassEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if isinstance(o, (datetime.datetime, datetime.timedelta, datetime.date)):
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

@dataclass
class ScheduleType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column()
    background_color_hex: Mapped[str] = mapped_column()
    text_color_hex: Mapped[str] = mapped_column()
    
    user_id = mapped_column(db.ForeignKey(User.id))
    user = db.relationship(User)

@dataclass
class Schedule(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    start: Mapped[datetime.datetime] = mapped_column()
    end: Mapped[datetime.datetime] = mapped_column()
    description: Mapped[str] = mapped_column()
    type_id: Mapped[int] = mapped_column(db.ForeignKey(ScheduleType.id))
    
    user_id = mapped_column(db.ForeignKey(User.id))
    type = db.relationship(ScheduleType)
    user = db.relationship(User)


@dataclass
class Goal(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    deadline: Mapped[datetime.datetime] = mapped_column()
    description: Mapped[str] = mapped_column()

    user_id = mapped_column(db.ForeignKey(User.id))
    user = db.relationship(User)

@dataclass
class ExamType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column()
    color_hex: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    
    user = db.relationship(User)

@dataclass
class ExamResult(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column()
    value: Mapped[float] = mapped_column()
    description: Mapped[str] = mapped_column()
    type_id: Mapped[int] = mapped_column(db.ForeignKey(ExamType.id))

    user_id = mapped_column(db.ForeignKey(User.id))
    type = db.relationship(ExamType)
    user = db.relationship(User)

@dataclass
class PlanType(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column()
    background_color_hex: Mapped[str] = mapped_column()
    text_color_hex: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(db.ForeignKey(User.id))

    user = db.relationship(User)

@dataclass
class Plan(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column()
    description: Mapped[str] = mapped_column()
    type_id: Mapped[int] = mapped_column(db.ForeignKey(PlanType.id))

    type = db.relationship(PlanType)
    user_id = mapped_column(db.ForeignKey(User.id))
    user = db.relationship(User)