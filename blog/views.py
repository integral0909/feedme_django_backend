from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from common.utils import paginate
from blog.models import Post


def display_post(request, slug):
    p = get_object_or_404(Post, slug=slug)
    return render(request, 'blog_post.html', {'post': p})


def list_posts(request):
    paginator = Paginator(Post.objects.all().order_by('-id'), 100)
    items = paginate(paginator, request.GET.get('page'))
    return render(request, 'blog_list.html', {'posts': items})
