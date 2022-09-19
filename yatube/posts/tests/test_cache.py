from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Post, Group, Comment

User = get_user_model()


class CacheTests(TestCase):
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
        cls.post_1 = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост №1',
            group=cls.group,
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост №2',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user_author,
            text='Тестовый комментарий',
            post=cls.post_1,
        )

    def setUp(self):
        pass

    def test_caching(self):
        response_before = self.authorized_author_client.get('/')
        self.post_2.delete()
        responce_after = self.authorized_author_client.get('/')
        self.assertEqual(
            response_before.content, responce_after.content)
        cache.clear()
        response_after_clearing_cache = self.authorized_author_client.get('/')
        self.assertNotEqual(responce_after, response_after_clearing_cache)
