import argparse
import logging
import os
from logging import exception

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import render_template
import models

from src.datasets.food.foodloader import FoodLoader
from src.datasets.wine.wineloader import WineLoader
from logging_config import setup_logging

sql_user = os.environ["MYSQL_USER"]
sql_pwd = os.environ["MYSQL_PWD"]
sql_db = os.environ["MYSQL_DB"]
key = os.environ["FLASK_SECRETKEY"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{sql_user}:{sql_pwd}@localhost/{sql_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = key

models.db.init_app(app)

admin = Admin(app, name='LLM Dashboard', template_mode='bootstrap3')
admin.add_view(ModelView(models.Model, models.db.session))
admin.add_view(ModelView(models.Application, models.db.session))
admin.add_view(ModelView(models.TrainingImage, models.db.session))
admin.add_view(ModelView(models.ImagePrompt, models.db.session))
admin.add_view(ModelView(models.SystemPrompt, models.db.session))

@app.route("/")
def index():
    return render_template("index.html", title="Home", status_message="All systems go")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

    '''
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dataset_location", type=str, help="Base path of the dataset files for reading/writing to.")
    parser.add_argument("-m", "--mode", type=str, help="Which dataset mode? Choose from 'food', 'pharma', 'wine'.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        log_level=logging.DEBUG
    else:
        log_level=logging.INFO

    setup_logging(level=log_level)

    dataset_location = args.dataset_location
    mode = args.mode
    path = os.path.join(dataset_location, "labeldetection-datagen-client", mode)

    if mode == "food":
        loader = FoodLoader(path)
    elif mode == "wine":
        loader = WineLoader(path)
    else:
        logging.critical("Invalid mode. Choose from 'food' or 'wine'")
        exit(0)

    loader.load()
    '''