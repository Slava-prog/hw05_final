import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.forms import PostForm
from posts.models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание1',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=cls.small_gif,
            content_type='image/gif'
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
        uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст1 с колвом символов более 15',
            'group': self.group.id,
            'image': uploaded
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
            post1.group.id: form_data['group'],
            post1.image.name: f"posts/{form_data['image'].name}"
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user}))

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='test_image1.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group1.id,
            'image': uploaded
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
            post.image.name: f"posts/{form_data['image'].name}"
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)

    def test_create_comment(self):
        """Валидная форма создает комментарий к посту."""
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Test_comment',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), 1)
        comment = Comment.objects.filter(post=self.post).first()
        self.assertEqual(comment.text, form_data['text'])
