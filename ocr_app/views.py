import easyocr
from paddleocr import PaddleOCR
import json
import re
import cv2
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
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
                transaksi["Volume"] = body[i + 1] + "L"if i + 1 < len(body) else None

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
                transaksi["Lama"] = text.split("Lama")[-1].strip()
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
    
class Exabytes(APIView):
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

            header = self.crop_and_ocr(image, w, h, 0, 0.5, 0, 0.6)
            body = self.crop_and_ocr(image, w, h, 0, 1, 0.6, 0.9)
            footer = self.crop_and_ocr(image, w, h, 0, 1, 0.9, 1)

            # **Format hasil menjadi JSON**
            hasil_json = self.format_json(header, body, footer)

            return Response({"hasil_ocr": hasil_json})
        
        return Response(serializer.errors, status=400)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        # return [entry[1][0] for result in results for entry in result] if results else []
       
        ocr_text = [entry[1][0] for result in results for entry in result] if results else []
        print("Hasil OCR:", ocr_text)  # Debug output
        return ocr_text

    def format_json(self, header, body, footer):
        transaksi = {
            "Layanan": header[0] if len(header) > 0 else "",
            "ID Invoice":"",
            "Kepada":"",
            "Tanggal":"",
            "pembayaran":"",
            "ID Transaksi":"",
            "Data":{},
            "Total":"",
        }
        # **Pisahkan data dengan regex**
        for i, text in enumerate (header):
            match = re.search(r'#\S+', text)  # Cari pola '#' diikuti teks tanpa spasi
            if match:
                transaksi["ID Invoice"] = match.group()
            elif "Invoiced To" in text and i + 1 < len(header):
                transaksi["Kepada"] = header[i + 1]if i + 1 < len(header) else None

        for j, text in enumerate (body):
            if "Description" in text and j + 1 < len(body):
                transaksi["Data"]["Deskripsi"] = body[j + 1]if j + 1 < len(body) else None
            elif "Sub Total" in text and j + 1 < len(body):
                transaksi["Data"]["Sub Total"] = int(body[j + 1].replace("Rp.","").replace(",","")if j + 1 < len(body) else None)
                transaksi["Data"]["Pajak"] = "11%"
            elif "%" in text and j + 1 < len(body):
                transaksi["Data"]["PPN"] = int(body[j + 1].replace("Rp.","").replace(",","")if j + 1 < len(body) else None)
            elif "Credit" in text and j + 1 < len(body):
                transaksi["Data"]["Credit"] = int(body[j + 1].replace("Rp.","").replace(",","")if j + 1 < len(body) else None)

        for k, text in enumerate (footer):
            if "Date" in text and k + 1 < len(footer):
                transaksi["Tanggal"] = footer[k + 4]if k + 1 < len(footer) else None
            elif "Gateway" in text and k + 1 < len(footer):
                transaksi["pembayaran"] = footer[k + 4]if k + 1 < len(footer) else None
            elif "ID" in text and k + 1 < len(footer):
                transaksi["ID Transaksi"] = footer[k + 4]if k + 1 < len(footer) else None
            elif "Amount" in text and k + 1 < len(footer):
                transaksi["Total"] = int(footer[k + 4].replace("Rp.","").replace(",","")if k + 4 < len(body) else None)

        return transaksi
    
