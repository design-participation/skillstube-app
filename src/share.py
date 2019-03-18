from aiohttp import web
import aiohttp_jinja2
from bson.objectid import ObjectId

from util import routes, get_user, login_required
from backend import comments, shares, notifications, friends

# TODO: deprecated
@routes.post('/view-shared/{share_id}')
@login_required
async def view_shared(request):
    user = await get_user(request)
    share_id = ObjectId(request.match_info['share_id'])
    share = await shares.get(share_id)
    data = await request.post()
    if 'notification' in data:
        notification_id = ObjectId(data['notification'])
        notification = await notifications.get(notification_id)
        if notification is not None and notification['data']['share_id'] == share_id:
            await notifications.dismiss(user['_id'], notification_id)
    if share is not None and share['recipient_id'] == user['_id']:
        raise web.HTTPFound('/watch/' + str(share['video_id']) + '#' + str(share['comment_id']))
    raise web.HTTPBadRequest()
        
#GET /share/{comment_id} => show friend selection ui for sharing
@routes.get('/share/{comment_id}')
@login_required
@aiohttp_jinja2.template('share.html')
async def share_select(request):
    user = await get_user(request)
    comment_id = ObjectId(request.match_info['comment_id'])
    comment = await comments.get(comment_id)
    if comment is not None and comment['user_id'] == user['_id']:
        friend_items = await friends.list(user['_id'], populate=True)
        initial_share = set([item['recipient_id'] for item in await shares.list(comment['video_id'], comment_id=comment_id)])
        for item in friend_items:
            if item['_id'] in initial_share:
                item['selected'] = True
        return {'comment': comment, 'friends': friend_items, 'nav': 'search'}
    raise web.HTTPBadRequest()

#POST /share/{comment_id} => perform the sharing
@routes.post('/share/{comment_id}')
@login_required
async def share_save(request):
    user = await get_user(request)
    comment_id = ObjectId(request.match_info['comment_id'])
    comment = await comments.get(comment_id)
    if comment is not None:
        #TODO: remove deselected users
        video_id = comment['video_id']
        data = await request.post()
        for key, other_id in data.items():
            if key == 'friend':
                print('adding', other_id)
                await shares.add(video_id, comment_id, {'thumbnail': 'https://i.ytimg.com/vi/%s/hqdefault.jpg' % video_id, 'text': comment['text']}, user['_id'], ObjectId(other_id))
        raise web.HTTPFound('/watch/' + comment['video_id'] + '#' + str(comment['_id']))
    raise web.HTTPBadRequest()

@routes.get('/shared')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    shared_with_me = await comments.list(user['_id'], shared_with_me=True, populate=True)
    return {'comments': shared_with_me, 'show_video': True, 'nav': 'shared'}

@routes.get('/shared/by-me')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    shared_by_myself = [item for item in await comments.list(user['_id'], populate=True) if len(item['shared_with']) > 0]
    return {'comments': shared_by_myself, 'show_video': True, 'nav': 'shared'}

@routes.get('/shared/{friend_id}')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    friend_id = ObjectId(request.match_info['friend_id'])
    shared_with_me = await comments.list(user['_id'], shared_with_me=True, owner_id=friend_id, populate=True)
    return {'comments': shared_with_me, 'show_video': True, 'nav': 'friends'}

