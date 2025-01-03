import graphene
from graphene_django import DjangoObjectType

import core.filters.operators as ops
from core.models import Content

class ContentType(DjangoObjectType):
    class Meta:
        model = Content
        fields = ('id', 'body', 'publish_date',)
        filter_fields = {
            'id': ops.ID_OPERATORS,
            'body': ops.STRING_OPERATORS,
            'publish_date': ops.DATE_OPERATORS,
        }