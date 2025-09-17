from django.shortcuts import render, redirect
from manage_account.models import Account, AccountBookCategory, TransactionAccount, TransactionCash
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery, Q
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime, timedelta, date
from django.db import transaction
from django.utils.timezone import make_aware, localtime
import calendar
import openpyxl
from .models import Category

User = get_user_model()

# ✅ 카테고리 조회
def get_categories_json(request):
    category_type = request.GET.get('type')
    categories = []
    if category_type in ['income', 'expense']:
        filtered_categories = AccountBookCategory.objects.filter(cat_kind=category_type).order_by('cat_type')
        categories = [{'id': category.id, 'name': category.cat_type} for category in filtered_categories]
    return JsonResponse({'categories': categories})

# ✅ 홈
def home(request):
    categories = AccountBookCategory.objects.all()
    year = request.GET.get('year')
    month = request.GET.get('month')
    now = timezone.now()
    current_year = int(year) if year else now.year
    current_month = int(month) if month else now.month

    cash_transactions = TransactionCash.objects.filter(
        use_date__year=current_year,
        use_date__month=current_month
    )
    account_transactions = TransactionAccount.objects.filter(
        txn_date__year=current_year,
        txn_date__month=current_month
    )

    combined_transactions = []
    for t in cash_transactions:
        combined_transactions.append({
            'id': t.id,
            'type': 'cash',
            'date': localtime(t.use_date),
            'side': t.cash_side,
            'amount': t.cash_amount,
            'category': t.cash_cat.cat_type if t.cash_cat else '',
            'content': t.cash_cont,
            'memo': t.memo,
            'photo_url': t.photo.url if t.photo else None,
            'asset_type': '현금',
        })
    for t in account_transactions:
        combined_transactions.append({
            'id': t.id,
            'type': 'account',
            'date': localtime(t.txn_date),
            'side': t.txn_side,
            'amount': t.txn_amount,
            'category': t.txn_cat.cat_type if t.txn_cat else '',
            'content': t.txn_cont,
            'memo': '',
            'photo_url': None,
            'asset_type': t.my_acc.acc_bank,
        })

    combined_transactions.sort(key=lambda x: x['date'], reverse=True)

    monthly_income = sum(t['amount'] for t in combined_transactions if t['side'] in ['수입', '입금'])
    monthly_expense = sum(t['amount'] for t in combined_transactions if t['side'] in ['지출', '출금'])

    # 로그인 없어도 빈 계좌 처리
    accounts = Account.objects.filter(acc_user_name=request.user) if request.user.is_authenticated else Account.objects.none()
    latest_transactions_subquery = TransactionAccount.objects.filter(
        my_acc=OuterRef('pk'),
        txn_date__year=current_year,
        txn_date__month=current_month
    ).order_by('-txn_date')
    accounts_with_latest_balance = accounts.annotate(
        latest_balance=Subquery(latest_transactions_subquery.values('txn_balance')[:1])
    )
    total_bank_balance = accounts_with_latest_balance.aggregate(
        total=Sum('latest_balance')
    )['total'] or 0

    last_day_of_month = calendar.monthrange(current_year, current_month)[1]
    end_of_month_date = date(current_year, current_month, last_day_of_month)
    latest_cash_transaction_up_to_month = TransactionCash.objects.filter(
        use_date__lte=end_of_month_date
    ).order_by('-use_date', '-id').first()
    current_cash_balance = latest_cash_transaction_up_to_month.cash_balance if latest_cash_transaction_up_to_month else 0

    total_assets = current_cash_balance + total_bank_balance

    return render(request, 'account_book/home.html', {
        'categories': categories,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'total_bank_balance': total_bank_balance,
        'total_assets': total_assets,
        'current_year': current_year,
        'current_month': current_month,
    })

# ✅ 단건 저장
def save_transaction(request):
    if request.method == "POST":
        cash_side = request.POST.get("cash_side")
        cash_amount = int(request.POST.get("amount", "0").replace(",", "") or 0)
        use_date_str = request.POST.get("date")
        category_name = request.POST.get("category")
        content = request.POST.get("content")
        memo = request.POST.get("memo")
        photo = request.FILES.get("photo")

        parsed_datetime_utc = None
        if use_date_str:
            try:
                parsed_date_obj = datetime.strptime(use_date_str, '%Y-%m-%d').date()
                parsed_datetime_utc = timezone.make_aware(datetime(parsed_date_obj.year, parsed_date_obj.month, parsed_date_obj.day))
            except ValueError:
                pass

        last_transaction = TransactionCash.objects.order_by('-use_date').first()
        last_balance = last_transaction.cash_balance if last_transaction else 0
        new_balance = last_balance + cash_amount if cash_side == '수입' else last_balance - cash_amount

        kind = 'income' if cash_side == '수입' else 'expense'
        category = AccountBookCategory.objects.filter(cat_type=category_name, cat_kind=kind).first()

        user = request.user if request.user.is_authenticated else None

        TransactionCash.objects.create(
            cash_side=cash_side,
            cash_amount=cash_amount,
            use_date=parsed_datetime_utc,
            cash_balance=new_balance,
            cash_cont=content or "",
            memo=memo,
            photo=photo,
            cash_cat=category,
            cash_user=user,
        )
        return redirect("account_book:home")
    return redirect("account_book:home")

