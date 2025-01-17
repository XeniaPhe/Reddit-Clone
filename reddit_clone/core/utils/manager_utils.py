from django.db import models
from core.models import Post
from typing import Type

def preselect(model: Type[models.Model], select_related: list[str]=None, prefetch_related: list[str]=None):
    manager = model.objects
    
    if select_related:
        manager = manager.select_related(*select_related)
        
    if prefetch_related:
        manager = manager.prefetch_related(*prefetch_related)
    
    return manager