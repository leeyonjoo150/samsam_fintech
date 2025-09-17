
import random
from django.core.management.base import BaseCommand
from acc_auth.models import User
from manage_account.models import Account
from datetime import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generates and previews dummy account data without saving to the database.'

    def handle(self, *args, **options):
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in the database. Please create users first.'))
            return

        dummy_data_preview = []
        existing_acc_nums = set(Account.objects.values_list('acc_num', flat=True))

        for user in users:
            num_accounts_to_create = random.randint(2, 5)
            for i in range(num_accounts_to_create):
                while True:
                    # Generate a unique account number
                    bank = random.choice(Account.BANK_CHOICES)[0]
                    acc_num = f"{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(10000, 99999)}"
                    if acc_num not in existing_acc_nums:
                        existing_acc_nums.add(acc_num)
                        break
                
                account_data = {
                    'acc_user_name': user.user_name,
                    'acc_bank': bank,
                    'acc_num': acc_num,
                    'acc_pw': '1234', # As requested
                    'acc_money': random.randint(0, 10000000),
                    'created_at': timezone.make_aware(datetime(2023, 1, 1))
                }
                dummy_data_preview.append(account_data)

        self.stdout.write(self.style.SUCCESS('--- Dummy Account Data Preview ---'))
        for data in dummy_data_preview:
            self.stdout.write(
                f"User: {data['acc_user_name']}, "
                f"Bank: {data['acc_bank']}, "
                f"Account Number: {data['acc_num']}, "
                f"Password: {data['acc_pw']}, "
                f"Balance: {data['acc_money']:,}, "
                f"Created At: {data['created_at'].strftime('%Y-%m-%d')}"
            )
        self.stdout.write(self.style.SUCCESS('--- End of Preview ---'))
        self.stdout.write(self.style.WARNING('This is only a preview. No data has been saved to the database.'))
