from django.shortcuts import render,redirect
from django.contrib.auth import login
from .forms import SignUpForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from .models import Medicine,DoseLog,Profile
from .serializer import MedicineSerializer,DoseLogSerializer,ReminderSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.views import LoginView
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
    permission_classes = [permissions.IsAuthenticated]
    
    
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
    
    
class DoseLogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = timezone.localdate()
        dose_logs = DoseLog.objects.filter(reminder__medicine__user=request.user,scheduled_for__date=today,).select_related('reminder__medicine').order_by('scheduled_for')
        serializer = DoseLogSerializer(dose_logs, many=True)
        return Response(serializer.data)
    
    
@login_required
def dashboard(request):
    return render(request,'dashboard.html')


@login_required 
def add_medicine(request):
    return render(request,'add_medicine.html')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_taken(request,pk):
    dose_log = get_object_or_404(DoseLog, pk=pk, reminder__medicine__user=request.user)
    dose_log.status = 'taken'
    dose_log.responded_at = timezone.now()
    dose_log.save()
    return Response({'status':'taken'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_missed(request,pk):
    dose_log = get_object_or_404(DoseLog, pk=pk, reminder__medicine__user=request.user)
    dose_log.status = 'missed'
    dose_log.responded_at = timezone.now()
    dose_log.save()
    return Response({'status':'missed'})



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_reminder(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, user=request.user)
    serializer = ReminderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(medicine=medicine)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def welcome(request):
    return render(request, 'welcome.html')


def signup(request, role):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(role=role)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form, 'role': role})


class RoleLoginView(LoginView):
    template_name = 'login.html'
    role = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.role
        return context

    def form_valid(self, form):
        user = form.get_user()
        user_role = Profile.objects.filter(user=user).values_list('role', flat=True).first() or 'owner'
        if user_role != self.role:
            article = 'an' if user_role == 'owner' else 'a'
            form.add_error(None, f'This is {article} {user_role} account. Please use the {user_role} login page.')
            return self.form_invalid(form)
        return super().form_valid(form)


@login_required
def home(request):
    role = Profile.objects.filter(user=request.user).values_list('role', flat=True).first() or 'owner'
    if role == 'caregiver':
        return redirect('caregiver-home')
    return redirect('dashboard')


@login_required
def caregiver_home(request):
    return render(request, 'caregiver_home.html')