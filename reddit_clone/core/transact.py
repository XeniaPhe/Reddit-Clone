from django.db import transaction
from custom_errors import graphql_error

def transact(transaction_callback, error_msg=None, *args, **kwargs):
    try:
        with transaction.atomic():
            return transaction_callback(*args, **kwargs)
    except Exception as e:
        error = 'Transaction Failed:'
        if error_msg is not None:
            error += f'\n{error_msg}'
            
        error += f'\n{e}'
        graphql_error(error)