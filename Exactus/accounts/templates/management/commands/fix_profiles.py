from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Exactus.accounts.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix all missing UserProfile records'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        error_count = 0
        
        for user in users:
            try:
                profile, created = UserProfile.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created profile for {user.username}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Profile already exists for {user.username}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creating profile for {user.username}: {e}')
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Successfully processed {len(users)} users. '
                f'Created {created_count} new profiles. '
                f'Errors: {error_count}'
            )
        )