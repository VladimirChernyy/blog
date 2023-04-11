import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment
from ..tests.constants import (
    AUTHOR_USERNAME,
    GROUP_TITLE,
    GROUP_SLUG,
    GROUP_DESCRIPTION,
    POST_TEXT,
    POST_EDIT_URL_NAME,
    POST_CREATE_URL_NAME,
    COMMENT_TEXT,
    POST_COMMENT_URL_NAME,
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=POST_TEXT,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text=COMMENT_TEXT,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_create_post(self):
        post_count = Post.objects.count()

        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
        }
        self.authorized_client_author.post(reverse(POST_CREATE_URL_NAME),
                                           data=form_data,
                                           follow=True,
                                           )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_create_post_guest(self):
        post_count = Post.objects.count()
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
        }
        response = self.client.post(reverse(POST_CREATE_URL_NAME),
                                    data=form_data,
                                    follow=True,
                                    )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_author(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'POST_TEXT',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client_author.post(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Post.objects.filter(
                text='POST_TEXT',
                group=self.group.id,
                image='posts/small.gif',
            ).exists()
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_post_edit_no_valid(self):
        form_data = {
            'text': '',
            'group': self.group.id,
        }
        response = self.authorized_client_author.post(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertFormError(response, 'post', 'text', None)

    def test_add_comment_user(self):
        comment = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.authorized_client_author.post(
            reverse(POST_COMMENT_URL_NAME, kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=COMMENT_TEXT,
            )
        )
