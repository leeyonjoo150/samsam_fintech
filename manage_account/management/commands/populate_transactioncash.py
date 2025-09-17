import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz
from manage_account.models import TransactionCash, AccountBookCategory, User

class Command(BaseCommand):
    help = 'Populates TransactionCash model with dummy data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate TransactionCash with dummy data...'))

        # Ensure there's at least one user
        user, created = User.objects.get_or_create(user_name='dummyuser', defaults={'password': 'password123', 'user_email': 'dummy@example.com'})
        if created:
            self.stdout.write(self.style.SUCCESS('Created dummy user: dummyuser'))
        
        # Get all income and expense categories
        income_categories = list(AccountBookCategory.objects.filter(cat_kind='income'))
        expense_categories = list(AccountBookCategory.objects.filter(cat_kind='expense'))

        if not income_categories and not expense_categories:
            self.stdout.write(self.style.WARNING('No income or expense categories found. Please create some first.'))
            return

        # Define date range
        start_date = datetime(2023, 1, 2, 0, 0, 0, tzinfo=pytz.utc)
        end_date = datetime(2025, 9, 18, 23, 59, 59, tzinfo=pytz.utc)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days

        # Define choices
        cash_sides = ['수입', '지출']
        asset_types = ['현금', '카드']
        contents = ['식사', '교통', '쇼핑', '월급', '용돈', '커피', '영화', '병원', '통신비']
        memos = ['친구와 함께', '온라인 구매', '선물', '출장', '경조사', '기타']

        # Get the last cash balance to start from
        last_transaction = TransactionCash.objects.order_by('-use_date', '-id').first()
        current_balance = last_transaction.cash_balance if last_transaction else 0

        transactions_to_create = []
        for i in range(500):
            # Random date
            random_number_of_days = random.randrange(days_between_dates)
            random_date = start_date + timedelta(days=random_number_of_days)

            # Random cash side and amount
            cash_side = random.choice(cash_sides)
            cash_amount = random.randint(1000, 100000)

            # Update balance
            if cash_side == '수입':
                current_balance += cash_amount
            else:
                current_balance -= cash_amount
            
            # Random category based on cash_side
            if cash_side == '수입':
                category = random.choice(income_categories) if income_categories else None
            else:
                category = random.choice(expense_categories) if expense_categories else None

            # Random content and memo
            content = random.choice(contents)
            memo = random.choice(memos)

            # Random asset type
            asset_type = random.choice(asset_types)

            transactions_to_create.append(
                TransactionCash(
                    cash_user=user,
                    use_date=random_date,
                    cash_side=cash_side,
                    cash_amount=cash_amount,
                    cash_balance=current_balance,
                    cash_cont=content,
                    memo=memo,
                    cash_cat=category,
                    asset_type=asset_type,
                )
            )
        
        # Bulk create for efficiency
        TransactionCash.objects.bulk_create(transactions_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully populated 500 TransactionCash records.'))
