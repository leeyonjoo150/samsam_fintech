# dashboard/management/commands/create_dummy_data.py
# 다른 팀 멤버가 설계된 Data 구조는 대시보드에 보여주기가 힘들어 dashboard app 개발을 위해 임시로 table을 생성함
# 신뢰성 있는 App 개발을 위해서는 많은 데이터가 필요하므로 임의로 다량의 Dummy Data를 생성함
# 본 프로그램은 기존 데이터를 모두 삭제하고, 2023-01-01부터 2025-09-11까지 임의 거래 데이터를 생성하고 저장하는 기능임
#
# 추후 팀에서 생성한 데이터로 전환 계획임
#
# 본 프로그램 작동 방법은 다음과 같다.
#
# 1. 본 소스 파일 create_dummy_data.py는 dashboard/management/command에 저장해야 한다
# 2. VSCode Terminal에서 다음과 같이 입력하여 생성한다.
#    > python manage.py create_dummy_data
# 3. 생성된 데이터는 admin 페이지에서 확인하거나 DBeaver 등으로 확인할 수 있다.
#
# 생성: 2024-09-11 by sskim
# 수정: 2024-09-11 by sskim 

from django.core.management.base import BaseCommand
from dashboard.models import Transaction
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = '3년치 더미 거래 데이터를 생성합니다. 기존 데이터는 모두 삭제됩니다.'

    def handle(self, *args, **kwargs):
        self.stdout.write("기존 거래 데이터를 모두 삭제 중...")
        Transaction.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("데이터 삭제 완료."))

        income_categories = ['월급', '부수입', '투자수익', '용돈']
        expense_categories = ['식비', '교통비', '쇼핑', '문화생활', '주거비', '통신비', '기타']
        
        start_date = date(2023, 1, 1)
        end_date = date(2025, 9, 11)
        
        current_date = start_date
        transactions_to_create = []

        self.stdout.write("더미 데이터 생성 시작...")

        while current_date <= end_date:
            num_transactions = random.randint(1, 4)
            for _ in range(num_transactions):
                is_income = random.random() < 0.3
                if is_income:
                    category = random.choice(income_categories)
                    amount = random.randint(10000, 5000000)
                    transaction_type = '수입'
                else:
                    category = random.choice(expense_categories)
                    amount = random.randint(5000, 200000)
                    transaction_type = '지출'
                
                transactions_to_create.append(
                    Transaction(
                        transaction_date=current_date,
                        transaction_type=transaction_type,
                        category=category,
                        amount=amount,
                        description=f"{current_date} 거래내역"
                    )
                )
            current_date += timedelta(days=1)

        Transaction.objects.bulk_create(transactions_to_create)
        
        self.stdout.write(self.style.SUCCESS(f"총 {len(transactions_to_create)}개의 더미 데이터가 성공적으로 생성되었습니다."))
