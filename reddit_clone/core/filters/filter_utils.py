import graphene
from django.db import models
from typing import Type
from graphene_django.types import DjangoObjectType

import core.filters.operators as ops
from core.utils.string_utils import to_camel_case, to_snake_case
from core.custom_errors import filter_error, bad_request

_django_to_graphene_type_map = {
    models.CharField: graphene.String,
    models.EmailField: graphene.String,
    models.JSONField: graphene.String,
    models.FileField: graphene.String,
    models.IPAddressField: graphene.String,
    models.GenericIPAddressField: graphene.String,
    models.UUIDField: graphene.UUID,
    models.IntegerField: graphene.Int,
    models.DurationField: graphene.Int,
    models.BigIntegerField: graphene.BigInt,
    models.FloatField: graphene.Float,
    models.DecimalField: graphene.Decimal,
    models.BooleanField: graphene.Boolean,
    models.DateField: graphene.Date,
    models.TimeField: graphene.Time,
    models.DateTimeField: graphene.DateTime,
    models.ForeignKey: graphene.ID,
    models.OneToOneField: graphene.ID,
    models.ManyToManyField: type(graphene.List(graphene.ID)),
}

_fixed_type_operator_map = {
    ops.BOOLEAN_TAKING_OPERATORS: graphene.Boolean,
    ops.STRING_TAKING_OPERATORS: graphene.String,
    tuple(ops.INTEGER_TAKING_OPERATORS.keys()): graphene.Int,
    ops.DATE_TAKING_OPERATORS: graphene.Date,
    ops.TIME_TAKING_OPERATORS: graphene.Time,
    ops.DATETIME_TAKING_OPERATORS: graphene.DateTime,
}

def _to_original_field_name(graphene_model_type: Type[DjangoObjectType], graphql_field_name: str):
    original_field_name = to_snake_case(graphql_field_name)
    django_model_fields = [field.name for field in graphene_model_type._meta.model._meta.get_fields()]
    
    #Field name is not snake_case so it changed when it was converted to camelCase and then to snake_case
    #This should work for camelCase, PascalCase and SCREAMING_SNAKE_CASE variables
    if original_field_name not in django_model_fields:
        for django_model_field in django_model_fields:
            if django_model_field.replace('_', '').lower() == graphql_field_name.lower():
                original_field_name = django_model_field
                break
    
    return original_field_name

def _get_graphene_field_type(graphene_field: str, model_type: Type[models.Model], suppress_logs=False) -> Type:
    try:
        model_field = model_type._meta.get_field(graphene_field)
    except:
        filter_error(f'Field "{graphene_field}" specified in "filter_fields" does not exist in the model.\n'
                    f'Please make sure the field exists in the "{model_type.__name__}" model and is correctly listed in the "fields" attribute of the DjangoObjectType Meta class.')
    
    for django_type, graphene_type in _django_to_graphene_type_map.items():
        if isinstance(model_field, django_type):
            return graphene_type
    
    if not suppress_logs:
        print(f'Could not find the type of "{model_field}" in recognized types, defaulting to "graphene.String"')
    
    return graphene.String

def _get_graphene_argument_type(filter_operator: str, graphene_field_type: Type) -> Type:
    is_numeric = graphene_field_type in (graphene.Int, graphene.BigInt, graphene.Float, graphene.Decimal)
    is_id = graphene_field_type in (graphene.ID, graphene.UUID)
    is_invalid = (is_numeric and filter_operator not in ops.NUMERIC_OPERATORS)
    is_invalid |= (is_id and filter_operator not in ops.ID_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.String and filter_operator not in ops.STRING_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.Boolean and filter_operator not in ops.BOOLEAN_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.Date and filter_operator not in ops.DATE_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.Time and filter_operator not in ops.TIME_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.DateTime and filter_operator not in ops.DATETIME_OPERATORS)
    is_invalid |= (graphene_field_type == graphene.List and filter_operator not in ops.LIST_OPERATORS)
    
    if is_invalid:
        filter_error(f'Invalid filter operator "{filter_operator}" for field type {graphene_field_type.__name__}')
    
    for fixed_type_operators, graphene_type in _fixed_type_operator_map.items():
        if filter_operator in fixed_type_operators:
            return graphene_type
    
    if filter_operator in ops.COMPARISON_OPERATORS:
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
            
        graphene_field_type = _get_graphene_field_type(filtered_field, django_model_type)
        
        for filter_operator in filter_operators:
            graphql_field = to_camel_case(filtered_field)
            
            if filter_operator != ops.EXACT:
                graphql_filter = graphql_field + '_' + filter_operator.capitalize()
            else:
                graphql_filter = graphql_field
            
            argument_type = _get_graphene_argument_type(filter_operator, graphene_field_type)
            argument = graphene.Argument(argument_type, name=graphql_filter, required=False)
            filter_arguments[graphql_filter] = argument

    return filter_arguments

def get_graphene_orderby_arguments(graphene_model_type: Type[DjangoObjectType]):
    django_model_type = graphene_model_type._meta.model
    graphene_fields = graphene_model_type._meta.fields
    
    ordering_choices = {}
    
    for ordered_field in graphene_fields:
        _get_graphene_field_type(ordered_field, django_model_type, True)
        graphql_field = to_camel_case(ordered_field)
        
        ordering_choices[graphql_field] = graphql_field
        ordering_choices[f'-{graphql_field}'] = f'-{graphql_field}'
        
    enum_type = type(f'{django_model_type.__name__}OrderByEnum', (graphene.Enum,), ordering_choices)
    
    return {'orderBy': graphene.Argument(enum_type, name='orderBy', required=False)}
        
def get_django_filter_arguments(graphene_model_type: Type[DjangoObjectType], **graphql_filter_params):
    all_filters = get_graphene_filter_arguments(graphene_model_type).keys()
    filter_arguments = {}
    
    for graphql_filter, filter_value in graphql_filter_params.items():
        if graphql_filter not in all_filters:
            continue
        
        graphql_filter_parts = graphql_filter.split('_')
        filtered_field = _to_original_field_name(graphene_model_type, graphql_filter_parts[0])
        filter_operator = '_'.join(graphql_filter_parts[1:]).lower()
        filter_operator = filter_operator if filter_operator != '' else ops.EXACT
        
        if filter_operator in ops.INTEGER_TAKING_OPERATORS.keys():
            allowed_range = ops.INTEGER_TAKING_OPERATORS[filter_operator]
            if not (filter_value >= allowed_range[0] and filter_value <= allowed_range[1]):
                bad_request(f'The provided filter value "{filter_value}" for filter "{graphql_filter}" is out of range. '
                            f'Allowed range for filter operator "{filter_operator}" = [{allowed_range[0]}, {allowed_range[1]}].')
        elif filter_operator == ops.RANGE:
            if filter_value.start >= filter_value.end:
                bad_request(f'The range filter provided is invalid: "[{filter_value.start}, {filter_value.end}]". '
                            'Start value cannot be greater than or equal to the end value')
                
            filter_value = (filter_value.start, filter_value.end)
        
        django_filter = filtered_field + '__' + filter_operator
        filter_arguments[django_filter] = filter_value
    
    return filter_arguments

def get_django_orderby_argument(graphene_model_type: Type[DjangoObjectType], **graphql_filter_params):
    orderby = graphql_filter_params.get('orderBy', None)
    if orderby:
        is_descending = True if orderby[0] == '-' else False
        original_field_name = _to_original_field_name(graphene_model_type, orderby.strip('-'))
        return f'-{original_field_name}' if is_descending else original_field_name
    return None