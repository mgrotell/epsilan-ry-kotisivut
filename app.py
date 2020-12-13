from flask import Flask
from flask_bootstrap import Bootstrap
from os import getenv

app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET_KEY")
Bootstrap(app)

import routesmanager