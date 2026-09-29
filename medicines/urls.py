from django.urls import path
from .views import MedicineListCreateView, MedicineDetailView,mark_taken,mark_missed,DoseLogListView

urlpatterns = [
    path('medicines/',MedicineListCreateView.as_view(),name='medicine-list'),
    path('medicines/<int:pk>/', MedicineDetailView.as_view(),name='medicine-detail'),
    path('doses/', DoseLogListView.as_view(), name='doselog-list'),
    path('doses/<int:pk>/taken/',mark_taken, name='mark-taken'),
    path('doses/<int:pk>/taken/',mark_missed, name='mark-missed'),      
]