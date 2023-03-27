import shutil
import tempfile

from ..models import Post, Group, User, Comment
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

POST_AUTH = 'auth'
POST_TEXT = 'Тестовый пост'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'slug'
GROUP_DESCRIPTION = 'Тестовое описание'
COMMENT_TEXT = 'Текст комментария'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=POST_AUTH)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text=COMMENT_TEXT,
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
    def setUp(self):
        self.guest_client = Client()
        self.user_not_author = User.objects.create_user(username='qwerty')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_author)
        self.user = self.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.image = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_post_create_author(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост - новый текст',
            'group': self.group.pk,
            'image': self.image,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.first())

    def test_form_post_edit_author(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост - новый текст 2',
            'group': self.group.pk,
            'image': self.image,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(Post.objects.first())

    def test_form_post_edit_guest(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост - новый текст',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_form_post_edit_guest(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост - новый текст 2',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:login')
                             + f'?next=/posts/{self.post.pk}/edit/')
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text='Новый пост - новый текст 2',
                group=self.group.pk
            ).exists()
        )

    def test_form_post_edit_autorized(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост - новый текст 2',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text='Новый пост - новый текст 2',
                group=self.group.pk
            ).exists()
        )

    def test_comments_guest_not_add(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(response, reverse('users:login')
                             + f'?next=/posts/{self.post.pk}/comment/')

    def test_comments_authorized_add(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.authorized_client_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.pk}))
