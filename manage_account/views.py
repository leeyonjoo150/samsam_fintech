import csv
import re
from urllib.parse import quote
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import Account, TransactionAccount
from django.db.models import OuterRef, Subquery, Sum, Q
from .forms import AccountModelForm
from acc_auth.models import User # User 모델의 위치에 따라 달라짐
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
# ReportLab 관련 모듈 import
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.conf import settings
import os
from django.http import JsonResponse

def check_acc_num(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)

    acc_num = request.GET.get('acc_num', None)
    data = {
        'is_taken': Account.objects.filter(acc_num__iexact=acc_num).exists()
    }
    return JsonResponse(data)

# Create your views here.
def debug_request(request) :
    #request의 메서드와
    #request의 path
    #request의 META>REMOTE_ADDR를 화면에 표시하자!
    content = f"""이것이 request가 가지고 있는 정보의 예시입니다. <br>\n        request.path = {request.path} <br>\n        request.method = {request.method} <br>\n        request.META.REMOTE_ADDR = {request.META.get('REMOTE_ADDR', 'Unknown')} <br>\n    """
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

@login_required
def account_detail(request, pk) :
    #계좌 거래 목록
    account = get_object_or_404(Account, pk=pk)
    
    # 계좌 소유자 확인
    if account.acc_user_name != request.user:
        return redirect('manage_account:account_list')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    search_query = request.GET.get('q', '').strip()
    txn_type = request.GET.get('type')

    transactions = TransactionAccount.objects.filter(my_acc=account)

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(txn_date__range=(start_date, end_date))

    if txn_type:
        transactions = transactions.filter(txn_side=txn_type)

    if search_query:
        transactions = transactions.filter(
            Q(cpart_acc__acc_bank__icontains=search_query) |
            Q(cpart_acc__acc_num__icontains=search_query) |
            Q(cpart_acc__acc_user_name__user_name__icontains=search_query)
        )

    transactions = transactions.order_by('-txn_date')

    paginator = Paginator(transactions, 20) # 한 페이지에 20개씩
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'account': account,
        'page_obj': page_obj,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'search_query': search_query,
        'type': txn_type,
    }
    return render(request, 'manage_account/account_detail.html', context)

@login_required
def account_create(request):
    #계좌 등록
    if request.method == 'POST':
        form = AccountModelForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            
            # Set the user to the currently logged-in user
            account.acc_user_name = request.user
            
            # Encrypt the password
            account.acc_pw = make_password(form.cleaned_data['acc_pw'])

            account.acc_user_name = request.user

            account.save()
            return redirect('manage_account:account_list')
    else:
        form = AccountModelForm()
    
    return render(request, 'manage_account/account_create.html', {'form': form})

@login_required
def export_transactions_csv(request, pk):
    """거래 내역을 CSV 파일로 내보내는 View"""
    
    # 1. account_detail 뷰와 동일하게 데이터를 필터링합니다.
    # ----------------------------------------------------
    account = get_object_or_404(Account, pk=pk, acc_user_name=request.user)
    
    # 계좌 소유자 확인
    if account.acc_user_name != request.user:
        return redirect('manage_account:account_list')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    search_query = request.GET.get('q', '').strip()
    txn_type = request.GET.get('type')

    transactions = TransactionAccount.objects.filter(my_acc=account)

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(txn_date__range=(start_date, end_date))

    if txn_type:
        transactions = transactions.filter(txn_side=txn_type)

    if search_query:
        transactions = transactions.filter(
            Q(cpart_acc__acc_bank__icontains=search_query) |
            Q(cpart_acc__acc_num__icontains=search_query) |
            Q(cpart_acc__acc_user_name__user_name__icontains=search_query)
        )
    
    transactions = transactions.order_by('-txn_date')
    # ----------------------------------------------------

    # 2. CSV 파일로 만들어서 응답(response)을 보냅니다.
    # ----------------------------------------------------
    response = HttpResponse(content_type='text/csv')

    # /// 파일명 생성 로직 시작 ///
    
    # 1. 계좌 식별자 (은행명 사용)
    account_identifier = account.get_acc_bank_display()
    
    # 2. 현재 시간 (YYYYMMDD_HHMMSS 형식)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 3. 최종 파일명 조합
    filename = f"{account_identifier}_거래내역_{timestamp}.csv"

    # 파일명에 포함될 수 없는 특수문자 제거 (안전장치)
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)

    # /// 파일명 생성 로직 끝 ///

    # 파일명을 지정합니다.
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    
    # Excel에서 한글이 깨지지 않도록 UTF-8 BOM을 추가합니다.
    response.write(u'\ufeff'.encode('utf8'))

    # CSV writer를 생성합니다.
    writer = csv.writer(response)
    
    # CSV 파일의 헤더(첫 번째 줄)를 작성합니다.
    writer.writerow(['거래일', '거래 종류', '금액', '잔액', '상대 계좌'])

    # 필터링된 거래 내역(transactions)을 한 줄씩 CSV 파일에 씁니다.
    for t in transactions:
        writer.writerow([
            t.txn_date.strftime('%Y-%m-%d %H:%M'), 
            t.txn_side,
            t.txn_amount,
            t.txn_balance,
            str(t.cpart_acc) # 객체를 문자열로 변환
        ])

    return response

@login_required
def export_transactions_pdf(request, pk):
    """거래 내역을 ReportLab을 이용해 PDF 파일로 내보내는 View"""
    
    # 1. 데이터 필터링 (기존과 동일)
    account = get_object_or_404(Account, pk=pk, acc_user_name=request.user)
    transactions = TransactionAccount.objects.filter(my_acc=account)
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    search_query = request.GET.get('q', '').strip()
    txn_type = request.GET.get('type')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(txn_date__range=(start_date, end_date))

    if txn_type:
        transactions = transactions.filter(txn_side=txn_type)

    if search_query:
        transactions = transactions.filter(
            Q(cpart_acc__acc_bank__icontains=search_query) |
            Q(cpart_acc__acc_num__icontains=search_query) |
            Q(cpart_acc__acc_user_name__user_name__icontains=search_query)
        )
    transactions = transactions.order_by('-txn_date')

    # 2. PDF 파일명 설정
    response = HttpResponse(content_type='application/pdf')
    account_identifier = account.get_acc_bank_display()
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f"{account_identifier}_거래명세서_{timestamp}.pdf"
    filename = re.sub(r'[\\/*?:\"<>|]', "", filename)
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"

    # 3. ReportLab으로 PDF 내용 그리기
    # 3-1. 한글 폰트 등록
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'NanumGothic.ttf')
    pdfmetrics.registerFont(TTFont('NanumGothic', font_path))

    # 3-2. PDF 문서(Canvas) 생성
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter # 페이지 크기

    # 3-3. 제목 및 계좌 정보 쓰기
    p.setFont('NanumGothic', 18)
    p.drawString(50, height - 50, "거래 명세서")
    p.setFont('NanumGothic', 10)
    p.drawString(50, height - 80, f"계좌: {account.get_acc_bank_display()} {account.acc_num}")
    p.drawString(50, height - 95, f"소유주: {account.acc_user_name.user_name}")

    # 3-4. 테이블 데이터 준비
    data = [['거래일', '종류', '금액', '잔액', '상대 계좌']]
    for t in transactions:
        amount_str = f"+{t.txn_amount:,}" if t.txn_side == '입금' else f"-{t.txn_amount:,}"
        row = [
            t.txn_date.strftime('%Y-%m-%d %H:%M'),
            t.txn_side,
            amount_str,
            f"{t.txn_balance:,}원",
            str(t.cpart_acc)
        ]
        data.append(row)

    # 3-5. 테이블 스타일 정의 및 생성
    table = Table(data, colWidths=[120, 50, 80, 100, 150])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')), # 헤더 배경색
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)

    # 3-6. 테이블 그리기
    table_height = len(data) * 20 # 근사치 높이 계산
    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 120 - table_height)

    # 3-7. PDF 저장
    p.showPage()
    p.save()

    return response