import FinanceDataReader as fdr
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import StockHoldingForm, StockAccountForm, SearchForm
from manage_account.models import StockContent, StockAccount
from django.db.models import Sum, F
from django.contrib import messages
from django.db import IntegrityError
import math
import random

@login_required
def my_stock_holdings(request):
    """
    로그인한 사용자의 보유 주식 정보를 조회하고 실시간 가격을 함께 반환하는 뷰
    """
    user = request.user
    
    # 사용자의 모든 주식 계좌를 가져옵니다.
    stock_accounts = StockAccount.objects.filter(st_user_id=user)
    
    holding_data_with_prices = []
    
    # 통화별 합계 계산을 위한 딕셔너리 초기화
    total_by_currency = {
        '원화': {'purchase_amount': 0, 'current_value': 0, 'profit_loss': 0, 'profit_rate': 0},
        '달러': {'purchase_amount': 0, 'current_value': 0, 'profit_loss': 0, 'profit_rate': 0},
    }

    # 각 계좌의 주식 보유 내역을 순회하며 데이터 처리
    for account in stock_accounts:
        # 해당 계좌에 연결된 모든 주식 보유 내역을 가져옵니다.
        holdings = StockContent.objects.filter(st_id=account)
        
        for holding in holdings:
            ticker = holding.ticker_code
            currency = holding.currency
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
                            'currency': currency,
                            'current_price': round(latest_price, 2),
                            'total_value': round(total_value, 2),
                            'profit_rate': round(profit_rate, 2)
                        })
                        # 합계 딕셔너리에 값 추가
                        if currency in total_by_currency:
                            total_by_currency[currency]['purchase_amount'] += total_purchase_amount
                            total_by_currency[currency]['current_value'] += total_value
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                continue

    # 딕셔너리에 저장된 각 통화별 합계 수익률 계산
    for currency, totals in total_by_currency.items():
        if totals['purchase_amount'] != 0:
            totals['profit_loss'] = totals['current_value'] - totals['purchase_amount']
            totals['profit_rate'] = (totals['profit_loss'] / totals['purchase_amount']) * 100

    context = {
        'holdings': holding_data_with_prices,
        'total_by_currency': total_by_currency,
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

def search_data(request):
    """
    사용자 입력에 따라 금융 데이터를 검색하고 결과를 반환하는 뷰
    """
    form = SearchForm(request.GET or None)
    results = None
    query = None
    
    # 검색창 위에 보여줄 주요 지표 및 환율 데이터
    market_data_tickers = ['KS11', 'IXIC', 'US10YT', 'USD/KRW', 'EUR/KRW']
    market_data = []

    for ticker in market_data_tickers:
        try:
            df = fdr.DataReader(ticker)
            if not df.empty and 'Close' in df.columns:
                latest_price = df.iloc[-1]['Close']
                market_data.append({
                    'name': ticker,
                    'price': f'{latest_price:,.2f}'
                })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    if form.is_valid():
        query = form.cleaned_data.get('query')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        if query:
            original_query = query
            found_ticker = None
            
            # 한글-영문 회사 이름 매핑
            name_to_ticker_mapping = {
                '삼성전자': '005930',
                '애플': 'AAPL',
                '테슬라': 'TSLA',
                '아마존': 'AMZN',
                '엔비디아': 'NVDA',
            }
            
            # 매핑 딕셔너리에서 먼저 검색 (소문자로 변환하여 검색)
            for name, ticker in name_to_ticker_mapping.items():
                if query.lower() == name.lower():
                    found_ticker = ticker
                    break
            
            # 매핑에 없으면 기존 로직대로 검색
            if not found_ticker:
                # 검색할 거래소 목록
                exchange_list = ['KRX', 'NASDAQ', 'NYSE', 'AMEX']
                
                # 사용자가 입력한 검색어가 암호화폐 거래쌍인지 확인
                if '/' in query:
                    found_ticker = query.upper()
                # 사용자가 입력한 검색어가 주식 종목 코드인지 확인
                elif query.isdigit() or (query.isupper() and len(query) < 5):
                    found_ticker = query.upper()
                else:
                    # 종목 코드가 아니면 회사 이름으로 검색
                    for exchange in exchange_list:
                        try:
                            stock_list = fdr.StockListing(exchange)
                            # 대소문자 구분 없이 회사 이름 검색
                            matched_stock = stock_list[stock_list['Name'].str.lower() == query.lower()]
                            if not matched_stock.empty:
                                try:
                                    found_ticker = matched_stock.iloc[0]['Symbol']
                                except KeyError:
                                    found_ticker = matched_stock.iloc[0]['Code']
                                break  # 종목을 찾았으면 루프 종료
                        except Exception as e:
                            print(f"Error fetching stock list for {exchange}: {e}")
                            continue
            
            if found_ticker:
                query = found_ticker
                try:
                    # 시작일과 종료일이 유효하면 해당 기간으로 검색, 아니면 최근 5일만 검색
                    if start_date and end_date:
                        df = fdr.DataReader(query, start=start_date, end=end_date)
                    else:
                        df = fdr.DataReader(query)
                        df = df.tail(5)

                    # 검색 결과를 날짜 기준으로 내림차순 정렬
                    df = df.sort_index(ascending=False)

                    results = df.to_html(classes='table table-striped table-hover', border=0)
                except Exception as e:
                    messages.error(request, f"'{original_query}'에 대한 데이터를 찾을 수 없습니다. 올바른 검색어를 입력해주세요.")
                    print(f"Error fetching data for {query}: {e}")
            else:
                messages.error(request, f"'{original_query}'에 대한 종목 코드를 찾을 수 없습니다. 올바른 회사 이름 또는 종목 코드를 입력해주세요.")


    context = {
        'form': form,
        'results': results,
        'query': query,
        'market_data': market_data,
    }
    return render(request, 'financial_data/search.html', context)


# GeoGuessr 게임 뷰
def geoguessr_game(request):
    # 게임에 사용할 장소 목록 (예시)
    locations = [
        {
            'name': '멋쟁이 사자처럼',
            'lat': 37.571026,
            'lng': 126.978920,
            'description': '종로에 위치한 멋쟁이 사자처럼 사무실입니다. 이곳에서 수많은 개발자들이 탄생했죠!',
            'image_url': 'https://i.namu.wiki/i/_P6imFJ5yHttguV3fNdLT5hY3QKeIxpwnY682vpxQcwqwvnsTTXLB1zOVrAVw6AHPZcpS66wmi-_le7tSDXbyg.webp',
        },
        {
            'name': '멋쟁이 사자처럼 세렝게티',
            'lat': 37.502402,
            'lng': 127.043464,
            'description': '강남에 위치한 멋쟁이 사자처럼 세렝게티 사무실입니다. 코딩 열기로 가득한 곳입니다!',
            'image_url': 'https://i.namu.wiki/i/_P6imFJ5yHttguV3fNdLT5hY3QKeIxpwnY682vpxQcwqwvnsTTXLB1zOVrAVw6AHPZcpS66wmi-_le7tSDXbyg.webp',
        },
        {
            'name': '멋쟁이 사자처럼 나이로비',
            'lat': 37.506703,
            'lng': 127.055722,
            'description': '멋쟁이 사자처럼의 또 다른 보금자리 나이로비 사무실입니다. 다양한 프로젝트가 탄생하는 곳입니다!',
            'image_url': 'https://i.namu.wiki/i/_P6imFJ5yHttguV3fNdLT5hY3QKeIxpwnY682vpxQcwqwvnsTTXLB1zOVrAVw6AHPZcpS66wmi-_le7tSDXbyg.webp',
        },
    ]
    # 랜덤으로 장소를 하나 선택합니다.
    random_location = random.choice(locations)

    context = {
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'start_location': random_location,
    }
    return render(request, 'financial_data/geoguessr_game.html', context)