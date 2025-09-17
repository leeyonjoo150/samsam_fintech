from django.db import models
from django.utils import timezone
from acc_auth.models import User
from manage_account.models import Account

class Transaction(models.Model):
    """송금 내역 모델"""
    TRANSACTION_TYPES = [
        ('SEND', '송금'),
        ('RECEIVE', '입금'),
    ]
    
    id = models.AutoField(primary_key=True)
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transactions', verbose_name="송금 계좌")
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transactions', verbose_name="수신 계좌")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="송금액")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="거래 유형")
    description = models.TextField(blank=True, null=True, verbose_name="송금 메모")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="거래 시간")
    is_success = models.BooleanField(default=True, verbose_name="성공 여부")
    
    class Meta:
        db_table = 'transaction_history'
        verbose_name = "거래 내역"
        verbose_name_plural = "거래 내역들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_account.acc_num} → {self.to_account.acc_num} ({self.amount}원)"
