# samsam-fintech

`samsam-fintech`는 개인의 재무 상태를 관리하고 투자 포트폴리오를 추적할 수 있도록 돕는 개인용 핀테크 웹 애플리케이션입니다. Django 프레임워크를 기반으로 개발되었습니다.

## ✨ 주요 기능

*   **사용자 인증**: 회원가입, 로그인, 로그아웃 기능을 통해 사용자별 데이터를 관리합니다.
*   **가계부**: 수입 및 지출 내역을 기록하고 카테고리별로 관리할 수 있습니다.
*   **금융 대시보드**: 전체 자산 현황, 소비 패턴 등을 시각적으로 요약하여 보여줍니다.
*   **주식/투자 관리**: 보유한 증권 계좌와 주식 종목을 등록하고 관리할 수 있습니다.
*   **주식 정보 검색**: 원하는 주식 종목을 검색하고 정보를 확인할 수 있습니다.
*   **미니 게임**: GeoGuessr와 유사한 미니게임을 통해 재미 요소를 더했습니다.

## 🛠️ 기술 스택

*   **Backend**: Python, Django
*   **Frontend**: HTML, CSS, JavaScript
*   **Database**: SQLite3 (기본 설정), `config/settings.py`에서 변경 가능

## 📂 프로젝트 구조

```
samsam_fintech/
├── acc_auth/         # 사용자 인증 및 계정 관리
├── account_book/     # 가계부(수입/지출) 관리
├── dashboard/        # 금융 데이터 시각화 대시보드
├── financial_data/   # 주식 계좌, 보유 종목 등 금융 데이터 관리
├── main/             # 메인 랜딩 페이지
├── manage_account/   # 계정 정보 및 더미 데이터 관리
├── static/           # CSS, JS 등 정적 파일
└── templates/        # HTML 템플릿 파일
```

## 🚀 설치 및 실행 방법

1.  **프로젝트 클론**
    ```bash
    git clone <repository-url>
    cd samsam_fintech
    ```

2.  **가상 환경 생성 및 활성화**
    *   Windows
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   macOS / Linux
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **의존성 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **데이터베이스 마이그레이션**
    ```bash
    python manage.py migrate
    ```
    *   이 과정에서 `manage_account` 앱의 `0002_populate_categories` 마이그레이션이 실행되어 가계부 카테고리 초기 데이터가 생성됩니다.

5.  **(선택) 더미 데이터 생성**
    개발 및 테스트를 위해 가상의 주식 데이터를 생성할 수 있습니다.
    ```bash
    python manage.py create_dummy_stock_data
    ```

6.  **개발 서버 실행**
    ```bash
    python manage.py runserver
    ```

7.  웹 브라우저에서 `http://127.0.0.1:8000/`으로 접속하여 애플리케이션을 확인합니다.
