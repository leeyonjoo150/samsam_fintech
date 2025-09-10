Sneat Dashboard Template 단계별 통합 가이드
안녕하세요! 이제부터 'Sneat Dashboard' 템플릿을 'samsam_fintech' 프로젝트에 통합하는 과정을 하나씩 따라해 보겠습니다.
너무 복잡하게 생각하지 마시고, 제가 안내하는 순서대로 천천히 진행하시면 됩니다.

1단계: 정적 파일 (Static Files) 통합
목표: 대시보드 디자인을 위한 모든 CSS, JavaScript, 이미지 파일들을 가져옵니다.

복사할 폴더/파일:

sneat-django-dashboard/theme/static/assets/

붙여넣을 위치:

samsam_fintech/static/

결과:

samsam_fintech/static/assets/ 폴더가 생성되고, 그 안에 Sneat 대시보드의 모든 정적 파일이 복사됩니다.

설명:
Django는 static 폴더에 있는 정적 파일들을 관리합니다. 템플릿의 모든 스타일과 스크립트가 theme/static/assets에 들어있기 때문에, 이 폴더를 우리 프로젝트의 static 폴더로 통째로 가져와야 합니다. 이렇게 하면 HTML 템플릿에서 {% static 'assets/...' %}와 같은 방식으로 파일에 접근할 수 있게 됩니다.

2단계: 템플릿 파일 (Templates) 통합
목표: 대시보드 페이지의 HTML 구조를 가져옵니다.

복사할 폴더/파일:

sneat-django-dashboard/theme/templates/

붙여넣을 위치:

samsam_fintech/templates/

결과:

samsam_fintech/templates/ 안에 partials, layouts, pages 등의 폴더가 생성됩니다.

설명:
Django는 templates 폴더에서 HTML 파일을 찾습니다. Sneat 템플릿은 레이아웃과 페이지를 구조적으로 잘 분리해 놓았기 때문에, 이 폴더 전체를 가져와서 우리 프로젝트의 템플릿 폴더에 그대로 넣어주면 됩니다. 이렇게 하면 base.html과 같은 기본 레이아웃 파일을 상속받아 사용할 수 있게 됩니다.

3단계: Django 앱 설정 수정
목표: 우리 프로젝트에 대시보드 앱을 등록하고 설정합니다.

samsam_fintech/config/settings.py 파일 수정:

INSTALLED_APPS 리스트에 dashboard 앱을 추가합니다.

# Application definition
INSTALLED_APPS = [
    ...
    'account_book',
    'acc_auth',
    'financial_data',
    'main',
    'dashboard',  # 새로 추가하는 대시보드 앱
    ...
]

수정 이유: Django가 dashboard 앱의 뷰(view), 템플릿, 정적 파일 등을 인식하고 관리할 수 있도록 하기 위해서입니다.

STATIC_URL 아래에 STATICFILES_DIRS를 추가합니다.

STATIC_URL = 'static/'

# 정적 파일 경로 추가
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

수정 이유: Django가 samsam_fintech 프로젝트의 루트에 있는 static 폴더를 정적 파일의 추가적인 위치로 인식하도록 설정합니다. 이는 1단계에서 복사한 assets 폴더를 올바르게 불러오는 데 필수적입니다.

TEMPLATES 설정에서 DIRS를 수정합니다.

TEMPLATES = [
    {
        ...
        'DIRS': [BASE_DIR / 'templates'], # 기존의 'templates' 폴더를 지정
        ...
    },
]

수정 이유: 템플릿 폴더를 프로젝트 루트에 명시적으로 지정하여 Django가 2단계에서 복사한 HTML 파일들을 찾을 수 있도록 합니다.

4단계: URL 라우팅 설정
목표: 대시보드 페이지에 접속할 수 있는 URL을 정의합니다.

samsam_fintech/dashboard/urls.py 파일 생성:

dashboard 앱 폴더 안에 urls.py 파일을 새로 만듭니다.

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
]

수정 이유: 이 파일은 dashboard 앱 내의 URL 경로들을 정의합니다. 위 코드는 dashboard/ 경로로 들어오는 요청을 views.py의 dashboard_view 함수로 연결하겠다는 의미입니다.

samsam_fintech/config/urls.py 파일 수정:

urlpatterns 리스트에 dashboard 앱의 URL을 추가합니다.

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')), # 대시보드 URL 추가
    ...
]

수정 이유: 이 파일은 프로젝트의 메인 URL 설정입니다. dashboard/라는 URL로 들어오는 모든 요청을 dashboard 앱의 urls.py로 전달하도록 지시하는 역할을 합니다.

5단계: 뷰(View) 파일 생성
목표: URL 요청에 응답하여 HTML 템플릿을 렌더링하는 함수를 작성합니다.

samsam_fintech/dashboard/views.py 파일 생성:

dashboard 앱 폴더 안에 views.py 파일을 새로 만듭니다.

from django.shortcuts import render

def dashboard_view(request):
    # 여기에 다른 앱의 데이터를 읽어오는 로직을 추가할 수 있습니다.
    # 예: from account_book.models import Transaction
    # data = Transaction.objects.all()
    # context = {'transactions': data}

    return render(request, 'pages/dashboards-analytics.html', {}) # Sneat 템플릿의 메인 대시보드 파일


수정 이유: views.py는 사용자의 요청을 처리하고 응답을 반환하는 핵심 파일입니다. dashboard_view 함수는 dashboard/ URL로 접속했을 때 실행되며, render 함수를 통해 Sneat 템플릿의 대시보드 페이지(pages/dashboards-analytics.html)를 사용자에게 보여줍니다.

6단계: 데이터 연동 및 테스트
목표: 대시보드와 기존 앱의 데이터베이스를 연동하고, 모든 것이 올바르게 작동하는지 확인합니다.

dashboard/views.py 수정 (데이터 연동):

이 단계는 실제 프로젝트의 데이터베이스 테이블 구조에 따라 달라집니다.

예시로 account_book 앱의 Transaction 모델을 사용한다고 가정해 보겠습니다.

from django.shortcuts import render
from account_book.models import Transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
import json

def dashboard_view(request):
    # 1. account_book 앱의 데이터를 가져옵니다.
    # 예: 모든 거래 내역 가져오기
    transactions = Transaction.objects.all()

    # 2. 데이터를 분석하여 대시보드에 표시할 포맷으로 가공합니다.
    # 예: 월별 지출 합계
    monthly_expenses = transactions.filter(type='expense').values('date__month').annotate(total_amount=Sum('amount')).order_by('date__month')

    # 3. 템플릿으로 전달할 Context를 만듭니다.
    context = {
        'monthly_expenses': json.dumps(list(monthly_expenses)), # JSON 형태로 변환
        'total_transactions': transactions.count(),
        'recent_transactions': transactions.order_by('-date')[:5]
    }

    return render(request, 'pages/dashboards-analytics.html', context)

수정 이유: 대시보드는 정적인 디자인만 보여주는 것이 아니라, 실시간 데이터를 시각적으로 표현해야 합니다. 위 코드는 account_book 앱의 모델에서 데이터를 가져와 가공한 뒤, context를 통해 HTML 템플릿으로 전달합니다. 이제 이 데이터를 템플릿의 그래프에 연결해야 합니다.

pages/dashboards-analytics.html 수정 (데이터 시각화):

Sneat 템플릿은 chart.js나 apexcharts.js 같은 라이브러리를 사용합니다.

dashboard_view에서 넘겨준 monthly_expenses 데이터를 JavaScript 변수로 받아와 그래프에 적용합니다.

HTML 파일의 <script> 태그 안을 찾아 수정해야 합니다.

<!-- assets/js/main.js 파일을 열고 해당 코드를 찾아서 수정해야 합니다. -->
<script>
  // Django context에서 데이터 가져오기
  const monthlyExpensesData = JSON.parse('{{ monthly_expenses|safe }}');

  // 차트 데이터 포맷으로 변환
  const chartLabels = monthlyExpensesData.map(item => item.date__month + '월');
  const chartData = monthlyExpensesData.map(item => item.total_amount);

  // ApexCharts 예시 (템플릿에 따라 다를 수 있음)
  const analyticsBarChart = document.querySelector('#analyticsBarChart');
  if (analyticsBarChart) {
    const analyticsBarChartConfig = {
      chart: {
        // ... 차트 설정
      },
      series: [
        {
          data: chartData // 여기에 우리가 가져온 데이터가 들어갑니다.
        }
      ],
      // ... 기타 설정
      xaxis: {
        categories: chartLabels // 여기에 월 라벨이 들어갑니다.
      }
    };
    const barChart = new ApexCharts(analyticsBarChart, analyticsBarChartConfig);
    barChart.render();
  }
</script>

수정 이유: views.py에서 전달한 백엔드 데이터를 프론트엔드인 HTML/JavaScript에서 사용하여 동적으로 차트를 그리기 위해서입니다. {{ monthly_expenses|safe }} 구문은 Django 템플릿 언어로, 파이썬 변수 monthly_expenses의 내용을 HTML에 삽입하며, safe 필터는 이 내용이 안전한 HTML로 인식되도록 합니다. JSON.parse를 사용하여 JSON 문자열을 JavaScript 객체로 변환합니다.

7단계: 최종 정리 및 실행
python manage.py runserver 명령어로 서버를 실행합니다.

브라우저에서 http://127.0.0.1:8000/dashboard/ 에 접속하여 통합이 성공했는지 확인합니다.

대시보드 페이지가 나타나고, 다른 앱의 데이터가 올바르게 표시되면 통합이 완료된 것입니다.

축하합니다! 이제 여러분의 핀테크 프로젝트에 아름다운 대시보드가 성공적으로 통합되었습니다.