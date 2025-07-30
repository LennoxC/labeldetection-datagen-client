from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Applications(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(512), nullable=False)

    training_images = db.relationship('TrainingImages', backref='application')
    image_prompts = db.relationship('ImagePrompts', backref='application')
    system_prompts = db.relationship('SystemPrompts', backref='application')

    def __str__(self):
        return self.name


class Models(db.Model):
    __tablename__ = "models"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    host = db.Column(db.String(512))
    port = db.Column(db.Integer)

    image_prompts = db.relationship('ImagePrompts', backref='target_model')
    system_prompts = db.relationship('SystemPrompts', backref='target_model')

    def __str__(self):
        return self.name


class TrainingImages(db.Model):
    __tablename__ = "training_images"
    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    #application = db.relationship('Applications', backref='training_images')

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
    target_model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    prompt = db.Column(db.Text)

    def __str__(self):
        return f"{self.prompt} | {self.target_model}"


class SystemPrompts(db.Model):
    __tablename__ = "system_prompts"
    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)

    target_model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)

    prompt = db.Column(db.Text)

    def __str__(self):
        return f"SystemPrompt {self.prompt} {self.target_model}"

class TrainingImagesView(ModelView):
    can_delete = False
    can_create = False
    can_edit = False
    can_view_details = True

class ImagePromptsView(ModelView):
    column_filters = ['application.name', 'target_model.name']