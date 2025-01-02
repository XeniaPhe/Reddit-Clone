# Generated by Django 5.1.4 on 2024-12-31 11:40

import core.managers
import core.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('username', models.CharField(max_length=48, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('join_date', models.DateField(auto_now_add=True)),
                ('score', models.IntegerField(default=0)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', core.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('body', models.TextField(blank=True, default='')),
                ('publish_date', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.IntegerField(choices=[(0, 'Post'), (1, 'Comment')])),
            ],
        ),
        migrations.CreateModel(
            name='Community',
            fields=[
                ('name', models.CharField(max_length=48, primary_key=True, serialize=False)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('Gst', 'Guest'), ('Mem', 'Member'), ('Mod', 'Moderator'), ('Fdr', 'Founder')], default='Mem', max_length=3)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.community')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'community')},
            },
        ),
        migrations.AddField(
            model_name='community',
            name='users',
            field=models.ManyToManyField(related_name='communities', through='core.Membership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('content', models.OneToOneField(default=core.models.get_post_content, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.content')),
                ('title', models.CharField(max_length=96)),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='core.community')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='posts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('content', models.OneToOneField(default=core.models.get_comment_content, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.content')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='children', to='core.content')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='comments', to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='comments', to='core.post')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('vote', models.IntegerField(choices=[(-1, 'Downvote'), (0, 'None'), (1, 'Upvote')], default=0)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='votes', to='core.content')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'content')},
            },
        ),
    ]
