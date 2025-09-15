from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('from_account', 'to_account', 'amount', 'created_at')
    search_fields = ('from_account__acc_num', 'to_account__acc_num')
    list_filter = ('created_at',)