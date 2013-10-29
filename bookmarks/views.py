# -*- coding: utf-8 -*-
#  Create your views here.

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from bookmarks.forms import *
from bookmarks.models import *
import sys


def main_page(request):
    print >> sys.stderr, 'Goodbye, cruel world!'
    return render_to_response(
        'main_page.html', RequestContext(request)
    )


def user_page(request, username):
    user = get_object_or_404(User, username=username)
    bookmarks = user.bookmark_set.order_by('-id')

    variables = RequestContext(request, {
        'bookmarks': bookmarks,
        'username': username,
        'show_tags': True
    })

    return render_to_response('user_page.html', variables)


def logout_page(request):
    logout(request)

    return HttpResponseRedirect('/')


def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            return HttpResponseRedirect('/register/success')
    else:
        form = RegistrationForm()

    variables = RequestContext(request, {
        'form': form
    })
    return render_to_response(
        'registration/register.html',
        variables
    )


@login_required
def bookmark_save_page(request):
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        print >> sys.stderr, request.POST

        if form.is_valid():
            link, dummy = Link.objects.get_or_create(
                url=form.cleaned_data['url']
            )

            bookmark, created = Bookmark.objects.get_or_create(
                user=request.user,
                link=link
            )

            bookmark.title = form.cleaned_data['title']

            if not created:
                bookmark.tag_set.clear()

            tag_names = form.cleaned_data['tags'].split()
            for tag_name in tag_names:
                tag, dummy = Tag.objects.get_or_create(name=tag_name)
                bookmark.tag_set.add(tag)

            bookmark.save()
            return HttpResponseRedirect(
                '/user/%s' % request.user.username
            )
    else:
        form = BookmarkSaveForm()

    variables = RequestContext(request, {'form': form})
    return render_to_response('bookmark_save.html', variables)


def tag_page(request, tag_name):
    print >> sys.stderr, 'tag_page'
    tag = get_object_or_404(Tag, name=tag_name)
    bookmarks = tag.bookmarks.order_by('-id')
    variables = RequestContext(request, {
        'bookmarks': bookmarks,
        'tag_name': tag_name,
        'show_tags': True,
        'show_user': True
    })
    return render_to_response('tag_page.html', variables)
