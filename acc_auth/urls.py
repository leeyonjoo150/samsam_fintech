from django.urls import path
from . import views

app_name = 'acc_auth'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
]
