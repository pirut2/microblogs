from django.test import TestCase
from ..models import Group, Post, User

POST_AUTH = 'auth'
POST_TEXT = 'Тестовый пост'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'Тестовый слаг'
GROUP_DESCRIPTION = 'Тестовое описание'


class PostModelTest(TestCase):
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

    def test_models_have_correct_object_names_group(self):
        """Проверяем, что у модели group корректно работает __str__."""
        task = PostModelTest.group
        expected_object_name = task.title
        self.assertEqual(expected_object_name, str(task))

    def test_models_have_correct_object_names_post(self):
        """Проверяем, что у модели post корректно работает __str__."""
        task = PostModelTest.post
        expected_object_name = task.text[:15]
        self.assertEqual(expected_object_name, str(task))

    def test_verbose_name(self):
        task = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        task = PostModelTest.post
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text, expected_value)
