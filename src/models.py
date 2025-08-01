from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

image_prompts_models = db.Table(
    'image_prompts_models',
    db.Column('image_prompt_id', db.Integer, db.ForeignKey('image_prompts.id'), primary_key=True),
    db.Column('model_id', db.Integer, db.ForeignKey('models.id'), primary_key=True)
)

class Applications(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    target_size = db.Column(db.Integer, nullable=False)

    training_images = db.relationship('TrainingImages', backref='application')
    image_prompts = db.relationship('ImagePrompts', backref='application')

    def __str__(self):
        return self.name


class Models(db.Model):
    __tablename__ = "models"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    host = db.Column(db.String(512))
    port = db.Column(db.Integer)

    image_prompts = db.relationship(
        'ImagePrompts',
        secondary=image_prompts_models,
        back_populates='models'
    )

    def __str__(self):
        return self.name

class Prompts(db.Model):
    __tablename__ = "prompts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    prompt = db.Column(db.Text)
    description = db.Column(db.Text)

    def __str__(self):
        return self.name

class TrainingImages(db.Model):
    __tablename__ = "training_images"
    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)

    guid = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(16), nullable=False)
    tesseract_ocr_extract = db.Column(db.Text)
    processed = db.Column(db.Boolean)

    def __str__(self):
        return f"Image {self.id}"

class ImagePrompts(db.Model):
    __tablename__ = "image_prompts"
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    prompt = db.Column(db.Text)
    json_property = db.Column(db.Text)
    json_placeholder = db.Column(db.Text)

    models = db.relationship(
        'Models',
        secondary=image_prompts_models,
        back_populates='image_prompts'
    )

    def __str__(self):
        model_names = ', '.join([model.name for model in self.models])
        return f"{self.prompt} | Models: {model_names}"

class Datasets(db.Model):
    __tablename__ = "datasets"
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    uuid = db.Column(db.Text)
    description = db.Column(db.Text)
    reviewed = db.Column(db.Boolean)
    evaluation = db.Column(db.Boolean)
    auto_description = db.Column(db.Text)

    def __str__(self):
        return self.id

class TrainingImagesView(ModelView):
    can_delete = False
    can_create = False
    can_edit = False
    can_view_details = True
