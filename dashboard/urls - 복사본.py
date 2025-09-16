from django.urls import path
from . import views
#원하는 뷰를 가져오는 형태

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]
