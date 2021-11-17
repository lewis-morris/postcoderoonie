from flask import Blueprint, request, render_template, url_for, redirect, current_app, jsonify, abort, session, flash, \
    session, send_file
from sqlalchemy.sql.expression import func, desc
import numpy as np

from postcoderoonie.models import *
import logging

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template('home.html')


