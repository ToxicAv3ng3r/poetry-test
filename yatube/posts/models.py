from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Post(models.Model):
    text = models.TextField(help_text='Текст нового поста',
                            verbose_name='Текст поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    help_text='Дата публикации',
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text='Автор поста',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text='Группа, к которой будет относиться пост',
        verbose_name='Группа поста'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        help_text='Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:settings.SYMBOLS_IN_STR]


class Group(models.Model):
    title = models.CharField(max_length=200,
                             verbose_name='Название группы')
    slug = models.SlugField(unique=True, verbose_name='Слаг')
    description = models.TextField(verbose_name='Описание группы')

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Комментарий к посту',
        verbose_name='Комментарий к посту'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Автор комментария',
        verbose_name='Автор'
    )
    text = models.TextField(help_text='Текст комментария',
                            verbose_name='Комментарий')
    created = models.DateTimeField(auto_now_add=True,
                                   help_text='Дата публикации комментария',
                                   verbose_name='Дата публикации комментария')

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий',
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:settings.SYMBOLS_IN_STR]


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
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name='twice_follow_constraint')
        ]


class Likes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likers',
        verbose_name='Понравилось'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Понравившийся пост',
        blank=True,
        null=True
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Понравившийся комментарий',
        blank=True,
        null=True
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text='Дата',
        verbose_name='Дата'
    )

    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'post'),
                name='twice_likes_post'
            ),
            models.UniqueConstraint(
                fields=('user', 'comment'),
                name='twice_likes_comment'
            )
        ]