class Struk(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ocr = PaddleOCR(lang="en")

    def post(self, request, *args, **kwargs):
        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_image = serializer.save()
            image_path = uploaded_image.image.path

            # Proses OCR setelah menyimpan gambar
            extracted_data = self.process_image(image_path)
            return Response(extracted_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def process_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Gambar tidak ditemukan atau tidak valid.")

        h, w, _ = image.shape  # Dapatkan dimensi gambar

        # **Pisahkan Body Struk**
        body = self.crop_and_ocr(image, w, h, 0, 1, 0, 1)

        # **Format hasil ke JSON**
        return self.format_json(body)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]

        temp_crop_path = "temp_cropped.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)

        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []


    def format_tanggal(self, input_text):
        match = re.search(r"(\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4})", input_text)
        if match:
            tanggal = match.group(1).replace(".", "/").strip()  
            return tanggal  
        return None 


    def get_valid_number(self, body, index):
        if index < len(body):
            text = body[index].strip()
            if re.match(r"^[=:\-]+$", text):  
                return self.sanitize_valid_number(body[index + 1]) if index + 1 < len(body) else ""
            return self.sanitize_valid_number(text)
        return ""

    def sanitize_valid_number(self, text):
        text = re.sub(r"([.,]\d{2})$", "", text)
        text = text.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","")
        return text.strip()

    def sanitize_number(self, text):
        text = re.sub(r"([.,]\d{2})$", "", text)
        text = re.sub(r"[^\d]", "", text)
        text = text.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","")
        return text.strip()

    def is_valid_amount(self, value):
        if not isinstance(value, str):  # Pastikan value adalah string
            return False
        return re.search(r"\d{1,3}([.,]\d{3})+", value) is not None

    def get_nama_toko(self, body):
        for i in range(min(len(body), 5)):
            if any(keyword in body[i].lower() for keyword in ["struk", "transaksi", "pembayaran"]):
                return body[i + 1] if i + 1 < len(body) and body[i + 1].strip() else ""

    def format_json(self, body):
        
        # Ambil nama toko
        Toko = body[0]  
        for word in body:
            result = self.get_nama_toko(body)
            if result is not None:
                Toko = result

        # Ambil tanggal
        tanggal = ""
        for line in body:
            if re.search(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}", line):
                tanggal  = self.format_tanggal(line)
        for text in body:
            if "Tanggal" in text:
                tanggal = text.split("Tanggal")[-1].strip()

        # Struktur transaksi awal
        transaksi = {
            "Nama Toko": Toko,
            "Tanggal": tanggal,
            "Data": {
                "Produk": [],
            },
            "Subtotal": 0,
            "Pajak": 0,
            "Biaya Layanan": 0,
            "Diskon": 0,
            "Lainnya": 0,
            "Grand Total": 0,
        }

        print("OCR:",body)

        i = 0
        while i < len(body):
            # SubTotal
            if any(keyword in body[i].lower() for keyword in ["subtotal", "sub total", "sub-total", "sub.ttl"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Subtotal"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Subtotal"] = int(nilai2)

            # Pajak
            elif any(keyword in body[i].lower() for keyword in ["pajak", "tax", "vat", "gst", "service charge", "sc"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Pajak"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Pajak"] = int(nilai2)

            # Biaya Layanan
            elif any(keyword in body[i].lower() for keyword in ["biaya", "charge", "fee", "service fee", "ppn", "admin fee", "ongkos", "cost","adm"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Biaya Layanan"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Biaya Layanan"] = int(nilai2) 

            # Lainnya
            elif any(keyword in body[i].lower() for keyword in ["lainnya", "miscellaneous", "other", "tambahan", "voucher", "coupon", "poin", "promo", "vc"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Lainnya"] = transaksi.get("Lainnya", 0) + int(nilai1.replace(",", "").replace(".", ""))
                elif is_valid_amount(nilai2):
                    transaksi["lainnya"] = transaksi.get("Lainnya", 0) + int(nilai2.replace(",", "").replace(".", ""))

            # Diskon
            elif any(keyword in body[i].lower() for keyword in ["diskon", "disc","discount", "potongan", "total discount"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Diskon"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Diskon"] = int(nilai2)

            # Total Bayar
            elif any(keyword in body[i].lower() for keyword in ["total:","total", "grand total", "total harga", "total belanja", "total pembayaran", "total amount", "jumlah", "total bayar","item", "tntal" ,"iten"]):
                nilai1 = self.get_valid_number(body, i + 1)
                nilai2 = self.get_valid_number(body, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 10000
                if is_valid_amount(nilai1):
                    transaksi["Grand Total"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Grand Total"] = int(nilai2)

            i += 1  

        def sanitize_number_produk(value):
            value = re.sub(r"([.,]\d{2})$", "", value)
            value = re.sub(r"[^\d]", "", value)
            value = value.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","")
            return value.strip()
       
        # Pengecekan Produk dalam Struk
        jumlah_harga_pattern = re.compile(r"(?:Rp\s*)?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?$")

        for i in range(len(body)):
            jumlah_harga_match = jumlah_harga_pattern.match(body[i].strip())

            if jumlah_harga_match:
                jumlah_harga = sanitize_number_produk(body[i].strip())
                nama_produk = None
                jumlah = None
                harga = None
            
                print("cek",jumlah_harga_match)

                if i >= 3:
                    nama_produk = body[i - 3].strip()
                if not (any(c.isalpha() for c in nama_produk)or "." in nama_produk) and i >= 2:  
                    nama_produk = body[i - 2].strip()
                if not (any(c.isalpha() for c in nama_produk)or "." in nama_produk) and i >= 1: 
                    nama_produk = body[i - 1].strip()


                # Regex pola untuk mencari jumlah dan harga dalam satu string
                regex_patterns = [
                    (r"x(\d+)\s*Rp\s*([\d.,]+)", "jumlah", "harga"),   # Contoh: "x25 Rp7.000"
                    (r"(\d+)x[@0]([\d.,]+)", "jumlah", "harga"),    # Contoh: "1x@7.000"
                    (r"x?(\d[\d.,]*)=", None, "harga"),               # Contoh: "x7.000="
                    (r"x([\d.,]+)@", None, "harga"),                  # Contoh: "x7.000@"
                    (r"(\d+)\s*x\s*Rp\s*([\d.,]+)", "jumlah", "harga"),  # Contoh: "25 x Rp 7.000"
                    (r"x(\d+)Rp([\d.,]+)", "jumlah", "harga"),           # Contoh: "x25Rp7.000"
                    (r"@([\d.,]+)x", None, "harga"),                  # Contoh: "@7.000x"
                ]   
                for j in range(1, 3): 
                    if i >= j:
                        for pattern, jumlah_group, harga_group in regex_patterns:
                            match = re.search(pattern, body[i - j])
                            if match:
                                if jumlah_group and not jumlah:
                                    jumlah = sanitize_number_produk(match.group(1))
                                if harga_group and not harga:
                                    harga = sanitize_number_produk(match.group(2) if jumlah_group else match.group(1))
                                break
                print("Jumlah",jumlah)
                print("harga",harga)

                # Regex pola untuk mencari Harga dan Jumlah dalam satu string
                regex_patterns_ = [
                    (r"Rp\s*([\d.,]+)\s*x\s*(\d+)", "harga", "jumlah"),  # Contoh: "Rp 7.000 x 25"
                    (r"(?<![a-zA-Z])([\d.,]+)x(\d+)(?![a-zA-Z])", "harga", "jumlah"),          # Contoh: "7.000x25"
                ]   
                for j in range(1, 3): 
                    if i >= j:
                        for pattern, jumlah_group, harga_group in regex_patterns_:
                            match = re.search(pattern, body[i - j])
                            if match:
                                if harga_group and not harga:
                                    harga = sanitize_number_produk(match.group(1))
                                if jumlah_group and not jumlah:
                                    jumlah = sanitize_number_produk(match.group(2) if harga_group else match.group(1))
                                break
                print("Jumlah_1",jumlah)
                print("harga_",harga)

                if jumlah and harga:
                    if  i >= 2:  
                        nama_produk = body[i - 2].strip()
                    if "." in nama_produk and i >= 1: 
                        nama_produk = body[i - 1].strip()

                if not jumlah and harga: 
                    for j in range(i-3, i):  
                        if body[j].isdigit():  
                            jumlah_int = int(body[j])
                            if 1 <= jumlah_int <= 1000:  
                                jumlah = jumlah_int 
                                break 

                # Validasi dengan Pola dengan regex
                pattern_1 = r'([\w\s-]+)\s+(\d{1,2})\s+([\d,.]+)\s+([\d,.]+)'  # Pola Nama, Jumlah, Harga, Total
                match_1 = re.fullmatch(pattern_1, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_1:
                    nama_produk = match_1.group(1).strip() + body[i + 1]
                    jumlah = sanitize_number_produk(match_1.group(2))
                    harga = sanitize_number_produk(match_1.group(3))
                    jumlah_harga = sanitize_number_produk(match_1.group(4))

                pattern_2 = r'(\d{1,2})\s+([\d,.]+)\s+([\w\s-]+)\s+([\d,.]+)'  #Pola Jumlah, Harga, Nama, Total
                match_2 =  re.fullmatch(pattern_2, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_2:
                    nama_produk = match_2.group(3).strip()
                    jumlah = sanitize_number_produk(match_2.group(1))
                    harga = sanitize_number_produk(match_2.group(2))
                    jumlah_harga = sanitize_number_produk(match_2.group(4))

                pattern_3 = r'(\d{1,2})\s+([\w\s-]+)\s+([\d,.]+)\s+([\d,.]+)' #Pola Jumlah, Nama, Harga, Total
                match_3 =  re.fullmatch(pattern_3, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_3:
                    nama_produk = match_3.group(2).strip()
                    jumlah = sanitize_number_produk(match_3.group(1))
                    harga = sanitize_number_produk(match_3.group(3))
                    jumlah_harga = sanitize_number_produk(match_3.group(4))

                pattern_4 = r'([\w\s-]+)\s+([\d,.]+)\s+(\d{1,2})\s+([\d,.]+)' #Pola Nama, Harga, Jumlah, Total
                match_4 =  re.fullmatch(pattern_4, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_4:
                    nama_produk = match_4.group(1).strip()
                    jumlah = sanitize_number_produk(match_4.group(3))
                    harga = sanitize_number_produk(match_4.group(2))
                    jumlah_harga = sanitize_number_produk(match_4.group(4))

                pattern_5 = r"([\d,.]+)\s+([\w\s-]+)\s+(\d{1,2})\s+([\d,.]+)" #Pola Total, Nama, Jumlah, Harga
                match_5 =  re.fullmatch(pattern_5, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_5:
                    nama_produk = match_5.group(2).strip()
                    jumlah = sanitize_number_produk(match_5.group(3))
                    harga = sanitize_number_produk(match_5.group(4))
                    jumlah_harga = sanitize_number_produk(match_5.group(1))

                pattern_6 = r"([\w\s-]+)\s+([\d,.]+)\s+(\d{1,2})\s+([\d,.]+)" #Pola Nama, Total, Jumlah, Harga
                match_6 =  re.fullmatch(pattern_6, f"{body[i-3]} {body[i-2]} {body[i-1]} {body[i]}".strip())
                if match_6:
                    nama_produk = match_6.group(1).strip()
                    jumlah = sanitize_number_produk(match_6.group(3))
                    harga = sanitize_number_produk(match_6.group(4))
                    jumlah_harga = sanitize_number_produk(match_6.group(2))

                # Hitung harga per unit jika jumlah dan jumlah_harga tersedia
                if not harga and jumlah and jumlah_harga:
                    harga = int(jumlah_harga) // int(jumlah) if int(jumlah) != 0 else None

                # Cek validitas produk sebelum menambahkan ke transaksi
                valid_produk = (
                    nama_produk and any(c.isalpha() for c in nama_produk)  
                    and jumlah and int(jumlah) <= 100
                    and harga and jumlah_harga 
                )

                if valid_produk:
                    transaksi["Data"]["Produk"].append({
                        "Nama": nama_produk,
                        "Jumlah": int(jumlah),
                        "Harga": int(harga),
                        "Jumlah Harga": int(jumlah_harga)
                    })

        with open("hasil_transaksi.json", "w") as file:
            json.dump(transaksi, file, indent=4)

        print("Transaksi berhasil disimpan sebagai hasil_transaksi.json")

        return transaksi