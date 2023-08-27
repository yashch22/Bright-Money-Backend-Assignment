from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from datetime import date
from django.core.validators import RegexValidator, EmailValidator
from math import ceil
import uuid
from django.forms.models import model_to_dict
from django.db.models import Sum
from .tasks import calculate_credit_score





class RegisterUserView(APIView):
    def post(self, request):
        data = request.data
        # user_id_validator = RegexValidator(r'^\d{12}$', 'Enter a valid Aadhar number (12 digits)')
        # try:
        #     user_id_validator(data['user_id'])
        # except ValidationError as e:
        #     return Response({"error": "Invalid user_id format"}, status=status.HTTP_400_BAD_REQUEST)

        # # Validate email using EmailValidator
        email_validator = EmailValidator(message='Enter a valid email address')
        # try:
        #     email_validator(data['email'])
        # except ValidationError as e:
        #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # user_id_validator(data['user_id'])
            email_validator(data['email'])
            user = User.objects.create(user_id = data['user_id'], name=data['name'], email=data['email'], annual_income=data['annual_income'])
            
            calculate_credit_score.delay(user.id)  # Trigger async task to calculate credit score
            return Response({"unique_user_id": str(data['user_id'])}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request): 
        users = User.objects.all()
        user_data = []
        for user in users:
            user_data.append({
                'id': user.id,
                'user_id':user.user_id,
                'name': user.name,
                'email': user.email,
                'annual_income': user.annual_income,
                'credit_score':user.credit_score
                # Add more fields if needed
            })
        return Response(user_data, status=status.HTTP_200_OK)




class ApplyLoanView(APIView):
    def post(self, request):
        data = request.data
        try:
            user = User.objects.get(user_id=data['user_id'])
            print("reached 1")
            if user.credit_score >= 450 and user.annual_income >= 150000:
                loan_amount_bounds = {
                    'Car': 750000,
                    'Home': 8500000,
                    'Education': 5000000,
                    'Personal': 1000000
                }
                loan_type = data['loan_type']
                loan_amount = data['loan_amount']
                disbursement_date = data['disbursement_date']
                tenure_months = data['tenure_months']
                interest_rate = data['interest_rate']
                print("reached 2")
                if loan_type in loan_amount_bounds and loan_amount <= loan_amount_bounds[loan_type]:
                    
                    #Formula used for calculating emi's P x R x (1+R)^N / [(1+R)^N-1] 
                    monthly_interest_rate = (interest_rate/12)/100
                    emi_numerator = ((loan_amount*monthly_interest_rate)*((1+monthly_interest_rate)**tenure_months))
                    emi_denominator = (((1+monthly_interest_rate)**tenure_months)-1)
                    
                    emi_amount = emi_numerator/emi_denominator
                    
                    total_amount_to_pay =  emi_amount*tenure_months
                    interest_earned = total_amount_to_pay  - loan_amount
                    
                    
                    
                    
                       
                    #error here somehow....
                    if (emi_amount>(user.annual_income*6/120)):
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Try with lower loan amount or greater tenure "})
                    elif (interest_earned<10000):
                        # don't create loan application
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Try increasing Interest Rate/Tenure"})
                    
                    
                    
                    loan_unique_id = uuid.uuid4() 
                    

                    # Save loan application
                    
                    # year = 
                    date_parsed = disbursement_date.split('-')
                    
                    disbursement_date =  date(int(date_parsed[0]), int(date_parsed[1]), int(date_parsed[2]))
                    loan_app = LoanApplication.objects.create(
                        loan_id = loan_unique_id,
                        user = user,
                        loan_type=loan_type,
                        loan_amount=loan_amount,
                        emi_amount=emi_amount,
                        interest_rate=interest_rate,  
                        tenure_months=tenure_months,
                        disbursement_date=disbursement_date
                    )
                    
                    # Create LoanPayment records for EMIs

                    emi_date = disbursement_date #0th emi
                    emi_month = int(emi_date.month)
                    emi_year = int(emi_date.year)
                    emi_map = {
                        "emi_dates":[],
                        "emi_amounts":[]
                    }
                    amount_paid_till_emi_date = 0
                    for _ in range(tenure_months):
                        print(emi_year,emi_month)
                        emi_year = emi_year + (1 if emi_month == 12 else 0)
                        emi_month = (emi_month % 12) + 1
                        
                        # Calculate the first day of the next month
                        emi_date = date(year=emi_year, month=emi_month, day=1)
                        emi_amount_month = 0
                        
                        if total_amount_to_pay-amount_paid_till_emi_date<ceil(emi_amount):
                            emi_amount_month = total_amount_to_pay-amount_paid_till_emi_date
                        else:
                            emi_amount_month = ceil(emi_amount)
                            
                        amount_paid_till_emi_date+=emi_amount_month
                        emi_map['emi_dates'].append(emi_date)
                        emi_map['emi_amounts'].append(emi_amount_month)
                        
                        LoanPayment.objects.create(
                            loan_application = loan_app,
                            due_date = emi_date,
                            amount_due=emi_amount_month
                        )
                   
    
                    return Response(status=status.HTTP_200_OK, data={"loan_application_id": loan_app.loan_id,"due_dates_amt":emi_map})
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Invalid loan amount"})
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "User not eligible for loan"})
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "User not found"})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)})
        
    def get(self, request):
        loans = LoanApplication.objects.all()
        loan_data = []
        for loan in loans:
            loan_data.append({
                "loan_id": loan.loan_id,
                "user": model_to_dict(loan.user),
                "loan_type": loan.loan_type,
                "loan_amount": float(loan.loan_amount),
                "interest_rate": float(loan.interest_rate),
                "tenure_months": loan.tenure_months,
                "emi_amount": float(loan.emi_amount),
                "disbursement_date": loan.disbursement_date.strftime('%Y-%m-%d')
            })
        
        return Response(loan_data, status=status.HTTP_200_OK)
    

    

