import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from core.managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=64, primary_key=True)
    email = models.EmailField(unique=True)
    join_date = models.DateField(auto_now_add=True)
    score = models.IntegerField(default=0)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    def __str__(self):
        return self.username
    
class Community(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
class Membership(models.Model):
    MEMBER, MODERATOR, FOUNDER = 'Mem', 'Mod', 'Fdr'
    ROLE_CHOICES = {
        MEMBER: 'Member',
        MODERATOR: 'Moderator',
        FOUNDER: 'Founder',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=3, choices=ROLE_CHOICES, default=MEMBER)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='memberships')
    community = models.ForeignKey(to=Community, on_delete=models.CASCADE, related_name='memberships')

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128)
    body = models.TextField(blank=True)
    publish_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='posts')
    community = models.ForeignKey(to=Community, on_delete=models.CASCADE, related_name='posts')
    
    def __str__(self):
        return self.title
    
class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField(blank=True)
    publish_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='comments')
    parent = models.ForeignKey(to='self', on_delete=models.DO_NOTHING, related_name='children')
    post = models.ForeignKey(to=Post, on_delete=models.DO_NOTHING, related_name='comments')
    
    def __str__(self):
        return f"{self.post}-{self.user}-{self.id}"