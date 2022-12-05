from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост более 15 символов',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверяем, что корректно работает cashe на главной странице."""
        response = self.authorized_client.get(reverse('posts:first'))
        post_list = response.content
        Post.objects.filter(id=self.post.id).delete()
        response = self.authorized_client.get(reverse('posts:first'))
        post_list1 = response.content
        cache.clear()
        response = self.authorized_client.get(reverse('posts:first'))
        post_list2 = response.content
        self.assertEqual(post_list, post_list1)
        self.assertNotEqual(post_list, post_list2)
