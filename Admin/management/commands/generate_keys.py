# admin/management/commands/generate_keys.py
import secrets
from django.core.management.base import BaseCommand
from Admin.models import AdminKey, StaffKey

class Command(BaseCommand):
    help = "Generate random admin or staff keys"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type", choices=["admin", "staff"], required=True, help="Type of key to generate"
        )
        parser.add_argument(
            "--count", type=int, default=1, help="Number of keys to generate"
        )

    def handle(self, *args, **options):
        key_type = options["type"]
        count = options["count"]

        self.stdout.write(self.style.SUCCESS(f"Generating {count} {key_type} key(s)..."))

        for _ in range(count):
            new_key = secrets.token_hex(8)  # 16-character hex key
            if key_type == "admin":
                AdminKey.objects.create(key=new_key)
            else:
                StaffKey.objects.create(key=new_key)

            self.stdout.write(self.style.SUCCESS(f"Generated key: {new_key}"))

        self.stdout.write(self.style.SUCCESS("Done!"))
