import os
import models
import redis
from flask import Flask, render_template, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from tasks import data_processing
from sqlalchemy.orm import configure_mappers
from models import TrainingImagesView, ImagePromptsView

sql_user = os.environ["MYSQL_USER"]
sql_pwd = os.environ["MYSQL_PWD"]
sql_db = os.environ["MYSQL_DB"]
key = os.environ["FLASK_SECRETKEY"]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{sql_user}:{sql_pwd}@localhost/{sql_db}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = key

models.db.init_app(app)

admin = Admin(app, name='LLM Dashboard')

configure_mappers()
admin.add_view(ModelView(models.Models, models.db.session))
admin.add_view(ModelView(models.Applications, models.db.session))
admin.add_view(TrainingImagesView(models.TrainingImages, models.db.session))
admin.add_view(ImagePromptsView(models.ImagePrompts, models.db.session))
admin.add_view(ModelView(models.SystemPrompts, models.db.session))

@app.route("/")
def index():
    return render_template("index.html", title="Home", status_message="All systems go")

@app.route("/start-job", methods=["POST"])
def start_job():
    task = data_processing.delay()
    return redirect(url_for("job_status", task_id=task.id))

@app.route("/job/<task_id>")
def job_status(task_id):
    redis_client = redis.Redis(host='localhost', port=6379, db=2)

    logs = redis_client.lrange(f"logs:{task_id}", 0, -1)
    status = redis_client.get(f"status:{task_id}")
    logs = [log.decode('utf-8') for log in logs]
    status = status.decode('utf-8') if status else "Unknown"
    return render_template("status.html", task_id=task_id, status=status, logs=logs)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')