from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.core.paginator import Page
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User, Follow
from posts.tests import constants

TEST_PAGINATOR_PAGE = 10


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(
            username=constants.AUTHOR_USERNAME
        )

        cls.group = Group.objects.create(
            title=constants.GROUP_TITLE,
            slug=constants.GROUP_SLUG,
            description=constants.GROUP_DESCRIPTION,
        )

    def setUp(self):
        self.user = User.objects.create_user(username=constants.USER_USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)
        self.post = Post.objects.create(
            text=constants.POST_TEXT,
            author=self.author,
            group=self.group,
        )
        cache.clear()

    def test_views_template(self):
        templates_url_names = {
            constants.INDEX_URL_NAME: ({}, constants.INDEX_TEMPLATE),
            constants.GROUP_LIST_URL_NAME:
                ({'slug': self.group.slug}, constants.GROUP_LIST_TEMPLATE),
            constants.PROFILE_URL_NAME:
                ({'username': self.author}, constants.PROFILE_TEMPLATE),
            constants.POST_DETAIL_URL_NAME:
                ({'post_id': self.group.pk}, constants.POST_DETAIL_TEMPLATE),
            constants.POST_EDIT_URL_NAME:
                ({'post_id': self.group.pk}, constants.CREATE_POST),
            constants.POST_CREATE_URL_NAME: ({}, constants.CREATE_POST),
        }
        for url, params in templates_url_names.items():
            with self.subTest(url=url):
                kwargs, template = params
                response = self.authorized_client_author.get(
                    reverse(url, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_context_index_image(self):
        response = self.authorized_client_author.get(
            reverse(constants.INDEX_URL_NAME)
        )
        context = ('title', 'heading', 'page_obj')
        for key in context:
            self.assertIn(key, context)
        response_index = response.context['page_obj'].object_list[0]
        self.assertEqual(response_index.image, self.post.image)

    def test_context_group_list(self):
        response = self.authorized_client_author.get(
            reverse(constants.GROUP_LIST_URL_NAME,
                    kwargs={'slug': self.group.slug}
                    ))
        context = ('page_obj', 'group')
        for key in context:
            self.assertIn(key, response.context)
        response_list = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_list, self.post)
        self.assertEqual(response_list.image, self.post.image)

    def test_context_profile(self):
        response = self.authorized_client_author.get(
            reverse(constants.PROFILE_URL_NAME,
                    kwargs={'username': self.author}
                    ))
        context = ('author', 'post_count', 'title', 'page_obj')
        for key in context:
            self.assertIn(key, response.context)
        response_profile = response.context.get('page_obj').object_list[0]
        self.assertEqual(response_profile, self.post)
        self.assertEqual(response_profile.image, self.post.image)

    def test_context_post_detail(self):
        response = self.authorized_client_author.get(
            reverse(constants.POST_DETAIL_URL_NAME,
                    kwargs={'post_id': self.post.id}
                    ))
        context = ('post', 'posts')
        for key in context:
            self.assertIn(key, response.context)
        response_post_detail = response.context.get('post')
        self.assertEqual(
            response_post_detail.author.username,
            constants.AUTHOR_USERNAME
        )
        self.assertEqual(
            response_post_detail.text,
            constants.POST_TEXT
        )
        self.assertEqual(
            response_post_detail.group.title,
            constants.GROUP_TITLE
        )
        self.assertEqual(response_post_detail.image, self.post.image)

    def test_context_post_edit(self):
        response = self.authorized_client_author.get(
            reverse(
                constants.POST_EDIT_URL_NAME,
                kwargs={'post_id': self.post.id}
            )
        )
        context = ('is_edit', 'form')
        for key in context:
            self.assertIn(key, response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_context_post_create(self):
        response = self.authorized_client_author.get(
            reverse(constants.POST_CREATE_URL_NAME)
        )
        context = ('form',)
        for key in context:
            self.assertIn(key, response.context)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_post_add_index(self):
        response_index = self.authorized_client_author.get(
            reverse(constants.INDEX_URL_NAME)
        )
        index = response_index.context['page_obj']
        self.assertIn(self.post, index, 'поста нет на главной')

    def test_post_add_group(self):
        response_group = self.authorized_client_author.get(
            reverse(
                constants.GROUP_LIST_URL_NAME,
                kwargs={'slug': self.group.slug}
            )
        )
        group = response_group.context['page_obj']
        self.assertIn(self.post, group, 'поста нет в группе')

    def test_post_add_profile(self):
        response_profile = self.authorized_client_author.get(reverse(
            constants.PROFILE_URL_NAME, kwargs={'username': self.author})
        )
        profile = response_profile.context['page_obj']
        self.assertIn(self.post, profile, 'поста нет в профиле')

    def test_cache_index(self):
        response = self.authorized_client_author.get(
            reverse(constants.INDEX_URL_NAME)
        )
        content = response.content
        self.post.delete()
        response_2 = self.authorized_client_author.get(
            reverse(constants.INDEX_URL_NAME)
        )
        content_cache = response_2.content
        self.assertEqual(content, content_cache)
        cache.clear()
        response_3 = self.authorized_client_author.get(
            reverse(constants.INDEX_URL_NAME)
        )
        cache_clear = response_3.content
        self.assertNotEqual(content, cache_clear)

    def test_follow_index_context(self):
        response = self.authorized_client.get(
            reverse(constants.POST_FOLLOW_INDEX_URL_NAME)
        )
        context = ('page_obj', 'title')
        for key in context:
            self.assertIn(key, response.context)

    def test_follow_author(self):
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                constants.POST_PROFILE_FOLLOW_URL_NAME,
                args={self.author}
            )
        )
        follow_id = Follow.objects.latest('id')
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow_id.author, self.author)
        self.assertEqual(follow_id.user, self.user)

    def test_unfollow_author(self):
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                constants.POST_PROFILE_FOLLOW_URL_NAME,
                args={self.author}
            )
        )

        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.get(
            reverse(
                constants.POST_PROFILE_UNFOLLOW_URL_NAME,
                args={self.author}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_add_new_post_follower(self):
        self.authorized_client.get(
            reverse(constants.POST_PROFILE_FOLLOW_URL_NAME, args={self.author})
        )
        response = self.authorized_client.get(
            reverse(constants.POST_FOLLOW_INDEX_URL_NAME)
        )
        print(response.context)
        new_post = response.context['page_obj'][0]
        self.assertEqual(new_post, self.post)

    def test_add_new_post_unfollower(self):
        count = Follow.objects.count()
        new_user = User.objects.create_user(username='TestFollowerUser')
        self.authorized_client.force_login(new_user)
        Post.objects.create(
            text='TestFollowerText',
            author=new_user,
        )
        self.authorized_client.get(
            reverse(
                constants.POST_FOLLOW_INDEX_URL_NAME
            )
        )
        self.assertEqual(Follow.objects.count(), count)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(
            username=constants.AUTHOR_USERNAME
        )
        cls.group = Group.objects.create(
            title=constants.GROUP_TITLE,
            slug=constants.GROUP_SLUG,
            description=constants.GROUP_DESCRIPTION,
        )
        Post.objects.bulk_create(
            [
                Post(
                    text=f'{constants.POST_TEXT} {i}', author=cls.author,
                    group=cls.group
                ) for i in range(TEST_PAGINATOR_PAGE + 3)
            ]
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text=constants.POST_TEXT,
            author=self.author,
            group=self.group,
        )
        cache.clear()

    def test_paginator(self):
        url_name = {
            constants.INDEX_URL_NAME: (
                {},
                Post.objects.all()[:TEST_PAGINATOR_PAGE],
            ),
            constants.GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug},
                self.group.posts.all()[:TEST_PAGINATOR_PAGE],
            ),
            constants.PROFILE_URL_NAME: (
                {'username': self.author.username},
                self.author.posts.all()[:TEST_PAGINATOR_PAGE],
            ),
        }
        for url, params in url_name.items():
            kwargs, queryset = params
            with self.subTest(url=url):
                response = self.client.get(reverse(url, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context['page_obj']
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, transform=lambda x: x
                )
