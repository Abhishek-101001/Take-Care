from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from .models import Medicine
from .serializer import MedicineSerializer
from django.shortcuts import get_object_or_404
# Create your views here.
class MedicineListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self ,request):
        medicines = Medicine.objects.filter(user=request.user)
        serializer = MedicineSerializer(medicines,many=True)
        return Response(serializer.data)
    
    
    def post(self, request):
        serializer = MedicineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicineDetailView(APIView):
    prmissions_classes = [permissions.IsAuthenticated]
    
    
    def get_object(self,pk,user):
        return get_object_or_404(Medicine, pk=pk, user=user)
    
    def get(self, request, pk):
        medicine = self.get_object(pk, request.user)
        serializer = MedicineSerializer(medicine)
        return Response(serializer.data)
    
    def put(self, request, pk):
        medicine = self.get_object(pk,request.user)
        serializer = MedicineSerializer(medicine, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        medicine = self.get_object(pk, request.user)
        medicine.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)