from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Имя группы')
    slug = models.SlugField(
        unique=True,
        verbose_name='Название группы латинницей без пробелов'
    )
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Напишите текст поста')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста'
    )

    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        related_name='posts',
        help_text='Выберите группу, к которой относится пост',
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Загрузите картинку'
    )

    def __str__(self):
        MAX_LENGTH = 15
        return self.text[:MAX_LENGTH]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Комментарий',
        related_name='comments',
        help_text='Пост, к которому относится комментарий',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор поста'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Напишите комментарий к посту',
    )

    def __str__(self):
        MAX_LENGTH = 15
        return self.text[:MAX_LENGTH]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
