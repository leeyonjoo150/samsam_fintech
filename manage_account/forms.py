from django import forms
from .models import Account

class AccountModelForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['acc_bank', 'acc_num', 'acc_pw']
        labels = {
            'acc_bank': '은행',
            'acc_num': '계좌번호',
            'acc_pw': '송금 비밀번호(4자리)',
        }
        widgets = {
            'acc_pw': forms.PasswordInput(),
        }
