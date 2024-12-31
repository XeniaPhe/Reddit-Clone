import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from core.managers import UserManager
from core.auth.roles import MEMBER, DB_ROLE_CHOICES

class User(AbstractBaseUser):
    username = models.CharField(max_length=48, primary_key=True)
    email = models.EmailField(unique=True)
    join_date = models.DateField(auto_now_add=True)
    score = models.IntegerField(default=0)
    
    last_login = None
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    def __str__(self):
        return self.username
    
    # Below fields and functions are for admin page only
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser
    
class Community(models.Model):
    name = models.CharField(max_length=48, primary_key=True)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(to=User, through='Membership', related_name='communities')
    
    def __str__(self):
        return self.name
    
class Membership(models.Model):    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=3, choices=DB_ROLE_CHOICES, default=MEMBER)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='memberships')
    community = models.ForeignKey(to=Community, on_delete=models.CASCADE, related_name='memberships')
    
    def __str__(self):
        return f'{self.community[:24]}-{self.user[:23]}'
    
    class Meta:
        unique_together = [['user', 'community']]

class Content(models.Model):
    class ContentType(models.IntegerChoices):
        POST = 0, 'Post'
        COMMENT = 1, 'Comment'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField(blank=True, default='')
    publish_date = models.DateTimeField(auto_now_add=True)
    content_type = models.IntegerField(choices=ContentType.choices)
    
    def is_comment(self):
        return self.content_type == Content.ContentType.COMMENT
    
    def is_post(self):
        return self.content_type == Content.ContentType.POST
    
    def get_related_object(self):
        manager = Post.objects if self.is_post() else Comment.objects
        return manager.get(id=self.id)
    
    def __str__(self):
        return self.body[:48]

def get_post_content():
    return Content.objects.create(content_type=Content.ContentType.POST)

def get_comment_content():
    return Content.objects.create(content_type=Content.ContentType.COMMENT)

class Post(models.Model):
    content = models.OneToOneField(to=Content, on_delete=models.CASCADE, primary_key=True, default=get_post_content)
    title = models.CharField(max_length=96)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='posts')
    community = models.ForeignKey(to=Community, on_delete=models.CASCADE, related_name='posts')
    
    def __str__(self):
        return self.title[:48]

class Comment(models.Model):
    content = models.OneToOneField(to=Content, on_delete=models.CASCADE, primary_key=True, default=get_comment_content)
    parent = models.ForeignKey(to=Content, on_delete=models.DO_NOTHING, related_name='children')
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='comments')
    post = models.ForeignKey(to=Post, on_delete=models.DO_NOTHING, related_name='comments')

class Vote(models.Model):
    class VoteType(models.IntegerChoices):
        DOWNVOTE = -1, 'Downvote'
        NONVOTE = 0, 'None'
        UPVOTE = 1, 'Upvote'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vote = models.IntegerField(choices=VoteType.choices, default=VoteType.NONVOTE)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='votes')
    content = models.ForeignKey(to=Content, on_delete=models.DO_NOTHING, related_name='votes')

    class Meta:
        unique_together = [['user', 'content']]