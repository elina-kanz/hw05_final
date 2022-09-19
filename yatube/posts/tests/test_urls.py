from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author_client = Client()
        cls.user_author = User.objects.create_user(username='author')
        cls.authorized_author_client.force_login(cls.user_author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='not_author')
        self.authorized_client.force_login(self.user)

    def test_about_url_available_to_everyone(self):
        """Страницы, доступные любому пользователю."""
        url_test_post_detail = f'/posts/{self.post.pk}/'
        responses = {
            '/': self.guest_client.get('/'),
            f'/group/{self.group.slug}/':
                self.guest_client.get(f'/group/{self.group.slug}/'),
            f'/profile/{self.user.username}/':
                self.guest_client.get(f'/profile/{self.user.username}/'),
            url_test_post_detail: self.guest_client.get(
                url_test_post_detail),
        }
        for request, response in responses.items():
            with self.subTest(request=request):
                self.assertEqual(
                    response.status_code, HTTPStatus.OK
                )

    def test_about_editing_post_available_to_author(self):
        """У автора поста есть доступ к редактированию поста."""
        response = self.authorized_author_client.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_editing_post_not_available_to_not_author(self):
        """Авторизированный пользователь-не автор перенаправится по запросу
        редактирования поста на страницу с деталями поста."""
        url_post_edit = f'/posts/{self.post.pk}/edit/'
        url_post_detail = f'/posts/{self.post.pk}/'
        response = self.authorized_client.get(url_post_edit)
        self.assertRedirects(response, url_post_detail)

    def test_about_creating_post_for_authorized_client(self):
        """Авторизированный пользователь может создать новый пост."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_not_available_for_guest_client(self):
        """Запрос к /posts/<post_id>/edit и /create/ перенаправят анонимного
        пользователя на страницу авторизации."""
        url_post_edit = f'/posts/{self.post.pk}/edit/'
        responses = {
            url_post_edit: self.guest_client.get(url_post_edit),
            '/create/': self.guest_client.get('/create/'),
        }
        for url, response in responses.items():
            with self.subTest():
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_about_unexisting_page(self):
        """Запрос к несуществующей странице вернет ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-group-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_commenting_for_authorized_client(self):
        """Авторизированный пользователь может комментировать пост"""
        response = self.authorized_client.post(
            f'/posts/{self.post.pk}/comment/')
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_commenting_not_available_for_guest_client(self):
        """Анонимный пользователь при попытке прокомментировать пост будет"""
        """ перенаправлен на страницу авторизации"""
        url = f'/posts/{self.post.pk}/comment/'
        response = self.guest_client.post(url)
        self.assertRedirects(
            response, f'/auth/login/?next={url}')

    def test_follow_inbility_guest_client(self):
        """Анонимный пользователь не сможет подписаться на другого
        пользователя и будет перенаправлен на страницу авторизации"""
        url = '/profile/author/follow/'
        response = self.guest_client.get(url)
        self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_follow_inbility_guest_client(self):
        """Анонимный пользователь не сможет отписаться от другого
        пользователя и будет перенаправлен на страницу авторизации"""
        url = '/profile/author/unfollow/'
        response = self.guest_client.get(url)
        self.assertRedirects(response, f'/auth/login/?next={url}')
