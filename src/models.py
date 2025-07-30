from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Application(db.Model):
    __tablename__ = 'Applications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(512), nullable=False)

    # Relationships
    training_images = db.relationship('TrainingImage', back_populates='application', cascade='all, delete-orphan')
    image_prompts = db.relationship('ImagePrompt', back_populates='application', cascade='all, delete-orphan')
    system_prompts = db.relationship('SystemPrompt', back_populates='application', cascade='all, delete-orphan')


class Model(db.Model):
    __tablename__ = 'Models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    host = db.Column(db.String(512), nullable=True)
    port = db.Column(db.Integer, nullable=True)

    # Relationships
    image_prompts = db.relationship('ImagePrompt', back_populates='target_model', cascade='all, delete-orphan')
    system_prompts = db.relationship('SystemPrompt', back_populates='target_model', cascade='all, delete-orphan')


class TrainingImage(db.Model):
    __tablename__ = 'TrainingImages'

    id = db.Column(db.Integer, primary_key=True)
    applicationId = db.Column(db.Integer, db.ForeignKey('Applications.id'), nullable=False)
    guid = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(16), nullable=False)
    tesseract_ocr_extract = db.Column(db.Text, nullable=True)
    processed = db.Column(db.Boolean, nullable=True)

    application = db.relationship('Application', back_populates='training_images')


class ImagePrompt(db.Model):
    __tablename__ = 'ImagePrompts'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('Applications.id'), nullable=False)
    target_model_id = db.Column('target_model', db.Integer, db.ForeignKey('Models.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=True)

    application = db.relationship('Application', back_populates='image_prompts')
    target_model = db.relationship('Model', back_populates='image_prompts')


class SystemPrompt(db.Model):
    __tablename__ = 'SystemPrompts'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('Applications.id'), nullable=False)
    target_model_id = db.Column('target_model', db.Integer, db.ForeignKey('Models.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=True)

    application = db.relationship('Application', back_populates='system_prompts')
    target_model = db.relationship('Model', back_populates='system_prompts')