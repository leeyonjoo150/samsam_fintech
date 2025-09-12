from django.urls import path
#원하는 뷰를 가져오는 형태
from .views import account_list, account_detail, account_create

app_name = 'manage_account'

urlpatterns = [
    path("acclist/", account_list, name='account_list'),
    path("account/<int:pk>/", account_detail, name='account_detail'),
    path("acc/create/", account_create, name='account_create')
]