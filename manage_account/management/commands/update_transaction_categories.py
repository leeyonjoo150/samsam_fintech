import random
from django.core.management.base import BaseCommand
from manage_account.models import TransactionAccount, AccountBookCategory
from django.db import transaction

class Command(BaseCommand):
    help = "Randomly assigns categories to existing transaction records based on the transaction side."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Starting to update transaction categories ---'))

        # 1. Fetch categories based on PK ranges
        try:
            withdrawal_cats = list(AccountBookCategory.objects.filter(pk__in=range(1, 13)))
            deposit_cats = list(AccountBookCategory.objects.filter(pk__in=range(13, 19)))

            if not withdrawal_cats or not deposit_cats:
                self.stdout.write(self.style.ERROR('Could not find all required categories. Make sure categories with PKs 1-18 exist.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching categories: {e}'))
            return

        self.stdout.write(f'Found {len(withdrawal_cats)} withdrawal categories and {len(deposit_cats)} deposit categories.')

        # 2. Fetch all transactions
        transactions = TransactionAccount.objects.all()
        transactions_to_update = []
        updated_count = 0

        self.stdout.write(f'Processing {transactions.count()} transactions...')

        # 3. Assign categories randomly based on txn_side
        for txn in transactions:
            original_cat = txn.txn_cat
            if txn.txn_side == '출금':
                if withdrawal_cats:
                    txn.txn_cat = random.choice(withdrawal_cats)
            elif txn.txn_side == '입금':
                if deposit_cats:
                    txn.txn_cat = random.choice(deposit_cats)
            
            # Only add to update list if the category has changed
            if original_cat != txn.txn_cat:
                transactions_to_update.append(txn)
                updated_count += 1

        # 4. Bulk update the changes for efficiency
        if transactions_to_update:
            self.stdout.write(f'Updating {len(transactions_to_update)} transactions in the database...')
            TransactionAccount.objects.bulk_update(transactions_to_update, ['txn_cat'])
            self.stdout.write(self.style.SUCCESS(f'--- Successfully updated categories for {len(transactions_to_update)} transactions. ---'))
        else:
            self.stdout.write(self.style.WARNING('--- No transactions needed an update. ---'))

