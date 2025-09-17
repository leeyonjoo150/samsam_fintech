from django.urls import path
from . import views

app_name = "account_book"

urlpatterns = [
    path("", views.home, name="home"),
    path("save_transaction/", views.save_transaction, name="save_transaction"),
    path("delete_transactions/", views.delete_transactions, name="delete_transactions"),
    path("save_bulk_transactions/", views.save_bulk_transactions, name="save_bulk_transactions"),
    path("get_categories/", views.get_categories_json, name="get_categories"),
    path("search_transactions/", views.search_transactions, name="search_transactions"),
    path("export/", views.export_transactions_excel, name="export_transactions_excel"),  # ✅ 쿼리 방식으로 변경
    path("get_categories/", views.get_categories, name="get_categories"),
]
