import easyocr
import json
import re
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedImage
from .serializers import ImageSerializer

# Fungsi untuk membersihkan angka dari teks OCR
def clean_number(value):
    value = re.sub(r"[^\d,]", "", value)  
    return float(value.replace(",", ".")) if value else None

class OCR2View(APIView): 
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()  
            
            # Proses OCR
            reader = easyocr.Reader(["id", "en"])  
            results = reader.readtext(uploaded_image.image.path, detail=0)

            produk_list = []
            total_belanja, non_tunai, anda_hemat = None, None, None
            i = 0

            while i < len(results):
                text = results[i].strip()

                # Deteksi produk, diskon, harga satuan, total harga
                if (
                    i + 3 < len(results) and
                    re.match(r"^\d+$", results[i + 1].strip())  
                ):
                    try:
                        nama_produk = text
                        jumlah = int(results[i + 1].strip())
                        harga_satuan = clean_number(results[i + 2])
                        total_harga = clean_number(results[i + 3])

                        # Cek apakah ada diskon setelah harga total
                        diskon = None
                        if i + 5 < len(results) and "DISKON" in results[i + 4].upper():
                            diskon = clean_number(results[i + 5])

                        produk_list.append({
                            "nama_produk": nama_produk,
                            "jumlah": jumlah,
                            "harga_satuan": harga_satuan,
                            "total_harga": total_harga,
                            "diskon": diskon
                        })
                    except Exception as e:
                        print(f"Error parsing produk: {e}")

                    i += 3  

                elif "HARGA JUAL" in text:
                    total_belanja = clean_number(results[i + 1]) if i + 1 < len(results) else None

                elif "NON TUNAI" in text:
                    non_tunai = clean_number(results[i + 1]) if i + 1 < len(results) else None

                elif "ANDA HEMAT" in text:
                    anda_hemat = clean_number(results[i + 1]) if i + 1 < len(results) else None

                i += 1  

            # Struktur JSON hasil OCR
            hasil_json = {
                "produk": produk_list,
                "total_belanja": total_belanja,
                "non_tunai": non_tunai,
                "anda_hemat": anda_hemat,
            }

            return Response({"hasil_ocr": hasil_json})

        return Response(serializer.errors, status=400)
