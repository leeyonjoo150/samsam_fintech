import FinanceDataReader as fdr
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q # 검색을 위해 Q 객체를 import 합니다.
from .forms import StockHoldingForm, StockAccountForm, SearchForm
from manage_account.models import StockContent, StockAccount
from django.db.models import Sum, F
from django.contrib import messages
from django.db import IntegrityError
import math
import random
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache

# 전역 변수로 종목 리스트 캐시.
# 서버가 시작될 때 데이터를 한 번만 로드하여 효율성을 높입니다.
# 오류 방지를 위해 try-except 블록을 사용합니다.
def load_stock_listings():
    # 캐시에서 'stock_listings' 데이터를 가져옵니다.
    listings = cache.get('stock_listings')
    if listings:
        print("종목 목록을 캐시에서 로드했습니다.")
        return listings
        
    print("종목 목록을 API에서 로드합니다.")
    listings = {}
    try:
        listings['KRX'] = fdr.StockListing('KRX')
    except Exception as e:
        print(f"KRX 종목 목록 로드 중 오류 발생: {e}")
        listings['KRX'] = pd.DataFrame()
    # ... (기존 NASDAQ, NYSE, AMEX 로직 동일) ...
    try:
        listings['NASDAQ'] = fdr.StockListing('NASDAQ')
    except Exception as e:
        print(f"NASDAQ 종목 목록 로드 중 오류 발생: {e}")
        listings['NASDAQ'] = pd.DataFrame()

    try:
        listings['NYSE'] = fdr.StockListing('NYSE')
    except Exception as e:
        print(f"NYSE 종목 목록 로드 중 오류 발생: {e}")
        listings['NYSE'] = pd.DataFrame()

    try:
        listings['AMEX'] = fdr.StockListing('AMEX')
        print("AMEX 종목 목록을 성공적으로 로드했습니다.")
    except Exception as e:
        print(f"AMEX 종목 목록 로드 중 오류 발생: {e}")
        listings['AMEX'] = pd.DataFrame()

    # 캐시에 저장합니다. (예: 1일 = 86400초)
    # 캐시는 서버 재시작 시 초기화됩니다.
    cache.set('stock_listings', listings, 60*60*24)
    return listings

STOCK_LISTINGS = load_stock_listings()


def get_company_name(ticker_code):
    """
    주어진 종목 코드에 해당하는 회사 이름을 캐시된 데이터에서 빠르게 조회합니다.
    """
    # 한국 주식 (KRX)에서 먼저 찾기
    kor_stocks = STOCK_LISTINGS.get('KRX')
    if not kor_stocks.empty and 'Code' in kor_stocks.columns:
        matched_kor = kor_stocks[kor_stocks['Code'] == ticker_code]
        if not matched_kor.empty and 'Name' in matched_kor.columns:
            return matched_kor['Name'].iloc[0]

    # 미국 주식 (NASDAQ, NYSE, AMEX)에서 찾기
    for exchange in ['NASDAQ', 'NYSE', 'AMEX']:
        stocks = STOCK_LISTINGS.get(exchange)
        if not stocks.empty and 'Symbol' in stocks.columns:
            matched_stock = stocks[stocks['Symbol'] == ticker_code]
            if not matched_stock.empty and 'Name' in matched_stock.columns:
                return matched_stock['Name'].iloc[0]

    return "이름 없음"

# 병렬 처리를 위한 헬퍼 함수
def fetch_stock_data(ticker):
    """
    단일 종목 코드로 주식 데이터를 가져오는 함수.
    """
    try:
        df = fdr.DataReader(ticker)
        if not df.empty:
            return ticker, df.iloc[-1]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
    return ticker, None

