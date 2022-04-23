from django.test import TestCase, Client
from django.urls import reverse


class AboutViewsTest(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_about_pages_uses_correct_template(self):
        templates = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, reverse_name in templates.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
