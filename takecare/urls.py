"""
URL configuration for takecare project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from medicines.views import dashboard,add_medicine,welcome,signup,RoleLoginView,home,caregiver_home
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView


urlpatterns = [
    path('home/', home, name='home'),
    path('caregiver/', caregiver_home, name='caregiver-home'),
    path('signup/owner/', signup, {'role': 'owner'}, name='signup-owner'),
    path('signup/caregiver/', signup, {'role': 'caregiver'}, name='signup-caregiver'),
    path('admin/', admin.site.urls),
    path('api/',include('medicines.urls')),
    path('api-auth/',include('rest_framework.urls')),
    path('add-medicine/', add_medicine, name='add-medicine'),
    path('',dashboard, name='dashboard'),
    path('login/owner/', RoleLoginView.as_view(role='owner'), name='login-owner'),
    path('login/caregiver/', RoleLoginView.as_view(role='caregiver'), name='login-caregiver'),
    path('login/', RedirectView.as_view(pattern_name='welcome'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('welcome/', welcome, name='welcome'),
] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
