import os
import secrets


class Config:
    SECRET_KEY = secrets.token_urlsafe(16)
    SQLALCHEMY_DATABASE_URI = "sqlite:///kara.sqlite"
    TEMPLATES_AUTO_RELOAD = True
