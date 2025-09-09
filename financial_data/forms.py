# financial_data/forms.py
from django import forms
from manage_account.models import StockContent, StockAccount
import FinanceDataReader as fdr
import math


class StockHoldingForm(forms.ModelForm):
    # st_id 필드를 모델 필드 대신 forms.ModelChoiceField로 정의
    st_id = forms.ModelChoiceField(
        queryset=None, # 초기에는 비워둡니다.
        label='주식 계좌',
        empty_label='--- 계좌를 선택하세요 ---'
    )

    class Meta:
        model = StockContent
        fields = ['st_id', 'ticker_code', 'pur_amount', 'share', 'currency']
        labels = {
            'ticker_code': '종목 코드',
            'pur_amount': '매수가',
            'share': '매수 수량',
            'currency': '통화',
        }
        widgets = {
            'ticker_code': forms.TextInput(attrs={'placeholder': '예: AAPL'}),
            'pur_amount': forms.NumberInput(attrs={'placeholder': '예: 180 (단위: 원)'}),
            'share': forms.NumberInput(attrs={'placeholder': '예: 5 (단위: 주)'}),
            'currency': forms.Select(choices=StockContent.CURRENCY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # 현재 로그인한 사용자의 주식 계좌만 선택지로 제공
            self.fields['st_id'].queryset = StockAccount.objects.filter(st_user_id=user)
    
    def clean_ticker_code(self):
        """
        입력된 종목 코드가 FinanceDataReader에 존재하는지 검증합니다.
        """
        ticker_code = self.cleaned_data.get('ticker_code')
        if not ticker_code:
            raise forms.ValidationError("종목 코드를 입력해주세요.")
            
        ticker_code = ticker_code.upper()

        try:
            df = fdr.DataReader(ticker_code)
            if df.empty or math.isnan(df.iloc[-1]['Close']):
                raise forms.ValidationError(f"'{ticker_code}' 종목 데이터를 찾을 수 없습니다. 올바른 종목 코드를 입력해주세요.")
        except Exception:
            raise forms.ValidationError(f"'{ticker_code}' 종목 데이터를 찾을 수 없습니다.")

        return ticker_code

    def clean(self):
        """
        종목 코드와 선택된 통화가 일치하는지 검증합니다.
        """
        cleaned_data = super().clean()
        ticker_code = cleaned_data.get('ticker_code')
        currency = cleaned_data.get('currency')

        if ticker_code and currency:
            # FinanceDataReader가 주식 코드를 판별하는 간단한 로직을 적용
            is_korean_stock = ticker_code.isdigit()
            
            if is_korean_stock and currency == '달러':
                raise forms.ValidationError("한국 주식 종목은 '원화'를 선택해야 합니다.")
            
            if not is_korean_stock and currency == '원화':
                # 'BTC/KRW'와 같이 원화로 거래되는 종목도 있으므로 추가적인 검증이 필요
                korean_currency_tickers = ['BTC/KRW', 'ETH/KRW', 'USD/KRW']
                if ticker_code not in korean_currency_tickers:
                    raise forms.ValidationError("해외 주식 종목은 '달러'를 선택해야 합니다.")
                    
        return cleaned_data
    
class StockAccountForm(forms.ModelForm):
    class Meta:
        model = StockAccount
        fields = ['st_acc_num', 'st_company']
        labels = {
            'st_acc_num': '계좌번호',
            'st_company': '증권사',
        }
        widgets = {
            'st_acc_num': forms.TextInput(attrs={'placeholder': '예: 1234567890'}),
            'st_company': forms.TextInput(attrs={'placeholder': '예: 삼성증권'}),
        }

class SearchForm(forms.Form):
    query = forms.CharField(
        label='검색어',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '예: AAPL, BTC/KRW, US5Y, 환율, 금', 'class': 'form-control'})
    )
    start_date = forms.DateField(
        label='시작일',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='종료일',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 폼이 GET 요청으로 비어있을 때만 기본값을 설정
        if not self.data:
            today = date.today()
            five_days_ago = today - timedelta(days=5)
            self.initial['end_date'] = today
            self.initial['start_date'] = five_days_ago