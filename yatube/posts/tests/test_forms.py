import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, Comment

from http import HTTPStatus

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUsername')
        cls.user_non_author = User.objects.create(username='TestUsername2')
        cls.group = Group.objects.create(
            title='Test_title',
            description='Test description',
            slug='test_slug'
        )
        cls.group2 = Group.objects.create(
            title='Test_title2',
            description='Test description2',
            slug='test_slug2'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(self.user_non_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_with_image(self):
        """Проверка, что пост создается с картинкой"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='smal1.gif',
            content=small_gif,
            content_type='image/gif'

        )
        form_data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
            'image': uploaded
        }

        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest('pub_date')
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group, self.group)
        self.assertEqual(last_post.text,
                         form_data['text'])
        self.assertEqual(last_post.image.name,
                         'posts/' + form_data['image'].name)

    def test_create_post_without_image(self):
        """Проверка, что пост создается без картинки"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст нового поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest('pub_date')
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group, self.group)
        self.assertEqual(last_post.text,
                         form_data['text'])
        self.assertFalse(last_post.image)

    def test_non_auth_user_cant_edit_post(self):
        """Неавторизованный юзер не отредактирует пост"""
        form_data = {
            'text': 'Пытаюсь редактировать пост'
        }
        response = self.guest_client.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=' + reverse(
                                 'posts:post_edit',
                                 kwargs={'post_id': self.post.id}))
        try_redact_post = Post.objects.get(id=self.post.id)
        self.assertEqual(try_redact_post.text, self.post.text)
        self.assertEqual(try_redact_post.author, self.post.author)
        self.assertEqual(try_redact_post.pub_date, self.post.pub_date)
        self.assertEqual(try_redact_post.group, self.post.group)

    def test_non_auth_user_cant_create_post(self):
        """Неавторизованный юзер не создаст новый пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'пытаюсь создать новый пост',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data, follow=True)
        self.assertRedirects(response, reverse('users:login')
                             + '?next=' + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_non_author_cant_edit_post(self):
        """Не автор поста не может его редактировать"""
        form_data = {
            'text': 'Пытаюсь редактировать чужой пост'
        }
        response = self.authorized_client_non_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        try_redact_post = Post.objects.get(id=self.post.id)
        self.assertEqual(try_redact_post.text, self.post.text)
        self.assertEqual(try_redact_post.author, self.post.author)
        self.assertEqual(try_redact_post.pub_date, self.post.pub_date)
        self.assertEqual(try_redact_post.group, self.post.group)

    def test_create_post_without_group(self):
        """Пост можно создать без группы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Создаем пост без группы'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest('pub_date')
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.text,
                         form_data['text'])
        self.assertFalse(last_post.group)

    def test_post_edit_with_group(self):
        """Пост можно редактировать с изменением группы"""
        form_data = {
            'text': 'Редактируем пост и указываем новую группу',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redacted_post = Post.objects.get(id=self.post.id)
        self.assertEqual(redacted_post.text, form_data['text'])
        self.assertEqual(redacted_post.author, self.post.author)
        self.assertEqual(redacted_post.group, self.group2)
        self.assertEqual(redacted_post.pub_date, self.post.pub_date)

    def test_post_edit_without_group(self):
        """Редактируем пост и не указываем новую группу"""
        form_data = {
            'text': 'Редактируем пост и не меняем группу',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redacted_post = Post.objects.get(id=self.post.id)
        self.assertEqual(redacted_post.text, form_data['text'])
        self.assertEqual(redacted_post.author, self.post.author)
        self.assertEqual(redacted_post.group, self.group)
        self.assertEqual(redacted_post.pub_date, self.post.pub_date)

    def post_edit_with_image(self):
        """Пост можно редактировать, добавляя картинку"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'

        )
        form_data = {
            'text': 'Редактируем пост и добавляем картинку',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redacted_post = Post.objects.get(id=self.post.id)
        self.assertEqual(redacted_post.text, form_data['text'])
        self.assertEqual(redacted_post.author, self.post.author)
        self.assertEqual(redacted_post.group, self.group)
        self.assertEqual(redacted_post.pub_date, self.post.pub_date)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_create(self):
        """Проверка, что комментарий создается"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Test comment'
        }
        response = self.authorized_client.post(reverse
                                               ('posts:add_comment',
                                                kwargs={
                                                    'post_id': self.post.id
                                                }),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        last_comment = Comment.objects.latest('created')
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.author, self.user)
        self.assertEqual(last_comment.post, self.post)

    def test_guest_cant_create_comment(self):
        """Неавторизованный юзер не напишет комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Test comment'
        }
        response = self.guest_client.post(reverse
                                          ('posts:add_comment',
                                           kwargs={
                                               'post_id': self.post.id
                                           }),
                                          data=form_data,
                                          follow=True)
        self.assertRedirects(response, reverse('users:login')
                             + '?next='
                             + reverse('posts:add_comment',
                                       kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count)
