from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Bill/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='OVO/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Pertamina/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Parkir/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Paket/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada