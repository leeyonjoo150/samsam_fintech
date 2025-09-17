import random
from django.core.management.base import BaseCommand
from manage_account.models import TransactionCash
from acc_auth.models import User

class Command(BaseCommand):
    help = 'Updates cash_user for all TransactionCash records to a random valid user ID.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to update TransactionCash user IDs...'))

        # Get all valid user IDs (assuming IDs 1 to 5 are the only valid ones)
        # Or, more robustly, get actual IDs from the User model
        valid_user_ids = list(User.objects.values_list('id', flat=True))

        if not valid_user_ids:
            self.stdout.write(self.style.ERROR('No users found in the database. Please create some users first.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found valid user IDs: {valid_user_ids}'))

        # Fetch all TransactionCash objects
        all_cash_transactions = TransactionCash.objects.all()
        updated_transactions = []

        for transaction in all_cash_transactions:
            # Assign a random valid user ID
            random_user_id = random.choice(valid_user_ids)
            
            # Check if the current user is already a valid one to avoid unnecessary updates
            if transaction.cash_user_id not in valid_user_ids:
                transaction.cash_user_id = random_user_id
                updated_transactions.append(transaction)
            elif transaction.cash_user_id == 6: # Specifically target user_id 6 if it exists
                transaction.cash_user_id = random_user_id
                updated_transactions.append(transaction)

        if updated_transactions:
            # Use bulk_update for efficiency
            TransactionCash.objects.bulk_update(updated_transactions, ['cash_user'])
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {len(updated_transactions)} TransactionCash records.'))
        else:
            self.stdout.write(self.style.WARNING('No TransactionCash records needed updating.'))

        self.stdout.write(self.style.SUCCESS('Finished updating TransactionCash user IDs.'))
