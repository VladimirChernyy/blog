from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow

POST_COUNT = 10
CACHE_TIME = 20


@cache_page(CACHE_TIME)
def index(request):
    posts = Post.objects.select_related('group', 'author').all()
    paginator = Paginator(posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'heading': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user_posts = Post.objects.filter(author__username=username)
    post_count = user_posts.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    template = 'posts/profile.html'
    title = f'Профиль пользователя {author}.'
    context = {
        'author': author,
        'post_count': post_count,
        'title': title,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts = post.author.posts.all()
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'posts': posts,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=True)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template = 'posts/create_post.html'
    if request.user != post.author:
        return redirect('posts:profile', username=request.user)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'is_edit': True,
        'form': form,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Посты авторов'
    context = {
        'page_obj': page_obj,
        'title': title
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(Follow, user=request.user,
                             author__username=username)
    user.delete()
    return redirect('posts:profile', username=username)
