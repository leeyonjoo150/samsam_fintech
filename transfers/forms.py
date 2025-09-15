from django import forms
from decimal import Decimal

class TransferForm(forms.Form):
    recipient_account = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '계좌번호를 입력하세요',
            'class': 'form-control'
        })
    )
    recipient_bank = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': '은행명',
            'class': 'form-control'
        })
    )
    recipient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': '받는 분 성명',
            'class': 'form-control'
        })
    )
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        min_value=Decimal('100'),
        widget=forms.NumberInput(attrs={
            'placeholder': '송금액',
            'class': 'form-control'
        })
    )
    memo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '메모 (선택사항)',
            'class': 'form-control'
        })
    )