class MakePaymentView(APIView):
    def post(self, request):
        data = request.data
        loan_id = data['loan_id']
        payment_amount = data['amount']
        print('payment_amount',payment_amount)
        
        current_year = date.today().year
        current_month = date.today().month
        current_month_start = date(year=current_year, month=current_month, day=1)
        
        try:
            loan_application = LoanApplication.objects.get(loan_id=loan_id)
            due_payments = LoanPayment.objects.filter(loan_application=loan_application, is_paid=False).order_by('due_date')
            due_payments_past = due_payments.filter(due_date__lte=current_month_start).order_by('-due_date')
            due_payments_now =  due_payments.filter(due_date__gt=current_month_start).order_by('due_date')

            if  len(due_payments_past) == 0:
                return Response({"Error": "No due payments found"}, status=status.HTTP_400_BAD_REQUEST)
            
            remaining_loan_amount = due_payments.aggregate(Sum('amount_due')) 
            remaining_loan_amount = remaining_loan_amount['amount_due__sum']
            print(remaining_loan_amount)
            remaining_amount_after_payment = remaining_loan_amount - payment_amount
            

            if len(due_payments_now) == 0 :
                print("entered here")
                payment_record = due_payments.first()
                payment_record.amount_due = remaining_amount_after_payment
                if remaining_amount_after_payment <= 0 :
                    payment_record.is_paid = True
                payment_amount.save()
             
            # Updating Past records   
            for i, payment_record in enumerate(due_payments_past):     
                print("not there here")          
                payment_record.amount_due = (payment_amount if i == 0 else 0)           
                payment_record.is_paid = True
                payment_record.save()
               
            
            # Updating future records

            updated_emi_amount = ceil(remaining_amount_after_payment/max(len(due_payments_now),1)) 
            for i, payment_record in enumerate(due_payments_now):    
    
                if(remaining_amount_after_payment<updated_emi_amount):
                    payment_record.amount_due = remaining_amount_after_payment
                else:   
                    payment_record.amount_due = updated_emi_amount   
                remaining_amount_after_payment-=updated_emi_amount   
                payment_record.save()        
                
            
             
                 

            return Response(status=status.HTTP_200_OK)
        except LoanApplication.DoesNotExist:
            return Response({"Error": "Loan application not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        # data = request.data
        # loan_id = data['loan_id']
        loan_application = LoanApplication.objects.get(loan_id= "e0e52489-f7c4-41bf-8f3b-8b286b675018",)
        loan_payments = LoanPayment.objects.filter(loan_application = loan_application)
        loan_payments_data = []
        for loan_payment_record in loan_payments:
            loan_payments_data.append({
                "loan_application": model_to_dict(loan_payment_record.loan_application),
                "due_date": loan_payment_record.due_date,
                "amount_due": loan_payment_record.amount_due,
                "is_paid": loan_payment_record.is_paid
            })
        
        return Response(loan_payments_data, status=status.HTTP_200_OK)
  
class GetStatementView(APIView):
    def get(self, request):
        try:
            
            loan_id = request.query_params.get('loan_id')
            loan = LoanApplication.objects.get(loan_id=loan_id)
            loan_payments = LoanPayment.objects.filter(loan_application = loan).order_by('-due_date')
            if loan_payments.first().is_paid==True:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Loan is closed"})
            
            
            
            #assuming recalculation is done
            due_payments = LoanPayment.objects.filter(loan_application=loan, is_paid=False).order_by('due_date')    
            tenure = loan.tenure_months
            remaining_tenure = len(due_payments)
            interest_rate = (loan.interest_rate/(12*100))
            emi_amount = due_payments.first().amount_due
            loan_amount = loan.loan_amount
            
            
            #Formula used for calculating principal => EMI/() R x (1+R)^N / [(1+R)^N-1] )
            principal_amount_left = emi_amount / ((interest_rate * (1 + interest_rate)**remaining_tenure) / ((1 + interest_rate)**remaining_tenure - 1))
            principal_amount_monthly = principal_amount_left/remaining_tenure
            interest_amount = emi_amount - principal_amount_monthly
            current_date = date.today()

            upcoming_transactions = []
            for payment_record in due_payments:
                upcoming_transactions.append({
                    
                    "due_date":payment_record.due_date,
                   "due_amount": payment_record.amount_due
                    })
                # due_dates.append(payment_record.due_date)
             
            statement = {
                "current_date":current_date,
                "Principal":principal_amount_monthly,
                "Interest":interest_amount,
                "upcoming_transactions":upcoming_transactions
                
            }   
                
            
            
            
            
            
            
            
            return Response(status=status.HTTP_200_OK, data=statement)
        except LoanApplication.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "Loan not found"})
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": str(e)})
