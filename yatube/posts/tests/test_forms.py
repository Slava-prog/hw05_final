from django.test import Client, TestCase
from django.urls import reverse
from django.shortcuts import get_object_or_404

from posts.forms import PostForm
from posts.models import Post, Group, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание1',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
        )

        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_id_list = Post.objects.values_list("id", flat=True)
        form_data = {
            'text': 'Тестовый текст1 с колвом символов более 15',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        for id in post_id_list:
            post_list_new = Post.objects.exclude(id=id)
        self.assertEqual(post_list_new.count(), 1)
        post1 = post_list_new[0]
        field_verboses = {
            post1.text: form_data['text'],
            post1.group.id: form_data['group']
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user}))

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group1.id
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = get_object_or_404(Post, id=self.post.id)
        self.assertEqual(Post.objects.count(), post_count)
        field_verboses = {
            post.text: form_data['text'],
            post.group.id: form_data['group'],
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
