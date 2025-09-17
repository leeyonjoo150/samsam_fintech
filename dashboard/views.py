# dashboard/views.py

from django.shortcuts import render
from django.db.models import Sum, F
# from .models import Transaction   # 같은 앱 내의 모델 import - dashboard 앱 테스트를 위해 만든 모델 import
from django.contrib.auth.decorators import login_required
from urllib3 import request
from manage_account.models import TransactionAccount, Account, AccountBookCategory # 가계부 앱 모델을 읽기 위해 import
from datetime import datetime, date, timedelta
from django.db.models.functions import TruncMonth
from django.utils import timezone                       # 이 라인 전체APP Merge후 추가하였음.
import json
from decimal import Decimal
import calendar # 이 라인을 추가하세요.

# JSON 직렬화를 위한 헬퍼 클래스
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        # date와 datetime 객체 모두 처리하도록 추가
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

@login_required         # 로그인한 사용자만 접근 가능하도록 데코레이터 추가
def dashboard_view(request):
    # 날짜 필터링 파라미터 가져오기
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # 기본 날짜 범위 설정: 현재 월
    today_aware = timezone.localdate() # 로컬 시간대의 오늘 날짜를 가져옵니다.
    if start_date_str:
        # URL 파라미터에서 넘어온 날짜 문자열을 datetime 객체로 변환
        start_datetime_naive = datetime.fromisoformat(start_date_str)
        # naive datetime에 시간대 정보를 추가하여 aware datetime으로 변환
        start_datetime = timezone.make_aware(start_datetime_naive)
    else:
        # 현재 월의 첫째 날 0시 0분 0초를 aware datetime으로 설정
        start_datetime = timezone.make_aware(datetime(today_aware.year, today_aware.month, 1))

    if end_date_str:
        # URL 파라미터에서 넘어온 날짜 문자열을 datetime 객체로 변환
        end_datetime_naive = datetime.fromisoformat(end_date_str)
        # 해당 날짜의 마지막 시간(23:59:59.999999)을 포함하도록 1일을 더하고 aware datetime으로 변환
        end_datetime = timezone.make_aware(end_datetime_naive + timedelta(days=1))
    else:
        # 현재 월의 마지막 날을 찾아, 그 다음 날의 자정을 aware datetime으로 설정
        last_day_of_month = calendar.monthrange(today_aware.year, today_aware.month)[1]
        end_datetime = timezone.make_aware(datetime(today_aware.year, today_aware.month, last_day_of_month) + timedelta(days=1))

    # 이후 쿼리에는 start_datetime과 end_datetime을 사용합니다.
    # `start_date`와 `end_date` 변수명은 이전에 사용하던 것과 다르게 설정하여 혼동을 막습니다.
        
    # 여기서 end_date에 하루를 더하여 필터링 범위를 확장합니다.
    # 이렇게 하면 end_date 하루 전체가 포함됩니다. 
    # 예를 들어, 종료일 그대로하면 2023-10-10 00:00:00 까지만 포함되어 2023-10-10일 전체가 포함되지 않음
    # end_date_inclusive = end_date + timedelta(days=1) -> 임시 코멘트 처리
    
    # 로그인한 사용자 계좌를 먼저 가져온다.
    # User 모델은 request.user를 통해 접근 가능
    user_accounts = Account.objects.filter(acc_user_name=request.user)
    
    # 로그인한 사용자 계좌와 연결된 거래 내역을 조회
    # filter(my_acc__in=user_accounts)를 사용하여 로그인한 사용자의 거래만 필터링
    # select_related('txn_cat')를 사용하여 TransactionAccount와 AccountBookCategory를 미리 조인하여 쿼리 횟수를 줄인다.
    # 또한, txn_date 필드를 사용하여 날짜 범위 필터링
    transactions = TransactionAccount.objects.filter(
        my_acc__in=user_accounts, 
        # 옛날 코드: txn_date__range=[start_date, end_date]
        # range 대신 gte와 lt를 조합하여 날짜 범위 필터링
        txn_date__gte=start_datetime, # 수정
        txn_date__lt=end_datetime, # 수정
    ).select_related('txn_cat')
    
    # 각 집계 및 조회 쿼리를 새로운 모델에 맞게 수정
    # 필드명도 'amount' -> 'txn_amount', 'transaction_type' -> 'txn_side', 'category' -> 'txn_cat'으로 변경
    # # OLD-총 수입/지출/순자산
    # total_income = Transaction.objects.filter(transaction_type='수입', transaction_date__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    # total_expense = Transaction.objects.filter(transaction_type='지출', transaction_date__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    # net_balance = total_income - total_expense
    #
    # 총 수입/지출/순자산
    total_income = transactions.filter(txn_side='입금').aggregate(Sum('txn_amount'))['txn_amount__sum'] or Decimal(0)
    total_expense = transactions.filter(txn_side='출금').aggregate(Sum('txn_amount'))['txn_amount__sum'] or Decimal(0)
    net_balance = total_income - total_expense   
    
    # 카테고리별 지출 집계
    # values()에 'txn_cat' (ForeignKey)을 사용하고 annotate(total=Sum('txn_amount'))로 집계합니다.
    # 이 경우 'txn_cat' 필드에는 카테고리의 ID가 반환되므로, 템플릿에서 카테고리 이름을 사용하려면 조인된 객체에 접근해야 합니다.
    # OLD-카테고리별 지출 집계
    # expense_by_category = list(Transaction.objects.filter(transaction_type='지출', transaction_date__range=[start_date, end_date]).values('category').annotate(total=Sum('amount')).order_by('-total'))
    #
    # JSON 직렬화를 위해 리스트를 생성할 때 category 이름을 직접 가져와야 합니다.
    expense_by_category_data = list(transactions.filter(txn_side='출금').values('txn_cat__cat_type').annotate(total=Sum('txn_amount')).order_by('-total'))
    # 필드명 변경: 'txn_cat__cat_type'을 'category'로, 'total'을 'total'로 유지합니다.
    expense_by_category = [{'category': item['txn_cat__cat_type'], 'total': item['total']} for item in expense_by_category_data]

    # OLD-월별 수입/지출 추이 집계
    # transactions_by_month = list(Transaction.objects.filter(transaction_date__range=[start_date, end_date]).annotate(month=TruncMonth('transaction_date')).values('month', 'transaction_type').annotate(total=Sum('amount')).order_by('month', 'transaction_type'))
    # 월별 수입/지출 추이 집계
    transactions_by_month_data = list(transactions.annotate(month=TruncMonth('txn_date')).values('month', 'txn_side').annotate(total=Sum('txn_amount')).order_by('month', 'txn_side'))
    # 필드명 변경: 'txn_side'를 'transaction_type'으로, 'total'을 'total'로 유지합니다.
    transactions_by_month = [{'month': item['month'], 'transaction_type': item['txn_side'], 'total': item['total']} for item in transactions_by_month_data]
    
    # OLD-최근 거래 내역 테이블 (수입/지출 분리)
    # recent_transactions = Transaction.objects.filter(transaction_date__range=[start_date, end_date]).order_by('-transaction_date')
    #
    # 최근 거래 내역 테이블 (수입/지출 분리)
    recent_transactions_income = list(transactions.filter(txn_side='입금').order_by('-txn_date').values('txn_date', 'txn_cat__cat_type', 'txn_cont', 'txn_amount'))
    recent_transactions_expense = list(transactions.filter(txn_side='출금').order_by('-txn_date').values('txn_date', 'txn_cat__cat_type', 'txn_cont', 'txn_amount'))

    # recent_income_transactions = list(recent_transactions.filter(transaction_type='수입').values('transaction_date', 'category', 'description', 'amount'))
    # recent_expense_transactions = list(recent_transactions.filter(transaction_type='지출').values('transaction_date', 'category', 'description', 'amount'))
    # JSON 직렬화를 위해 필드 이름을 기존 대시보드 형식에 맞게 변경합니다.
    recent_income_transactions = [
        {'transaction_date': item['txn_date'].date(), 'category': item['txn_cat__cat_type'], 'description': item['txn_cont'], 'amount': item['txn_amount']}
        for item in recent_transactions_income
    ]
    recent_expense_transactions = [
        {'transaction_date': item['txn_date'].date(), 'category': item['txn_cat__cat_type'], 'description': item['txn_cont'], 'amount': item['txn_amount']}
        for item in recent_transactions_expense
    ]

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'start_date': start_datetime.date().isoformat(),  # HTML 템플릿에 사용할 때는 date 형식으로 변환하여 전달
        'end_date': (end_datetime - timedelta(days=1)).date().isoformat(), # HTML 템플릿에 사용할 때는 1일 빼고 전달
        # 'transactions': json.dumps(list(recent_transactions.values()), cls=CustomJSONEncoder),
        # 'recent_income_transactions': json.dumps(recent_income_transactions, cls=CustomJSONEncoder),
        # 'recent_expense_transactions': json.dumps(recent_expense_transactions, cls=CustomJSONEncoder),
        # 'expense_by_category': json.dumps(expense_by_category, cls=CustomJSONEncoder),
        # 'transactions_by_month': json.dumps(transactions_by_month, cls=CustomJSONEncoder),
        # JSON 직렬화 시 필드명 변경
        'recent_income_transactions': json.dumps(recent_income_transactions, cls=CustomJSONEncoder),
        'recent_expense_transactions': json.dumps(recent_expense_transactions, cls=CustomJSONEncoder),
        'expense_by_category': json.dumps(expense_by_category, cls=CustomJSONEncoder),
        'transactions_by_month': json.dumps(transactions_by_month, cls=CustomJSONEncoder),
    }

    return render(request, 'dashboards/dashboard.html', context)