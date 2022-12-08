import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post, Group, User
from posts.forms import PostForm, CommentForm
from posts.constants import VIEW_LIST_COUNT_OF_PAGINATOR as VIEW_LIST
from posts.constants import POSTS_COUNT_FOR_TEST as POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
            image=cls.uploaded
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def context_testing(self, post, *args):
        post_testing_parameters = {
            post.author.username: self.post.author.username,
            post.text: self.post.text,
            post.group.title: self.post.group.title,
            post.id: self.post.id,
            post.image: self.post.image
        }
        for new_parameter, parameter in post_testing_parameters.items():
            with self.subTest(new_parameter=new_parameter):
                self.assertEqual(new_parameter, parameter)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:first'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:profile', kwargs={
                'username': self.user}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:first'))
        post = response.context['page_obj'][0]
        self.context_testing(post, self)

    def test_group_posts_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': self.group.slug}))
        group = (response.context['group'])
        self.assertEqual(group.title, self.post.group.title)
        post = response.context['page_obj'][0]
        self.context_testing(post, self)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={
                'username': self.user}))
        author = response.context['author']
        post = response.context['page_obj'][0]
        self.context_testing(post, self)
        self.assertEqual(author.username, self.post.author.username)
        following = response.context['following']
        self.assertEqual(following, self.user.follower.filter(
            author=author).exists())

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={
                'post_id': self.post.id}))
        post = response.context['post']
        self.context_testing(post, self)
        self.assertEqual(post.id, self.post.id)
        self.assertIsInstance(response.context.get('form'), CommentForm)

    def test_create_post_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_create_post_correct_context_to_index_group_profile(self):
        """При создании пост попадает на первую позицию на главной странице,
            в группе и профиле."""
        post = Post.objects.create(
            text='Тестовый текст на первой позиции',
            group=self.group,
            author=self.user,
        )
        pages_fields = [
            reverse('posts:first'),
            reverse('posts:group_list', kwargs={'slug': post.group.slug}),
            reverse('posts:profile', kwargs={
                'username': post.author.username})
        ]
        for value in pages_fields:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                post1 = response.context['page_obj'][0]
                self.assertEqual(post, post1)

    def test_create_not_in_other_group_list(self):
        """При создании пост попадает не попадает в чужую группу."""
        group_new = Group.objects.create(
            title='Тестовая группа создания',
            slug='test_slug_new',
            description='Тестовое описание',
        )
        post = Post.objects.create(
            text='Тестовый текст другой группы',
            group=group_new,
            author=self.user,
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertNotIn(post, response.context['page_obj'])

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            follow=True
        )
        form_field = response.context.get('form').instance
        field_verboses = {
            form_field.text: self.post.text,
            form_field.group: self.post.group,
            form_field.image: self.post.image
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
        post = response.context.get('post')
        self.assertEqual(post.id, self.post.id)
        self.assertTrue(response.context.get('is_edit'))


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(POSTS):
            cls.post = Post.objects.create(
                text=f'Тестовый текст_{i}',
                group=cls.group,
                author=cls.user,
            )

    def test_first_page_index_contains_ten_records(self):
        '''Количество постов на первой странице равно 10.'''
        field_verboses = {
            reverse('posts:first'): VIEW_LIST,
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): VIEW_LIST,
            reverse('posts:profile', kwargs={
                'username': self.user}): VIEW_LIST
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                response = self.client.get(value)
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_index_contains_three_records(self):
        '''Количество постов на второй странице: 3'''
        field_verboses = {
            reverse('posts:first'): (POSTS - VIEW_LIST),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): (POSTS - VIEW_LIST),
            reverse('posts:profile', kwargs={
                'username': self.user}): (POSTS - VIEW_LIST)
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_unexisting_page_to_castom_page(self):
        """Cтраница 404 отдаёт кастомный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
