from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

from notifications.signals import notify
from .models import Transaction

@receiver(post_save, sender=Transaction)
def my_handler(sender, instance, created, **kwargs):
    recipient = instance.partnership.partner1
    print(sender)
    company_employee = User.objects.filter(Q(employee__company=recipient) | Q(employee__company=instance.partnership.partner2))
    
    notify.send(instance, recipient=company_employee, verb='wurde angelegt',)

