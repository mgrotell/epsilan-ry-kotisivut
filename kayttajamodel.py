from flask_login import UserMixin
from db import db

class Kayttajat(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nimi = db.Column(db.String(15), unique=True)
    sahkoposti = db.Column(db.String(50), unique=True)
    salasana = db.Column(db.String(80))
    isadmin = db.Column(db.Boolean)
    isbanned = db.Column(db.Boolean)