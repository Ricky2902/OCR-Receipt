from rest_framework import serializers
from .models import UploadedImage, DataStruk, DataProduk

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['id', 'image']

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataProduk
        fields = ['id', 'nama', 'jumlah', 'harga', 'jumlah_harga']

class StrukSerializer(serializers.ModelSerializer):
    produk = ProdukSerializer(many=True)  # karena related_name='produk' di ForeignKey

    class Meta:
        model = DataStruk
        fields = [
            'id', 'nama_toko', 'tanggal', 'subtotal', 'pajak',
            'biaya_layanan', 'diskon', 'lainnya', 'grand_total', 'produk'
        ]

    def create(self, validated_data):
        produk_data = validated_data.pop('produk')
        struk = DataStruk.objects.create(**validated_data)
        for produk in produk_data:
            DataProduk.objects.create(struk=struk, **produk)
        return struk