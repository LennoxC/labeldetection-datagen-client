import os
import uuid

import models
import redis
import pymysql
from flask import Flask, render_template, redirect, url_for, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from sql_helper import SqlHelper
from model_helper import ModelHelper
from src.ocr_helper import OCRHelper
from tasks import data_processing_task
from sqlalchemy.orm import configure_mappers
from models import TrainingImagesView #, ImagePromptsView
import json
from tasks import celery_app
import pandas as pd
import numpy as np

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
    cursor = SqlHelper().get_cursor()

    # Get all unique applications for the filter dropdown
    cursor.execute("SELECT DISTINCT name FROM applications ORDER BY name")
    applications = [row[0] for row in cursor.fetchall()]

    # Optional filter
    selected_app = request.args.get("application")

    query = '''
            SELECT ds.uuid, \
                   ds.description, \
                   ds.reviewed, \
                   ds.evaluation, \
                   ds.auto_description, \
                   app.name AS application, \
                   app.path, \
                   app.target_size
            FROM datasets AS ds
                     LEFT JOIN applications AS app ON app.id = ds.application_id \
            '''

    params = ()
    if selected_app:
        query += " WHERE app.name = %s"
        params = (selected_app,)

    cursor.execute(query, params)
    datasets = cursor.fetchall()

    # Column names for the table headers
    column_names = [desc[0] for desc in cursor.description]

    return render_template(
        "index.html",
        datasets=datasets,
        columns=column_names,
        applications=applications,
        selected_app=selected_app
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

# In-memory cache to avoid reloading CSV every time (for demonstration)
csv_cache = {}

@app.route("/dataset/<dataset_id>")
def view_dataset(dataset_id):
    cursor = SqlHelper().get_cursor()
    query = f'''
        SELECT 
            ds.uuid,
            ds.description,
            ds.reviewed,
            ds.evaluation,
            ds.auto_description,
            app.name AS application,
            app.path,
            app.target_size
        FROM datasets AS ds
        LEFT JOIN applications AS app ON app.id = ds.application_id
        WHERE ds.uuid = '{dataset_id}'
    '''
    cursor.execute(query)
    row = cursor.fetchone()
    if not row:
        return "Dataset not found", 404

    dataset = {
        "uuid": row[0],
        "description": row[1],
        "reviewed": row[2],
        "evaluation": row[3],
        "auto_description": row[4],
        "application": row[5],
        "path": row[6],
        "target_size": row[7],
    }

    full_path = os.path.join(dataset["path"], dataset["uuid"])
    csv_path = os.path.join(full_path, "outputs.csv")

    if not os.path.exists(csv_path):
        return f"CSV file not found at {csv_path}", 404

    dataset_df = pd.read_csv(csv_path)
    rows_count = len(dataset_df)

    # Optional filtering
    show_only_unmatched = request.args.get("unmatched") == "true"
    if show_only_unmatched:
        dataset_df = dataset_df[dataset_df["matches"] == False]

    dataset_df["matches"] = dataset_df["matches"].astype(bool)

    # Store in cache: both dataframe and path
    csv_cache[dataset_id] = {
        "df": dataset_df,
        "path": full_path
    }


    unmatched_rows_count = len(dataset_df[dataset_df["matches"] == False])

    return render_template("dataset_view.html",
                           dataset=dataset,
                           rows_count=rows_count,
                           unmatched_rows_count=unmatched_rows_count,
                           records=dataset_df.to_dict(orient="records"),
                           show_only_unmatched=show_only_unmatched)


@app.route("/dataset/<dataset_id>/image/<image_name>", methods=["GET", "POST"])
def view_image(dataset_id, image_name):
    cached = csv_cache.get(dataset_id)
    if cached is None:
        return "Dataset not loaded", 400

    dataset_df = cached["df"]
    full_path = cached["path"]
    records = dataset_df[dataset_df["image_name"] == image_name].copy()

    if request.method == "POST":
        for i, row in records.iterrows():
            r1 = request.form.get(f"result1_{i}", "").strip()
            r2 = request.form.get(f"result2_{i}", "").strip()
            result = request.form.get(f"result_{i}", "").strip()

            # Update the main DataFrame at the same index
            dataset_df.at[i, "result1"] = r1
            dataset_df.at[i, "result2"] = r2
            dataset_df.at[i, "result"] = result
            dataset_df.at[i, "matches"] = (r1 == r2)

        csv_path = os.path.join(full_path, "outputs.csv")

        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        dataset_df.to_csv(csv_path, index=False)

        return redirect(url_for("view_image", dataset_id=dataset_id, image_name=image_name))

    image_path = os.path.join(full_path, "images", image_name)
    if not os.path.exists(image_path):
        return f"Image not found at {image_path}", 404

    # Expose image path via static route:
    static_url_path = f"/dataset/{dataset_id}/images/{image_name}"

    return render_template("image_view.html",
                           image_name=image_name,
                           image_path=static_url_path,
                           records=records.to_dict(orient="records"),
                           dataset_id=dataset_id)

from flask import send_file

@app.route("/dataset/<dataset_id>/images/<image_name>")
def serve_dataset_image(dataset_id, image_name):
    cached = csv_cache.get(dataset_id)
    if cached is None:
        return "Dataset not loaded", 400

    image_path = os.path.join(cached["path"], "images", image_name)
    if not os.path.exists(image_path):
        return f"Image not found at {image_path}", 404

    return send_file(image_path)


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

        # Remove image after use
        if image_path:
            try:
                os.remove(image_path)
            except OSError:
                pass

        return render_template("test_model.html", model_names=model_names, result=result,
                               selected_model=model_name, prompt=prompt)

    return render_template("test_model.html", model_names=model_names, result=None)

@app.route("/ocr", methods=["GET", "POST"])
def test_ocr():
    ocr = OCRHelper()

    if request.method == "POST":
        image_file = request.files.get("image")

        if image_file and image_file.filename != "":
            image_path = f"/tmp/{uuid.uuid4()}_{image_file.filename}"
            image_file.save(image_path)

            lines = ocr.inference(image_path)
            output = "\n".join(lines)

            # Clean up image file
            #try:
            #    os.remove(image_path)
            #except OSError:
            #    pass

            #json_string = json.dumps(output, indent=4, ensure_ascii=False)

            return render_template("test_ocr.html", result=output)

    return render_template("test_ocr.html", result=None)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')