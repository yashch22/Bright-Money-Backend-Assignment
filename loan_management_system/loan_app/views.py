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
    """
    API View for registering users.

    This view allows the registration of new users by processing a POST request.
    User data including user ID, name, email, and annual income should be provided
    in the request body. Upon successful registration, a new user record is created
    in the database, and an asynchronous task is triggered to calculate the user's
    credit score.

    Methods:
    - POST: Register a new user.

    Usage:
    To register a new user, make a POST request with user data including user ID,
    name, email, and annual income. The email address provided will be validated
    for correctness.

    Example POST data:
    {
        "user_id": "12345",
        "name": "John Doe",
        "email": "john@example.com",
        "annual_income": 60000
    }

    Example successful response:
    HTTP 200 OK
    {
        "unique_user_id": "12345"
    }

    Example error response:
    HTTP 400 Bad Request
    {
        "error": "Details about the encountered error."
    }
    """

    def post(self, request):
        """
        Register a new user.

        Args:
        - request: The incoming HTTP request containing user data.

        Returns:
        - Response: A success message or an error message if registration fails.
          HTTP 200 OK on success, HTTP 400 Bad Request on failure.
        """
        data = request.data
        email_validator = EmailValidator(message='Enter a valid email address')
        
        try:
            email_validator(data['email'])
            user = User.objects.create(
                user_id=data['user_id'],
                name=data['name'],
                email=data['email'],
                annual_income=data['annual_income']
            )
            calculate_credit_score.delay(user.id)  # Trigger async task to calculate credit score
            return Response({"unique_user_id": str(data['user_id'])}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class ApplyLoanView(APIView):
    """
    API View for applying for a loan.

    This view allows users to apply for a loan by submitting necessary loan details
    in a POST request. The eligibility of the user for the loan is checked based on
    their credit score and annual income. If eligible, the loan application is processed
    and relevant loan payments are scheduled.

    Methods:
    - POST: Apply for a loan.

    Usage:
    To apply for a loan, make a POST request with loan details including user ID,
    loan type, loan amount, disbursement date, tenure in months, and interest rate.

    Example POST data:
    {
        "user_id": "12345",
        "loan_type": "Home",
        "loan_amount": 5000000,
        "disbursement_date": "2023-09-01",
        "tenure_months": 120,
        "interest_rate": 8.5
    }

    Example successful response:
    HTTP 200 OK
    {
        "loan_application_id": "a1b2c3d4e5f6",
        "due_dates_amt": {
            "emi_dates": ["2023-09-01", "2023-10-01", ...],
            "emi_amounts": [50000, 50000, ...]
        }
    }

    Example error response:
    HTTP 400 Bad Request
    {
        "error": "Details about the encountered error."
    }
    """

    def post(self, request):
        """
        Apply for a loan.

        Args:
        - request: The incoming HTTP request containing loan application data.

        Returns:
        - Response: A success message or an error message if loan application fails.
          HTTP 200 OK on success, HTTP 400 Bad Request on failure.
        """
        data = request.data
        try:
            user = User.objects.get(user_id=data['user_id'])
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
        

   








    

    
class MakePaymentView(APIView):
    """
    API View for making payments towards a loan.

    This view allows users to make payments towards an existing loan by submitting
    the loan ID and payment amount in a POST request. The payment is applied to the
    outstanding dues in the following manner:
    - Current dues are prioritized first.
    - Any remaining payment is applied to past dues, starting from the earliest.
    - Any remaining payment is distributed evenly among future dues.

    Methods:
    - POST: Make a payment towards a loan.

    Usage:
    To make a payment towards a loan, make a POST request with the loan ID and
    the payment amount.

    Example POST data:
    {
        "loan_id": "a1b2c3d4e5f6",
        "amount": 50000
    }

    Example successful response:
    HTTP 200 OK

    Example error response:
    HTTP 400 Bad Request
    {
        "Error": "Details about the encountered error."
    }
    """

    def post(self, request):
        """
        Make a payment towards a loan.

        Args:
            request (Request): The incoming HTTP request containing loan payment data.

        Returns:
            Response: A success message or an error message if payment processing fails.
            HTTP 200 OK on success, HTTP 400 Bad Request on failure.
        """
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

 
  
class GetStatementView(APIView):
    """
    API View for getting the loan statement.

    This view allows users to retrieve the loan statement for a specific loan by providing the loan ID.
    The loan statement includes details such as the current date, principal amount, interest amount,
    and upcoming payment transactions.

    Methods:
    - GET: Get the loan statement.

    Usage:
    To get the loan statement, make a GET request with the loan ID as a query parameter.

    Example request:
    GET /api/get-statement/?loan_id=a1b2c3d4e5f6

    Example successful response:
    HTTP 200 OK
    {
        "current_date": "2023-08-30",
        "Principal": 5000.0,
        "Interest": 833.33,
        "upcoming_transactions": [
            {
                "due_date": "2023-09-01",
                "due_amount": 5833.33
            },
            {
                "due_date": "2023-10-01",
                "due_amount": 5833.33
            },
            ...
        ]
    }

    Example error response:
    HTTP 400 Bad Request
    {
        "error": "Details about the encountered error."
    }
    """

    def get(self, request):
        """
        Get the loan statement.

        Args:
            request (Request): The incoming HTTP request containing the loan ID as a query parameter.

        Returns:
            Response: The loan statement or an error message if the statement cannot be generated.
            HTTP 200 OK on success, HTTP 400 Bad Request on failure.
        """

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
