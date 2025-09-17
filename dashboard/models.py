# dashboard/models.py
from django.db import models

class Transaction(models.Model):
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50) # '수입' 또는 '지출'
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.transaction_date} - {self.amount}"
        # return f"{self.transaction_date} - {self.amount} - {self.transaction_type} - {self.category}"