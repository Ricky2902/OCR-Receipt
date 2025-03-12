import easyocr
from paddleocr import PaddleOCR
import json
import re
import cv2
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UploadedImage
from .serializers import ImageSerializer

class Bill(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # **Baca gambar dengan OpenCV**
            image = cv2.imread(image_path)
            if image is None:
                return Response({"error": "Gambar tidak ditemukan atau tidak valid."}, status=400)
            
            h, w, _ = image.shape  # Dapatkan dimensi gambar

            # **Pisahkan Header (atas) & Body (bawah)**
            header = self.crop_and_ocr(image, w, h, 0, 1, 0, 0.35)
            body = self.crop_and_ocr(image, w, h, 0, 1, 0.35, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(header, body)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)  
        results = self.ocr.ocr(temp_crop_path, cls=False)
        
        ocr_text = [entry[1][0] for result in results for entry in result] if results else []
        print("Hasil OCR:", ocr_text)  # Debug output
        return ocr_text

    def get_valid_number(self, body, index):
        """Mengambil angka valid dari body[index] atau body[index+1] jika index pertama adalah simbol"""
        if index < len(body):
            if re.match(r"^[=:\-]+$", body[index]):  
                return self.sanitize_number(body[index + 1]) if index + 1 < len(body) else ""
            return self.sanitize_number(body[index])
        return ""

    def sanitize_number(self, text):
         # Hilangkan semua titik (.) dan koma (,)
        text = re.sub(r"[.,]", "", text)
    
         # Jika diakhiri dengan "00", hapus bagian tersebut
        text = re.sub(r"00$", "", text)

        return text.strip()
    
    def format_json(self, header, body):
        tanggal, waktu = self.pisahkan_tanggal_waktu(header[6] if len(header) > 6 else "")
        transaksi = {
            "Nama Toko": header[0] if len(header) > 0 else "",
            "No Ref": header[5] if len(header) > 5 else "",
            "Tanggal": tanggal,
            "Waktu": waktu,
            "Data": {
                "Produk": [],
                "Total": "",
                "Cash": "",
                "Kembali": ""
            }
        }

        i = 0
        while i < len(body):
            if "Total" in body[i]:
                transaksi["Data"]["Total"] = self.get_valid_number(body, i + 1)
            elif "Cash" in body[i]:
                transaksi["Data"]["Cash"] = self.get_valid_number(body, i + 1)
            elif "Kembali" in body[i]:
                transaksi["Data"]["Kembali"] = self.get_valid_number(body, i + 1)
            elif i + 2 < len(body):
                text_next = body[i + 2].lower()
                
                if "x" in text_next:  
                    parts = re.sub(r"[^\d]", "", text_next)  
                    if  i + 2 < len(body):
                        nama_produk = body[i] if not body[i].isdigit() else ""
                        jumlah = self.sanitize_number(body[i + 1])
                        harga = self.sanitize_number(parts)
                        jumlah_harga = self.sanitize_number(body[i + 3])

                        if nama_produk and jumlah and harga and jumlah_harga:
                            transaksi["Data"]["Produk"].append({
                            "Nama": nama_produk,
                            "Jumlah": jumlah,
                            "Harga": harga,
                            "Jumlah Harga": jumlah_harga
                        })
                        i += 3  
            i += 1  # Pastikan loop tetap berjalan dengan benar
        return transaksi

    def pisahkan_tanggal_waktu(self, text):
        pattern = r"(\d{1,2}[\-\/\s]?\d{2}[\-\/\s]?\d{4})(\d{2}.\d{2}.\d{2})?"
        match = re.search(pattern, text)
        if match:
            tanggal = match.group(1).replace(".", "/").strip()
            waktu = match.group(2).replace(".", ":").strip() if match.group(2) else ""
            return tanggal, waktu
        return text, ""

class OVO(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # **Baca gambar dengan OpenCV**
            image = cv2.imread(image_path)
            if image is None:
                return Response({"error": "Gambar tidak ditemukan atau tidak valid."}, status=400)
            
            h, w, _ = image.shape  # Dapatkan dimensi gambar

            # **Pisahkan Header Kiri (50%) & Body Kanan (50%)**
            header = self.crop_and_ocr(image, w, h, 0, 1, 0.05, 0.6)
            body = self.crop_and_ocr(image, w, h, 0, 1, 0.6, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(header, body)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def format_json(self, header, body):
        # Pastikan header cukup panjang sebelum mengakses indeks tertentu
        tanggal, waktu = self.pisahkan_tanggal_waktu(header[2] if len(header) > 2 else "")

        transaksi = {
            "Layanan": header[0] if len(header) > 0 else "",
            "Status": header[1] if len(header) > 1 else "",
            "Tanggal": tanggal,
            "Waktu": waktu,
            "Merchant": header[4] if len(header) > 4 else "",
            "NO.Referensi": header[6] + header[7] if len(header) > 7 else header[6] if len(header) > 6 else "",
            "Data": {}
        }

        # **Pisahkan data dengan regex**
        for i, text in enumerate(body):
            if "Sumber Dana" in text:
                transaksi["Data"]["Sumber Dana"] = body[i + 1].replace("Rp","").replace(".","") if i + 1 < len(body) else None
            elif "Nominal" in text:
                transaksi["Data"]["Nominal"] = int(body[i + 1].replace("Rp","").replace(".","")) if i + 1 < len(body) else ""
            elif "Biaya" in text:
                transaksi["Data"]["Biaya"] = int(body[i + 1].replace("Rp","").replace(".","")) if i + 1 < len(body) else ""
            elif "Total" in text:
                transaksi["Data"]["Total"] = int(body[i + 1].replace("Rp","").replace(".","")) if i + 1 < len(body) else ""

        return transaksi

    def pisahkan_tanggal_waktu(self, text):
        pattern = r"(\d{1,2}[\-\/\s]?[A-Za-z0-9]{3,}[\-\/\s]?\d{4})[.,]?\s*(\d{2}:\d{2})?"
        match = re.search(pattern, text)
        if match:
            tanggal = match.group(1).replace(".", "").strip()
            waktu = match.group(2) if match.group(2) else ""
            return tanggal, waktu
        return None, None


class Pertamina(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # **Baca gambar dengan OpenCV**
            image = cv2.imread(image_path)
            if image is None:
                return Response({"error": "Gambar tidak ditemukan atau tidak valid."}, status=400)
            
            h, w, _ = image.shape  # Dapatkan dimensi gambar

            # header = self.crop_and_ocr(image, w, h, 0, 1, 0, 0)
            body = self.crop_and_ocr(image, w, h, 0, 1, 0, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(body)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def format_json(self, body):
        # Pastikan header cukup panjang sebelum mengakses indeks tertentu
        tanggal, waktu = self.pisahkan_tanggal_waktu(body[8] if len(body) > 8 else "")
         
        transaksi = {
            "Tempat":body[0] if len(body) > 0 else "",
            "No PIN":"",
            "Tanggal":tanggal,
            "Waktu":waktu,
            "Nominal":"",
            "Produk":"",
            "Harga":"",
            "Volume":"",
        }

        # **Pisahkan data dengan regex**
        for i, text in enumerate(body):
            if "PIN" in text:
                transaksi["No PIN"] = body[i + 1]if i + 1 < len(body) else None
            elif "Nominal" in text:
                transaksi["Nominal"] = body[i + 1]if i + 1 < len(body) else None
            elif "Produk" in text:
                transaksi["Produk"] = body[i + 1]if i + 1 < len(body) else None
            elif "Harga" in text:
                transaksi["Harga"] = body[i + 1]if i + 1 < len(body) else None
            elif "Volume" in text:
                transaksi["Volume"] = body[i + 1]if i + 1 < len(body) else None

        return transaksi

    def pisahkan_tanggal_waktu(self, text):
        pattern = r"(\d{1,2})([A-Za-z]{3})(\d{4})(\d{2}):(\d{2}):(\d{2})"
        match = re.search(pattern, text)
        if match:
            tanggal = match.group(1).replace(".", "").strip()
            waktu = match.group(2) if match.group(2) else ""
            return tanggal, waktu
        return None, None

class Parkir(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # **Baca gambar dengan OpenCV**
            image = cv2.imread(image_path)
            if image is None:
                return Response({"error": "Gambar tidak ditemukan atau tidak valid."}, status=400)
            
            h, w, _ = image.shape  # Dapatkan dimensi gambar

            # header = self.crop_and_ocr(image, w, h, 0, 1, 0, 0)
            body = self.crop_and_ocr(image, w, h, 0, 1, 0, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(body)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def format_json(self, body):
        # Pastikan header cukup panjang sebelum mengakses indeks tertentu

         
        transaksi = {
            "Tempat":body[0] if len(body) > 0 else "",
            "transaksi": body[1] if len(body) > 1 else "",
            "Jenis Kendaraan":body[2] if len(body) > 2 else "",
            "Masuk" :"",            
            "Keluar" :"",  
            "Lama" :"",  
            "Biaya":"",  
        }

        # **Pisahkan data dengan regex**
        for i, text in enumerate(body):
            if "In" in text:
                transaksi["Masuk"] = text.split("In")[-1].strip()
            elif "Out" in text:
                transaksi["Keluar"] = text.split("Out")[-1].strip()
            elif "Lama" in text:
                transaksi["Lama"] = text.split("Lama:")[-1].strip()
            elif "Sewa Parkir" in text:
                transaksi["Biaya"] = body[i + 2]if i + 2 < len(body) else None

        return transaksi
    
class Paket(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # **Baca gambar dengan OpenCV**
            image = cv2.imread(image_path)
            if image is None:
                return Response({"error": "Gambar tidak ditemukan atau tidak valid."}, status=400)
            
            h, w, _ = image.shape  # Dapatkan dimensi gambar

            # **Pisahkan Header Kiri (50%) & Body Kanan (50%)**
            header_kiri = self.crop_and_ocr(image, w, h, 0, 0.5, 0, 1)
            body_kanan = self.crop_and_ocr(image, w, h, 0.5, 1, 0, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(header_kiri, body_kanan)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def format_json(self, header_kiri, body_kanan):
        transaksi = {
            "Barcode": header_kiri[0] if len(header_kiri) > 0 else "",
            "Layanan": header_kiri[1] if len(header_kiri) > 1 else "",
            "Pengirim": self.clean_text(header_kiri[2]) if len(header_kiri) > 2 else "",
            "Penerima": self.clean_text(header_kiri[4]) if len(header_kiri) > 4 else "",
            "Data": {}
        }

        # **Pisahkan data dengan regex**
        for text in body_kanan:
            if "Tangga" in text:
                transaksi["Data"]["Tanggal"], transaksi["Data"]["Waktu"] = self.pisahkan_tanggal_waktu(text)
            elif "No.Pelanggan" in text:
                transaksi["Data"]["No.Pelanggan"] = text.split("No.Pelanggan")[-1].strip()
            elif "Berat" in text:
                transaksi["Data"]["Berat"] = text.split("Berat:")[-1].strip()
            elif "Deskripsi" in text:
                transaksi["Data"]["Deskripsi"] = text.split("Deskripsi")[-1].strip()
            elif "Jumlah Kiriman" in text:
                transaksi["Data"]["Jumlah Kiriman"] = text.split(":")[-1].strip()
            elif "Baya Kirim" in text or "Biaya Kirim" in text:
                transaksi["Data"]["Biaya Kirim"] = self.clean_number(text)
            elif "Kota" in text:
                transaksi["Data"]["Kota Tujuan"] = self.clean_text(text.split(":")[-1])
            elif "Asuransi" in text:
                transaksi["Data"]["Asuransi"] = text.split("Asuransi")[-1].strip()
            elif "Dlantar maks." in text or "Diantar maks." in text:
                transaksi["Data"]["Diantar"] = text.split(".")[-1].strip()

        return transaksi

    def pisahkan_tanggal_waktu(self, text):
        pattern = r"(\d{2}-\d{2}-\d{4})\s*(\d{2}:\d{2})?"
        match = re.search(pattern, text)
        if match:
            return match.group(1), match.group(2) if match.group(2) else ""
        return text, ""

    def clean_number(self, value):
        return "".join(re.findall(r"\d+", value))

    def clean_text(self, value):
        return re.sub(r"^(Pengirim:|Penerima:)\s*", "", value).strip()