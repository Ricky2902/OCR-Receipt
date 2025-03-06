import easyocr
import json
import re
from decimal import Decimal
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import UploadedImage, Transaksi, Produk
from .serializers import ImageSerializer

# Fungsi untuk membersihkan angka dari teks OCR
def clean_number(value):
    value = re.sub(r"[^\d,]", "", value)
    return float(value.replace(",", ".")) if value else None

class OCRView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            
            # Proses OCR
            reader = easyocr.Reader(["id", "en"])
            results = reader.readtext(uploaded_image.image.path, detail=0)

            produk_list = []
            total_belanja, cash, kembali = None, None, None
            i = 0

            while i < len(results):
                text = results[i].strip()
                
                # Deteksi produk dengan jumlah & harga
                if i + 3 < len(results) and re.match(r"^\d+$", results[i + 1].strip()):
                    try:
                        nama_produk = text
                        jumlah = int(results[i + 1].strip())
                        harga_satuan = clean_number(results[i + 2])
                        total_harga = clean_number(results[i + 3])

                        if total_harga is None and i + 4 < len(results):
                            total_harga = clean_number(results[i + 4])

                        if re.search(r"\b\d+\b", nama_produk):
                            jumlah = 1

                        produk_list.append({
                            "nama_produk": nama_produk,
                            "jumlah": jumlah,
                            "harga_satuan": harga_satuan,
                            "total_harga": total_harga
                        })
                    except Exception as e:
                        print(f"Error parsing produk: {e}")
                    
                    i += 3
                elif "Total" in text or "Tota]" in text:
                    total_belanja = clean_number(results[i + 1]) if i + 1 < len(results) else None
                elif "Cash" in text:
                    cash = clean_number(results[i + 1]) if i + 1 < len(results) else None
                elif "Kembali" in text or "Kemba | i" in text:
                    kembali = clean_number(results[i + 1]) if i + 1 < len(results) else None
                
                i += 1
            
            hasil_json = {
                "produk": produk_list,
                "total_belanja": total_belanja,
                "cash": cash,
                "kembali": kembali,
            }
            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

@api_view(['GET'])
def split_bill(request, transaksi_id, jumlah_orang):
    transaksi = get_object_or_404(Transaksi, id=transaksi_id)
    produk_list = Produk.objects.filter(transaksi=transaksi)
    
    spill_bill = []
    orang_bayar = [{} for _ in range(jumlah_orang)]
    total_orang = [Decimal('0') for _ in range(jumlah_orang)]
    
    index = 0
    for produk in produk_list:
        for _ in range(produk.jumlah):
            orang_bayar[index % jumlah_orang].setdefault(produk.nama_produk, 0)
            orang_bayar[index % jumlah_orang][produk.nama_produk] += 1
            total_orang[index % jumlah_orang] += Decimal(produk.harga_satuan)
            index += 1
    
    for i in range(jumlah_orang):
        spill_bill.append({
            "orang": i + 1,
            "produk": [{"nama_produk": nama, "jumlah": jumlah} for nama, jumlah in orang_bayar[i].items()],
            "total": float(total_orang[i])
        })
    
    return Response({
        "transaksi_id": transaksi.id,
        "total_belanja": transaksi.total_belanja,
        "jumlah_orang": jumlah_orang,
        "spill_bill": spill_bill
    })
