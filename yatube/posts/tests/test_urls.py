from django.test import TestCase, Client
from ..models import Post, Group, User
from http import HTTPStatus

POST_AUTH = 'auth'
POST_TEXT = 'Тестовый пост'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'slug'
GROUP_DESCRIPTION = 'Тестовое описание'


class TaskURLTests(TestCase):
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
        )
        cls.access_dict = {
            '/': 'all',
            f'/group/{cls.group.slug}/': 'all',
            f'/profile/{cls.post.author}/': 'all',
            f'/posts/{cls.post.pk}/': 'all',
            f'/posts/{cls.post.pk}/edit/': 'author',
            '/create/': 'authorized',
            '/follow/': 'authorized',
        }
        cls.template_dict = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user_not_author = User.objects.create_user(username='qwerty')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_author)
        self.user = self.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_url_access_for_all(self):
        for address, access, in self.access_dict.items():
            if access == 'all':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_authorized(self):
        for address, access, in self.access_dict.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_access_for_author(self):
        for address, access, in self.access_dict.items():
            if access == 'author':
                with self.subTest(address=address):
                    response = self.authorized_client_author.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates(self):
        for address, templates, in self.template_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, templates)

    def test_url_404(self):
        response_author = self.authorized_client_author.get(
            '/unexisting_page/')
        self.assertEqual(response_author.status_code, HTTPStatus.NOT_FOUND)

    def test_template_404(self):
        response_author = self.authorized_client_author.get(
            '/unexisting_page/')
        self.assertTemplateUsed(response_author, 'core/404.html')

    def test_url_comment_redirect(self):
        response_author = self.authorized_client_author.get(
            f'/posts/{self.post.pk}/comment/')
        self.assertEqual(response_author.status_code, HTTPStatus.FOUND)
