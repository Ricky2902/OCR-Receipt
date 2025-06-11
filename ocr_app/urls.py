from django.urls import path
from .views import Bensin
from .views import Struk4
from .views import Struk3
from .views import upload_Struk
from .views import upload_Struk3
from .views import upload_Bensin
from .views import upload_Home
from .views import Daftarlist
from .views import Split_Bill
from .views import save_struk
from .views import save_bensin
from .views import struk_list
from .views import bensin_list
from .views import StrukTerbaruView
from .views import bensinTerbaruView

urlpatterns = [
  
    path("Bensin/", Bensin.as_view(), name="Bensin"),
    path("Struk/", Struk4.as_view(), name="Struk"),
    path("Struk3/", Struk3.as_view(), name="Struk3"),
    path('Home', upload_Home, name='upload_Home'),
    path('upload-struk/', upload_Struk, name='upload_Struk'),
    path('upload-struk3/', upload_Struk3, name='upload_Struk3'),
    path('Daftar-list/', Daftarlist, name='Daftar_list'),
    path('struk-list/', struk_list, name='struk_list'),
    path('bensin-list/', bensin_list, name='bensin_list'),
    path('upload-struk/split-bill/', Split_Bill, name='Split_Bill'),
    path('upload-struk3/split-bill/', Split_Bill, name='Split_Bill3'),
    path("bensin-terbaru/<int:bensin_id>/", bensinTerbaruView.as_view(), name="bensin_terbaru"),
    path("struk-terbaru/<int:struk_id>/", StrukTerbaruView.as_view(), name="struk_terbaru"),
    path('save-struk/', save_struk, name='save_struk'),
    path('save-bensin/', save_bensin, name='save_bensin'),
    path('upload-bensin/', upload_Bensin, name='upload_bensin'),
]



