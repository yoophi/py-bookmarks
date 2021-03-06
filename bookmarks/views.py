# -*- coding: utf-8 -*-
#  Create your views here.

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template

from bookmarks.forms import *
from bookmarks.models import *

import sys
from datetime import datetime, timedelta

ITEMS_PER_PAGE = 10


def main_page(request):
    shared_bookmarks = SharedBookmark.objects.order_by('-date')[:10]
    variables = RequestContext(request, {'shared_bookmarks': shared_bookmarks})

    return render_to_response('main_page.html', variables)


def user_page(request, username):
    print >> sys.stderr, 'user_page'
    user = get_object_or_404(User, username=username)
    query_set = user.bookmark_set.order_by('-id')
    paginator = Paginator(query_set, ITEMS_PER_PAGE)
    try:
        page = int(request.GET['page'])
    except:
        page = 1
    try:
        bookmarks = paginator.page(page)
    except:
        raise Http404
    is_friend = Friendship.objects.filter(
        from_friend=request.user,
        to_friend=user
    )
    variables = RequestContext(request, {
        'bookmarks': bookmarks.object_list,
        'username': username,
        'show_tags': True,
        'show_edit': username == request.user.username,
        'show_paginator': paginator.num_pages > 1,
        'has_prev': bookmarks.has_previous(),
        'has_next': bookmarks.has_next(),
        'page': page,
        'pages': paginator.num_pages,
        'next_page': bookmarks.next_page_number(),
        'prev_page': bookmarks.previous_page_number(),
        'is_friend': is_friend
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
            if 'invitation' in request.session:
                invitation = Invitation.objects.get(id=request.session['invitation'])
                friendship = Friendship(
                    from_friend=user,
                    to_friend=invitation.sender
                )
                friendship.save()
                friendship = Friendship(
                    from_friend=invitation.sender,
                    to_friend=user
                )
                friendship.save()
                invitation.delete()
                del request.session['invitation']

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
    ajax = 'ajax' in request.GET
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)

        if form.is_valid():
            bookmark = _bookmark_save(request, form)
            if ajax:
                variables = RequestContext(request, {
                    'bookmarks': [bookmark],
                    'show_edit': True,
                    'show_tags': True
                })
                return render_to_response('bookmark_list.html', variables)
            else:
                return HttpResponseRedirect(
                    '/user/%s' % request.user.username
                )
        else:
            if ajax:
                return HttpResponse('failure')
    elif 'url' in request.GET:
        url = request.GET['url']
        title = ''
        tags = ''
        try:
            link = Link.objects.get(url=url)
            bookmark = Bookmark.objects.get(
                link=link,
                user=request.user
            )
            title = bookmark.title
            tags = ' '.join(
                tag.name for tag in bookmark.tag_set.all()
            )
        except ObjectDoesNotExist:
            pass
        form = BookmarkSaveForm({
            'url': url,
            'title': title,
            'tags': tags
        })
    else:
        form = BookmarkSaveForm()

    variables = RequestContext(request, {'form': form})

    if ajax:
        return render_to_response('bookmark_save_form.html', variables)
    else:
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


def tag_cloud_page(request):
    MAX_WEIGHT = 5
    tags = Tag.objects.order_by('name')

    # Calculate tag, min and max counts
    min_count = max_count = tags[0].bookmarks.count()
    for tag in tags:
        tag.count = tag.bookmarks.count()
        if tag.count < min_count:
            min_count = tag.count
        if max_count < tag.count:
            max_count = tag.count

    # Calculate count range. Avoid dividing by zero.
    range = float(max_count - min_count)
    if range == 0.0:
        range = 1.0

    # Calculate tag weights.
    for tag in tags:
        tag.weight = int(
            MAX_WEIGHT * (tag.count - min_count) / range
        )
    variables = RequestContext(request, {'tags': tags})
    return render_to_response('tag_cloud_page.html', variables)


def search_page(request):
    form = SearchForm()
    bookmarks = []
    show_results = False
    if 'query' in request.GET:
        show_results = True
        query = request.GET['query'].strip()
        if query:
            keywords = query.split()
            q = Q()
            for keyword in keywords:
                q = q & Q(title__icontains=keyword)
            form = SearchForm({'query': query})
            bookmarks = Bookmark.objects.filter(q)[:10]
    variables = RequestContext(request, {
        'form': form,
        'bookmarks': bookmarks,
        'show_results': show_results,
        'show_tags': True,
        'show_user': True
    })
    if 'ajax' in request.GET:
        return render_to_response('bookmark_list.html', variables)
    else:
        return render_to_response('search.html', variables)


def _bookmark_save(request, form):
    link, dummy = Link.objects.get_or_create(url=form.cleaned_data['url'])

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

    if form.cleaned_data['share']:
        shared_bookmark, created = SharedBookmark.objects.get_or_create(bookmark=bookmark)
        if created:
            shared_bookmark.users_voted.add(request.user)
            shared_bookmark.save()

    bookmark.save()
    return bookmark


def ajax_tag_autocomplete(request):
    if 'q' in request.GET:
        tags = Tag.objects.filter(name__istartswith=request.GET['q'])[:10]
        return HttpResponse('\n'.join(tag.name for tag in tags))
    return HttpResponse()


@login_required
def bookmark_vote_page(request):
    if 'id' in request.GET:
        try:
            id = request.GET['id']
            shared_bookmark = SharedBookmark.objects.get(id=id)
            user_voted = shared_bookmark.users_voted.filter(
                username=request.user.username
            )
            if not user_voted:
                shared_bookmark.votes += 1
                shared_bookmark.users_voted.add(request.user)
                shared_bookmark.save()
        except ObjectDoesNotExist:
            raise Http404('북마크를 찾을 수 없습니다.')

    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return HttpResponseRedirect('/')


def popular_page(request):
    today = datetime.today()
    yesterday = today - timedelta(1)
    shared_bookmarks = SharedBookmark.objects.filter(date__gt=yesterday)
    shared_bookmarks = shared_bookmarks.order_by('-votes')[:10]
    variables = RequestContext(request, {'shared_bookmarks': shared_bookmarks})

    return render_to_response('popular_page.html', variables)


def bookmark_page(request, bookmark_id):
    shared_bookmark = get_object_or_404(SharedBookmark, id=bookmark_id)
    variables = RequestContext(request, {'shared_bookmark': shared_bookmark})
    return render_to_response('bookmark_page.html', variables)


def friends_page(request, username):
    user = get_object_or_404(User, username=username)
    friends = [friendship.to_friend for friendship in user.friend_set.all()]
    friend_bookmarks = Bookmark.objects.filter(user__in=friends).order_by('-id')
    variables = RequestContext(request, {
        'username': username,
        'friends': friends,
        'bookmarks': friend_bookmarks[:10],
        'show_tags': True,
        'show_user': True
    })
    return render_to_response('friends_page.html', variables)

@login_required
def friend_add(request):
    if 'username' in request.GET:
        friend = get_object_or_404(User, username=request.GET['username'])
        friendship = Friendship(
            from_friend=request.user,
            to_friend=friend
        )
        try:
            friendship.save()
            request.user.message_set.create(
                message=u'%s를 친구로 추가했습니다.' % friend.username
            )
        except:
            request.user.message_set.create(
                message=u'%s는 이미 친구입니다.' % friend.username
            )
        return HttpResponseRedirect(
            '/friends/%s/' % request.user.username
        )
    else:
        raise Http404


@login_required
def friend_invite(request):
    if request.method == 'POST':
        form = FriendInviteForm(request.POST)
        if form.is_valid():
            invitation = Invitation(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                code=User.objects.make_random_password(20),
                sender=request.user
            )
            invitation.save()
            try:
                invitation.send()
                request.user.message_set.create(
                    message=u'%s에게 초대 메세지를 보냈습니다.' % invitation.email
                )
            except:
                request.user.message_set.create(
                    message=u'초대하는 과정에서 오류가 있었습니다.'
                )
            return HttpResponseRedirect('/friend/invite/')
    else:
        form = FriendInviteForm()

    variables = RequestContext(request, {'form': form})

    return render_to_response('friend_invite.html', variables)


def friend_accept(request, code):
    invitation = get_object_or_404(Invitation, code__exact=code)
    request.session['invitation'] = invitation.id
    return HttpResponseRedirect('/register/')


