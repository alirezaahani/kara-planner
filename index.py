from flask import Blueprint, render_template


index = Blueprint("index", __name__)


@index.route("/", methods=["GET"])
def show():
    return render_template("index.html.jinja")


support = Blueprint("support", __name__)


@support.route("/support", methods=["GET"])
def show():
    return render_template("index.html.jinja")
