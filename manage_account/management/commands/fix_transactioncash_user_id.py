from django.core.management.base import BaseCommand
from manage_account.models import TransactionCash

class Command(BaseCommand):
    help = 'Changes cash_user_id from 6 to 1 for all TransactionCash records.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to fix TransactionCash user IDs...'))

        # Filter records where cash_user_id is 6
        records_to_update = TransactionCash.objects.filter(cash_user_id=6)
        count = records_to_update.count()

        if count > 0:
            # Update cash_user_id to 1
            records_to_update.update(cash_user_id=1)
            self.stdout.write(self.style.SUCCESS(f'Successfully changed {count} TransactionCash records from user_id 6 to 1.'))
        else:
            self.stdout.write(self.style.WARNING('No TransactionCash records found with user_id 6.'))

        self.stdout.write(self.style.SUCCESS('Finished fixing TransactionCash user IDs.'))
