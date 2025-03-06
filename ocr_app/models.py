from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class Transaksi(models.Model):
    total_belanja = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Produk(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name="produk")
    nama_produk = models.CharField(max_length=255)
    jumlah = models.IntegerField()
    harga_satuan = models.DecimalField(max_digits=10, decimal_places=2)
    total_harga = models.DecimalField(max_digits=10, decimal_places=2)


