from rest_framework import serializers
from .models import User, LoanApplication, LoanPayment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanPayment
        fields = '__all__'
