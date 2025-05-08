from django.db import models

# Create your models here.
class User(models.Model):
    name=models.CharField(max_length=122)
    email=models.CharField(max_length=122)
    password=models.CharField(max_length=122)
    confirm_password=models.CharField(max_length=122)
