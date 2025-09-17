from django.urls import path
#원하는 뷰를 가져오는 형태
from .views import login_view, logout_view, signup_view

app_name = 'acc_auth'

urlpatterns = [
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout_view'),
    path('signup/', signup_view, name='signup_view')
]