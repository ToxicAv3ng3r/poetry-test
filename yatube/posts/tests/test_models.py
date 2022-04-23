from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        post = PostModelTest.post
        expected = post.text[:settings.SYMBOLS_IN_STR]
        self.assertEqual(expected, str(post))
        group = PostModelTest.group
        expected_group = group.title
        self.assertEqual(expected_group, str(group))

    def test_model_verbose_name(self):
        """Проверяем, что у полей модели Post корректные verbose"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа поста',
            'image': 'Картинка'
        }
        for field, expected_values in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_values)

    def test_model_help_text(self):
        """Проверяем, что у полей модели Post корректные help_text"""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка'
        }
        for field, expected_values in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_values)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_2')
        cls.post = Post.objects.create(author=cls.user, text='Test text')
        cls.comment = Comment.objects.create(post=cls.post,
                                             author=cls.user,
                                             text='Test comment text')

    def test_comment_have_correct_str(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        comment = self.comment
        expected = comment.text[:settings.SYMBOLS_IN_STR]
        self.assertEqual(expected, str(comment))

    def test_comment_have_correct_verbose(self):
        """Проверяем, что у модели Comment корректные verbose_name"""
        comment = self.comment
        field_verbose_names = {
            'post': 'Комментарий к посту',
            'author': 'Автор',
            'text': 'Комментарий',
            'created': 'Дата публикации комментария'
        }
        for field, expected_values in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_values)

    def test_comment_have_correct_lep_texts(self):
        """Проверяем, что у модели Comment корректные help_text"""
        comment = self.comment
        field_help_texts = {
            'post': 'Комментарий к посту',
            'author': 'Автор комментария',
            'text': 'Текст комментария',
            'created': 'Дата публикации комментария'
        }
        for field, expected_values in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text,
                    expected_values)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Test_author')
        cls.user_follower = User.objects.create(username='Test_follower')
        cls.follow = Follow.objects.create(
            author=cls.user_author, user=cls.user_follower)

    def test_follow_have_correct_verbose(self):
        """Проверяем, что у модели Follow корректные verbose_name"""
        follow = self.follow
        field_verbose_names = {
            'user': 'Подписчик',
            'author': 'Автор'
        }
        for field, expected_value in field_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name,
                    expected_value)
