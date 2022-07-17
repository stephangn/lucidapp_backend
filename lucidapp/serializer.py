from .models import Company, CustomDeclaration, CustomsOffice, Document, Employee, Invoice, InvoiceItem, Partnership, Product, Transaction, File
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.utils import html, model_meta, representation

from notifications.models import Notification

from notifications.signals import notify

from lucidapp.models import Employee



class CompanySerializer(serializers.ModelSerializer):    
#    exporteur = TransactionSerializer(read_only=True, many=True)
#    importeur = TransactionSerializer(read_only=True, many=True)
    class Meta:
        model = Company
        fields = '__all__'


class CustomDeclationSerializer(serializers.ModelSerializer):


    class Meta:
        model = CustomDeclaration
        fields = '__all__'
    def create(self, validated_data):
        
        #raise_errors_on_nested_writes('create', self, validated_data)

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        transaction = Transaction.objects.get(pk=validated_data['transaction'].id)
        transaction.status = 3
        transaction.save()

        instance = ModelClass._default_manager.create(**validated_data)


        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance
 





class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['product','unit','amount','price',]


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'



class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


class PartnershipSerializer(serializers.ModelSerializer):
    #use method get_partner to customize endpoint to deliever only counterwise partner
    partner = serializers.SerializerMethodField()

    class Meta:
        model = Partnership
        fields = ['confirmed','date_added','partner','id','is_archived','partner1', 'timestamp_added', 'timestamp_processed']
        extra_kwargs = {'partner1': {'required': False}}


    #show only other partner in partnership
    def get_partner(self,obj):
        #get user out out request data
        user =  self.context['request'].user
        if user.is_superuser:
            return CompanySerializer(obj.partner1).data
        elif user.employee.custom_office is not None:
            return CompanySerializer(obj.partner1).data
        else:
            user_company = user.employee.company
            #check wether partner 1 or Partner 2
            if user_company == obj.partner1:
                return CompanySerializer(obj.partner2).data
            else:
                return CompanySerializer(obj.partner1).data


    def create(self, validated_data):
        # collect added partner eori 
        company1 = self.context['request'].data['added_partner']
        print(company1)
        partner2 = Company.objects.get(pk=company1)
        # collect requestors company
        partner1 = self.context['request'].user.employee.company
        # add partnership
        partnership = Partnership.objects.create(partner2=partner2,partner1=partner1,**validated_data)
        return partnership


class SimpleCustomOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomsOffice
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    #user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    custom_office = SimpleCustomOfficeSerializer(read_only=True)
    class Meta: 
        model = Employee
        fields = ['company','custom_office']
#deliever username with token 

class UserListSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username','employee']

class UserSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    
    # Rollen für Berechtigungssystem im Front-End
    role = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username','employee', 'role']

    #Methode um Informationen zur Rolle bereitzustellen
    def get_role(self,obj):

        if obj.employee.custom_office is None:
            return "company_employee"
        else:
            return "custom_officer"
    

class CustomOfficeSerializer(serializers.ModelSerializer):
    custom_officers = EmployeeSerializer(read_only=True)
    class Meta:
        model = CustomsOffice
        fields = '__all__'



class DocumentSerializer(serializers.ModelSerializer):
    
    owner = UserSerializer(read_only=True)
    representation = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        extra_kwargs = {'owner': {'required': False}}


    # Custom Method zur String Darstellung

    def get_representation(self, obj):
        return f"{obj.type} - {obj.description} - {obj.issue_date}"

    
    def create(self, validated_data):
        owner = self.context['request'].user
        document = Document.objects.create(owner=owner,**validated_data)

        return document




class InvoiceSerializer(serializers.ModelSerializer):
    invoiceItem = InvoiceItemSerializer(read_only=False,many=True)
    total_value = serializers.IntegerField(required=False)
    class Meta:
        model = Invoice
        #disable owner and total value field - 
        extra_kwargs = {
            'owner': {'required': False},
            }
        fields = '__all__'

    def create(self, validated_data):
        owner = self.context['request'].user
        #save invoice item data 
        invoiceItem_data = validated_data.pop('invoiceItem')
        invoice = Invoice.objects.create(owner=owner,**validated_data)
        #iterate through invoice data
        for invoiceItem_data in invoiceItem_data:
           InvoiceItem.objects.create(invoice=invoice, **invoiceItem_data)
        return invoice
    

    def update(self, instance, validated_data):
        instance.confirmed = validated_data.get('confirmed', instance.confirmed)
        instance.transaction = validated_data.get('transaction', instance.transaction)
        if instance.confirmed:
            transaction = Transaction.objects.get(pk=instance.transaction.id)
            transaction.status = 2
            transaction.save()
        instance.save()
        return instance


