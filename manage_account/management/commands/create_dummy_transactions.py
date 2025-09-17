
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from manage_account.models import Account, TransactionAccount
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates dummy transaction records. Balance will not go below zero.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually save the generated data to the database.',
        )

    def handle(self, *args, **options):
        self.stdout.write('Generating dummy transaction data...')

        accounts = list(Account.objects.all())
        if len(accounts) < 2:
            self.stdout.write(self.style.ERROR('Need at least 2 accounts to generate transactions.'))
            return

        generated_transactions = []
        
        # Use a temporary dictionary to track balances during generation for more realistic chaining
        temp_balances = {acc.pk: None for acc in accounts}

        def get_latest_balance(account):
            if temp_balances.get(account.pk) is not None:
                return temp_balances[account.pk]
            
            try:
                balance = TransactionAccount.objects.filter(my_acc=account).latest('txn_date').txn_balance
                temp_balances[account.pk] = balance
                return balance
            except TransactionAccount.DoesNotExist:
                balance = 1000000  # Starting balance
                temp_balances[account.pk] = balance
                return balance

        attempts = 0
        while len(generated_transactions) < 30 and attempts < 100:
            attempts += 1

            account_a, account_b = random.sample(accounts, 2)
            
            balance_a = get_latest_balance(account_a)

            if balance_a < 1000:
                continue
            
            amount = random.randint(1000, int(balance_a / 2)) # Make amount a bit more reasonable

            balance_b = get_latest_balance(account_b)

            transaction_time = datetime.now() - timedelta(days=random.randint(1, 365), hours=len(generated_transactions) // 2, minutes=random.randint(0, 59))

            # Create and store withdrawal
            new_balance_a = balance_a - amount
            withdrawal = TransactionAccount(
                my_acc=account_a, cpart_acc=account_b, txn_side='출금',
                txn_amount=amount, txn_balance=new_balance_a, txn_date=transaction_time,
                txn_cont=f'{account_b.acc_user_name.user_name}에게 송금'
            )
            generated_transactions.append(withdrawal)
            temp_balances[account_a.pk] = new_balance_a # Update temp balance

            # Create and store deposit
            new_balance_b = balance_b + amount
            deposit = TransactionAccount(
                my_acc=account_b, cpart_acc=account_a, txn_side='입금',
                txn_amount=amount, txn_balance=new_balance_b, txn_date=transaction_time,
                txn_cont=f'{account_a.acc_user_name.user_name}로부터 입금'
            )
            generated_transactions.append(deposit)
            temp_balances[account_b.pk] = new_balance_b # Update temp balance

        # --- Preview Data ---
        self.stdout.write(self.style.SUCCESS('--- Generated Transaction Data (Preview) ---'))
        # Sort by date for a more readable preview
        generated_transactions.sort(key=lambda t: t.txn_date, reverse=True)
        for t in generated_transactions:
            preview_str = f"My Account: {t.my_acc}, Partner: {t.cpart_acc}, Type: {t.txn_side}, Amount: {t.txn_amount}, New Balance: {t.txn_balance}, Date: {t.txn_date.strftime('%Y-%m-%d %H:%M')}"
            self.stdout.write(preview_str)
        self.stdout.write(self.style.SUCCESS(f'--- Generated {len(generated_transactions)} transactions ---'))

        if options['execute']:
            try:
                with transaction.atomic():
                    # Sort by date before saving to ensure correct balance calculation order if we were to save
                    generated_transactions.sort(key=lambda t: t.txn_date)
                    for t in generated_transactions:
                        # Re-fetch latest balance before saving to be absolutely sure
                        last_txn = TransactionAccount.objects.filter(my_acc=t.my_acc).order_by('-txn_date').first()
                        last_balance = last_txn.txn_balance if last_txn else 1000000
                        if t.txn_side == '출금':
                            t.txn_balance = last_balance - t.txn_amount
                        else: # 입금
                            t.txn_balance = last_balance + t.txn_amount
                        t.save()
                self.stdout.write(self.style.SUCCESS('Successfully saved all generated transactions to the database.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
                self.stdout.write(self.style.ERROR('Transaction rolled back. No data was saved.'))
        else:
            self.stdout.write(self.style.WARNING('\nThis was a preview. No data has been saved to the database yet.'))
            self.stdout.write(self.style.WARNING("To save this data, run the command again with the '--execute' flag."))
            self.stdout.write(self.style.WARNING("Example: python manage.py create_dummy_transactions --execute"))
