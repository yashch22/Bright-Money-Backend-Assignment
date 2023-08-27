from django.db import models
from django.core.validators import RegexValidator, EmailValidator



class User(models.Model):
    name = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100,unique=True)
    email = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2)
    credit_score = models.PositiveIntegerField(default=0)  # Store calculated credit score here



class LoanApplication(models.Model):
    loan_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=20, choices=[
        ('Car', 'Car Loan'),
        ('Home', 'Home Loan'),
        ('Education', 'Educational Loan'),
        ('Personal', 'Personal Loan')
    ])
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14)
    tenure_months = models.PositiveIntegerField()
    emi_amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursement_date = models.DateField()



class LoanPayment(models.Model):
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)


