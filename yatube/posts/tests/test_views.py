import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


from posts.models import Post, Group, Comment, Follow
from posts.views import NUMBER_OF_POSTS_ON_PAGE


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
NUMBER_OF_POSTS_IN_DATABASE = 13
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-group-slug-1',
            description='Тестовое описание группы 1',
        )
        posts = []
        for i in range(1, NUMBER_OF_POSTS_IN_DATABASE):
            posts.append(
                Post(
                    author=cls.user_author,
                    text=f'Тестовый пост №{i}',
                    group=cls.group,
                )
            )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posts[NUMBER_OF_POSTS_IN_DATABASE - 2].image = cls.uploaded
        Post.objects.bulk_create(posts)
        cls.post = Post.objects.create(
            author=cls.user_author,
            text=f'Тестовый пост №{NUMBER_OF_POSTS_IN_DATABASE}',
            group=cls.group_1,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user_author,
            text='Тестовый комментарий',
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user_not_author = User.objects.create_user(username='not_author')
        self.authorized_client.force_login(self.user_not_author)
        self.follow_conversely = Follow.objects.create(
            author=self.user_not_author,
            user=self.user_author,
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        reverse_index = reverse('posts:index')
        reverse_group_list = reverse('posts:group_list', kwargs={
                                     'slug': self.group.slug})
        reverse_profile = reverse('posts:profile', kwargs={
                                  'username': self.user_author.username})
        reverse_post_detail = reverse('posts:post_detail', kwargs={
                                      'post_id': self.post.pk})
        reverse_post_edit = reverse('posts:create_post')
        reverse_post_create = reverse('posts:post_edit', kwargs={
                                      'post_id': self.post.pk})
        templates_pages_names = {
            reverse_index: 'posts/index.html',
            reverse_group_list: 'posts/group_list.html',
            reverse_profile: 'posts/profile.html',
            reverse_post_detail: 'posts/post_detail.html',
            reverse_post_edit: 'posts/create_post.html',
            reverse_post_create: 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        ten_posts = Post.objects.select_related('author', 'group')[
            :NUMBER_OF_POSTS_ON_PAGE]
        last_post = page_obj[0]
        last_text = last_post.text
        last_author = last_post.author
        last_image = last_post.image
        # lambda нужна, чтобы убрать кавычки из элементов ten_posts
        self.assertQuerysetEqual(ten_posts, page_obj, transform=lambda x: x)
        self.assertEqual(last_text, self.post.text)
        self.assertEqual(last_author, self.post.author)
        self.assertEqual(last_image, self.post.image)

    def test_first_page_index_contains_right_quantity_records(self):
        """Проверка: количество постов на первой странице равно"""
        """NUMBER_OF_POSTS_ON_PAGE."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), NUMBER_OF_POSTS_ON_PAGE)

    def test_second_page_index_contains_right_quantity_records(self):
        # Проверка: на второй странице должно быть
        # NUMBER_OF_POSTS_IN_DATABASE - NUMBER_OF_POSTS_ON_PAGE постов.
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(
            response.context['page_obj']),
            NUMBER_OF_POSTS_IN_DATABASE - NUMBER_OF_POSTS_ON_PAGE)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        page_obj = response.context['page_obj']
        group = response.context['group']
        ten_posts = Post.objects.filter(group=self.group)[
            :NUMBER_OF_POSTS_ON_PAGE]
        last_image_on_page = page_obj[0].image
        last_image_in_base = Post.objects.filter(
            text=f'Тестовый пост №{NUMBER_OF_POSTS_IN_DATABASE-1}')[0].image
        # lambda нужна, чтобы убрать кавычки из элементов ten_posts
        self.assertQuerysetEqual(ten_posts, page_obj, transform=lambda x: x)
        self.assertEqual(group, self.group)
        self.assertEqual(
            last_image_on_page, last_image_in_base)

    def test_first_page_group_list_contains_right_quantity_records(self):
        """Проверка: количество постов на первой странице равно"""
        """NUMBER_OF_POSTS_ON_PAGE."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(
            len(response.context['page_obj']), NUMBER_OF_POSTS_ON_PAGE)

    def test_second_page_group_list_contains_right_quantity_records(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}) + '?page=2')
        # В последнем посте не указана группа,
        # поэтому постов с указанной группой на один меньше
        self.assertEqual(len(response.context['page_obj']),
                         NUMBER_OF_POSTS_IN_DATABASE
                         - NUMBER_OF_POSTS_ON_PAGE - 1)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_author.username}))
        page_obj = response.context['page_obj']
        author = str(response.context['author'])
        ten_posts = Post.objects.filter(author=self.user_author)[
            :NUMBER_OF_POSTS_ON_PAGE]
        last_image_on_page = page_obj[0].image
        # lambda нужна, чтобы убрать кавычки из элементов ten_posts
        self.assertQuerysetEqual(ten_posts, page_obj, transform=lambda x: x)
        self.assertEqual(author, self.user_author.username)
        self.assertEqual(
            list(last_image_on_page.chunks()), list(self.uploaded.chunks()))

    def test_first_page_profile_contains_right_quantity_records(self):
        """Первая страница сформирована корректно"""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_author.username}))
        self.assertEqual(
            len(response.context['page_obj']), NUMBER_OF_POSTS_ON_PAGE)

    def test_second_page_profile_contains_right_quantity_records(self):
        """Вторая страница сформирована корректно"""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_author.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         NUMBER_OF_POSTS_IN_DATABASE - NUMBER_OF_POSTS_ON_PAGE)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован корректно"""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context['post'], self.post)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_appeаrring_on_right_pages(self):
        """Новый пост появится на главной странице, странице группы поста,"""
        """странице автора и не появится на странице не группы поста."""
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk
        }
        posts_before_posting = list(Post.objects.values_list('id', flat=True))
        self.authorized_author_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.exclude(id__in=posts_before_posting).get()
        response_index = self.guest_client.get(reverse('posts:index'))
        response_group = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        response_author = self.guest_client.get(
            reverse('posts:profile', kwargs={
                'username': self.user_author.username}))
        posts_on_pages = {
            response_index: response_index.context['page_obj'],
            response_author: response_author.context['page_obj'],
            response_group: response_group.context['page_obj']
        }
        for responses, posts in posts_on_pages.items():
            with self.subTest(posts=posts):
                self.assertIn(new_post, posts)
        response_group = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        posts_on_page_of_group = response_group.context['page_obj']
        self.assertNotIn(new_post, posts_on_page_of_group)

    def test_post_detail_show_right_context_image(self):
        """На странице поста есть картинка поста"""
        response = self.guest_client.get(reverse('posts:post_detail', kwargs={
            'post_id': self.post.pk}))
        last_image_on_page = response.context['post'].image
        self.assertEqual(
            list(last_image_on_page.chunks()), list(self.uploaded.chunks()))

    def test_comment_appearing_on_post_page_after_sending(self):
        """После создания нового комментария он появится на странице поста"""
        comments_on_page_before = list(self.authorized_author_client.get(
            f'/posts/{self.post.pk}/').context['comments'].values_list(
                'id', flat=True))
        comments_count_before = len(comments_on_page_before)
        form_data = {
            'text': self.comment.text,
            'post': self.post.pk
        }
        response = self.authorized_author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        comments_on_page_after = self.authorized_client.get(
            f'/posts/{self.post.pk}/').context['comments']
        comments_count_after = len(comments_on_page_after)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(comments_count_after, comments_count_before + 1)
        self.assertTrue(
            comments_on_page_after.filter(
                text=self.comment.text,
                post=self.post.pk,
                author=self.user_author,
            ).exclude(id__in=comments_on_page_before).exists()
        )

    def test_follow_ability_authorized_user(self):
        """Авторизированный пользователь not_author может подписаться
        на другого пользователя author"""
        follow_list_before = list(Follow.objects.filter(
            user=self.user_not_author).values_list('id', flat=True))
        follow_count_before = len(follow_list_before)
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'author'})
        )
        follow_list_after = list(Follow.objects.filter(
            user=self.user_not_author).values_list('id', flat=True))
        follow_count_after = len(follow_list_after)
        self.assertEqual(follow_count_after, follow_count_before + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user_not_author,
            author=self.user_author
        ).exclude(id__in=follow_list_before).exists())

    def test_unfollow_ability_authorized_user(self):
        """Авторизированный пользователь not_author может отписаться от
        другого пользователя author"""
        follow_list_before = list(Follow.objects.filter(
            user=self.user_author).values_list('id', flat=True))
        follow_count_before = len(follow_list_before)
        self.authorized_author_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': 'not_author'})
        )
        follow_list_after = list(Follow.objects.filter(
            user=self.user_not_author).values_list('id', flat=True))
        follow_count_after = len(follow_list_after)
        self.assertEqual(follow_count_after, follow_count_before - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.user_author,
            author=self.user_not_author
        ).exclude(id__in=follow_list_before).exists())

    def test_new_post_appearing_in_following_feed(self):
        """Новый пост пользователя not_author появится в ленте подписанного
        на него пользователя author"""
        posts_before_posting = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk
        }
        self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.filter(
            text='Тестовый новый пост',
            group=self.group.pk,
            author=self.user_not_author
        ).exclude(id__in=posts_before_posting).get()
        response = self.authorized_author_client.get(reverse(
            'posts:follow_index'
        ))
        posts_follow_list_after = response.context['page_obj']
        self.assertIn(new_post, posts_follow_list_after)

    def test_new_post_not_appearing_in_not_following_feed(self):
        """Новый пост пользователя author появится в ленте не подписанного
        на него пользователя not_author"""
        posts_before_posting = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk
        }
        self.authorized_author_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.filter(
            text='Тестовый новый пост',
            group=self.group.pk,
            author=self.user_author
        ).exclude(id__in=posts_before_posting).get()
        response = self.authorized_client.get(reverse(
            'posts:follow_index'
        ))
        posts_follow_list_after = response.context['page_obj']
        self.assertNotIn(new_post, posts_follow_list_after)

    def test_inability_follow_yourself(self):
        followers_count_before = Follow.objects.filter(
            user=self.user_not_author).count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': 'not_author'})
        )
        followers_count_after = Follow.objects.filter(
            user=self.user_not_author).count()
        self.assertEqual(followers_count_before, followers_count_after)
