from django.db import models

class AdminKey(models.Model):
    key = models.CharField(max_length=50, unique=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key

class StaffKey(models.Model):
    key = models.CharField(max_length=50, unique=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key
