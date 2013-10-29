# -*- coding: utf-8 -*-
#  Create your views here.

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404, HttpResponseRedirect
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
    try:
        user = User.objects.get(username=username)
    except:
        raise Http404('사용자를 찾을 수 없습니다.')

    bookmarks = user.bookmark_set.all()

    template = get_template('user_page.html')
    variables = RequestContext(request, {
        'username': username,
        'bookmarks': bookmarks
    })
    output = template.render(variables)

    return HttpResponse(output)


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
