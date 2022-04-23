from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow, Likes
from .forms import PostForm, CommentForm


def paginator(queryset, request):
    paginator = Paginator(queryset, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }


def index(request):
    posts = Post.objects.select_related('author', 'group').all()
    context = paginator(posts, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(paginator(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group').all()
    user = request.user
    following = (user.is_authenticated
                 and Follow.objects.filter(user=user, author=author).exists())

    context = {
        'author': author,
        'following': following
    }
    context.update(paginator(posts, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count()
    comments = post.comments.all()
    user = request.user
    liked = (user.is_authenticated
             and Likes.objects.filter(user=user, post=post).exists())
    form = CommentForm()
    context = {
        'post': post,
        'posts_count': posts_count,
        'comments': comments,
        'liked': liked,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request,
                  'posts/create_post.html', {'form': form,
                                             'is_edit': True,
                                             'post_id': post_id})


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
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    context = paginator(posts, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = request.user
    if request.user == author:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=follower, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.author:
        return redirect('posts:post_detail', post_id=post_id)
    liker = request.user
    Likes.objects.create(user=liker, post=post)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def dislike(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Likes.objects.filter(user=request.user, post=post).delete()
    return redirect('posts:post_detail', post_id=post_id)
