from django.urls import path
#원하는 뷰를 가져오는 형태
from .views import account_list, account_detail

app_name = 'manage_account'

urlpatterns = [
    path("acclist/", account_list, name='account_list'),
    path("acclist/<int:pk>/", account_detail, name='account_detail')
]