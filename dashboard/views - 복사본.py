# dashboard/views.py

from django.shortcuts import render
from django.db.models import Sum
from .models import Transaction
from datetime import date, timedelta
from django.db.models.functions import TruncMonth
import json
from decimal import Decimal
import calendar # 이 라인을 추가하세요.

# JSON 직렬화를 위한 헬퍼 클래스
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Decimal을 float로 변환하여 JSON에서 숫자로 인식
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

def dashboard_view(request):
    # 날짜 필터링 파라미터 가져오기
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # 기본 날짜 범위 설정: 현재 월
    today = date.today()
    if start_date_str:
        start_date = date.fromisoformat(start_date_str)
    else:
        start_date = today.replace(day=1)

    if end_date_str:
        end_date = date.fromisoformat(end_date_str)
    else:
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    
    # 총 수입/지출/순자산
    total_income = Transaction.objects.filter(transaction_type='수입', transaction_date__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    total_expense = Transaction.objects.filter(transaction_type='지출', transaction_date__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
    net_balance = total_income - total_expense

    # 카테고리별 지출 집계
    expense_by_category = list(Transaction.objects.filter(transaction_type='지출', transaction_date__range=[start_date, end_date]).values('category').annotate(total=Sum('amount')).order_by('-total'))

    # 월별 수입/지출 추이 집계
    transactions_by_month = list(Transaction.objects.filter(transaction_date__range=[start_date, end_date]).annotate(month=TruncMonth('transaction_date')).values('month', 'transaction_type').annotate(total=Sum('amount')).order_by('month', 'transaction_type'))

    # 최근 거래 내역 테이블 (수입/지출 분리)
    recent_transactions = Transaction.objects.filter(transaction_date__range=[start_date, end_date]).order_by('-transaction_date')

    recent_income_transactions = list(recent_transactions.filter(transaction_type='수입').values('transaction_date', 'category', 'description', 'amount'))
    recent_expense_transactions = list(recent_transactions.filter(transaction_type='지출').values('transaction_date', 'category', 'description', 'amount'))

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'transactions': json.dumps(list(recent_transactions.values()), cls=CustomJSONEncoder),
        'recent_income_transactions': json.dumps(recent_income_transactions, cls=CustomJSONEncoder),
        'recent_expense_transactions': json.dumps(recent_expense_transactions, cls=CustomJSONEncoder),
        'expense_by_category': json.dumps(expense_by_category, cls=CustomJSONEncoder),
        'transactions_by_month': json.dumps(transactions_by_month, cls=CustomJSONEncoder),
    }

    return render(request, 'dashboards/dashboard.html', context)