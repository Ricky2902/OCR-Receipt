from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Bensin/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='Struk/')
    created_at = models.DateTimeField(auto_now_add=True)  # Tambahkan jika belum ada

class DataStruk(models.Model):
    nama_toko = models.CharField(max_length=255)
    tanggal = models.CharField(max_length=100)
    subtotal = models.CharField(max_length=50, null=True)
    pajak = models.CharField(max_length=50, null=True)
    biaya_layanan = models.CharField(max_length=50, null=True)              
    diskon = models.CharField(max_length=50, null=True)
    lainnya = models.CharField(max_length=50, null=True)
    grand_total = models.CharField(max_length=50, null=True)

    def __str__(self):
        same_toko = DataStruk.objects.filter(nama_toko=self.nama_toko).order_by('id')
        count = same_toko.count()

        if count > 1:
            index = list(same_toko).index(self) + 1  # Menambahkan angka pembeda
            return f"{self.nama_toko} #{index}"

        return f"{self.nama_toko}"
    
class DataProduk(models.Model):
    struk = models.ForeignKey(DataStruk, on_delete=models.CASCADE, related_name='produk')
    nama = models.CharField(max_length=255)
    jumlah = models.CharField(max_length=50)
    harga = models.CharField(max_length=50)
    jumlah_harga = models.CharField(max_length=50)

    def __str__(self):
        return self.nama
