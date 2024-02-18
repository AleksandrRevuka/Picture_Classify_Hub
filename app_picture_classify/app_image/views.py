import os

from django.core.files.uploadedfile import InMemoryUploadedFile

from .utils import save_picture_to_claud, svg_reshape_to_32x32x3, svg_classification, save_jpeg_and_url_from_svg, \
    jpg_classification, save_jpeg_and_url_from_jpg_and_jpeg
from django.http import HttpResponseServerError
from django.apps import apps
from django.shortcuts import render, redirect
from .forms import ImageForm
from .models import ImageModel
from .utils import preprocess_image, remove_img_from_cloud, PUBLIC_ID

from wand.image import Image as WandImage
from wand.color import Color
from PIL import Image as PillowImage
import io
import numpy as np
import matplotlib.pyplot as plt
import cloudinary



def destroy_original_image_from_cloud(func):
    """
Функція destroy_original_image_from_cloud — це декоратор, 
який видалить оригінальне зображення з cloudinary після виконнання основної функції
    """
    def inner(*args, **kwargs):
        if PUBLIC_ID.get("public_id"):
            remove_img_from_cloud(PUBLIC_ID.get("public_id"))
        result = func(*args)
        
        return result
    
    return inner



class ModelInference:
    def __init__(self, model):
        self.model = model

    def predict_class(self, img):
        сlass_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
        prediction = self.model.predict(img)
        predicted_class = prediction.argmax()

        return сlass_names[predicted_class]



@destroy_original_image_from_cloud
def home(request):
    form = ImageForm(instance=ImageModel())
    predicted_class = ''
    img_url = None

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES, instance=ImageModel())
        if form.is_valid():

            uploaded_image = request.FILES['original_file_name']  # отримуємо завантажену картинку (тимчасовий файл)

            file_extension = os.path.splitext(uploaded_image.name)[1]  # отримуємо розширення тимчасового файла

            if file_extension == '.svg':
                # ---------------------------------------Векторні зображення (чорно-білі та кольорові)

                # Створюємо тимчасовий файл для збереження PNG-зображення"
                with WandImage(blob=uploaded_image.read(), format='svg',width=32, height=32,
                           background=Color('#00000000')) as img:
                    # Конвертуємо SVG у PNG
                    with img.convert('png') as converted_img:
                        # Замінюємо вміст uploaded_image на вміст конвертованого PNG-файлу
                        uploaded_image1 = converted_img.make_blob()

                # створюємо об'єкт зображення Pillow з байтового рядка
                image = PillowImage.open(io.BytesIO(uploaded_image1))
                
                # отримуємо масив із зображення з необхідною розмірністю (32, 32, 3)
                image_array, img_32x32, original_image = svg_reshape_to_32x32x3(image)
            
                # Класифікація
                predicted_class = svg_classification(image_array, ModelInference)

                # збереження зображення в хмару, його url в базу даних
                img_url, img_public_id = save_jpeg_and_url_from_svg(form, image)
                save_jpeg_and_url_from_svg(form, img_32x32)
                PUBLIC_ID['public_id'] = img_public_id

            else:
                img_url, img_public_id = save_picture_to_claud(PillowImage.open(uploaded_image))
                PUBLIC_ID['public_id'] = img_public_id
                # ---------------------------------------Растрові зображення (чорно-білі та кольорові)
                # отримуємо зображення розміром 32х32 пікселі з оригінального зображення та відповідного масиву
                img_32x32, img_32x32_array = preprocess_image(uploaded_image)

                # Класифікація
                predicted_class = jpg_classification(img_32x32_array, ModelInference)

                # збереження зображення в хмару, його url в базу даних
                save_jpeg_and_url_from_jpg_and_jpeg(form, img_32x32)

            # видаляємо тимчасовий файл
            os.remove(uploaded_image.name)

    return render(request,
                  template_name='app_image/index.html',
                  context={"form": form, "output_text": predicted_class, "uploaded_image_url": img_url})

