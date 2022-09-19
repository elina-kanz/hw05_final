from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов из приложения about."""
        response_author = self.guest_client.get('/about/author/')
        response_tech = self.guest_client.get('/about/tech/')
        responses = {
            '/about/author/': response_author,
            '/about/tech/': response_tech,
        }
        for request, responce in responses.items():
            with self.subTest(request=request):
                self.assertEqual(
                    responce.status_code, 200
                )

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов из приложения about."""
        template_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in template_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
