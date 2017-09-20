from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from common.utils import paginate
from blog.models import Post


def display_post(request, slug):
    p = get_object_or_404(Post, slug=slug)
    extract = p.content.split('.')[:3]
    extract = '%s.' % '.'.join(extract)
    return render(request, 'blog_post.html', {
        'post': p, 'meta_description': extract, 'meta_img': p.image_url,
        'page_title': ' | %s' % p.title,
        'meta_keywords': ', '.join((m.tag for m in p.metatags.all()))
    })


def list_posts(request):
    paginator = Paginator(Post.objects.all().order_by('-id'), 100)
    items = paginate(paginator, request.GET.get('page'))
    return render(request, 'blog_list.html', {'posts': items})
