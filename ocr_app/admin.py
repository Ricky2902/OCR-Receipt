from django.contrib import admin
from .models import UploadedImage, DataStruk, DataProduk, DataBensin

admin.site.register(UploadedImage)
admin.site.register(DataStruk)
admin.site.register(DataProduk)
admin.site.register(DataBensin)