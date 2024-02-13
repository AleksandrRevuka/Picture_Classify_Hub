from .utils import cutting_image, save_picture_to_claud, save_image_url_to_db
from django.apps import apps
from django.shortcuts import render, redirect
from .forms import ImageForm
from .models import ImageModel
from .image_handler import preprocess_image


class ModelInference:
    def __init__(self, model):
        self.model = model

    def predict_class(self, img):
        сlass_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
        prediction = self.model.predict(img)
        predicted_class = prediction.argmax()

        return сlass_names[predicted_class]


def home(request):
    form = ImageForm(instance=ImageModel())
    predicted_class = ''

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES, instance=ImageModel())
        if form.is_valid():
            image_instance = form.save(commit=False)  # Отримуємо екземпляр моделі без збереження в базу даних
            uploaded_image = request.FILES['original_file_name']  # отримаємо завантажену картинку

            # перетворення картинки в масив
            img_32x32_array = preprocess_image(uploaded_image)

            # отримання конфігурації додатка 'app_image'
            AppConfig = apps.get_app_config('app_image')
            # з отриманої конфігурації отримується модель
            model = AppConfig.model

            # передбачення класу зображення за допомогою переданої моделі
            model_inference = ModelInference(model)
            predicted_class = model_inference.predict_class(img_32x32_array)

            # перетворюємо зображення в 32х32 пікселя
            img_32x32 = cutting_image(uploaded_image)

            # збереження зображення в хмару, отримання його url
            cloudinary_url = save_picture_to_claud(img_32x32)

            # зберігаємо URL в базі даних
            save_image_url_to_db(form, cloudinary_url)

    return render(request,
                  template_name='app_image/index.html', 
                  context={"form": form, "output_text": predicted_class})


def action(request):
    r = request
    if r:
        print("action")
    return redirect('app_image:home')
