from django.db import models
from acc_auth.models import User
from django.conf import settings
import os
from PIL import Image
from datetime import date, datetime
from django.utils import timezone

# Create your models here.
# 마이그레이션 명령어:
# python manage.py makemigrations acc_auth
# python manage.py makemigrations manage_account  
# python manage.py migrate
class Account(models.Model):
    """일반계좌 모델"""
    BANK_CHOICES = [
        ('국민', '국민은행'),
        ('신한', '신한은행'),
        ('우리', '우리은행'),
        ('하나', '하나은행'),
        ('농협', '농협은행'),
        ('기업', '기업은행'),
    ]
    
    acc_bank = models.CharField('은행', max_length=5, choices=BANK_CHOICES)
    acc_num = models.CharField('계좌번호', max_length=50, unique=True)
    acc_pw = models.CharField('계좌비밀번호', max_length=128)
    acc_user_name = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='소유자'
    )
    acc_money = models.DecimalField('잔액', max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField('생성일', default=timezone.now)
    
    def __str__(self):
        return f"{self.acc_bank} {self.acc_num} ({self.acc_user_name})"
    
    class Meta:
        verbose_name = "일반계좌"
        verbose_name_plural = "일반계좌 목록"
        ordering = ['created_at']


class StockAccount(models.Model):
    """주식용계좌 모델"""
    st_company = models.CharField('증권사', max_length=20)
    st_acc_num = models.CharField('계좌번호', max_length=50, unique=True)  
    st_acc_pw = models.CharField('주식계좌비밀번호', max_length=4)
    st_user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stock_accounts',
        verbose_name='소유자'
    )
    created_at = models.DateTimeField('생성일', default=timezone.now)
    
    def __str__(self):
        return f"{self.st_company} {self.st_acc_num} ({self.st_user_id})"
    
    class Meta:
        verbose_name = "주식용계좌"
        verbose_name_plural = "주식용계좌 목록"
        ordering = ['created_at']


class StockContent(models.Model):
    """주식내역 모델"""
    CURRENCY_CHOICES = [
        ('원화', '원화'),
        ('달러', '달러'),
    ]
    
    ticker_code = models.CharField('주식식별번호', max_length=10)
    pur_amount = models.IntegerField('매수금액')
    share = models.IntegerField('주식개수')
    currency = models.CharField('통화', max_length=10, choices=CURRENCY_CHOICES, default='원화')
    st_id = models.ForeignKey(
        StockAccount,
        on_delete=models.CASCADE,
        related_name='stock_contents',
        verbose_name='주식용계좌'
    )
    created_at = models.DateTimeField('생성일', default=timezone.now)
    
    def __str__(self):
        return f"{self.ticker_code} {self.share}주 매수완료"
    
    class Meta:
        verbose_name = "주식내역"
        verbose_name_plural = "주식내역 목록"
        ordering = ['created_at']


class AccountBookCategory(models.Model):
    """가계부 카테고리 모델"""
    CATEGORY_CHOICES = [
        ('식비', '식비'),
        ('교통/차량', '교통/차량'),
        ('문화생활', '문화생활'),
        ('마트/편의점', '마트/편의점'),
        ('패션/미용', '패션/미용'),
        ('생활용품', '생활용품'),
        ('주거/통신', '주거/통신'),
        ('건강', '건강'),
        ('교육', '교육'),
        ('경조사/회비', '경조사/회비'),
        ('부모님', '부모님'),
        ('기타', '기타'),
    ]
    
    cat_type = models.CharField(
        '카테고리종류', 
        max_length=20, 
        choices=CATEGORY_CHOICES
    )
    created_at = models.DateTimeField('생성일', default=timezone.now)
    
    def __str__(self):
        return self.cat_type + " 카테고리"
    
    class Meta:
        verbose_name = "가계부카테고리"
        verbose_name_plural = "가계부카테고리 목록"
        ordering = ['cat_type']


class TransactionAccount(models.Model):
    """계좌거래내역 모델"""
    TRANSACTION_SIDE_CHOICES = [
        ('입금', '입금'),
        ('출금', '출금'),
    ]
    
    txn_side = models.CharField('거래종류', max_length=10, choices=TRANSACTION_SIDE_CHOICES)
    txn_amount = models.IntegerField('금액')
    txn_balance = models.IntegerField('잔액')
    txn_cont = models.CharField('내용', max_length=300, null=True, blank=True)
    my_acc = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='my_transactions',
        verbose_name='내계좌아이디'
    )
    cpart_acc = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='partner_transactions',
        verbose_name='상대계좌아이디'
    )
    txn_date = models.DateTimeField('거래날짜', default=timezone.now)
    txn_cat = models.ForeignKey(
        AccountBookCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='가계부카테고리'
    )
    
    def __str__(self):
        return f"{self.txn_side}: {self.txn_amount:,}원 거래완료"
    
    class Meta:
        verbose_name = "계좌거래내역"
        verbose_name_plural = "계좌거래내역 목록"
        ordering = ['-txn_date']


class TransactionCash(models.Model):
    """현금거래내역 모델"""
    CASH_SIDE_CHOICES = [
        ('수입', '수입'),
        ('지출', '지출'),
    ]
    
    cash_side = models.CharField('방식', max_length=10, choices=CASH_SIDE_CHOICES)
    cash_amount = models.IntegerField('금액')
    use_date = models.DateTimeField('사용날짜', default=timezone.now)
    cash_balance = models.IntegerField('잔액')
    cash_cont = models.CharField('내용', max_length=300, null=True, blank=True)
    cash_cat = models.ForeignKey(
        AccountBookCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='가계부카테고리'
    )
    cash_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cash_transactions',
        verbose_name='사용자'
    )
    
    def __str__(self):
        return f"{self.cash_side}: {self.cash_amount:,}원 현금거래완료"
    
    class Meta:
        verbose_name = "현금거래내역"
        verbose_name_plural = "현금거래내역 목록"
        ordering = ['-use_date']