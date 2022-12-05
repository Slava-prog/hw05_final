from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User, Follow


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
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
        self.authorized_client1 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_follow_add_delete(self):
        """Авторизованный пользователь может подписываться
            на других пользователей и удалять их из подписок."""
        follow_count = Follow.objects.count()
        self.authorized_client1.post(
            f'/profile/{self.post.author.username}/follow/')
        follow_count_add = Follow.objects.count()
        self.authorized_client1.post(
            f'/profile/{self.post.author.username}/unfollow/')
        follow_count_del = Follow.objects.count()
        self.assertEqual(follow_count_add, (follow_count + 1))
        self.assertEqual(follow_count_del, follow_count)

    def test_follow_index_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
            подписан и не появляется в ленте тех, кто не подписан."""
        self.authorized_client2.post(
            f'/profile/{self.post.author.username}/follow/')
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        post_list = response.context['page_obj']
        self.assertNotIn(post, post_list)
