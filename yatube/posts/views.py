from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Follow
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm

NUMBER_OF_POSTS_ON_PAGE = 10


def get_page_obj(post_list, NUMBER_OF_POSTS_ON_PAGE, request):
    paginator = Paginator(post_list, NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group')
    page_obj = get_page_obj(post_list, NUMBER_OF_POSTS_ON_PAGE, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_list(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_obj = get_page_obj(post_list, NUMBER_OF_POSTS_ON_PAGE, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    #
    post_list = author.posts.all()
    page_obj = get_page_obj(post_list, NUMBER_OF_POSTS_ON_PAGE, request)
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=request.user)
        context = {
            'page_obj': page_obj,
            'author': author,
            'following': Follow.objects.filter(
                user=user, author=author).exists(),
        }
        return render(request, template, context)
    context = {
        'page_obj': page_obj,
        'author': author,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    old_post = get_object_or_404(Post, pk=post_id)
    if request.user != old_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        instance=old_post,
        files=request.FILES or None
    )
    context = {
        'form': form,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follower = get_object_or_404(User, username=request.user)
    post_list = Post.objects.filter(
        author__following__user=follower).exclude(author=follower)
    page_obj = get_page_obj(post_list, NUMBER_OF_POSTS_ON_PAGE, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if author != user and not Follow.objects.filter(user=user, author=author).exists():
        Follow.objects.create(
            user=user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=user,
        author=author,
    ).delete()
    return render(request, 'posts/follow.html')
