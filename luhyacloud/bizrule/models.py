from django.db import models

# Create your models here.
class bizRule(models.Model):
    rule_name             = models.CharField(max_length=100)
    rule_array            = models.TextField()