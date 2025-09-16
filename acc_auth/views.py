from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '회원가입이 완료되었습니다. 로그인해주세요.')
            return redirect('transfers:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'acc_auth/signup.html', {'form': form})