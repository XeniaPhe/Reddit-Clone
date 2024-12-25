import graphene
from django.db import models
from typing import Type
from graphene_django.types import DjangoObjectType

import core.filters.operators as ops
from core.custom_errors import filter_error

_type_map = {
    models.CharField: graphene.String,
    models.EmailField: graphene.String,
    models.IntegerField: graphene.Int,
    models.FloatField: graphene.Float,
    models.DecimalField: graphene.Decimal,
    models.BooleanField: graphene.Boolean,
    models.DateField: graphene.Date,
    models.DateTimeField: graphene.DateTime,
}

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

def get_graphene_field_type(graphene_field: str, model_type: Type[models.Model]) -> Type:
    try:
        model_field = model_type._meta.get_field(graphene_field)
    except:
        filter_error(f'Field "{graphene_field}" specified in "filter_fields" does not exist in the model.\n'
                    f'Please make sure the field exists in the "{model_type.__name__}" model and is correctly listed in the "fields" attribute of the DjangoObjectType Meta class.')
    
    for key, value in _type_map.items():
        if isinstance(model_field, key):
            return value
        
    print(f'Could not find the type of "{model_field}" in recognized types, defaulting to "graphene.String"')
    return graphene.String

def get_graphene_argument_type(filter_operator: str, graphene_field_type: Type) -> Type:
    is_numeric = graphene_field_type in (graphene.Int, graphene.Float, graphene.Decimal)
    is_invalid = (is_numeric and filter_operator not in ops.NUMERIC_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.String and filter_operator not in ops.STRING_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.Boolean and filter_operator not in ops.BOOLEAN_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.Date and filter_operator not in ops.DATE_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.DateTime and filter_operator not in ops.DATETIME_OPERATORS)
    
    if is_invalid:
        filter_error(f'Invalid filter operator "{filter_operator}" for field type {graphene_field_type.__name__}')
    
    if filter_operator in ops.BOOLEAN_TAKING_OPERATORS:
        return graphene.Boolean
    elif filter_operator in ops.STRING_TAKING_OPERATORS:
        return graphene.String
    elif filter_operator in ops.INTEGER_TAKING_OPERATORS:
        return graphene.Int
    elif filter_operator in ops.DATE_TAKING_OPERATORS:
        return graphene.Date
    elif filter_operator in ops.DATETIME_TAKING_OPERATORS:
        return graphene.DateTime
    elif filter_operator in ops.COMPARISON_OPERATORS:
        return graphene_field_type
    elif filter_operator == ops.IN:
        return graphene.List(graphene_field_type)
    elif filter_operator == ops.RANGE:
        class Range(graphene.InputObjectType):
            start = graphene_field_type(required=True)
            end = graphene_field_type(required=True)
                
        return Range
        
    filter_error(f'Filter operator {filter_operator} is undefined')
    
def get_graphene_filter_arguments(graphene_model_type: Type[DjangoObjectType]):
    django_model_type = graphene_model_type._meta.model
    graphene_fields = graphene_model_type._meta.fields
    filter_fields = graphene_model_type._meta.filter_fields
    
    filter_arguments = {}
    
    for filtered_field, filter_operators in filter_fields.items():
        if filtered_field not in graphene_fields:
            filter_error(f'Field "{filtered_field}" specified in "filter_fields" does not exist in the "fields" attribute.\n'
                        f'Make sure the field exists in the "{django_model_type.__name__}" model and is correctly listed in the "fields" attribute of the DjangoObjectType Meta class.')
            
        graphene_field_type = get_graphene_field_type(filtered_field, django_model_type)
        
        for filter_operator in filter_operators:
            graphql_field = to_camel_case(filtered_field)
            
            if filter_operator != ops.EXACT:
                graphql_filter = graphql_field + '_' + filter_operator.capitalize()
            else:
                graphql_filter = graphql_field
            
            argument_type = get_graphene_argument_type(filter_operator, graphene_field_type)
            argument = graphene.Argument(argument_type, required=False)
            filter_arguments[graphql_filter] = argument
    
    return filter_arguments

def get_django_filter_arguments(graphene_model_type: Type[DjangoObjectType], **graphql_filter_params):
    all_filters = get_graphene_filter_arguments(graphene_model_type).keys()
    graphene_fields = graphene_model_type._meta.fields
    filter_arguments = {}
    
    for graphql_filter, filter_value in graphql_filter_params.items():
        if graphql_filter not in all_filters:
            continue
        
        graphql_filter_parts = graphql_filter.split('_')
        filtered_field = to_snake_case(graphql_filter_parts[0])
        
        #Field name is not snake_case so it changed when it was converted to camelCase and then to snake_case
        if filtered_field not in graphene_fields:
            for graphene_field in graphene_fields:
                if graphene_field.lower() == graphql_filter_parts[0].lower():
                    filtered_field = graphene_field
                    break
        
        filter_operator = '_'.join(graphql_filter_parts[1:]).lower()
        filter_operator = filter_operator if filter_operator != '' else ops.EXACT
        django_filter = filtered_field + '__' + filter_operator
        filter_arguments[django_filter] = filter_value
    
    return filter_arguments