from django.shortcuts import render
from blog.models import Post


def display_post(request, slug):
    p = Post.objects.get(slug=slug)
    return render(request, 'blog_post.html', {'post': p})
