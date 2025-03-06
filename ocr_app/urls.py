from django.urls import path
from .views import OCRView

urlpatterns = [
    path("upload/", OCRView.as_view(), name="ocr_upload"),
]



