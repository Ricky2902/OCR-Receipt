from django.urls import path
from .views import Bill
from .views import Parkir
from .views import OVO
from .views import Pertamina
from .views import Paket

urlpatterns = [
    path("Bill/", Bill.as_view(), name="Bill"),
    path("OVO/", OVO.as_view(), name="OVO"),
    path("Pertamina/", Pertamina.as_view(), name="Pertamina"),
    path("Parkir/", Parkir.as_view(), name="Parkir"),
    path("Paket/", Paket.as_view(), name="Paket"),
]


