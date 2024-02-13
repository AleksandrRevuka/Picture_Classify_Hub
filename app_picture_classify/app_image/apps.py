from django.apps import AppConfig
from keras.models import load_model
import os

class AppImageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_image'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None

    def ready(self):
        model_path = os.path.join('app_image', 'ml_models', 'model_cifar10_90_vgg16.h5')
        self.model = load_model(model_path)
