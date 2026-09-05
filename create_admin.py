import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myslot.settings")
django.setup()

from accounts.models import User

username = os.environ.get("ADMIN_USERNAME")
email = os.environ.get("ADMIN_EMAIL")
password = os.environ.get("ADMIN_PASSWORD")

if username and email and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email}
    )

    user.email = email
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()

    print("Admin user created/updated successfully.")
else:
    print("Admin environment variables are missing.")