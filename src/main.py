import os
import models
import redis
import pymysql
from flask import Flask, render_template, redirect, url_for, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from sql_helper import SqlHelper
from model_helper import ModelHelper
from tasks import data_processing_task
from sqlalchemy.orm import configure_mappers
from models import TrainingImagesView #, ImagePromptsView
import json
from tasks import celery_app

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
admin.add_view(ModelView(models.ImagePrompts, models.db.session))
admin.add_view(ModelView(models.Datasets, models.db.session))
admin.add_view(ModelView(models.Prompts, models.db.session))

@app.route("/")
def index():
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    cursor = SqlHelper().get_cursor()

    query = '''
            SELECT COUNT(*)
            FROM training_images
                     INNER JOIN applications
                                ON applications.id = training_images.application_id
            WHERE applications.name = %s ;
            '''

    categories = ['food', 'wine', 'pharma']
    counts = {}

    for category in categories:
        cursor.execute(query, (category,))
        counts[category] = cursor.fetchone()[0]

    return render_template(
        "index.html",
        title="Home",
        food_images=counts['food'],
        wine_images=counts['wine'],
        pharma_images=counts['pharma']
    )

@app.route("/jobs")
def jobs():
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    job_entries = redis_client.lrange("job_list", 0, 20)  # show latest 20 jobs
    jobs_list = []
    for job_json in job_entries:
        job = json.loads(job_json)
        status = redis_client.get(f"status:{job['task_id']}")
        job["status"] = status.decode('utf-8') if status else "Unknown"
        jobs_list.append(job)
    return render_template("jobs.html", jobs=jobs_list)

@app.route("/start-job", methods=["POST"])
def start_job():
    mode = request.form['mode']
    task = data_processing_task.delay(mode)
    return redirect(url_for("job_status", task_id=task.id))

@app.route("/stop-job", methods=["POST"])
def stop_job():
    task_id = request.form['task_id']

    # Revoke the task
    celery_app.control.revoke(task_id, terminate=True)

    # Update status in Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    redis_client.set(f"status:{task_id}", "Stopped")

    return redirect(url_for("job_status", task_id=task_id))


@app.route("/job/<task_id>")
def job_status(task_id):
    redis_client = redis.Redis(host='localhost', port=6379, db=2)

    logs = redis_client.lrange(f"logs:{task_id}", 0, -1)
    status = redis_client.get(f"status:{task_id}")
    logs = [log.decode('utf-8') for log in logs]
    status = status.decode('utf-8') if status else "Unknown"
    return render_template("status.html", task_id=task_id, status=status, logs=logs)


@app.route("/chat", methods=["GET", "POST"])
def test_model():

    sql = SqlHelper()

    cursor = sql.get_cursor()  # or self.get_cursor() if inside a class
    cursor.execute("SELECT name FROM models")
    model_names = [row[0] for row in cursor.fetchall()]

    if request.method == "POST":
        model_name = request.form.get("model_name")
        prompt = request.form.get("prompt")
        image_file = request.files.get("image")

        model = ModelHelper(model_name)

        image_path = None
        if image_file and image_file.filename != "":
            image_path = f"/tmp/{image_file.filename}"
            image_file.save(image_path)

        result = model.query_model(prompt, image=image_path)

        #try:

        #except Exception as e:
        #    result = f"Error: {str(e)}"

        # Remove image after use
        if image_path:
            try:
                os.remove(image_path)
            except OSError:
                pass

        return render_template("test_model.html", model_names=model_names, result=result,
                               selected_model=model_name, prompt=prompt)

    return render_template("test_model.html", model_names=model_names, result=None)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')