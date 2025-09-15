from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import json

from .models import User, Account, Transaction

class LoginView(View):
    """로그인 뷰"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('transfers:dashboard')  # 이미 로그인된 경우 대시보드로
        return render(request, 'transfers/login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'{user.username}님 환영합니다!')
                return redirect('transfers:dashboard')
            else:
                messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
        else:
            messages.error(request, '아이디와 비밀번호를 입력해주세요.')
        
        return render(request, 'transfers/login.html')

def logout_view(request):
    """로그아웃 뷰"""
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('transfers:login')

@login_required
def dashboard(request):
    """대시보드 (메인 페이지)"""
    user_accounts = Account.objects.filter(acc_user_name=request.user)
    recent_transactions = Transaction.objects.filter(
        Q(from_account__acc_user_name=request.user) |
        Q(to_account__acc_user_name=request.user)
    )[:5]
    
    context = {
        'user_accounts': user_accounts,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def transaction_history(request):
    """송금 내역 페이지"""
    user_accounts = Account.objects.filter(acc_user_name=request.user)
    
    # 사용자의 모든 거래 내역 조회
    transactions = Transaction.objects.filter(
        Q(from_account__acc_user_name=request.user) |
        Q(to_account__acc_user_name=request.user)
    ).select_related('from_account', 'to_account')
    
    # 계좌별 필터링
    selected_account = request.GET.get('account')
    if selected_account:
        transactions = transactions.filter(
            Q(from_account__acc_num=selected_account) |
            Q(to_account__acc_num=selected_account)
        )
    
    context = {
        'transactions': transactions,
        'user_accounts': user_accounts,
        'selected_account': selected_account,
    }
    return render(request, 'accounts/transaction_history.html', context)

@login_required
def transfer_form(request):
    """계좌 이체 폼 페이지"""
    user_accounts = Account.objects.filter(acc_user_name=request.user)
    
    context = {
        'user_accounts': user_accounts,
    }
    return render(request, 'transfers/transfer_form.html', context)

@login_required
def verify_account_password(request):
    """계좌 비밀번호 확인 페이지"""
    if request.method == 'POST':
        from_account_num = request.POST.get('from_account')
        to_account_num = request.POST.get('to_account')
        recipient_bank = request.POST.get('recipient_bank')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        account_password = request.POST.get('account_password')
        
        try:
            from_account = get_object_or_404(Account, acc_num=from_account_num, acc_user_name=request.user)
            
            # 계좌 비밀번호 확인
            if check_password(account_password, from_account.acc_pw):
                # 받는 계좌 확인
                try:
                    to_account = Account.objects.get(acc_num=to_account_num)
                    # 송금 처리
                    return process_transfer(request, from_account, to_account, amount, description)
                except Account.DoesNotExist:
                    # 외부 계좌로 처리 (실제로는 외부 은행 API 호출)
                    context = {
                        'error_message': f'{recipient_bank} {to_account_num} 계좌를 찾을 수 없습니다. 계좌 정보를 다시 확인해주세요.',
                        'transfer_data': {
                            'from_account': from_account_num,
                            'to_account': to_account_num,
                            'amount': amount,
                        },
                        'attempted_at': timezone.now(),
                    }
                    return render(request, 'transfers/transfer_error.html', context)
            else:
                messages.error(request, '계좌 비밀번호가 올바르지 않습니다.')
                
        except Account.DoesNotExist:
            messages.error(request, '계좌를 찾을 수 없습니다.')
        except Exception as e:
            messages.error(request, f'오류가 발생했습니다: {str(e)}')
    
    # GET 요청이거나 비밀번호 확인 실패 시
    transfer_data = {
        'from_account': request.POST.get('from_account') or request.GET.get('from_account'),
        'to_account': request.POST.get('to_account') or request.GET.get('to_account'),
        'recipient_bank': request.POST.get('recipient_bank') or request.GET.get('recipient_bank'),
        'amount': request.POST.get('amount') or request.GET.get('amount'),
        'description': request.POST.get('description') or request.GET.get('description', ''),
    }
    
    context = {
        'transfer_data': transfer_data,
    }
    return render(request, 'transfers/verify_password.html', context)

def process_transfer(request, from_account, to_account, amount, description):
    """송금 처리 함수"""
    try:
        with transaction.atomic():
            amount = Decimal(str(amount))
            
            # 잔액 확인
            if from_account.acc_money < amount:
                context = {
                    'error_message': '송금할 금액이 잔액보다 큽니다.',
                    'current_balance': from_account.acc_money,
                    'requested_amount': amount,
                }
                return render(request, 'transfers/transfer_error.html', context)
            
            # 잔액 업데이트
            from_account.acc_money -= amount
            to_account.acc_money += amount
            
            from_account.save()
            to_account.save()
            
            # 거래 내역 저장
            new_transaction = Transaction.objects.create(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                description=description,
            )
            
            messages.success(request, f'{to_account.acc_user_name}님께 {amount:,}원을 송금했습니다.')
            return redirect('transfers:transfer_success', transaction_id=new_transaction.id)
            
    except ValueError:
        messages.error(request, '올바른 금액을 입력해주세요.')
        return redirect('transfers:transfer_form')
    except Exception as e:
        messages.error(request, f'송금 처리 중 오류가 발생했습니다: {str(e)}')
        return redirect('transfers:transfer_form')

@login_required
def transfer_success(request, transaction_id):
    """송금 성공 페이지"""
    transaction = get_object_or_404(Transaction, id=transaction_id)
    context = {
        'transaction': transaction,
    }
    return render(request, 'transfers/transfer_success.html', context)


@login_required
@csrf_exempt
def get_account_info(request):
    """AJAX로 계좌 정보 조회"""
    if request.method == 'GET':
        account_num = request.GET.get('account_num')
        
        try:
            account = Account.objects.get(acc_num=account_num)
            return JsonResponse({
                'success': True,
                'account_holder': account.acc_user_name.username,
                'bank_name': '우리은행',  # 실제로는 계좌의 은행 정보
                'balance': str(account.acc_money)
            })
        except Account.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '계좌를 찾을 수 없습니다.'
            })
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})

@login_required
def transfer_confirmation(request):
    """송금 확인 페이지"""
    if request.method == 'POST':
        transfer_data = {
            'from_account': request.POST.get('from_account'),
            'to_account': request.POST.get('to_account'),
            'recipient_bank': request.POST.get('recipient_bank'),
            'amount': request.POST.get('amount'),
            'description': request.POST.get('description', ''),
        }
        
        try:
            # 송금 계좌 정보 확인
            from_account = get_object_or_404(Account, 
                                           acc_num=transfer_data['from_account'], 
                                           acc_user_name=request.user)
            
            # 받는 계좌 정보 조회 (있는 경우)
            to_account = None
            try:
                to_account = Account.objects.get(acc_num=transfer_data['to_account'])
            except Account.DoesNotExist:
                pass
            
            context = {
                'from_account': from_account,
                'to_account': to_account,
                'transfer_data': transfer_data,
            }
            
            return render(request, 'transfers/transfer_confirmation.html', context)
            
        except Account.DoesNotExist:
            messages.error(request, '송금 계좌를 찾을 수 없습니다.')
            return redirect('transfers:transfer_form')
    
    return redirect('transfers:transfer_form')

@login_required 
def account_detail(request, account_num):
    """계좌 상세 정보 페이지"""
    account = get_object_or_404(Account, acc_num=account_num, acc_user_name=request.user)
    
    # 해당 계좌의 거래 내역
    transactions = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account)
    ).order_by('-created_at')
    
    # 월별 거래 통계 (최근 6개월)
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count
    
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_stats = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account),
        created_at__gte=six_months_ago
    ).extra(
        select={'month': "date_trunc('month', created_at)"}
    ).values('month').annotate(
        total_amount=Sum('amount'),
        transaction_count=Count('id')
    ).order_by('month')
    
    context = {
        'account': account,
        'transactions': transactions,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'accounts/account_detail.html', context)

@login_required
def create_account(request):
    """새 계좌 생성"""
    if request.method == 'POST':
        account_password = request.POST.get('account_password')
        confirm_password = request.POST.get('confirm_password')
        initial_deposit = request.POST.get('initial_deposit', 0)
        
        if account_password != confirm_password:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'accounts/create_account.html')
        
        try:
            # 새 계좌번호 생성 (간단한 예시)
            import random
            new_account_num = f"110-{random.randint(100, 999)}-{random.randint(100000, 999999)}"
            
            # 중복 확인
            while Account.objects.filter(acc_num=new_account_num).exists():
                new_account_num = f"110-{random.randint(100, 999)}-{random.randint(100000, 999999)}"
            
            # 계좌 생성
            new_account = Account.objects.create(
                acc_num=new_account_num,
                acc_user_name=request.user,
                acc_pw=make_password(account_password),
                acc_money=Decimal(str(initial_deposit))
            )
            
            messages.success(request, f'새 계좌({new_account_num})가 생성되었습니다.')
            return redirect('transfers:dashboard')
            
        except Exception as e:
            messages.error(request, f'계좌 생성 중 오류가 발생했습니다: {str(e)}')
    
    return render(request, 'accounts/create_account.html')

@login_required
def change_account_password(request, account_num):
    """계좌 비밀번호 변경"""
    account = get_object_or_404(Account, acc_num=account_num, acc_user_name=request.user)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # 현재 비밀번호 확인
        if not check_password(current_password, account.acc_pw):
            messages.error(request, '현재 비밀번호가 올바르지 않습니다.')
            return render(request, 'accounts/change_password.html', {'account': account})
        
        # 새 비밀번호 확인
        if new_password != confirm_password:
            messages.error(request, '새 비밀번호가 일치하지 않습니다.')
            return render(request, 'accounts/change_password.html', {'account': account})
        
        # 비밀번호 변경
        account.acc_pw = make_password(new_password)
        account.save()
        
        messages.success(request, '계좌 비밀번호가 변경되었습니다.')
        return redirect('transfers:account_detail', account_num=account_num)
    
    return render(request, 'accounts/change_password.html', {'account': account})