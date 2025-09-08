import FinanceDataReader as fdr
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .forms import StockHoldingForm
from .forms import StockAccountForm
from manage_account.models import StockContent, StockAccount
from django.db.models import Sum, F
from django.contrib import messages
from django.db import IntegrityError
import math

@login_required
def my_stock_holdings(request):
    """
    로그인한 사용자의 보유 주식 정보를 조회하고 실시간 가격을 함께 반환하는 뷰
    """
    user = request.user
    
    # 사용자의 모든 주식 계좌를 가져옵니다.
    stock_accounts = StockAccount.objects.filter(st_user_id=user)
    
    holding_data_with_prices = []
    
    # 각 계좌의 주식 보유 내역을 순회하며 데이터 처리
    for account in stock_accounts:
        # 해당 계좌에 연결된 모든 주식 보유 내역을 가져옵니다.
        holdings = StockContent.objects.filter(st_id=account)
        
        for holding in holdings:
            ticker = holding.ticker_code
            try:
                # FinanceDataReader를 사용하여 실시간 주식 데이터 조회
                df = fdr.DataReader(ticker)
                if not df.empty:
                    latest_price = df.iloc[-1]['Close']
                    if not math.isnan(latest_price):
                        # 총 평가액 계산
                        total_value = latest_price * holding.share
                        
                        # 총 매수 금액 계산 (보유량 * 매수가)
                        total_purchase_amount = holding.pur_amount * holding.share
                        
                        # 수익률 계산: (총 평가액 - 총 매수 금액) / 총 매수 금액 * 100
                        profit_rate = 0
                        if total_purchase_amount != 0:
                            profit_rate = ((total_value - total_purchase_amount) / total_purchase_amount) * 100
    
                        holding_data_with_prices.append({
                            'account_info': account, # 계좌 정보를 추가합니다.
                            'ticker_code': ticker,
                            'share': holding.share,
                            'purchase_amount': holding.pur_amount,
                            'currency': holding.currency,
                            'current_price': round(latest_price, 2),
                            'total_value': round(total_value, 2),
                            'profit_rate': round(profit_rate, 2)
                        })
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                continue

    context = {
        'holdings': holding_data_with_prices,
    }
    return render(request, 'financial_data/stock_holdings.html', context)

@login_required
def add_stock_holding(request):
    user = request.user
    
    # 사용자의 주식 계좌를 가져옵니다.
    user_accounts = StockAccount.objects.filter(st_user_id=user)
    if not user_accounts.exists():
        messages.error(request, '주식 계좌가 없어 보유 종목을 추가할 수 없습니다. 먼저 계좌를 등록해주세요.')
        return redirect('manage_account:add_stock_account')

    if request.method == 'POST':
        form = StockHoldingForm(request.POST, user=user) # 폼에 user 객체를 전달합니다.
        if form.is_valid():
            new_ticker_code = form.cleaned_data['ticker_code']
            new_share = form.cleaned_data['share']
            new_pur_amount = form.cleaned_data['pur_amount']
            new_currency = form.cleaned_data['currency']
            stock_account = form.cleaned_data['st_id'] # 선택된 계좌 객체를 가져옵니다.

            existing_holding = StockContent.objects.filter(
                st_id=stock_account,
                ticker_code=new_ticker_code,
                currency=new_currency
            ).first()

            if existing_holding:
                total_value = (existing_holding.pur_amount * existing_holding.share) + (new_pur_amount * new_share)
                total_share = existing_holding.share + new_share
                
                new_avg_pur_amount = total_value / total_share
                
                existing_holding.pur_amount = new_avg_pur_amount
                existing_holding.share = total_share
                existing_holding.save()
                messages.success(request, f'{new_ticker_code} 종목이 기존 계좌에 성공적으로 추가되었습니다.')
            else:
                holding = form.save(commit=False)
                holding.st_id = stock_account
                holding.save()
                messages.success(request, f'{new_ticker_code} 종목이 성공적으로 추가되었습니다.')
            
            return redirect('financial_data:my_stock_holdings')
    else:
        form = StockHoldingForm(user=user) # GET 요청에도 user 객체를 전달합니다.
    
    context = {
        'form': form,
    }
    return render(request, 'financial_data/add_holding.html', context)


@login_required
def add_stock_account(request):
    """
    주식 계좌를 추가하는 뷰
    """
    if request.method == 'POST':
        form = StockAccountForm(request.POST)
        if form.is_valid():
            try:
                stock_account = form.save(commit=False)
                stock_account.st_user_id = request.user
                stock_account.save()
                messages.success(request, '주식 계좌가 성공적으로 등록되었습니다.')
                return redirect('financial_data:my_stock_holdings')
            except IntegrityError:
                # 데이터베이스에 이미 동일한 계좌번호가 있을 경우 발생하는 오류를 처리
                messages.error(request, '이미 등록된 계좌번호입니다. 다른 계좌번호를 입력해주세요.')
    else:
        form = StockAccountForm()
        
    context = {
        'form': form,
    }
    return render(request, 'financial_data/add_stock_account.html', context)