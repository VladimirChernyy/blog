from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Post, Group, User
from ..tests.constants import (
    AUTHOR_USERNAME,
    USER_USERNAME,
    GROUP_TITLE,
    GROUP_SLUG,
    GROUP_DESCRIPTION,
    POST_TEXT,
    INDEX_TEMPLATE,
    GROUP_LIST_TEMPLATE,
    PROFILE_TEMPLATE,
    POST_DETAIL_TEMPLATE,
    CREATE_POST,
)


class PostURLTest(TestCase):
    author = None

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
        )

    def setUp(self):
        self.user = User.objects.create_user(username=USER_USERNAME)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.post.author)

    def test_urls_uses_correct_template_guest(self):
        templates_url_names = {
            '/': INDEX_TEMPLATE,
            f'/group/{self.group.slug}/': GROUP_LIST_TEMPLATE,
            f'/profile/{self.user}/': PROFILE_TEMPLATE,
            f'/posts/{self.post.id}/': POST_DETAIL_TEMPLATE,
            f'/posts/{self.post.id}/edit/': CREATE_POST,
            '/create/': CREATE_POST,
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response_author = self.authorized_client_author.get(address)
                self.assertEqual(response_author.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response_author, template)

    def test_url_create_post_guest(self):
        address_edit_post = f'/posts/{self.post.id}/edit/'
        response = self.guest_client.get(
            address_edit_post
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_create_post_redirect_user(self):
        address_edit_post = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(
            address_edit_post
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_create_post_redirect_guest(self):
        address_edit_post = f'/posts/{self.post.id}/edit/'
        response = self.guest_client.get(
            address_edit_post
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_url_create_post_redirect_user(self):
        address_edit_post = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(
            address_edit_post
        )
        self.assertRedirects(
            response, f'/profile/{self.user}/'
        )
