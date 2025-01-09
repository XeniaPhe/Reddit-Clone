from django.db import models

def add_to_query_dict(query_dict: dict, model_field_name: str, field_value):
    if isinstance(field_value, models.Model):
        query_dict[model_field_name] = field_value
    else:
        query_dict[f'{model_field_name}_id']=field_value