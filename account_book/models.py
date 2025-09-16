from django.db import models

# Create your models here.
from manage_account.models import AccountBookCategory

class Category(models.Model):
    cat_type = models.CharField(max_length=100)  # 카테고리 이름 (예: 식비, 급여)
    cat_kind = models.CharField(                 # 카테고리 종류 (수입/지출)
        max_length=10,
        choices=[("수입", "수입"), ("지출", "지출")]
    )

    def __str__(self):
        return f"{self.cat_kind} - {self.cat_type}"

