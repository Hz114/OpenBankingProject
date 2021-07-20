# OpenBankingController / urls.py

from django.urls import path
from . import views

app_name = 'OpenBankingController'
urlpatterns = [
    path('user/', views.getUserInfo),
    path('allAccountList/', views.getAllAccountList),
    path('allAccountTransList/', views.getAllAcountTransList),
]