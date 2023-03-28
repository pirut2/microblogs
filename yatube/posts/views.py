from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Follow
from django.core.paginator import Paginator
from .consts import PAGINATOR_CONST
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = f'Это страница сообщества {group}.'
    context = {
        'title': title,
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author__username=username)
    post_count = posts_list.filter(author__username=username).count()
    paginator = Paginator(posts_list, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    follow_one = Follow.objects.filter(
        user=request.user.id, author=author.id).exists()
    if follow_one is True:
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'author': author,
        'post_count': post_count,
        'username': username,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_one = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.filter(author=post_one.author).count()
    form = CommentForm(files=request.FILES or None)
    comments = post_one.comments.all()
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'post_one': post_one,
        'post_count': post_count,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if not form.is_valid():
            return render(request, 'posts/create_post.html', {'form': form})
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    form = PostForm(files=request.FILES or None)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    required_post = get_object_or_404(Post, pk=post_id)
    if request.user.id != required_post.author.id:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST, instance=required_post,
                    files=request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=required_post.id)
    form = PostForm(instance=required_post, files=request.FILES or None)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


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
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Лента подписок'
    context = {
        'page_obj': page_obj,
        'title': title
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    test = Follow.objects.filter(user=request.user.id,
                                 author=author).exists()
    if request.user != author and test is False:
        Follow.objects.create(user=request.user, author=author)
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username)
