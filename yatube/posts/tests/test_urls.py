from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post, User, Comment, Follow


class StaticURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_homepage(self):
        """Проверяем, что главная страница доступна"""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст'
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Test comment text'
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = PostURLTest.user
        self.user_2 = User.objects.create(username='TestUser2')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_non_author = Client()
        self.authorized_client_non_author.force_login(self.user_2)

    def test_urls_uses_correct_template(self):
        """Проверяем, что в posts используеются верные шаблоны"""
        urls = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse('posts:group_list_page',
                    kwargs={
                        'slug': self.group.slug
                    }): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': self.user.username
                    }): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': self.post.id
                    }): 'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

        for adress, template in urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_auth_only(self):
        """Шаблон редактирования поста использует верный шаблон"""
        post_id = PostURLTest.post.id
        urls = {
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for adress, template in urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_correct_redir(self):
        """Анонимный юзер не может открыть страницу создания поста"""
        post_id = PostURLTest.post.id
        urls = {
            f'/posts/{post_id}/edit/': (f'/auth/login/?next=/posts/'
                                        f'{post_id}/edit/'),
            '/create/': '/auth/login/?next=/create/'
        }
        for adress, redir_adress in urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertRedirects(response, redir_adress)

    def test_anonimus_comment_redir(self):
        """Анонимный юзер не напишет комментарий"""
        post_id = self.post.id
        form_data = {
            'text': 'Test comment text'
        }
        response = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': post_id}), data=form_data, follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post_id}/comment/')

    def test_anonimus_cant_follow(self):
        """Аноним не сможет создать подписку"""
        follows_count = Follow.objects.count()
        username = self.user.username
        response = self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': username}))
        self.assertRedirects(
            response, f'/auth/login/?next=/profile/{username}/follow/')
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_follow_availible(self):
        """Система подписки доступна"""
        username = self.user.username
        urls = [
            reverse('posts:profile_follow', kwargs={'username': username}),
            reverse('posts:profile_unfollow', kwargs={'username': username})
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client_non_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_author_edit_only(self):
        """Не автора должно перекинуть на детали поста"""
        post_id = PostURLTest.post.id
        response = (self.authorized_client_non_author.get
                    (f'/posts/{post_id}/edit/'))
        self.assertRedirects(response, f'/posts/{post_id}/')

    def test_all_status(self):
        """Проверка доступности всех страниц"""
        post_id = PostURLTest.post.id
        slug = PostURLTest.group.slug
        username = PostURLTest.post.author.username
        urls_status = {
            '/': HTTPStatus.OK,
            f'/group/{slug}/': HTTPStatus.OK,
            f'/profile/{username}/': HTTPStatus.OK,
            f'/posts/{post_id}/': HTTPStatus.OK,
            f'/posts/{post_id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for adress, status_code in urls_status.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status_code)
