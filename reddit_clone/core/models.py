import uuid
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    username = models.CharField(max_length=64, primary_key=True)
    email = models.CharField(max_length=64, unique=True)
    join_date = models.DateField(default=timezone.now)
    communities = models.ManyToManyField(to='Community', related_name='users')
    
class Community(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    founder = models.ForeignKey(to=User, on_delete=models.DO_NOTHING)

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField(blank=True)
    publish_date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='posts')

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128)
    body = models.TextField(blank=True)
    publish_date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='posts')
    community = models.ForeignKey(to=Community, on_delete=models.DO_NOTHING, related_name='posts')