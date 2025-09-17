from django.shortcuts import render, redirect
from manage_account.models import Account, AccountBookCategory, TransactionAccount, TransactionCash
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, OuterRef, Subquery
from django.http import JsonResponse
import json
from django.db import transaction


User = get_user_model()

def home(request):
    categories = AccountBookCategory.objects.all()
    # 거래내역도 함께 가져오기
    transactions = TransactionCash.objects.all().order_by('-use_date')

    # Get current month's start and end dates
    now = timezone.now()
    current_year = now.year
    current_month = now.month

    # Calculate total income for the current month
    monthly_income = TransactionCash.objects.filter(
        cash_side='수입',
        use_date__year=current_year,
        use_date__month=current_month
    ).aggregate(total=Sum('cash_amount'))['total'] or 0

    # Calculate total expense for the current month
    monthly_expense = TransactionCash.objects.filter(
        cash_side='지출',
        use_date__year=current_year,
        use_date__month=current_month
    ).aggregate(total=Sum('cash_amount'))['total'] or 0

    # Calculate total balance from all bank accounts
    user = User.objects.first() # Placeholder user
    accounts = Account.objects.filter(acc_user_name=user)
    
    latest_transactions_subquery = TransactionAccount.objects.filter(
        my_acc=OuterRef('pk')
    ).order_by('-txn_date')
    
    accounts_with_latest_balance = accounts.annotate(
        latest_balance=Subquery(latest_transactions_subquery.values('txn_balance')[:1])
    )
    
    total_bank_balance = accounts_with_latest_balance.aggregate(
        total=Sum('latest_balance')
    )['total'] or 0

    # Calculate current cash balance from the latest cash transaction
    latest_cash_transaction = TransactionCash.objects.order_by('-use_date').first()
    current_cash_balance = latest_cash_transaction.cash_balance if latest_cash_transaction else 0

    # Calculate total assets
    total_assets = current_cash_balance + total_bank_balance
    
    context = {
        'categories': categories,
        'transactions': transactions,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'total_bank_balance': total_bank_balance,
        'total_assets': total_assets,
    }

    return render(request, 'account_book/home.html', context)

#거래내역 저장 뷰 (POST로 넘어온 데이터를 받아서 DB에 저장하는 view 함수를 만든다.)
def save_transaction(request):
    if request.method == "POST":
        cash_side = request.POST.get("cash_side")   # '수입', '지출'
        cash_amount = request.POST.get("amount", "0").replace(",", "")
        try:
            cash_amount = int(cash_amount) if cash_amount else 0
        except ValueError:
            cash_amount = 0
        use_date = request.POST.get("date")
        category_name = request.POST.get("category")
        content = request.POST.get("content")
        memo = request.POST.get("memo")
        photo = request.FILES.get("photo") # Get photo from request.FILES

        # --- Calculate new cash balance ---
        last_transaction = TransactionCash.objects.order_by('-use_date').first()
        last_balance = last_transaction.cash_balance if last_transaction else 0

        if cash_side == '수입':
            new_balance = last_balance + cash_amount
        else: # 지출
            new_balance = last_balance - cash_amount
        # -------------------------------------

        # Map front-end '수입'/'지출' to model's 'income'/'expense'
        kind = 'income' if cash_side == '수입' else 'expense'

        category = None
        if category_name:
            try:
                category = AccountBookCategory.objects.get(cat_type=category_name, cat_kind=kind)
            except AccountBookCategory.DoesNotExist:
                # This can happen if JS categories are out of sync with DB
                pass  # Silently ignore if category does not exist

        user = User.objects.first()  # 🔹 로그인 붙이기 전 임시

        TransactionCash.objects.create(
            cash_side=cash_side,
            cash_amount=cash_amount,
            use_date=use_date,
            cash_balance=new_balance,  # Use calculated balance
            cash_cont=content if content else "",
            memo=memo,
            photo=photo,
            cash_cat=category,
            cash_user=user,
        )
        return redirect("account_book:home")

    return redirect("account_book:home")

@require_POST
def delete_transactions(request):
    ids = request.POST.getlist('ids[]')
    if ids:
        # TODO: Add user ownership check when user authentication is fully implemented
        TransactionCash.objects.filter(id__in=ids).delete()
    return redirect('account_book:home')

@require_POST
def delete_transactions(request):
    ids = []

    # fetch(Ajax) JSON 요청 처리
    if request.headers.get("Content-Type") == "application/json":
        try:
            data = json.loads(request.body)
            ids = data.get("ids", [])
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "잘못된 요청"}, status=400)
    else:
        # 기존 form 전송 처리
        ids = request.POST.getlist('ids[]')

    if ids:
        # TODO: Add user ownership check when user authentication is fully implemented
        TransactionCash.objects.filter(id__in=ids).delete()

        # Ajax 요청인 경우 JSON 응답
        if request.headers.get("Content-Type") == "application/json":
            return JsonResponse({"success": True})

    # 기본적으로는 홈으로 리다이렉트
    return redirect('account_book:home')

@require_POST
def save_bulk_transactions(request):
    if request.headers.get("Content-Type") != "application/json":
        return JsonResponse({"success": False, "error": "Invalid content type"}, status=400)

    try:
        data = json.loads(request.body)
        transactions_data = data.get('transactions', [])
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    user = User.objects.first()  # 임시 사용자

    try:
        with transaction.atomic():
            # 마지막 잔액 가져오기
            last_transaction = TransactionCash.objects.order_by('-use_date', '-id').first()
            current_balance = last_transaction.cash_balance if last_transaction else 0

            # 날짜 기준으로 먼저 정렬 (잔액 계산의 정확성을 위해)
            transactions_data.sort(key=lambda x: x.get('date', ''))

            for item in transactions_data:
                cash_side = item.get('type')
                cash_amount_str = item.get('amount')
                use_date = item.get('date')
                
                # 단건 입력 패널의 유효성 검사와 동일하게, 타입, 금액, 날짜가 모두 있어야 함
                if not all([cash_side, cash_amount_str, use_date]):
                    continue

                try:
                    cash_amount = int(cash_amount_str)
                except (ValueError, TypeError):
                    continue # 금액이 유효한 숫자가 아니면 건너뛰기

                category_name = item.get('category')
                content = item.get('content')
                memo = item.get('memo')

                # 잔액 계산
                if cash_side == '수입':
                    current_balance += cash_amount
                else: # 지출
                    current_balance -= cash_amount
                
                kind = 'income' if cash_side == '수입' else 'expense'
                category = None
                if category_name:
                    try:
                        category = AccountBookCategory.objects.filter(cat_type=category_name, cat_kind=kind).first()
                    except AccountBookCategory.DoesNotExist:
                        pass

                TransactionCash.objects.create(
                    cash_user=user,
                    use_date=use_date,
                    cash_side=cash_side,
                    cash_cat=category,
                    cash_amount=cash_amount,
                    cash_cont=content,
                    memo=memo,
                    cash_balance=current_balance
                )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)