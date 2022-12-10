from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Автор')
        cls.user1 = User.objects.create_user(username='Автор1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client1.force_login(self.user1)

    def test_guest_client_urls(self):
        """Страницы доступна любому пользователю."""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/',
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                error_acces = f'address{address}, dont have access'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_post_create_post_edit_url(self):
        """Страницы доступны авторизованному пользователю."""
        url_names = (
            '/create/',
            f'/posts/{self.post.id}/comment/',
            f'/posts/{self.post.id}/edit/'
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                error_acces = f'address{address}, dont have access'
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    error_acces
                )

    def test_post_edit_url_redirect_anonymous(self):
        """Страницы перенаправляют неавтаризованного пользователя."""
        url_names = {
            f'/posts/{self.post.id}/edit/': reverse(
                'users:login') + '?next=' + reverse(
                    'posts:post_edit', kwargs={'post_id': self.post.id}),
            f'/posts/{self.post.id}/comment/': reverse(
                'users:login') + '?next=' + reverse(
                    'posts:add_comment', kwargs={'post_id': self.post.id}),
            '/create/': reverse('users:login') + '?next=' + reverse(
                    'posts:post_create')
        }
        for address, reverse_name in url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(response, reverse_name)

    def test_post_edit_url_redirect_not_athor(self):
        """Страница posts/<post_id>/edit/ перенаправление неавтора."""
        response = self.authorized_client1.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, (f'/posts/{self.post.id}/'))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Несуществующая страница."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
