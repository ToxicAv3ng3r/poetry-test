import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django import forms
from django.urls import reverse
from django.conf import settings

from http import HTTPStatus

from ..models import Group, Post, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test_User')
        cls.user2 = User.objects.create(username='Test_User_2')
        cls.user3 = User.objects.create(username='Test_User_3')
        cls.group = Group.objects.create(
            title='Test title',
            description='Test description',
            slug='testslug'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'

        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Test comment'
        )
        cls.group_2 = Group.objects.create(
            title='Test title 2',
            description='Test description 2',
            slug='test_slug_2'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user3
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_3 = Client()
        self.user = PostViewsTest.user
        self.authorized_client.force_login(self.user)
        self.user2 = PostViewsTest.user2
        self.authorized_client_2.force_login(self.user2)
        self.user3 = PostViewsTest.user3
        self.authorized_client_3.force_login(self.user3)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse(
                'posts:group_list_page',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': PostViewsTest.user}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): 'posts/create_post.html'
        }

        for reverse_name, template in templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main_page'))
        post_object = response.context['page_obj'][0]
        post_text_0 = post_object.text
        post_image_0 = post_object.image
        post_author_0 = post_object.author.username
        post_group_0 = post_object.group.title
        self.assertEqual(post_text_0, PostViewsTest.post.text)
        self.assertEqual(post_image_0, PostViewsTest.post.image)
        self.assertEqual(post_author_0, PostViewsTest.post.author.username)
        self.assertEqual(post_group_0, PostViewsTest.post.group.title)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get
                    (reverse('posts:group_list_page',
                             kwargs={'slug': PostViewsTest.group.slug})))
        context_group_object = response.context['group']
        group_title_0 = context_group_object.title
        group_slug_0 = context_group_object.slug
        self.assertEqual(group_title_0, self.group.title)
        self.assertEqual(group_slug_0, self.group.slug)
        post_object = response.context['page_obj'][0]
        post_group = post_object.group
        post_author = post_object.author
        post_text = post_object.text
        post_image = post_object.image
        post_pub_date = post_object.pub_date
        self.assertEqual(post_group, PostViewsTest.post.group)
        self.assertEqual(post_author, PostViewsTest.post.author)
        self.assertEqual(post_text, PostViewsTest.post.text)
        self.assertEqual(post_image, PostViewsTest.post.image)
        self.assertEqual(post_pub_date, PostViewsTest.post.pub_date)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': PostViewsTest.user}))
        context_author_object = response.context['author']
        self.assertEqual(context_author_object, PostViewsTest.post.author)
        post_object = response.context['page_obj'][0]
        post_author_0 = post_object.author
        post_group_0 = post_object.group
        post_text_0 = post_object.text
        post_image_0 = post_object.image
        post_pub_date_0 = post_object.pub_date
        self.assertEqual(post_group_0, PostViewsTest.post.group)
        self.assertEqual(post_author_0, PostViewsTest.post.author)
        self.assertEqual(post_text_0, PostViewsTest.post.text)
        self.assertEqual(post_image_0, PostViewsTest.post.image)
        self.assertEqual(post_pub_date_0, PostViewsTest.post.pub_date)

    def test_comments_context(self):
        """Комментарий передается в шаблон post_detail"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        comment_object = response.context['comments'][0]
        comment_author = comment_object.author
        comment_text = comment_object.text
        comment_form = response.context.get('form')
        form_field = comment_form.fields.get('text')
        self.assertIsNotNone(comment_form)
        self.assertIsInstance(form_field, forms.fields.CharField)
        self.assertEqual(comment_author, self.comment.author)
        self.assertEqual(comment_text, self.comment.text)

    def test_cache_main_page(self):
        """Проверка кэширования главной страницы"""
        response_before_create = self.authorized_client.get(reverse(
            'posts:main_page'))
        page_content = response_before_create.content
        Post.objects.create(
            author=self.user,
            text='New post'
        )
        response_after_create = (self.authorized_client.get
                                 (reverse('posts:main_page')))
        self.assertEqual(page_content, response_after_create.content)
        cache.clear()
        response_after_clear = (self.authorized_client.get
                                (reverse('posts:main_page')))
        new_post_obj = response_after_clear.context['page_obj'][0]
        self.assertEqual(new_post_obj.text, Post.objects.latest('pk').text)

    def test_another_group(self):
        """Пост отображается на нужных страницах
        и не попадает в правильную группу"""
        urls_lst = [
            reverse('posts:main_page'),
            reverse('posts:group_list_page',
                    kwargs={'slug': PostViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostViewsTest.user})
        ]
        for url in urls_lst:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0],
                                 PostViewsTest.post)

        response = (self.authorized_client.get
                    (reverse('posts:group_list_page',
                             kwargs={'slug': PostViewsTest.group.slug})))
        post_obj = response.context['page_obj']
        self.assertIn(self.post, post_obj, 'Поста нет в этой группе!!!')

    def test_follow(self):
        """Авторизованный пользователь может подписаться на другого"""
        follows_count = Follow.objects.count()
        response = self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user2.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follows_count + 1)

    def test_unfollow(self):
        """Авторизованный пользователь может отписаться от другого"""
        follows_count = Follow.objects.count()
        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user3.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follows_count - 1)

    def test_follow_yourself(self):
        """Юзер не может подписаться на самого себя"""
        follows_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertRedirects(response, f'/profile/{self.user.username}/')
        user = self.user
        constraint_name = 'twice_follow_constraint'
        with self.assertRaisesMessage(IntegrityError, constraint_name):
            Follow.objects.create(user=user, author=user)

    def test_follow_twice(self):
        """Юзер не может подписаться дважды на одного автора"""
        follows_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user3.username}))
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertRedirects(response, f'/profile/{self.user3.username}/')

    def test_follower_lent_update(self):
        """Новый пост появляется у подписчика в ленте
         и не появится у того, кто не подписан"""
        form_data = {
            'text': 'Test text'
        }
        response_create = (self.authorized_client_3.post
                           (reverse('posts:post_create'),
                            data=form_data, follow=True))
        response_follower = (self.authorized_client.get
                             (reverse('posts:follow_index')))
        post_obj = response_follower.context['page_obj'][0]
        self.assertEqual(response_create.status_code, HTTPStatus.OK)
        self.assertEqual(post_obj.text, form_data['text'])
        response_not_follower = (self.authorized_client_2.get
                                 (reverse('posts:follow_index')))
        self.assertEqual(len(response_not_follower.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Test title',
            description='Test description',
            slug='test_slug'
        )
        cls.TOTAL_POSTS: int = 14
        cls.POSTS_ON_PAGE: int = 10
        cls.post_lst = []
        for post_number in range(cls.TOTAL_POSTS):
            cls.post_lst.append(Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Текст тестового поста номер {post_number}'
            ))

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_records(self):
        """На первых страницах создается по 10 постов"""
        urls_lst = [
            reverse('posts:main_page'),
            reverse('posts:group_list_page',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user})
        ]
        for url in urls_lst:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 self.POSTS_ON_PAGE)

    def test_second_page_contains_four_records(self):
        """На вторых страницах создается по 4 поста"""
        records_on_page: int = self.TOTAL_POSTS - self.POSTS_ON_PAGE
        urls_lst = [
            reverse('posts:main_page'),
            reverse('posts:group_list_page',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user})
        ]
        for url in urls_lst:
            with self.subTest(url=url):
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 records_on_page)
