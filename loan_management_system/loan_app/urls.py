from django.urls import path
from .views import *

urlpatterns = [
    path('register-user/', RegisterUserView.as_view(), name='register-user'),
    path('apply-loan/', ApplyLoanView.as_view(), name='apply-loan'),
    path('make-payment/', MakePaymentView.as_view(), name='make-payment'),
    path('get-statement/', GetStatementView.as_view(), name='get-statement'),
]
