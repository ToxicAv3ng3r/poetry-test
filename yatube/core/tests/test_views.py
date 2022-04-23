from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus

User = get_user_model()


class CoreViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUsername')

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_404_use_correct_template_guest(self):
        """Неавторизованный пользователь увидит кастомный шаблон 404"""
        response = self.guest_client.get('/unexist_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_404_use_correct_template_authorized(self):
        """Авторизованный пользователь увидит кастомный шаблон 404"""
        response = self.authorized_client.get('/unexist_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
