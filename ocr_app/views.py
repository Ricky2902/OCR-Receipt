import easyocr
from paddleocr import PaddleOCR
import json
import re
import cv2
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import UploadedImage, DataStruk, DataProduk, DataBensin
from .serializers import ImageSerializer, StrukSerializer, BensinSerializer
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

def upload_Home(request):
    return render(request, 'ocr_app/Home.html') 
def upload_Struk(request):
    return render(request, 'ocr_app/Struk.html')
def upload_Struk3(request):
    return render(request, 'ocr_app/Struk3.html')
def Split_Bill(request):
    return render(request, 'ocr_app/Split.html')  
def upload_Bensin(request):
    return render(request, 'ocr_app/Bensin.html') 
def Daftarlist(request):
    return render(request, 'ocr_app/StrukList.html')

@csrf_exempt
def save_struk(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("data",data)

            nama_toko = data.get("Nama Toko", "")
            tanggal = data.get("Tanggal", "")

            subtotal = data.get("Subtotal", "")
            pajak = data.get("Pajak", "")
            biaya_layanan = data.get("Biaya Layanan", "")
            diskon = data.get("Diskon", "")
            lainnya = data.get("Lainnya", "")
            grand_total = data.get("Grand Total", "")

            # Simpan struk
            struk = DataStruk.objects.create(
                nama_toko=nama_toko,
                tanggal=tanggal,
                subtotal=subtotal,
                pajak=pajak,
                biaya_layanan=biaya_layanan,
                diskon=diskon,
                lainnya=lainnya,
                grand_total=grand_total
            )

            # Simpan produk-produk terkait
            for item in data.get("Data", {}).get("Produk", []):
                DataProduk.objects.create(
                    struk=struk,
                    nama=item.get("Nama", ""),
                    jumlah=item.get("Jumlah", ""),
                    harga=item.get("Harga", ""),
                    jumlah_harga=item.get("Jumlah Harga", "")
                )

            return JsonResponse({"status": "success", "message": "Data struk berhasil disimpan."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Terjadi kesalahan: {e}"})
    else:
        return JsonResponse({"status": "error", "message": "Metode tidak diizinkan."})
@csrf_exempt
def save_bensin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("data",data)

            nama_SPBU = data.get("Nama SPBU", "")
            tanggal = data.get("Tanggal", "")
            total_bayar = data.get("Total Harga", "")
            harga_per_liter = data.get("Nominal", "")
            jumlah_liter = data.get("Volume", "")

            # Simpan data Bensin
            bensin = DataBensin.objects.create(
                nama_SPBU=nama_SPBU,
                tanggal=tanggal,
                total_bayar=total_bayar,
                harga_per_liter=harga_per_liter,
                jumlah_liter=jumlah_liter
            )

            return JsonResponse({"status": "success", "message": "Data Bensin berhasil disimpan."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Terjadi kesalahan: {e}"})
    else:
        return JsonResponse({"status": "error", "message": "Metode tidak diizinkan."})

@api_view(['GET'])
def struk_list(request):
    struks = DataStruk.objects.all()
    serializer = StrukSerializer(struks, many=True)
    return Response(serializer.data)
@api_view(['GET'])
def bensin_list(request):
    bensins = DataBensin.objects.all()
    serializer2 = BensinSerializer(bensins, many=True)
    return Response(serializer2.data)

class StrukTerbaruView(APIView):
    def get(self, request, struk_id):
        struk = DataStruk.objects.get(id = struk_id)
        produk = DataProduk.objects.filter(struk_id=struk)

        # Format data untuk JSON
        data = {
            "toko": struk.nama_toko,
            "tanggal": struk.tanggal,
            "produk": [
                {
                    "namaProduk": p.nama,
                    "jumlah": p.jumlah,
                    "harga": p.harga,
                    "jumlahHarga": p.jumlah_harga
                } for p in produk
            ],
            "summary": {
                "Subtotal": struk.subtotal,
                "Pajak": struk.pajak,
                "Biaya Layanan": struk.biaya_layanan,
                "Diskon": struk.diskon,
                "Lainnya": struk.lainnya,
                "Grand Total": struk.grand_total
            }
        }
        return Response(data)

class bensinTerbaruView(APIView):
    def get(self, request, bensin_id):
        bensin = DataBensin.objects.get(id=bensin_id)

        # Format data untuk JSON
        data = {
            "nama_SPBU": bensin.nama_SPBU,
            "tanggal": bensin.tanggal,
            "total_bayar": bensin.total_bayar,
            "harga_per_liter": bensin.harga_per_liter,
            "jumlah_liter": bensin.jumlah_liter
        }
        return Response(data)
    
class Bensin(APIView):
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

        temp_crop_path = "Crop/temp_cropped_Bensin.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)

        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def extract_number(self,text):
        # Hapus titik sebagai pemisah ribuan (misal: 12.000 → 12000)
        cleaned_text = text.replace(".", "").replace(",","")
        # Ambil hanya angka
        numbers = re.findall(r"\d+", cleaned_text)
        # Jika ada angka yang ditemukan, gabungkan dan kembalikan sebagai integer
        return int("".join(numbers)) if numbers else 0
    
    def clear_vol(self,text):
        vol = text.replace("L","")
        return vol
    
    def format_tanggal(self, input_text):
        match = re.search(r"(\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4})", input_text)
        if match:
            tanggal = match.group(1).replace(".", "/").strip()  
            return tanggal  
        return None
    
    def get_nama_toko(self, body):
        keywords = {"shell", "pertamina","spbu", "vivo", "bp", "akr"}  # Set untuk pencarian lebih cepat
        for line in body:
            for keyword in keywords:
                if keyword in line.lower():
                    return keyword  # Hanya mengembalikan keyword yang cocok
        return None  # Jika tidak ada yang cocok, kembalikan None
    
    def SPBU(self, text):
        if text == "shell":
            return "SHELL"
        if text == "vivo":
            return "VIVO"

    def extract_and_format_flexible(self, data):
            digits = re.findall(r'\d+', data)
            combined = ''.join(digits)

            if len(combined) >= 10:
                nilai1_raw = combined[:5]
                nilai2_raw = combined[5:10]
                nilai1 = int(nilai1_raw)
                nilai2 = int(nilai2_raw)
                return nilai1, nilai2
    
    def extract_and_format_flexible2(self, data):
        pattern = r'(\d{1,3}\.\d{3})(\d{1,3}\.\d{3})(\d{1,3}\.\d{2})'
        match = re.fullmatch(pattern, data)
        if match:
            volume = int(match.group(1).replace('.', ''))
            nominal = int(match.group(2).replace('.', ''))
            return volume, nominal
        
    def format_tiga_angka_belakang(self, value):
        value_str = str(value)
        if len(value_str) <= 2:
            return f"0,{value_str.zfill(2)}"
        return f"{value_str[:-3]}.{value_str[-3:]}"
    
    def format_total_Harga(self, value):
        value_str = str(value)
        if len(value_str) <= 2:
            return f"0,{value_str.zfill(2)}"
        return f"{value_str[:-3]}"

    def format_json(self, body):
        # **Deteksi Nama Toko**
        nama_toko = self.get_nama_toko(body) or body[0].lower
        print("bod", body)
        # **Pilih metode parsing berdasarkan toko**
        if nama_toko in ["bp", "akr"]:
            return self.parse_bp_akr(body)
        elif nama_toko in ["pertamina","spbu"]:  
            return self.parse_pertamina(body)  
        else:
            return self.parse_generic_receipt(body, nama_toko)
                
    def parse_generic_receipt(self, body, nama_toko):

        toko = self.SPBU(nama_toko)
        transaksi = {
            "Nama SPBU": toko,
            "Tanggal": "",
            "Produk": "",
            "Nominal": 0,
            "Volume": "",
            "Total Harga": 0,
        }
        found_nominal = False

        tanggal_pattern = r"\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}"
        for i in range(len(body)):
             # Ambil Tanggal
            if not transaksi["Tanggal"]:
                match = re.search(tanggal_pattern, body[i], re.IGNORECASE)
                if match:
                    date = match.group().strip()
                    transaksi["Tanggal"] = date

            # Produk
            if any(keyword in body[i].lower() for keyword in ["grade", "product", "produk", "produet", "nama produk"]):
                transaksi["Produk"] = body[i + 1] if i + 1 < len(body) else ""

            # Nominal
            if not found_nominal and any(keyword in body[i].lower() for keyword in ["unit price", "price", "harga", "harga/liter"]):
                transaksi["Nominal"] = self.extract_number(body[i + 1]) if i + 1 < len(body) else 0
                found_nominal = True  

            # Volume
            if any(keyword in body[i].lower() for keyword in ["volume", "quantity", "total quantity"]):
                transaksi["Volume"] =  self.clear_vol(body[i + 1]) if i + 1 < len(body) else 0 

            # Total Harga
            if any(keyword in body[i].lower() for keyword in ["amount", "total", "total harga", "nominal"]):
                transaksi["Total Harga"] = self.extract_number(body[i + 1]) if i + 1 < len(body) else 0

        return transaksi
    
    def parse_bp_akr(self, body):
        transaksi = {
            "Nama SPBU": "BP AKR",
            "Tanggal": "",
            "Produk": "",
            "Nominal": 0,
            "Volume": 0,
            "Total Harga": 0,
        }

        # Pattern tanggal fleksibel (dengan bulan teks + opsional prefix "date:" atau "tgl:")
        tanggal_pattern = r"(?:date|tgl)?[:\s-]*\d{1,2}[-\s](?:[A-Za-z]{3,})[-\s]?\d{2,4}"

        for i in range(len(body)):
            line = body[i]

            # Ambil Tanggal
            if not transaksi["Tanggal"]:
                match = re.search(tanggal_pattern, line, re.IGNORECASE)
                if match:
                    date = match.group().strip().replace("Date:","").replace("Date","")
                    transaksi["Tanggal"] = date
            
            # Cek apakah cocok dengan format volume+nominal
            if re.fullmatch(r'\d{10,}|\d{1,3}\.\d{2,3}\d{1,3}\.\d{2,3}', line):
                previous_line = body[i - 1] if i > 0 else ""
                transaksi["Produk"] = previous_line
                volume, nominal = self.extract_and_format_flexible(line)
                if volume and nominal:
                    transaksi["Volume"] = self.format_tiga_angka_belakang(volume)
                    transaksi["Nominal"] = nominal
                    transaksi["Total Harga"] = self.format_total_Harga(volume * nominal)

            if re.fullmatch(r'\d{1,3}\.\d{3}\d{1,3}\.\d{3}\d{1,3}\.\d{2}', line):
                previous_line = body[i - 1] if i > 0 else ""
                transaksi["Produk"] = previous_line

                volume, nominal = self.extract_and_format_flexible2(line)
                if volume and nominal:
                    transaksi["Volume"] = self.format_tiga_angka_belakang(volume)
                    transaksi["Nominal"] = nominal
                    transaksi["Total Harga"] = self.format_total_Harga(volume * nominal)
        return transaksi
    
    def parse_pertamina(self, body):

        transaksi = {
            "Nama SPBU": "PERTAMINA",
            "Tanggal": "",
            "Produk": "",
            "Nominal": 0,
            "Volume": "",
            "Total Harga": 0,
        }
        found_nominal = False

        tanggal_pattern = r"\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}"
        for i in range(len(body)):
             # Ambil Tanggal
            if not transaksi["Tanggal"]:
                match = re.search(tanggal_pattern, body[i], re.IGNORECASE)
                if match:
                    date = match.group().strip()
                    transaksi["Tanggal"] = date

            # Produk
            if any(keyword in body[i].lower() for keyword in ["produk", "nama produk"]):
                transaksi["Produk"] = body[i + 1] if i + 1 < len(body) else ""

            # Nominal
            if not found_nominal and any(keyword in body[i].lower() for keyword in [ "harga", "harga/liter"]):
                transaksi["Nominal"] = self.extract_number(body[i + 1]) if i + 1 < len(body) else 0
                found_nominal = True  

            # Volume
            if any(keyword in body[i].lower() for keyword in ["volume", "volune"]):
                transaksi["Volume"] =  self.clear_vol(body[i + 1]) if i + 1 < len(body) else 0 

            # Total Harga
            if any(keyword in body[i].lower() for keyword in [ "total", "total harga", "nominal"]):
                transaksi["Total Harga"] = self.extract_number(body[i + 1]) if i + 1 < len(body) else 0

        if transaksi["Nominal"] == 0 and transaksi["Total Harga"] == 0:
            produk_keywords = ["pertalite", "pertamax", "pertamax dex", "pertamax green", "pertamax turbo", "solar"]
            
            for i in range(len(body)):
                line = body[i].lower()
                
                # Cari nama produk
                for keyword in produk_keywords:
                    if keyword in line:
                        transaksi["Produk"] = keyword
                        break  # Keluar dari loop jika sudah ketemu

                # Cari nominal (harga/liter)
                if any(x in line for x in ["harga/liter", "unit price", "price"]):
                    match = re.search(r"\d[\d.,]*", line)
                    if match:
                        transaksi["Nominal"] = self.extract_number(match.group())

                # Cari total harga
                transaksi["Total Harga"] = float(transaksi["Volume"])*transaksi["Nominal"]
        return transaksi

class Struk4(APIView):
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

        temp_crop_path = "Crop/temp_cropped_Bill.jpg"
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
        text = text.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","").replace("@","").replace("x","").replace("X","")
        return text.strip()

    def sanitize_number(self, text):
        text = re.sub(r"([.,]\d{2})$", "", text)
        text = re.sub(r"[^\d]", "", text)
        text = text.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","").replace("@","").replace("x","").replace("X","")
        return text.strip()
    
    def clear_jumlah(self, jumlah):
        if jumlah:
            jumlah = ''.join(filter(str.isdigit, str(jumlah)))
        return jumlah or "0"

    def is_valid_amount(self, value):
        if not isinstance(value, str):  # Pastikan value adalah string
            return False
        return re.search(r"\d{1,3}([.,]\d{3})+", value) is not None

    def get_nama_toko(self, body):
        keywords = {"struk", "transaksi", "pembayaran", "receipt"}  # Gunakan set untuk pencarian lebih cepat
        for i in range(min(len(body), 5)):
            if any(keyword in body[i].lower() for keyword in keywords):
                if i + 1 < len(body) and body[i + 1].strip():
                    if not any(keyword in body[i + 1].lower() for keyword in keywords):
                        return body[i + 1]
        return body[0]
    
    def clean_text(self, body):
        """ Membersihkan angka yang typo tanpa mengubah teks lainnya """
        def fix_numbers(match):
            return match.group(1).replace('O', '0').replace('C', '0').replace('l', '1').replace('J', "0")

        # Jika body berupa string, langsung bersihkan
        if isinstance(body, str):
            body2 = re.sub(r'(\b[\dOCoCIlJ]+\b)', fix_numbers, body)
        
        # Jika body adalah JSON (dictionary atau list), perbaiki teksnya satu per satu
        elif isinstance(body, dict):
            body2 = {key: self.clean_text(value) if isinstance(value, str) else value for key, value in body.items()}
        
        elif isinstance(body, list):
            body2 = [self.clean_text(item) if isinstance(item, str) else item for item in body]

        else:
            raise ValueError("Format body tidak dikenali")

        return body2
        

    def format_json(self, body):
        
        fixbody = self.clean_text(body)
        
        # Jika hasilnya list atau dict, tidak diubah menjadi JSON string
        if isinstance(fixbody, (list, dict)):
            body2 = fixbody
        else:
            body2 = json.loads(json.dumps(fixbody))  # Ini hanya untuk normalisasi jika diperlukan

        print("body", body)
        print("fixbody", body2)        

        # Ambil nama toko
        Toko = body2[0]  
        for word in body:
            result = self.get_nama_toko(body2)
            if result is not None:
                Toko = result

        # Ambil tanggal
        tanggal = ""
        for line in body2:
            if re.search(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}", line):
                tanggal  = self.format_tanggal(line)
        for text in body2:
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

        i = 0
        while i < len(body2):
            # SubTotal
            if any(keyword in body2[i].lower() for keyword in ["subtotal", "sub total", "sub-total", "sub.ttl", "harga jual"]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Subtotal"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Subtotal"] = int(nilai2)

            # Pajak
            elif any(keyword in body2[i].lower() for keyword in ["pajak", "tax", "vat", "gst", "service charge", "ppn", "pb1", "pb"]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Pajak"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Pajak"] = int(nilai2)

            # Biaya Layanan
            elif any(keyword in body2[i].lower() for keyword in ["biaya", "charge", "fee", "service fee", "sc", "admin fee", "ongkos", "cost","adm"]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Biaya Layanan"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Biaya Layanan"] = int(nilai2) 

            # Lainnya
            elif any(keyword in body2[i].lower() for keyword in ["lainnya", "miscellaneous", "other", "tambahan", "voucher", "coupon", "poin", "promo", "vc" ]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Lainnya"] = transaksi.get("Lainnya", 0) + int(nilai1.replace(",", "").replace(".", ""))
                elif is_valid_amount(nilai2):
                    transaksi["lainnya"] = transaksi.get("Lainnya", 0) + int(nilai2.replace(",", "").replace(".", ""))

            # Diskon
            elif any(keyword in body2[i].lower() for keyword in ["diskon", "disc","discount", "potongan", "total discount", "anda hemat"]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
                def is_valid_amount(value):
                    return value.isdigit() and int(value) >= 1000 
                if is_valid_amount(nilai1):
                    transaksi["Diskon"] = int(nilai1)
                elif is_valid_amount(nilai2):
                    transaksi["Diskon"] = int(nilai2)

            # Total Bayar
            elif any(keyword in body2[i].lower() for keyword in ["total:","total", "grand total", "total harga", "total belanja", "total pembayaran", "total amount", "jumlah", "total bayar","item", "tntal" ,"iten"]):
                nilai1 = self.get_valid_number(body2, i + 1)
                nilai2 = self.get_valid_number(body2, i + 2)
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
            value = value.replace(",", "").replace(".", "").replace("=","").replace("@","").replace(":","").replace("-","").replace("Rp","").replace("Re","").replace("Fp","").replace("R","").replace("x","").replace("X","")
            return value.strip()
        
        self.jumlah_harga_pattern = re.compile(r"(?:Rp\s*)?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?$")
        self.regex_patterns = [
            (r"x(\d+)\s*Rp\s*([\d.,]+)", "jumlah", "harga"),  # Mencari pola seperti "x25 Rp 7.000" -> jumlah = 25, harga = 7.000
            (r"(\d+)x[@0]([\d.,]+)", "jumlah", "harga"),  # Mencari pola seperti "25x@7000" atau "25x07000" -> jumlah = 25, harga = 7000
             (r"(\d+)x([\d.,]+)", "jumlah", "harga"),  # Mencari pola seperti "25x@7000" atau "25x07000" -> jumlah = 25, harga = 7000
            (r"x?(\d[\d.,]*)=", None, "harga"),  # Mencari pola seperti "x7000=" atau "7000=" -> harga = 7000
            (r"x([\d.,]+)@", None, "harga"),  # Mencari pola seperti "x7000@" -> harga = 7000
            (r"(\d+)\s*x\s*Rp\s*([\d.,]+)", "jumlah", "harga"),  # Mencari pola seperti "25 x Rp 7.000" -> jumlah = 25, harga = 7.000
            (r"(\d+)\s*X\s*Rp\s*([\d\.]+)", "jumlah", "harga"), # Mencari pola seperti "25x Rp 7.000" -> jumlah = 25, harga = 7.000
            (r"@([\d.,]+)x", None, "harga"),  # Mencari pola seperti "@7000x" -> harga = 7000
            (r"([\d.,]+)x", "jumlah", None),  # Mencari pola seperti "1x" -> jumlah = 1
        ]
        self.regex_patterns_ = [
            (r"Rp\s*([\d.,]+)\s*x\s*(\d+)", "harga", "jumlah"),  # Mencari pola seperti "Rp 7.000 x 25" -> harga = 7.000, jumlah = 25
            (r"([\d.,]+)\s*x\s*(\d+)", "harga", "jumlah"),  # Mencari pola seperti "7.000 x 25"-> harga = 7.000, jumlah = 25
            (r"@([\d.,])","harga", None),  # Mencari pola seperti "@7000" -> harga = 7000
        ]
        self.pola_patterns = [
            r'((?=.*[A-Za-z])[\w\s.-]+)\s+(\d{1,3}+[xX]?)\s+(@?[\d,.]+)\s+([\d,.]+)',  # Nama Produk -> Jumlah -> Harga -> Total Harga | Contoh: "Roti Tawar 3 5.000 10.000"
            r'(\d{1,3})\s+([\d,.]+)\s+((?=.*[A-Za-z])[\w\s.-]+)\s+([\d,.]+)',  # Jumlah -> Harga -> Nama Produk -> Total Harga | Contoh: "2 5.000 Roti Tawar 10.000"
            r'(\d{1,3})\s+((?=.*[A-Za-z])[\w\s.-]+)\s+([\d,.]+)\s+([\d,.]+)',  # Jumlah -> Nama Produk -> Harga -> Total Harga | Contoh: "2 Roti Tawar 5.000 10.000"
            r'((?=.*[A-Za-z])[\w\s.-]+)\s+([\d,.]+)\s+(\d{1,3})\s+([\d,.]+)',  # Nama Produk -> Harga -> Jumlah -> Total Harga | Contoh: "Roti Tawar 5.000 3 10.000"
            r'([\d,.]+)\s+((?=.*[A-Za-z])[\w\s.-]+)\s+(\d{1,3})\s+([\d,.]+)',  # Harga -> Nama Produk -> Jumlah -> Total Harga | Contoh: "5.000 Roti Tawar 3 10.000"
            r'((?=.*[A-Za-z])[\w\s.-]+)\s+([\d,.]+)\s+(\d{1,3})\s+([\d,.]+)',  # Nama Produk -> Harga -> Jumlah -> Total Harga | Contoh: "Roti Tawar 5.000 3 10.000"
        ]


        pola_utama = None

        for i in range(len(body2)):
            if not self.jumlah_harga_pattern.match(body2[i].strip()):
                continue
            
            jumlah_harga = sanitize_number_produk(body2[i].strip())
            nama_produk, jumlah, harga = None, None, None
            regex_success = False

            print("CEK Nilai :", body2[i])
            if i >= 3:
                nama_produk = body2[i - 3].strip()
                if not (any(c.isalpha() for c in nama_produk)or "Rp" in nama_produk) and i >= 2:  
                    nama_produk = body2[i - 2].strip()
                if not (any(c.isalpha() for c in nama_produk)or "Rp" in nama_produk) and i >= 1: 
                    nama_produk = body2[i - 1].strip()

            for j in range(1, 3):
                if i >= j:
                    for pattern, jumlah_group, harga_group in self.regex_patterns:
                        match = re.search(pattern, body2[i - j])
                        if match:
                            regex_success = True
                            jumlah = sanitize_number_produk(match.group(1)) if jumlah_group else jumlah
                            harga = sanitize_number_produk(match.group(2 if jumlah_group else 1)) if harga_group else harga
                            break
            print("Jumlah",jumlah)
            print("harga",harga)

            for j in range(1, 3): 
                if i >= j:
                    for pattern, jumlah_group, harga_group in self.regex_patterns_:
                        match = re.search(pattern, body2[i - j])
                        if match:
                            regex_success = True
                            if harga_group and not harga:
                                harga = sanitize_number_produk(match.group(1))
                            if jumlah_group and not jumlah:
                                jumlah = sanitize_number_produk(match.group(2) if harga_group else match.group(1))
                            break
            print("Jumlah_1",jumlah)
            print("harga_",harga)
            
            if jumlah and harga:
                    if  i >= 2:  
                        nama_produk = body2[i - 2].strip()
                    if "." in nama_produk and i >= 1: 
                        nama_produk = body2[i - 1].strip()

            if not harga and jumlah:
                # Cek harga dari baris sebelum atau sesudah baris jumlah
                for j in [i-1, i+1]:
                    if 0 <= j < len(body2):  # pastikan index valid
                        candidate = body2[j]
                        if candidate:
                            # Regex cari angka (dengan atau tanpa '@', titik/koma ribuan)
                            match = re.search(r'@?\s?([\d.,]+)', candidate)
                            if match:
                                harga_str = match.group(1).replace(',', '').replace('.', '').replace("@","")
                                harga = harga_str
                                break

            if not jumlah and harga: 
                for j in range(i-3, i):  
                    if body2[j].isdigit():  
                        jumlah_int = int((body2[j]))
                        if 1 <= jumlah_int <= 500:  
                            jumlah = jumlah_int 
                            break 

            valid_produk = (
                nama_produk and any(c.isalpha() for c in nama_produk)
                and jumlah and int(jumlah) <= 500
                and int(sanitize_number_produk(harga)) >= 100 and int(sanitize_number_produk(jumlah_harga)) >= 100
            )
            print("Nam_1",nama_produk)
            print("har_1",harga)
            print("Jum_1",jumlah)
            print("Tol_1",jumlah_harga)
            
            if valid_produk:
                transaksi["Data"]["Produk"].append({
                        "Nama": nama_produk,
                        "Jumlah": jumlah,
                        "Harga": harga,
                        "Jumlah Harga": jumlah_harga
                    })
            if regex_success:
                continue

            pola_ditemukan = False
            pola_check = [pola_utama] if pola_utama else self.pola_patterns

            for pattern in pola_check:
                match = re.fullmatch(pattern, f"{body2[i-3]} {body2[i-2]} {body2[i-1]} {body2[i]}".strip())
                if match:
                    pola_ditemukan = True
                    if pola_utama is None:
                        pola_utama = pattern
                    
                    if pattern == self.pola_patterns[0]:
                        nama_produk, jumlah, harga, jumlah_harga = match.groups()
                    elif pattern == self.pola_patterns[1]:
                        jumlah, harga, nama_produk, jumlah_harga = match.groups()
                    elif pattern == self.pola_patterns[2]:
                        jumlah, nama_produk, harga, jumlah_harga = match.groups()
                    elif pattern == self.pola_patterns[3]:
                        nama_produk, harga, jumlah, jumlah_harga = match.groups()
                    elif pattern == self.pola_patterns[4]:
                        jumlah_harga, nama_produk, jumlah, harga = match.groups()
                    elif pattern == self.pola_patterns[5]:
                        nama_produk, jumlah_harga, jumlah, harga = match.groups()

                    break
          
            if not harga and jumlah and jumlah_harga:
                harga = int(jumlah_harga) // int(jumlah) if int(jumlah) != 0 else None

            if not jumlah and harga and jumlah_harga:
                jumlah = int(jumlah_harga)// int(harga) if int(jumlah_harga) >= int(harga) else None

            valid_produk = (
                nama_produk and any(c.isalpha() for c in nama_produk)
                and jumlah and int(jumlah) <= 500
                and int(sanitize_number_produk(harga)) >= 100 and int(sanitize_number_produk(jumlah_harga)) >= 100
            )
            print("patt",pattern)
            print("Nam_2",nama_produk)
            print("har_2",harga)
            print("Jum_2",jumlah)
            print("Tol_2",jumlah_harga)
            
            if valid_produk:
                transaksi["Data"]["Produk"].append({
                    "Nama": nama_produk.strip(),
                    "Jumlah": int(sanitize_number_produk(jumlah)),
                    "Harga": int(sanitize_number_produk(harga)),
                    "Jumlah Harga": int(sanitize_number_produk(jumlah_harga))
                })

        return transaksi

class Struk3(APIView):
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

        h, w, _ = image.shape
        body = self.crop_and_ocr(image, w, h, 0, 1, 0, 1)
        return self.format_json(body)

    def crop_and_ocr(self, image, w, h, x_start, x_end, y_start, y_end):
        start_x, end_x = int(w * x_start), int(w * x_end)
        start_y, end_y = int(h * y_start), int(h * y_end)
        cropped_image = image[start_y:end_y, start_x:end_x]
        temp_crop_path = "Crop/temp_cropped_Struk3.jpg"
        cv2.imwrite(temp_crop_path, cropped_image)
        results = self.ocr.ocr(temp_crop_path, cls=False)
        return [entry[1][0] for result in results for entry in result] if results else []

    def sanitize_number(self, text):
        text = re.sub(r"[^\d]", "", text)
        return text.strip()

    def format_tanggal(self, input_text):
        match = re.search(r"(\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4})", input_text)
        if match:
            tanggal = match.group(1).replace(".", "/").strip()
            return tanggal
        return ""

    def get_nama_toko(self, body):
        # Ambil baris pertama yang bukan angka sebagai nama toko
        for line in body:
            if any(c.isalpha() for c in line):
                return line
        return body[0] if body else ""

    def format_json(self, body):
        print("=== HASIL OCR ===")
        for idx, line in enumerate(body):
            print(f"{idx}: {repr(line)}")
        print("=================")
    
        # --- Ambil Nama Toko & Tanggal ---
        Toko = self.get_nama_toko(body)
        tanggal = ""
        for line in body:
            if re.search(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{2,4}", line):
                tanggal = self.format_tanggal(line)
                break
    
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
    
        # --- Ambil Subtotal, Pajak, dst ---
        for i, line in enumerate(body):
            l = line.lower()
            if any(k in l for k in ["subtotal", "sub total", "sub-total", "sub.ttl", "harga jual"]):
                transaksi["Subtotal"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
            elif any(k in l for k in ["pajak", "tax", "vat", "gst", "service charge", "ppn", "pb1", "pb"]):
                transaksi["Pajak"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
            elif any(k in l for k in ["biaya", "charge", "fee", "service fee", "sc", "admin fee", "ongkos", "cost","adm"]):
                transaksi["Biaya Layanan"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
            elif any(k in l for k in ["lainnya", "miscellaneous", "other", "tambahan", "voucher", "coupon", "poin", "promo", "vc"]):
                transaksi["Lainnya"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
            elif any(k in l for k in ["diskon", "disc","discount", "potongan", "total discount", "anda hemat"]):
                transaksi["Diskon"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
            elif any(k in l for k in ["total:","total", "grand total", "total harga", "total belanja", "total pembayaran", "total amount", "jumlah", "total bayar","item", "tntal" ,"iten"]):
                transaksi["Grand Total"] = int(self.sanitize_number(body[i+1])) if i+1 < len(body) else 0
    
        produk_list = []
        summary_keywords = [
            "total", "payment", "bayar", "kembali", "cash", "change", "grand", "jumlah", "subtotal", "pajak", "diskon", "service", "admin", "biaya", "lainnya"
        ]
        for i, line in enumerate(body):
            baris = line.strip()
            # Cari angka besar di akhir baris (jumlah harga)
            match_total = re.search(r'([\d.,]{4,})\s*$', baris)
            if match_total:
                jumlah_harga_str = match_total.group(1)
                jumlah_harga = int(self.sanitize_number(jumlah_harga_str))
    
                # Cek 2 baris sebelumnya untuk pattern produk
                found = False
                for offset in [1, 2]:
                    if i - offset < 0:
                        continue
                    prev_line = body[i - offset].strip()
                    # Skip jika baris sebelumnya mengandung kata summary
                    if any(k in prev_line.lower() for k in summary_keywords):
                        continue
                    # Pattern: nama_barang jumlah
                    match = re.match(r'(.+)\s+(\d{1,3})$', prev_line)
                    if match:
                        nama_produk = match.group(1)
                        jumlah = int(self.sanitize_number(match.group(2)))
                        harga = jumlah_harga // jumlah if jumlah else 0
                        if nama_produk and jumlah and harga > 0 and jumlah_harga > 0:
                            produk_list.append({
                                "Nama": nama_produk.strip(),
                                "Jumlah": jumlah,
                                "Harga": harga,
                                "Jumlah Harga": jumlah_harga
                            })
                            print(f"Produk ditemukan: {nama_produk}, {jumlah}, {harga}, {jumlah_harga}")
                            found = True
                            break
                    # Pattern: jumlah nama_barang
                    match = re.match(r'(\d{1,3})\s+(.+)', prev_line)
                    if match:
                        jumlah = int(self.sanitize_number(match.group(1)))
                        nama_produk = match.group(2)
                        harga = jumlah_harga // jumlah if jumlah else 0
                        if nama_produk and jumlah and harga > 0 and jumlah_harga > 0:
                            produk_list.append({
                                "Nama": nama_produk.strip(),
                                "Jumlah": jumlah,
                                "Harga": harga,
                                "Jumlah Harga": jumlah_harga
                            })
                            print(f"Produk ditemukan: {nama_produk}, {jumlah}, {harga}, {jumlah_harga}")
                            found = True
                            break
                # Jika tidak ditemukan pattern, cek baris sebelumnya hanya nama
                if not found and i - 1 >= 0:
                    prev_line = body[i - 1].strip()
                    if not any(k in prev_line.lower() for k in summary_keywords) and any(c.isalpha() for c in prev_line):
                        nama_produk = prev_line
                        jumlah = 1
                        harga = jumlah_harga
                        produk_list.append({
                            "Nama": nama_produk.strip(),
                            "Jumlah": jumlah,
                            "Harga": harga,
                            "Jumlah Harga": jumlah_harga
                        })
                        print(f"Produk ditemukan (default jumlah=1): {nama_produk}, {jumlah}, {harga}, {jumlah_harga}")
    
        transaksi["Data"]["Produk"] = produk_list
    
        print("=== PRODUK YANG MASUK ===")
        for p in transaksi["Data"]["Produk"]:
            print(p)
        print("=========================")
    
        return transaksi