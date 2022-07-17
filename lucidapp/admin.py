from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from lucidapp.models import Company, CustomDeclaration, CustomsOffice, Document, Employee, File, Invoice, InvoiceItem, Partnership, Product, Transaction

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'employee'

""" class CustomOfficerInline(admin.StackedInline):
    model = CustomOfficer
    can_delete = False
    verbose_name_plural = 'customofficer' """

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline, )

# Register your models here.
admin.site.register(Invoice)
admin.site.register(Transaction)
admin.site.register(Company)
admin.site.register(InvoiceItem)
admin.site.register(Product)
admin.site.register(Partnership)
admin.site.register(CustomsOffice)
admin.site.register(CustomDeclaration)
admin.site.register(Document)
admin.site.register(File)


# Re-register UserAdmin

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# hier werden die Modelle registriert und hinterlegt
# Infos: https://realpython.com/customize-django-admin-python/#modifying-a-change-list-using-list_display

