from django.urls import path
from . import views

app_name = "account_book"

urlpatterns = [
    path("", views.home, name="home"),  # 홈
    path("save_transaction/", views.save_transaction, name="save_transaction"),
    path("delete_transactions/", views.delete_transactions, name="delete_transactions"),
    path("save_bulk_transactions/", views.save_bulk_transactions, name="save_bulk_transactions"),
    path("get_categories/", views.get_categories_json, name="get_categories"),
]