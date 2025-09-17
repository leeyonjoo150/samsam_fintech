from django.urls import path
#원하는 뷰를 가져오는 형태
from .views import account_list, account_detail, account_create, export_transactions_csv, export_transactions_pdf, check_acc_num

app_name = 'manage_account'

urlpatterns = [
    path("acclist/", account_list, name='account_list'),
    path("account/<int:pk>/", account_detail, name='account_detail'),
    path("acc/create/", account_create, name='account_create'),
    path('check-acc-num/', check_acc_num, name='check_acc_num'),
    path('account/<int:pk>/export/csv/', export_transactions_csv, name='export_transactions_csv'),
    path('account/<int:pk>/export/pdf/', export_transactions_pdf, name='export_transactions_pdf')
]