from django.urls import path
#원하는 뷰를 가져오는 형태
from .views import index

app_name = 'main'

urlpatterns = [
    path("", index, name = 'index')
]