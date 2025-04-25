from rest_framework import serializers
from .models import UploadedImage, Struk, Produk

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['id', 'image']

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = ['id', 'nama', 'jumlah', 'harga', 'jumlah_harga']

class StrukSerializer(serializers.ModelSerializer):
    produk = ProdukSerializer(many=True)  # karena related_name='produk' di ForeignKey

    class Meta:
        model = Struk
        fields = [
            'id', 'nama_toko', 'tanggal', 'subtotal', 'pajak',
            'biaya_layanan', 'diskon', 'lainnya', 'grand_total', 'produk'
        ]

    def create(self, validated_data):
        produk_data = validated_data.pop('produk')
        struk = Struk.objects.create(**validated_data)
        for produk in produk_data:
            Produk.objects.create(struk=struk, **produk)
        return struk