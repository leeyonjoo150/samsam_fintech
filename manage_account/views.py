from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import Account, TransactionAccount
from django.db.models import OuterRef, Subquery, Sum

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

def account_list(request) :
    #계좌 전체 리스트 가져오기
    
    #예금주 : account[].acc_user_name 만 하면 User객체를 가져와서 에러남
    #account[].acc_user_name.user_name 해야 함
    
    # 각 계좌의 최신 거래 잔액을 가져오는 서브쿼리
    latest_transaction_balance = TransactionAccount.objects.filter(
        my_acc=OuterRef('pk')
    ).order_by('-txn_date').values('txn_balance')[:1]

    # 계좌 목록에 최신 잔액을 주석으로 추가
    accounts = Account.objects.annotate(
        latest_balance=Subquery(latest_transaction_balance)
    )
    
    # 총 자산 계산
    total_assets = accounts.aggregate(total=Sum('latest_balance'))['total'] or 0
    
    context = {
        "accounts" : accounts,
        "total_assets" : total_assets
    }
    return render(request, 'manage_account/account_list.html', context)

def account_detail(request, pk) :
    account = get_object_or_404(Account, pk=pk)
    # 이 계좌와 관련된 TransactionAccount 객체들 가져오기
    transactions = TransactionAccount.objects.filter(my_acc=account).order_by('-txn_date')
    
    context = {
        'account': account,
        'transactions': transactions
    }
    return render(request, 'manage_account/account_detail.html', context)