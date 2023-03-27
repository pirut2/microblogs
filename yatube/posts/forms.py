from django import forms
from .models import Post, Comment
from django.utils.translation import gettext_lazy as ola


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ola('Текст'),
            'group': ola('Группа'),
        }
        help_texts = {
            'text': ola('Запишите свои мысли в этом поле *^*'),
        }

    def clean_subject(self):
        data = self.cleaned_data['subject']
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {'text', }
        labels = {
            'author': ola('Текст'),
            'text': ola('Группа'),
            'created': ola('Дата публикации')
        }
        help_texts = {
            'text': ola('Запишите свои мысли в этом поле *^*'),
        }
