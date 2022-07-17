from datetime import datetime, timezone
from http.client import ACCEPTED
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.forms import CharField
from django.db.models import F, Sum

# Create your models here.

class AnnotatedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(total_value=Sum(F('invoiceItem__price')*F('invoiceItem__amount')))
        
class Company(models.Model):
    eori_nr = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=30)
    street = models.CharField(max_length = 60)
    city_code = models.IntegerField()
    city = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    publickey = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name}"


class CustomsOffice(models.Model):
    name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=50)
    street = models.CharField(max_length = 60)
    city_code = models.IntegerField()
    city = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=17, blank=True)
    publickey = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name}" 

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='employee',blank=True, null=True)
    custom_office = models.ForeignKey(CustomsOffice, on_delete=models.PROTECT, related_name='customs_officers',blank=True, null=True)


    def __str__(self):
        return f"{self.user}" 


    
class Partnership(models.Model):
    
    partner1 = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='partner1')
    partner2 = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='partner2')
    confirmed = models.BooleanField(default=False)
    date_added = models.DateField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    timestamp_added = models.DateTimeField(auto_now_add=True)
    timestamp_processed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.partner1} mit {self.partner2}" 

class Transaction(models.Model):

    CREATED = 1
    COMPLETE = 2
    DECLARATION_PENDING = 3
    APPROVED = 4

    STATUS = [
        (CREATED, "Transaktion wurde angelegt - Bestätigung ausstehend"),
        (COMPLETE, "Alle Dokumente liegen vor"),
        (DECLARATION_PENDING, "Zollantrag gestellt - Wartet auf Bearbeitung"),
        (APPROVED, "Zollfreigabe durch Zollamt erteilt"),

    ]

    partnership = models.ForeignKey(Partnership, on_delete=models.PROTECT, related_name='partnership')
    importeur = models.ForeignKey(Company, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    date_added = models.DateField(auto_now_add=True)
    date_processed = models.DateField(auto_now=True)
    timestamp_added = models.DateTimeField(auto_now_add=True)
    timestamp_processed = models.DateTimeField(auto_now=True)
    status = models.PositiveSmallIntegerField(
        choices=STATUS,
        default=CREATED,
        blank=True
    )

    
    #string representation im Backend 
    def __str__(self):
        return f"{self.partnership.partner1} an {self.partnership.partner2} vom {self.date_added}"





class File(models.Model):
    file = models.FileField(upload_to='docs', blank=True) 
    
    def __str__(self):
        return f"{self.file}" 

class Document(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='document_set') 
    type = models.CharField(max_length=500, blank=False)
    description = models.CharField(max_length=345, blank=True)
    blockchain_id = models.CharField(max_length=30, blank=True)
    file = models.OneToOneField(File, on_delete=models.CASCADE, blank=True, null=True)
    owner = models.ForeignKey(User, blank=False, on_delete=models.CASCADE)
    upload_date = models.DateField(auto_now_add=True)
    timestamp_added = models.DateTimeField(auto_now_add=True)

    issue_date = models.DateField(blank=True)
    confirmed = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.type} - {self.description} - {self.issue_date}"

class Invoice(Document):

    invoice_text = models.CharField(max_length=500, blank=True)
    currency = models.CharField(max_length=3, default="EUR")
    transport_costs = models.FloatField(blank=False, default=0)
    objects = AnnotatedManager()
    
    def __str__(self):
        return f"Rechnung: {self.description}"


class Product(models.Model):
    product_name = models.CharField(max_length=300)
    #ID des Products 
    tariccode = models.CharField(primary_key=True, max_length=13)
    tax_rate = models.IntegerField()
   
    def __str__(self):
        return f"{self.product_name}"    

    
class InvoiceItem(models.Model):
    #Verlinkung zu einem Product 
    #product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product = models.CharField(max_length=90)
    unit = models.CharField(max_length=90)
    amount = models.IntegerField()
    #Zuordnung des Rechnungsposten zu einer Rechnung
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='invoiceItem')
    #Gesamtpreis 
    price = models.IntegerField()

    def __str__(self):
        return f"Posten: {self.amount} {self.unit} {self.product} "


    

class CustomDeclaration(models.Model):
    
    #Allgemeine technische Parameter 

    date_added = models.DateField(auto_now=True)
    document = models.ManyToManyField(Document, related_name='document', blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="invoice", blank=False, null=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name='transaction', blank=True, null=True)
    blockchain_zid = models.CharField(max_length=400, default="")
    #transportcost_currency = models.CharField(max_length=3, default='EUR')
    customs_office = models.ForeignKey(CustomsOffice, on_delete=models.PROTECT, blank=False, null =True)
    custom_officer = models.ForeignKey(Employee, on_delete=models.PROTECT, blank=True, null=True, related_name='processing_custom_officer')


    #Inhaltliche Felder

    anmeldeArt = models.CharField(blank=False, max_length=400)
    geschaeftArt = models.CharField(max_length=300, blank=False)
    zahlungsart = models.CharField(blank=True, max_length=400)



    #lieferdaten 
    ausfuhrland = models.CharField(blank=False, max_length=100)
    bestimmungsland = models.CharField(blank=False, max_length=100)
    befoerderungsmittel = models.CharField(blank=False, max_length=100)
    lieferbedingung = models.CharField(blank=False, max_length=100)
    lieferort = models.CharField(blank=False, max_length=100)
    warenort = models.CharField(blank=True, max_length=100)

    timestamp_added = models.DateTimeField(auto_now_add=True)


    status_verificiation = models.CharField(default="ausstehend", max_length=30)
    status_confirmation = models.CharField(default="ausstehend", max_length=30)



    #confirmed = models.BooleanField(default=False)
    #rejected = models.BooleanField(default=False)
    #verified = models.BooleanField(default=False) 


    #Festlegung des Bearbeitungsstatusses 

    PENDING = 'PE'
    VERIFIED = 'VF'
    ACCEPTED = 'AC'
    INQUIRY = 'IQ'
    REJECTED = 'RJ'
    STATUS_CHOICES = [
        (VERIFIED, 'Verifiziert'),
        (PENDING, 'in Bearbeitung'),
        (ACCEPTED, 'akzeptiert'),
        (INQUIRY, 'aktive Untersuchung'),
        (REJECTED, 'Einfuhr abgelehnt'),
    ]    
    
    status = models.CharField(
        max_length = 2,
        choices = STATUS_CHOICES,
        default=PENDING,
        blank = True
        )


    def __str__(self):
        return f"Zollanmeldung vom {self.date_added}"

#Hallo Team