import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from ..models import Post, Group, User, Comment, Follow
from django.urls import reverse
from django import forms
from ..consts import PAGINATOR_CONST
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


POST_AUTH = 'auth'
POST_TEXT = 'Тестовый пост'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'slug'
GROUP_DESCRIPTION = 'Тестовое описание'
COMMENT_TEXT = 'Текст комментария'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif')
        cls.user = User.objects.create_user(username=POST_AUTH)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        for _ in range(PAGINATOR_CONST + 1):
            cls.post = Post.objects.create(
                author=cls.user,
                text=POST_TEXT,
                group=cls.group,
                image=cls.image
            )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text=COMMENT_TEXT,
        )
        cls.url_address_map = {
            'index': reverse('posts:index'),
            'group_posts': reverse('posts:group_posts',
                                   kwargs={'slug': TaskViewsTests.group.slug}),
            'profile': reverse('posts:profile',
                               kwargs={'username':
                                       TaskViewsTests.post.author}),
            'detail': reverse('posts:post_detail',
                              kwargs={'post_id': TaskViewsTests.post.id}),
            'edit': reverse('posts:post_edit',
                            kwargs={'post_id': TaskViewsTests.post.id}),
            'create': reverse('posts:post_create'),
        }
        cls.url_template_map = {
            cls.url_address_map['index']: 'posts/index.html',
            cls.url_address_map['group_posts']: 'posts/group_list.html',
            cls.url_address_map['profile']: 'posts/profile.html',
            cls.url_address_map['detail']: 'posts/post_detail.html',
            cls.url_address_map['edit']: 'posts/create_post.html',
            cls.url_address_map['create']: 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user_not_author = User.objects.create_user(username='qwerty')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_not_author)
        self.user_not_author_2 = User.objects.create_user(username='qwerty2')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_not_author_2)
        self.user = self.post.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_pages_uses_correct_template(self):
        for reverse_name, template in self.url_template_map.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_page_paginator(self):
        response_1 = self.authorized_client_author.get(self.url_address_map
                                                       ['index'])
        self.assertEqual(len(response_1.context['page_obj']), PAGINATOR_CONST)
        response_2 = self.authorized_client_author.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response_2.context['page_obj']), 1)

    def test_group_page_paginator(self):
        response_1 = self.authorized_client_author.get(self.url_address_map
                                                       ['group_posts'])
        self.assertEqual(len(response_1.context['page_obj']), PAGINATOR_CONST)
        response_2 = self.authorized_client_author.get(reverse(
            'posts:group_posts',
            kwargs={'slug': TaskViewsTests.group.slug}) + '?page=2')
        self.assertEqual(len(response_2.context['page_obj']), 1)

    def test_profile_page_paginator(self):
        response_1 = self.authorized_client_author.get(self.url_address_map
                                                       ['profile'])
        self.assertEqual(len(response_1.context['page_obj']), PAGINATOR_CONST)
        response_2 = self.authorized_client_author.get(reverse(
            'posts:profile',
            kwargs={'username': TaskViewsTests.post.author}) + '?page=2')
        self.assertEqual(len(response_2.context['page_obj']), 1)

    def test_index_context(self):
        response = self.authorized_client_author.get(self.url_address_map
                                                     ['index'])
        first_object = response.context['page_obj'][0]
        task_author_0 = first_object.author
        task_text_0 = first_object.text
        task_group_0 = first_object.group
        task_image_0 = first_object.image
        self.assertEqual(task_author_0, TaskViewsTests.post.author)
        self.assertEqual(task_text_0, TaskViewsTests.post.text)
        self.assertEqual(task_group_0, TaskViewsTests.post.group)
        self.assertEqual(task_image_0, self.post.image)

    def test_group_context(self):
        response = self.authorized_client_author.get(
            self.url_address_map['group_posts'])
        first_group = response.context['group']
        first_object = response.context['page_obj'][0]
        task_image_0 = first_object.image
        self.assertEqual(first_group.pk, TaskViewsTests.post.group_id)
        self.assertEqual(task_image_0, self.post.image)

    def test_profile_context(self):
        response = self.authorized_client_author.get(
            self.url_address_map['profile'])
        first_author = response.context['author']
        first_object = response.context['page_obj'][0]
        task_image_0 = first_object.image
        self.assertEqual(first_author, TaskViewsTests.post.author)
        self.assertEqual(task_image_0, self.post.image)

    def test_post_detail_context(self):
        response = self.authorized_client_author.get(
            self.url_address_map['detail'])
        one_post = response.context['post_one']
        one_comment = response.context['comments'][0]
        task_image_0 = one_post.image
        task_comments = one_comment.post
        self.assertEqual(one_post.pk, TaskViewsTests.post.pk)
        self.assertEqual(task_image_0, TaskViewsTests.post.image)
        self.assertEqual(task_comments, one_post)

    def test_create_post_context(self):
        response = self.authorized_client_author.get(
            self.url_address_map['create'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_context(self):
        response = self.authorized_client_author.get(
            self.url_address_map['edit'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_is_edit_context_in_create_and_edit(self):
        response_1 = self.authorized_client_author.get(
            self.url_address_map['create'])
        response_2 = self.authorized_client_author.get(
            self.url_address_map['edit'])
        is_edit_create = response_1.context['is_edit']
        is_edit_edit = response_2.context['is_edit']
        self.assertEqual(is_edit_create, False)
        self.assertEqual(is_edit_edit, True)

    def test_index_cache(self):
        response = self.authorized_client_author.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='tyuio',
            author=self.user,
        )
        response_old = self.authorized_client_author.get(
            reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client_author.get(
            reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_following(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': TaskViewsTests.post.author}))
        self.assertEqual(Follow.objects.count(), 1)

    def test_following_author(self):
        self.authorized_client_author.get(
            reverse('posts:profile_follow',
                    kwargs={'username': TaskViewsTests.post.author}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_unfollowing(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': TaskViewsTests.post.author}))
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': TaskViewsTests.post.author}))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_index(self):
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': TaskViewsTests.post.author}))
        response_1 = self.authorized_client.get(
            reverse('posts:follow_index'))
        response_2 = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertEqual(response_1.context['page_obj'][0], self.post)
        self.assertNotEqual(response_2.context['page_obj'], self.post)
