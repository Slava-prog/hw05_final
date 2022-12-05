from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import pager_list
from posts.constants import VIEW_LIST_COUNT_OF_PAGINATOR as VIEW_LIST


@cache_page(20, key_prefix='index_page')
def index(request):
    '''Вьювс главной страницы: постранично по десять публикаций.'''
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group')
    page_obj = pager_list(request, post_list, VIEW_LIST)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    '''Вьювс групп: постранично по десять публикаций группы.'''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.select_related('author'
                                            ).filter(group=group)
    page_obj = pager_list(request, post_list, VIEW_LIST)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    '''Вьювс автора: постранично по десять публикаций.'''
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        for follow in request.user.follower.all():
            if author == follow.author:
                following = True
    post_list = author.posts.all()
    page_obj = pager_list(request, post_list, VIEW_LIST)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    '''Вьювс публикации.'''
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }

    return render(request, template, context)


@login_required
def post_create(request):
    '''Вьювс создание нового поста.'''
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', post.author)
    context = {
        'form': form,
    }

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    '''Вьювс редактирование поста.'''
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    is_edit = True
    if author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        cache.clear()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': is_edit,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    '''Вьювс добавления комментария'''
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        cache.clear()

    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    '''Посты, на которых подписан пользователь:
        постранично по десять публикаций.'''
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = pager_list(request, post_list, VIEW_LIST)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user == author:
        return redirect('posts:profile', author.username)
    for follow in request.user.follower.all():
        if author == follow.author:
            return redirect('posts:profile', author.username)
    Follow.objects.create(author=author, user=user)

    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(author=author, user=user).delete()

    return redirect('posts:profile', author.username)
