from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Bensin/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Struk/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class Struk(models.Model):
    nama_toko = models.CharField(max_length=255)
    tanggal = models.CharField(max_length=100)
    subtotal = models.CharField(max_length=50, null=True)
    pajak = models.CharField(max_length=50, null=True)
    biaya_layanan = models.CharField(max_length=50, null=True)              
    diskon = models.CharField(max_length=50, null=True)
    lainnya = models.CharField(max_length=50, null=True)
    grand_total = models.CharField(max_length=50, null=True)
    
class Produk(models.Model):
    struk = models.ForeignKey(Struk, on_delete=models.CASCADE, related_name='produk')
    nama = models.CharField(max_length=255)
    jumlah = models.CharField(max_length=50)
    harga = models.CharField(max_length=50)
    jumlah_harga = models.CharField(max_length=50)
