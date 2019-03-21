from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, login_required, get_user, to_objectid
from backend import notifications, shares

#get /dismiss/{notification_id} => dismiss notification (json result)
@routes.get('/dismiss/{notification_id}')
@login_required
async def dismiss_notification(request):
    user = await get_user(request)
    notification_id = request.match_info['notification_id']
    await notifications.dismiss(user['_id'], to_objectid(notification_id))
    return web.json_response('ok')

#get /notification/{notification_id} => when clicked on notification, process and redirect user
@routes.get('/notification/{notification_id}')
@login_required
async def process_notification(request):
    user = await get_user(request)
    notification_id = to_objectid(request.match_info['notification_id'])
    notification = await notifications.get(notification_id)
    if notification is not None and notification['user_id'] == user['_id']: 
        await notifications.dismiss(user['_id'], notification_id)
        if notification['type'] == 'shared content':
            share = await shares.get(notification['data']['share_id'])
            if share is not None and share['recipient_id'] == user['_id']:
                raise web.HTTPFound('/watch/' + str(share['video_id']) + '#' + str(share['comment_id']))
        elif notification['type'] == 'friend request':
            raise web.HTTPFound('/friend/request/' + str(notification['data']['friend_id']))
        elif notification['type'] == 'friend accept':
            raise web.HTTPFound('/friends')
        else:
            raise web.HTTPBadRequest()
    raise web.HTTPBadRequest()

@routes.get('/notifications')
@login_required
@aiohttp_jinja2.template('notifications.html')
async def show_notifications(request):
    user = await get_user(request)
    notification_items = await notifications.list(user['_id'], return_all=False, populate=True)
    return {'notifications': notification_items, 'subset': 'new', 'nav': 'notifications'}

@routes.get('/notifications/all')
@login_required
@aiohttp_jinja2.template('notifications.html')
async def show_all_notifications(request):
    user = await get_user(request)
    notification_items = await notifications.list(user['_id'], return_all=True, populate=True)
    return {'notifications': notification_items, 'subset': 'all', 'nav': 'notifications'}

@routes.get('/notifications/old')
@login_required
@aiohttp_jinja2.template('notifications.html')
async def show_old_notifications(request):
    user = await get_user(request)
    notification_items = await notifications.list(user['_id'], return_old=True, populate=True)
    return {'notifications': notification_items, 'subset': 'old', 'nav': 'notifications'}

