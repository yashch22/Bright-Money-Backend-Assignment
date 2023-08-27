from celery import shared_task
from .models import User
import pandas as pd

@shared_task
def calculate_credit_score(user_id):
    user = User.objects.get(pk=user_id)
    transaction_df = pd.read_csv('loan_app/transactions_data Backend.csv')
    user_transaction_df = transaction_df[transaction_df['user'] == user.user_id]
    total_balance = user_transaction_df[user_transaction_df['transaction_type']=='CREDIT']['amount'].sum() -  user_transaction_df[user_transaction_df['transaction_type']=='DEBIT']['amount'].sum()
    
    if total_balance >= 1000000:
        user.credit_score = 900
    elif total_balance <= 100000:
        user.credit_score = 300
    else:
        credit_change = ((total_balance - 100000) // 15000 )*10
        user.credit_score = min( 400 + credit_change, 900)
        
    user.save()
