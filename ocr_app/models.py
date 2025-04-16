from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Bensin/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Struk/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada