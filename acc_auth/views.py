from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from .models import User

# Create your views here.
def login_view(request) :
    if request.method == "POST" :
        #디버깅 할때 request.user     request.GET    request.POST 이런 식으로 가능
        user_id = request.POST["user_id"]
        password = request.POST["password"]

        #인증, 정보가 있으면 리턴, 없으면 안나옴
        user = authenticate(request, user_id=user_id, password=password)
        if user is not None :
            login(request, user)
            messages.success(request, "로그인 성공")
            return redirect('main:index')
        else :
            messages.error(request, "아이디나 패스워드가 올바르지 않습니다.")
            #일단은 이대로 두고 수정하자
            return render(request, 'acc_auth/login.html')
    else :
        return render(request, 'acc_auth/login.html')
    
def logout_view(request) :
    user_id = request.user.user_id
    user_name = request.user.user_name
    logout(request)
    messages.info(request, f'{user_name}님 로그아웃되었습니다.')

    return redirect('acc_auth:login_view')

def signup_view(request) :
    """회원가입 처리 함수형 뷰"""
    if request.user.is_authenticated:
        #이미 로그인 한 사람이 회원가입창에 접근시 메인 페이지로 보냄
        return redirect('main:index')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_name = request.POST.get('user_name')
        user_phone = request.POST.get('user_phone')
        user_email = request.POST.get('user_email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # 유효성 검사
        errors = []

        if not all([user_id, password, user_name, user_email]):
            errors.append('아이디, 이름, 이메일, 비밀번호는 필수입니다.')

        if password != password2:
            errors.append('비밀번호가 일치하지 않습니다.')

        if len(password) < 8:
            errors.append('비밀번호는 8자 이상이어야 합니다.')

        if User.objects.filter(user_id=user_id).exists():
            errors.append('이미 사용중인 아이디입니다.')
        
        if User.objects.filter(user_email=user_email).exists():
            errors.append('이미 사용중인 이메일입니다.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # 사용자 생성
                user = User.objects.create_user(
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    password=password,
                    user_phone=user_phone
                )

                # 자동 로그인
                login(request, user)
                messages.success(request, f'{user.user_name}님 가입을 환영합니다!')
                return redirect('main:index')

            except IntegrityError:
                messages.error(request, '회원가입 중 오류가 발생했습니다.')

    return render(request, 'acc_auth/signup.html')