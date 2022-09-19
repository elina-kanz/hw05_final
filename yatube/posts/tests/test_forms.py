import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, User, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-group-slug-1',
            description='Тестовое описание 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 0',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        pass

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_before_posting = list(Post.objects.values_list('id', flat=True))
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
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'image': uploaded,
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                group=self.group.pk,
                author=self.user,
                image='posts/small.gif',
            ).exclude(id__in=posts_before_posting).exists()
        )

    def test_edit_post(self):
        """Валидная форма меняет запись Post, post_id остается тот же."""
        form_new_data = {
            'text': 'Тестовый текст 2',
            'group': self.group_1.pk,
        }
        old_text = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk})).context['form'].instance.text
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}), data=form_new_data, follow=True
        )
        new_text = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk})).context['form'].instance.text
        new_list_posts_group = list(Post.objects.filter(
            group=self.group).values_list('id', flat=True))
        list_posts_group_1 = list(Post.objects.filter(
            group=self.group_1).values_list('id', flat=True))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertNotEqual(new_text, old_text)
        self.assertNotIn(self.post.pk, new_list_posts_group)
        self.assertIn(self.post.pk, list_posts_group_1)
