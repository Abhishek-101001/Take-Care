from django.urls import path
from .views import MedicineListCreateView, MedicineDetailView

urlpatterns = [
    path('medicine/',MedicineListCreateView.as_view,name='medicine-list'),
    path('medicines/<int:pk>/', MedicineDetailView.as_view(),name='medicine-detail'),
         
]