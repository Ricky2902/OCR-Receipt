from django.urls import path
from .views import Bill
from .views import Parkir
from .views import OVO
from .views import Bensin
from .views import Paket
from .views import Exabytes
from .views import Struk
from .views import upload_Struk
from .views import upload_Bensin
from .views import upload_Home
from .views import Split_Bill
<<<<<<< Updated upstream
=======
from .views import save_struk
>>>>>>> Stashed changes

urlpatterns = [
    path("Bill/", Bill.as_view(), name="Bill"),
    path("OVO/", OVO.as_view(), name="OVO"),
    path("Bensin/", Bensin.as_view(), name="Bensin"),
    path("Parkir/", Parkir.as_view(), name="Parkir"),
    path("Paket/", Paket.as_view(), name="Paket"),
    path("Exabytes/", Exabytes.as_view(), name="Exabytes"),
    path("Struk/", Struk.as_view(), name="Struk"),
    path('', upload_Home, name='upload_Home'),
    path('upload-struk/', upload_Struk, name='upload_Struk'),
    path('upload-struk/split-bill/', Split_Bill, name='Split_Bill'),
<<<<<<< Updated upstream
=======
    path('save-struk/', save_struk, name='save_struk'),
>>>>>>> Stashed changes
    path('upload-bensin/', upload_Bensin, name='upload_bensin'),
]



