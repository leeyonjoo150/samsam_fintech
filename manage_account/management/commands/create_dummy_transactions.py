import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from manage_account.models import Account, TransactionAccount
from acc_auth.models import User
from django.db import transaction
from django.utils import timezone

class Command(BaseCommand):
    help = 'Creates 500 dummy transaction records between 2023-01-31 and 2025-09-16.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually save the generated data to the database.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['execute']:
            self.stdout.write(self.style.SUCCESS('--- Deleting existing transaction data ---'))
            TransactionAccount.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('--- Existing data deleted ---'))


        self.stdout.write('Generating 500 dummy transaction data entries...')

        accounts = list(Account.objects.all())
        if len(accounts) < 2:
            self.stdout.write(self.style.ERROR('Need at least 2 accounts to generate transactions.'))
            return

        # --- Start generating transactions ---
        start_date = datetime(2023, 1, 31)
        end_date = datetime(2025, 9, 16)
        total_days = (end_date - start_date).days
        
        for i in range(500):
            # 1. Select sender and receiver
            sender_acc, receiver_acc = random.sample(accounts, 2)

            # 2. Get latest balances
            try:
                sender_last_txn = TransactionAccount.objects.filter(my_acc=sender_acc).latest('txn_date')
                sender_balance = sender_last_txn.txn_balance
            except TransactionAccount.DoesNotExist:
                sender_balance = sender_acc.acc_money

            try:
                receiver_last_txn = TransactionAccount.objects.filter(my_acc=receiver_acc).latest('txn_date')
                receiver_balance = receiver_last_txn.txn_balance
            except TransactionAccount.DoesNotExist:
                receiver_balance = receiver_acc.acc_money

            # 3. Define transaction amount
            if sender_balance < 1000:
                continue # Skip if sender has no money
            
            amount = random.randint(1000, int(sender_balance / 10)) # Transfer up to 10% of balance

            # 4. Define transaction date (sequential)
            days_to_add = int(i * (total_days / 500))
            naive_txn_date = start_date + timedelta(days=days_to_add, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            txn_date = timezone.make_aware(naive_txn_date)


            # 5. Create withdrawal transaction for sender
            sender_new_balance = sender_balance - amount
            withdrawal = TransactionAccount(
                my_acc=sender_acc,
                cpart_acc=receiver_acc,
                txn_side='출금',
                txn_amount=amount,
                txn_balance=sender_new_balance,
                txn_date=txn_date,
                txn_cont=f'{receiver_acc.acc_user_name.user_name}에게 송금'
            )

            # 6. Create deposit transaction for receiver
            receiver_new_balance = receiver_balance + amount
            deposit = TransactionAccount(
                my_acc=receiver_acc,
                cpart_acc=sender_acc,
                txn_side='입금',
                txn_amount=amount,
                txn_balance=receiver_new_balance,
                txn_date=txn_date,
                txn_cont=f'{sender_acc.acc_user_name.user_name}로부터 입금'
            )

            if options['execute']:
                withdrawal.save()
                deposit.save()

            self.stdout.write(f"  - Txn {i+1}: {sender_acc.acc_user_name} -> {receiver_acc.acc_user_name}, Amount: {amount}, Date: {txn_date.strftime('%Y-%m-%d')}")


        if options['execute']:
            self.stdout.write(self.style.SUCCESS('Successfully saved 1000 new transaction records.'))
        else:
            self.stdout.write(self.style.WARNING('\nThis was a preview. No data has been saved.'))
            self.stdout.write(self.style.WARNING("To save this data, run the command again with the '--execute' flag."))
            self.stdout.write(self.style.WARNING("Example: python manage.py create_dummy_transactions --execute"))
