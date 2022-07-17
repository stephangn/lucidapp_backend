"""customchain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static

from django import urls
from django.contrib import admin
from django.urls import path, re_path
from django.urls import include, path
from lucidapp import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

import notifications.urls


router = routers.DefaultRouter()
router.register(r'transactions', views.CompanyTransactionList, basename='transactionslist')
router.register(r'invoice', views.InvoiceViewSet)
#router.register(r'Transaction', views.TransactionViewSet)
router.register(r'companies', views.CompanyViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'invoiceItems', views.InvoiceItemViewSet)
router.register(r'partnership', views.PartnershipViewSet, basename="partners")
router.register(r'declaration', views.CustomDeclarationViewSet, basename="declarations")
router.register(r'documents', views.DocumentViewSet, basename="documents")
router.register(r'file', views.UploadedFileViewSet, basename="file")
router.register(r'employee', views.EmployeeViewSet, basename="employee")
router.register(r'user', views.UserViewSet, basename="user")
router.register(r'customoffices', views.CustomOficesView, basename="customoffices")
router.register(r'alerts', views.NotificationsViewSet, basename="notifications")

router.register(r'declaration_auth', views.ComplexCustomDeclarationViewSet, basename="declarations2")





#show all Partnerships 

#initialize instance for nested router 
# 'basename' is optional. Needed only if the same viewset is registered more than once
# Official DRF docs on this option: http://www.django-rest-framework.org/api-guide/routers/

urlpatterns = [
    path(r'', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), 
    path('users/', views.UserList.as_view()),
    path('user/', views.UserDetail.as_view()),    
    #show transactions for company
    #path('transactions', views.CompanyTransactionList.as_view()),
    #route for JWT Authenfication
    path('api/token/', views.UserTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh2/', views.UserTokenRefreshView.as_view(), name='token_refresh'),

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    #path(r'alerts', views.NotificationSerializer.as_view(), name='all'),
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