@login_required
def my_stock_holdings(request):
    """
    로그인한 사용자의 보유 주식 정보를 조회하고 실시간 가격을 함께 반환하는 뷰
    """
    user = request.user
    
    stock_accounts = StockAccount.objects.filter(st_user_id=user)
    
    # 사용자가 보유한 모든 종목을 가져옵니다.
    holdings = StockContent.objects.filter(st_id__in=stock_accounts).select_related('st_id')
    
    holding_data_with_prices = []
    total_by_currency = {
        '원화': {'purchase_amount': 0, 'current_value': 0, 'profit_loss': 0, 'profit_rate': 0},
        '달러': {'purchase_amount': 0, 'current_value': 0, 'profit_loss': 0, 'profit_rate': 0},
    }

    # 보유 종목의 고유한 종목 코드 목록을 생성합니다.
    unique_tickers = list(holdings.values_list('ticker_code', flat=True).distinct())

    # 병렬 처리를 사용하여 모든 종목 데이터를 동시에 가져옵니다.
    # 최대 워커 수를 10으로 설정하여 동시에 10개의 API 호출을 처리합니다.
    with ThreadPoolExecutor(max_workers=10) as executor:
        # map 함수는 각 ticker에 대해 fetch_stock_data 함수를 병렬로 실행합니다.
        # 결과는 제출된 순서대로 반환됩니다.
        price_data = list(executor.map(fetch_stock_data, unique_tickers))

    # 가져온 가격 데이터를 딕셔너리 형태로 변환하여 빠른 조회를 가능하게 합니다.
    price_dict = {ticker: data for ticker, data in price_data if data is not None}
    
    # 각 보유 종목에 대해 가격 데이터를 합칩니다.
    for holding in holdings:
        ticker = holding.ticker_code
        currency = holding.currency
        company_name = get_company_name(ticker)
        
        latest_price = None
        total_value = None
        profit_rate = None
        
        if ticker in price_dict:
            latest_price_series = price_dict[ticker]
            latest_price = latest_price_series.get('Close')
            
            if latest_price is not None and not math.isnan(latest_price):
                total_value = latest_price * holding.share
                total_purchase_amount = holding.pur_amount * holding.share
                
                profit_rate = 0
                if total_purchase_amount != 0:
                    profit_rate = ((total_value - total_purchase_amount) / total_purchase_amount) * 100

                if currency in total_by_currency:
                    total_by_currency[currency]['purchase_amount'] += total_purchase_amount
                    total_by_currency[currency]['current_value'] += total_value

        holding_data_with_prices.append({
            'account_info': holding.st_id,
            'ticker_code': ticker,
            'company_name': company_name,
            'share': holding.share,
            'purchase_amount': holding.pur_amount,
            'currency': currency,
            'current_price': round(latest_price, 2) if latest_price is not None else 'N/A',
            'total_value': round(total_value, 2) if total_value is not None else 'N/A',
            'profit_rate': round(profit_rate, 2) if profit_rate is not None else 'N/A'
        })
    
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
        return redirect('financial_data:add_stock_account')

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
    form = SearchForm(request.GET or None)
    results = None
    query = None
    
    # 캐시에서 'market_data'를 먼저 가져옵니다.
    market_data = cache.get('market_data')
    if not market_data:
        # 캐시가 없으면 API를 호출하여 데이터를 가져옵니다.
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
        # 데이터를 캐시에 저장합니다. (예: 10분 = 600초)
        cache.set('market_data', market_data, 600)

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
            if query.lower() in [name.lower() for name in name_to_ticker_mapping.keys()]:
                # 딕셔너리에서 검색어와 일치하는 키를 찾아서 종목 코드를 가져옴
                for name, ticker in name_to_ticker_mapping.items():
                    if query.lower() == name.lower():
                        found_ticker = ticker
                        break
            
            # 매핑에 없으면 기존 로직대로 검색
            if not found_ticker:
                # 검색할 거래소 목록
                exchange_list = ['KRX', 'NASDAQ', 'NYSE', 'AMEX']
                
                # 사용자가 입력한 검색어가 암호화폐 거래쌍인지 또는 점(.)이 포함된 종목 코드인지 확인
                if '/' in query or '.' in query:
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

def refresh_stock_cache(request):
    """
    주요 지수 및 종목 목록 캐시를 수동으로 삭제하는 뷰
    """
    cache.delete('stock_listings')
    cache.delete('market_data')
    messages.success(request, '데이터가 성공적으로 갱신되었습니다.')
    return redirect('financial_data:search_data')

# GeoGuessr 게임 뷰
def geoguessr_game(request):
    # 게임에 사용할 장소 목록
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
        # Maps Platform API Key - API 제한사항 Street View Static API, Maps JavaScript API 허용하고 사용
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'start_location': random_location,
    }
    return render(request, 'financial_data/geoguessr_game.html', context)



# 자동 완성 기능 구현 시도중

def search_stock_ticker(request):
    """
    주식 종목을 검색하여 JSON 응답을 반환하는 뷰
    """
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        # FinanceDataReader를 사용하여 종목 목록 캐시를 가져옵니다.
        kor_stocks = STOCK_LISTINGS.get('KRX')
        us_stocks = pd.concat([STOCK_LISTINGS.get('NASDAQ'), STOCK_LISTINGS.get('NYSE'), STOCK_LISTINGS.get('AMEX')])

        # 한글 또는 영문 검색어에 따라 필터링
        # 한국 주식 검색 (Code와 Name을 모두 검사)
        if not kor_stocks.empty:
            matched_kor = kor_stocks[
                kor_stocks['Code'].str.contains(query, case=False, na=False) |
                kor_stocks['Name'].str.contains(query, case=False, na=False)
            ]
            for _, row in matched_kor.iterrows():
                results.append({
                    'id': row['Code'],
                    'text': f"{row['Name']} ({row['Code']})"
                })

        # 미국 주식 검색 (Symbol과 Name을 모두 검사)
        if not us_stocks.empty:
            matched_us = us_stocks[
                us_stocks['Symbol'].str.contains(query, case=False, na=False) |
                us_stocks['Name'].str.contains(query, case=False, na=False)
            ]
            for _, row in matched_us.iterrows():
                results.append({
                    'id': row['Symbol'],
                    'text': f"{row['Name']} ({row['Symbol']})"
                })
        
    # 결과 개수 제한
    return JsonResponse({'results': results[:20]}, safe=False)

@login_required
def add_stock_holding_new(request):
    user = request.user
    
    # 사용자의 주식 계좌를 가져옵니다.
    user_accounts = StockAccount.objects.filter(st_user_id=user)
    if not user_accounts.exists():
        messages.error(request, '주식 계좌가 없어 보유 종목을 추가할 수 없습니다. 먼저 계좌를 등록해주세요.')
        return redirect('financial_data:add_stock_account')

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
    return render(request, 'financial_data/add_holding_new.html', context) # 이 부분을 수정

# 여기까지가 자동완성 기능 