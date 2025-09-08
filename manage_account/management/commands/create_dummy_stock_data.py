from django.core.management.base import BaseCommand
from acc_auth.models import User
from manage_account.models import StockAccount, StockContent

class Command(BaseCommand):
    help = 'Creates dummy stock account and content data for testing purposes.'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- 주식 더미 데이터 생성을 시작합니다. ---")

        # 1. 슈퍼유저 'admin'을 찾습니다.
        try:
            user = User.objects.get(user_id='admin')
            if not user.is_superuser:
                self.stdout.write(self.style.ERROR("'admin' 사용자가 슈퍼유저가 아닙니다. DBeaver에서 is_superuser를 1로 변경하세요."))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("사용자 'admin'이 존재하지 않습니다. createsuperuser 명령어를 사용하세요."))
            return

        # 2. 'admin' 사용자의 주식 계좌를 가져오거나 새로 만듭니다.
        stock_account, created = StockAccount.objects.get_or_create(
            st_user_id=user,
            defaults={
                'st_company': '키움증권',
                'st_acc_num': '1234567890',
                'st_acc_pw': '1234'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✅ 주식 계좌가 성공적으로 생성되었습니다."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ 기존 주식 계좌를 사용합니다."))

        # 3. 기존 주식 보유량 더미 데이터를 모두 삭제합니다.
        deleted_count, _ = StockContent.objects.filter(st_id=stock_account).delete()
        self.stdout.write(f"🗑️ 기존 주식 보유량 {deleted_count}개를 삭제했습니다.")

        # 4. 새로운 주식 보유량 더미 데이터를 생성합니다.
        dummy_data = [
            {'ticker_code': '005930', 'pur_amount': 78500, 'share': 10, 'currency': '원화'},
            {'ticker_code': 'AAPL', 'pur_amount': 180, 'share': 5, 'currency': '달러'},
            {'ticker_code': 'TSLA', 'pur_amount': 250, 'share': 3, 'currency': '달러'},
        ]
        
        for item in dummy_data:
            StockContent.objects.create(
                st_id=stock_account,
                ticker_code=item['ticker_code'],
                pur_amount=item['pur_amount'],
                share=item['share'],
                currency=item['currency']
            )
        
        self.stdout.write(self.style.SUCCESS("✨ 주식 보유량 더미 데이터 생성이 완료되었습니다."))