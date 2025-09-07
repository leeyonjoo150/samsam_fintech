from django.contrib import admin
from .models import (
    Account, 
    StockAccount, 
    StockContent, 
    AccountBookCategory, 
    TransactionAccount, 
    TransactionCash
)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """일반계좌 Admin"""
    list_display = ['acc_user_name', 'acc_bank', 'acc_num', 'created_at']
    search_fields = ['acc_num', 'acc_user_name__user_name']
    list_filter = ['acc_bank', 'created_at']

@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    """주식용계좌 Admin"""
    list_display = ['st_user_id', 'st_company', 'st_acc_num', 'created_at']
    search_fields = ['st_acc_num', 'st_user_id__user_name']
    list_filter = ['st_company', 'created_at']

@admin.register(StockContent)
class StockContentAdmin(admin.ModelAdmin):
    """주식내역 Admin"""
    list_display = ['st_id', 'ticker_code', 'share', 'pur_amount', 'currency', 'created_at']
    search_fields = ['ticker_code']
    list_filter = ['currency', 'created_at']

@admin.register(AccountBookCategory)
class AccountBookCategoryAdmin(admin.ModelAdmin):
    """가계부 카테고리 Admin"""
    list_display = ['cat_type', 'created_at']
    search_fields = ['cat_type']
    list_filter = ['cat_type']

@admin.register(TransactionAccount)
class TransactionAccountAdmin(admin.ModelAdmin):
    """계좌거래내역 Admin"""
    list_display = ['txn_date', 'my_acc', 'txn_side', 'txn_amount', 'txn_balance', 'txn_cat']
    search_fields = ['txn_cont', 'my_acc__acc_num']
    list_filter = ['txn_side', 'txn_cat', 'txn_date']

@admin.register(TransactionCash)
class TransactionCashAdmin(admin.ModelAdmin):
    """현금거래내역 Admin"""
    list_display = ['use_date', 'cash_user', 'cash_side', 'cash_amount', 'cash_cat']
    search_fields = ['cash_cont', 'cash_user__user_name']
    list_filter = ['cash_side', 'cash_cat', 'use_date']
