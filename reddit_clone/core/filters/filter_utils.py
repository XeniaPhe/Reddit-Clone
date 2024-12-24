import graphene
from django.db import models
from typing import Type
from graphene_django.types import DjangoObjectType

import core.filters.operators as ops
from core.custom_errors import internal_server_error

def to_camel_case(string: str) -> str:
    camel_case = ''
    upper = False
    
    for ch in string:
        if ch == '_':
            upper = True
            continue
        
        if upper:
            ch = ch.upper()
            upper = False
        
        camel_case += ch
    
    return camel_case
        
def to_snake_case(string: str) -> str:
    snake_case = ''
    prev_lower = False
    
    for ch in string:
        is_lower = ch.islower()
        
        if prev_lower and not is_lower: #hump!
            ch = '_' + ch.lower()
        
        snake_case += ch
        prev_lower = is_lower
    
    return snake_case

def get_graphene_field_type(field_name: str, model_type: Type) -> Type:
    try:
        field = model_type._meta.get_field(field_name)
    except:
        internal_server_error(f'Filter Error: Field "{field}" specified in "filter_fields" does not exist in the model.\n'
                             f'Please make sure the field exists in the "{model_type.__name__}" model and is correctly listed in the "fields" attribute of the DjangoObjectType Meta class.')
    
    global type_map
    type_map = {
        models.CharField: graphene.String,
        models.EmailField: graphene.String,
        models.IntegerField: graphene.Int,
        models.FloatField: graphene.Float,
        models.DecimalField: graphene.Decimal,
        models.BooleanField: graphene.Boolean,
        models.DateField: graphene.Date,
        models.DateTimeField: graphene.DateTime,
    }
    
    for key, value in type_map:
        if isinstance(field, key):
            return value
        
    print(f'Could not find the type of "{field}" in recognized types, defaulting to "graphene.String"')
    return graphene.String

def get_graphene_input_type(filter_operator: str, field_type: Type) -> Type:
    is_numeric = field_type in (graphene.Int, graphene.Float, graphene.Decimal)
    is_invalid = (is_numeric and filter_operator not in ops.NUMERIC_OPERATORS)
    is_invalid |= (field_type == graphene.String and filter_operator not in ops.STRING_OPERATORS)
    is_invalid |= (field_type == graphene.Boolean and filter_operator not in ops.BOOLEAN_OPERATORS)
    is_invalid |= (field_type == graphene.Date and filter_operator not in ops.DATE_OPERATORS)
    is_invalid |= (field_type == graphene.DateTime and filter_operator not in ops.DATETIME_OPERATORS)
    
    if is_invalid:
        internal_server_error(f'Filter Error: Invalid filter operator "{filter_operator}" for field type {field_type.__name__}')
    
    #filter operator categories:
    #1-always expect string (e.g. 'contains', 'icontains', 'iexact', 'regex')
    #2-always expext integer (e.g. 'week_day', 'year')
    #3-always expect boolean (e.g. 'isnull')
            
    pass

def get_graphene_filter_arguments(django_object_type: DjangoObjectType):
    model_type = django_object_type._meta.model
    graphql_fields = django_object_type._meta.fields
    filter_fields = django_object_type._meta.filter_fields
    
    filter_arguments = {}
    
    for field in filter_fields.keys():
        if field not in graphql_fields:
            internal_server_error(f'Filter Error: Field "{field}" specified in "filter_fields" does not exist in the "fields" attribute.\n'
                             f'Make sure the field exists in the "{model_type.__name__}" model and is correctly listed in the "fields" attribute of the DjangoObjectType Meta class.')
            
        graphene_field_type = get_graphene_field_type(field, model_type)
        filters = filter_fields[field]
        
        for filter in filters:
            #TODO: check if the filter supports this type
            filter_name = to_camel_case(field) + '_' + filter.capitalize()
            argument = graphene.Argument(graphene_field_type, required=False)
            filter_arguments[filter_name] = argument
    
    return filter_arguments

def get_django_filter_arguments(django_object_type: DjangoObjectType, **graphene_filter_params):
    all_filters = get_graphene_filter_arguments(django_object_type).keys()
    
    filter_arguments = {}
    
    for filter_key in graphene_filter_params.keys():
        if filter_key not in all_filters:
            continue
        
        filter_parts = filter_key.split('_')
        filtered_field = to_snake_case(filter_parts[0])
        filter_name = '_'.join(filter_parts[1:]).lower()
        filter_value = graphene_filter_params[filter_key]
        filter_arguments[filtered_field + '__' + filter_name] = filter_value
    
    return filter_arguments