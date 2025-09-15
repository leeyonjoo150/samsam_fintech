# transfers/urls.py (앱 레벨 URLs)
from django.urls import path
from . import views

app_name = 'transfers'

urlpatterns = [
    # 로그인/로그아웃
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # 대시보드
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 거래 관련
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transfer/', views.transfer_form, name='transfer_form'),
    path('transfer/verify/', views.verify_account_password, name='verify_password'),
    path('transfer/process/', views.process_transfer, name='process_transfer'),
    path('transfer/success/<int:transaction_id>/', views.transfer_success, name='transfer_success'),
    
    # AJAX
    path('api/account-info/', views.get_account_info, name='get_account_info'),
]

# config/urls.py (프로젝트 레벨 URLs)에 추가할 내용:
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('transfers:dashboard')),  # 루트 URL을 대시보드로 리다이렉트
    path('transfers/', include('transfers.urls')),
    path('main/', include('main.urls')),
    path('findata/', include('financial_data.urls')),
]
"""