class TransactionSerializer(serializers.ModelSerializer):
    #deliever company details within transaction
    partnership = PartnershipSerializer(read_only=True)
    #invoices = InvoiceSerializer(source='document_set', many=True)    # Anzeigen des String des Statusses und nicht des Integers
    status = serializers.CharField(source='get_status_display', required=False)
    class Meta:
        model = Transaction
        fields = ['partnership', 'importeur','description', 'id', 'date_added', 'date_processed','status', 'timestamp_added','timestamp_processed',] 

    def create(self, validated_data):
        validated_data['partnership_id'] = self.context['request'].data['partnership']
        user = self.context['request'].user
        #company_employee = User.objects.filter(employee__company=validated_data['importeur'])
        #notify.send(sender=user, actor=user, recipient=company_employee, verb='Transaktion angelegt.')
        return super(TransactionSerializer, self).create(validated_data)


    def validate_importeur(self, value):
        partnership_id = self.context['request'].data['partnership']
        partnership = Partnership.objects.get(pk=partnership_id)
        if partnership.partner1 != value and partnership.partner2 != value:
            raise serializers.ValidationError("Importeur muss einer der Partner sein")

        return value

"""     def create(self, validated_data):
        # collect added partner eori 
        validated_data['partnership_id'] = self.context['request'].data['partnership']
        user = self.context['request'].user
        # collect requestors company
        # add partnership
        newTransaction = Transaction.objects.create(**validated_data)
        partner_company_employee = User.objects.filter(employee__company=validated_data['importeur'])
        verb = "Transaktion mit der" + str(newTransaction.id) + " angelegt"
        #notify.send(sender=user, actor=user, recipient=user, verb=verb)
        newTransaction.save()
        return Transaction """



class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self,attrs):
        # The default result (access/refresh tokens)
        data = super().validate(attrs)
        # Custom data you want to include
        data.update({'user': self.user.username})
        #data.update({'company': self.user.employee.company.name})
        # and everything else you want to send in the response
        return data

class UserTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self,attrs):
        user = self.context['request'].user
        print(user)
        # The default result (access/refresh tokens)
        data = super().validate(attrs)
        # Custom data you want to include
        data.update({'user': self.user.username})
        #data.update({'company': self.user.employee.company.name})
        # and everything else you want to send in the response
        return data


# Custom Methods für Zollview 

class DocumentViewSerializer(serializers.ModelSerializer):
    
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        extra_kwargs = {'owner': {'required': False}}

class SimplePartnershipSerializer(serializers.ModelSerializer):
    #use method get_partner to customize endpoint to deliever only counterwise partner
    partner1 = CompanySerializer(read_only=True)
    partner2 = CompanySerializer(read_only=True)

    class Meta:
        model = Partnership
        fields = ['partner1','partner2']


class TransactionViewSerializer(serializers.ModelSerializer):
    #deliever company details within transaction
    partnership = SimplePartnershipSerializer(read_only=True)
    # Anzeigen des String des Statusses und nicht des Integers
    status = serializers.CharField(source='get_status_display', required=False)
    class Meta:
        model = Transaction
        fields = ['partnership', 'importeur','description', 'id', 'date_added', 'date_processed','status'] 





class ComplexCustomDeclationSerializer(serializers.ModelSerializer):
    invoice = InvoiceSerializer(read_only=True)
    document = DocumentViewSerializer(read_only=True, many=True)
    transaction = TransactionViewSerializer(read_only=True)
    customs_office = CustomOfficeSerializer(read_only=True)
    importeur = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source='get_status_display', required=False)

    exporteur = serializers.SerializerMethodField(read_only=True)

    def get_exporteur(self,obj):
        #get user out out request data
        importeur = obj.transaction.importeur
        partner1 = obj.transaction.partnership.partner1 
        if importeur==partner1:
            return CompanySerializer(obj.transaction.partnership.partner2).data
        else:
            return CompanySerializer(obj.transaction.partnership.partner1).data
    
    def get_importeur(self,obj):
        #get user out out request data
        importeur = obj.transaction.importeur
        partner1 = obj.transaction.partnership.partner1 
        if importeur==partner1:
            return CompanySerializer(obj.transaction.partnership.partner1).data
        else:
            return CompanySerializer(obj.transaction.partnership.partner2).data


    class Meta:
        model = CustomDeclaration
        fields = '__all__'


# Serializer for Notification

class GenericNotificationRelatedField(serializers.RelatedField):                                                          

    def to_representation(self, value):                                                                                   
                                                                  
        if isinstance(value, User):                                                                                       
            serializer = UserSerializer(value)                                                                        
        return serializer.data                                                                                            


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer()
    actor = UserSerializer()
    verb = serializers.CharField()
    level = serializers.CharField()
    description = serializers.CharField()
    timestamp = serializers.DateTimeField(read_only=True)
    unread = serializers.BooleanField()
    public = serializers.BooleanField()
    deleted = serializers.BooleanField()
    emailed = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'target', 'verb', 'level', 'description', 'unread', 'public', 'deleted',
                  'emailed', 'timestamp']



class ModelNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'