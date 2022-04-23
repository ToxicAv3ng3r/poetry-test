from http import HTTPStatus

from django.test import TestCase, Client


class AboutURLTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_about_pages_status(self):
        """Проверяем что неизменяемые страницы доступны"""
        urls_list = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK
        }
        for url, status_code in urls_list.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_about_pages_heve_correct_templates(self):
        """Проверяем, что страницы используют корректные шаблоны"""
        urls_list = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in urls_list.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
