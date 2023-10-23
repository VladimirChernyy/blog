from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel

User = get_user_model()
NUMBER_OF_CHARACTERS = 15


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        null=True

    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.text[:NUMBER_OF_CHARACTERS]

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comment',
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comment',
    )
    text = models.TextField(
        'Текст',
        help_text='Текст нового комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