# ✅ 삭제
def delete_transactions(request):
    ids = []
    if request.headers.get("Content-Type") == "application/json":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "잘못된 요청"}, status=400)
    else:
        ids = request.POST.getlist('ids[]')

    if ids:
        TransactionCash.objects.filter(id__in=ids).delete()
        if request.headers.get("Content-Type") == "application/json":
            return JsonResponse({"success": True})

    return redirect('account_book:home')

# ✅ 대량 저장
@require_POST
def save_bulk_transactions(request):
    if request.headers.get("Content-Type") != "application/json":
        return JsonResponse({"success": False, "error": "Invalid content type"}, status=400)

    try:
        data = json.loads(request.body)
        transactions_data = data.get('transactions', [])
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    user = request.user if request.user.is_authenticated else None

    try:
        with transaction.atomic():
            last_transaction = TransactionCash.objects.order_by('-use_date', '-id').first()
            current_balance = last_transaction.cash_balance if last_transaction else 0
            transactions_data.sort(key=lambda x: x.get('date', ''))

            for item in transactions_data:
                cash_side = item.get('type')
                cash_amount_str = item.get('amount')
                use_date_str = item.get('date')
                if not all([cash_side, cash_amount_str, use_date_str]):
                    continue
                try:
                    parsed_date = make_aware(datetime.strptime(use_date_str, '%Y-%m-%d'))
                except ValueError:
                    continue
                try:
                    cash_amount = int(cash_amount_str)
                except (ValueError, TypeError):
                    continue
                if cash_side == '수입':
                    current_balance += cash_amount
                else:
                    current_balance -= cash_amount
                kind = 'income' if cash_side == '수입' else 'expense'
                category = AccountBookCategory.objects.filter(cat_type=item.get('category'), cat_kind=kind).first()
                TransactionCash.objects.create(
                    cash_user=user,
                    use_date=parsed_date,
                    cash_side=cash_side,
                    cash_cat=category,
                    cash_amount=cash_amount,
                    cash_cont=item.get('content'),
                    memo=item.get('memo'),
                    cash_balance=current_balance
                )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# ✅ 검색
from django.db.models import Q
from django.utils.timezone import make_aware, localtime
from datetime import datetime, timedelta
from django.http import JsonResponse

def search_transactions(request):
    transactions = TransactionCash.objects.all().order_by('-use_date')
    filters = Q()

    # GET 파라미터
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')
    amount_str = request.GET.get('amount')
    year = request.GET.get('year')
    month = request.GET.get('month')

    # --- 날짜 필터 ---
    if start_date_str and end_date_str:
        # 날짜 범위 검색 (여러 달 가능)
        start_date = make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = make_aware(datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1))
        filters &= Q(use_date__gte=start_date, use_date__lt=end_date)
    elif year and month:
        # start/end 없을 때만 year+month 적용
        filters &= Q(use_date__year=year, use_date__month=month)

    # --- 수입/지출 필터 ---
    if transaction_type == 'income':
        filters &= Q(cash_side='수입')
    elif transaction_type == 'expense':
        filters &= Q(cash_side='지출')

    # --- 카테고리 필터 ---
    if category_id:
        filters &= Q(cash_cat__id=category_id)

    # --- 금액 필터 ---
    if amount_str:
        try:
            filters &= Q(cash_amount=int(amount_str))
        except ValueError:
            pass

    # 최종 쿼리
    transactions = transactions.filter(filters)

    # 직렬화
    serialized_transactions = [{
        'id': t.id,
        'use_date': localtime(t.use_date).strftime('%Y-%m-%d'),
        'cash_side': t.cash_side,
        'asset_type': '현금',
        'category_name': t.cash_cat.cat_type if t.cash_cat else '',
        'cash_amount': t.cash_amount,
        'cash_cont': t.cash_cont,
        'memo': t.memo,
        'photo_url': t.photo.url if t.photo else None,
    } for t in transactions]

    return JsonResponse({'transactions': serialized_transactions})

# ✅ Excel 내보내기
def export_transactions_excel(request):
    year = request.GET.get("year")
    month = request.GET.get("month")

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "계좌거래내역"
    ws1.append(["날짜", "거래종류", "금액", "내용", "잔액", "카테고리"])
    account_txns = TransactionAccount.objects.all()
    if year and month:
        account_txns = account_txns.filter(txn_date__year=year, txn_date__month=month)
    for t in account_txns:
        ws1.append([t.txn_date.strftime("%Y-%m-%d"), t.txn_side, t.txn_amount, t.txn_cont, t.txn_balance, t.txn_cat.cat_type if t.txn_cat else ""])

    ws2 = wb.create_sheet(title="현금거래내역")
    ws2.append(["날짜", "구분", "금액", "내용", "메모", "잔액", "카테고리"])
    cash_txns = TransactionCash.objects.all()
    if year and month:
        cash_txns = cash_txns.filter(use_date__year=year, use_date__month=month)
    for t in cash_txns:
        ws2.append([t.use_date.strftime("%Y-%m-%d"), t.cash_side, t.cash_amount, t.cash_cont, t.memo, t.cash_balance, t.cash_cat.cat_type if t.cash_cat else ""])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"transactions_{year}_{month}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

# ✅ 메인 인덱스
def index(request):
    return render(request, "main/index.html")

# ✅ 카테고리 검색
def get_categories(request):
    type_map = {"income": "수입", "expense": "지출"}
    type_param = request.GET.get("type")
    if type_param not in type_map:
        return JsonResponse({"categories": []})
    categories = Category.objects.filter(cat_kind=type_map[type_param])
    data = [{"id": c.id, "name": c.cat_type} for c in categories]
    return JsonResponse({"categories": data})