from aiohttp import web
import aiohttp_jinja2

from util import routes, get_user, login_required, to_objectid
from backend import comments, shares, notifications, friends, history

# TODO: deprecated
@routes.post('/view-shared/{share_id}')
@login_required
async def view_shared(request):
    user = await get_user(request)
    share_id = to_objectid(request.match_info['share_id'])
    share = await shares.get(share_id)
    data = await request.post()
    if 'notification' in data:
        notification_id = to_objectid(data['notification'])
        notification = await notifications.get(notification_id)
        if notification is not None and notification['data']['share_id'] == share_id:
            await notifications.dismiss(user['_id'], notification_id)
    if share is not None and share['recipient_id'] == user['_id']:
        await history.add(user['_id'], 'view-shared', {'share_id': share_id})
        raise web.HTTPFound('/watch/' + str(share['video_id']) + '#' + str(share['comment_id']))
    raise web.HTTPBadRequest()
        
#GET /share/{comment_id} => show friend selection ui for sharing
@routes.get('/share/{comment_id}')
@login_required
@aiohttp_jinja2.template('share.html')
async def share_select(request):
    user = await get_user(request)
    comment_id = to_objectid(request.match_info['comment_id'])
    comment = await comments.get(comment_id)
    if comment is not None and comment['user_id'] == user['_id']:
        friend_items = await friends.list(user['_id'], populate=True)
        initial_share = set([item['recipient_id'] for item in await shares.list(comment['video_id'], comment_id=comment_id)])
        for item in friend_items:
            if item['_id'] in initial_share:
                item['selected'] = True
        await history.add(user['_id'], 'share-select-friends', {'comment_id': comment_id})
        return {'comment': comment, 'friends': friend_items, 'nav': 'search'}
    raise web.HTTPBadRequest()

#POST /share/{comment_id} => perform the sharing
@routes.post('/share/{comment_id}')
@login_required
async def share_save(request):
    user = await get_user(request)
    comment_id = to_objectid(request.match_info['comment_id'])
    comment = await comments.get(comment_id)
    if comment is not None:
        #TODO: remove deselected users
        video_id = comment['video_id']
        data = await request.post()
        for key, other_id in data.items():
            if key == 'friend':
                print('adding', other_id)
                await shares.add(video_id, comment_id, {'thumbnail': 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id, 'text': comment['text']}, user['_id'], to_objectid(other_id))
        await history.add(user['_id'], 'share-comment', {'comment_id': comment_id, 'friends': [v for k, v in data.items() if k == 'friend']})
        raise web.HTTPFound('/watch/' + comment['video_id'] + '#' + str(comment['_id']))
    raise web.HTTPBadRequest()

@routes.get('/shared')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    shared_with_me = await comments.list(user['_id'], shared_with_me=True, populate=True)
    await history.add(user['_id'], 'view-shared-with-me')
    return {'comments': shared_with_me, 'show_video': True, 'nav': 'shared'}

@routes.get('/shared/by-me')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    shared_by_myself = [item for item in await comments.list(user['_id'], populate=True) if len(item['shared_with']) > 0]
    await history.add(user['_id'], 'view-shared-by-me')
    return {'comments': shared_by_myself, 'show_video': True, 'nav': 'shared'}

@routes.get('/shared/{friend_id}')
@login_required
@aiohttp_jinja2.template('shared.html')
async def show_shared(request):
    user = await get_user(request)
    friend_id = to_objectid(request.match_info['friend_id'])
    shared_with_me = await comments.list(user['_id'], shared_with_me=True, owner_id=friend_id, populate=True)
    await history.add(user['_id'], 'view-shared-by-friend', {'friend': friend_id})
    return {'comments': shared_with_me, 'show_video': True, 'nav': 'friends'}

