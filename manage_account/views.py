from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Account, TransactionAccount
from django.db.models import OuterRef, Subquery, Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import Account, TransactionAccount
from django.db.models import OuterRef, Subquery, Sum
from .forms import AccountModelForm
from acc_auth.models import User # User 모델의 위치에 따라 달라짐
from django.contrib.auth.decorators import login_required

# Create your views here.
def debug_request(request) :
    #request의 메서드와
    #request의 path
    #request의 META>REMOTE_ADDR를 화면에 표시하자!
    content = f"""이것이 request가 가지고 있는 정보의 예시입니다. <br>
        request.path = {request.path} <br>
        request.method = {request.method} <br>
        request.META.REMOTE_ADDR = {request.META.get('REMOTE_ADDR', 'Unknown')} <br>
    """
    return HttpResponse(content)

@login_required
def account_list(request) :
    #계좌 전체 리스트 가져오기
    
    #예금주 : account[].acc_user_name 만 하면 User객체를 가져와서 에러남
    #account[].acc_user_name.user_name 해야 함
    
    # 각 계좌의 최신 거래 잔액을 가져오는 서브쿼리
    latest_transaction_balance = TransactionAccount.objects.filter(
        my_acc=OuterRef('pk')
    ).order_by('-txn_date').values('txn_balance')[:1]

    # 현재 로그인한 사용자의 계좌만 가져오기
    accounts = Account.objects.filter(acc_user_name=request.user).annotate(
        latest_balance=Subquery(latest_transaction_balance)
    )
    
    # 총 자산 계산
    total_assets = accounts.aggregate(total=Sum('latest_balance'))['total'] or 0
    
    context = {
        "accounts" : accounts,
        "total_assets" : total_assets
    }
    return render(request, 'manage_account/account_list.html', context)

from datetime import datetime, timedelta

@login_required
def account_detail(request, pk) :
    account = get_object_or_404(Account, pk=pk)
    
    # 계좌 소유자 확인
    if account.acc_user_name != request.user:
        return redirect('manage_account:account_list')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    transactions = TransactionAccount.objects.filter(my_acc=account)

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(txn_date__range=(start_date, end_date))

    transactions = transactions.order_by('-txn_date')

    context = {
        'account': account,
        'transactions': transactions,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'manage_account/account_detail.html', context)

from django.contrib.auth.hashers import make_password

@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountModelForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            
            # 비밀번호를 암호화하여 저장
            account.acc_pw = make_password(form.cleaned_data['acc_pw'])

            account.acc_user_name = request.user

            account.save()
            return redirect('manage_account:account_list')
    else:
        form = AccountModelForm()
    
    return render(request, 'manage_account/account_create.html', {'form': form})