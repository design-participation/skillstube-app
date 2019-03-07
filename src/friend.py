from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, login_required, get_user
from backend import friends, users, notifications
from navigation import Breadcrumb
from bson.objectid import ObjectId

#GET /personal => show personal information
@routes.get('/friends')
@login_required
@aiohttp_jinja2.template('friends.html')
async def show_friends(request):
    user = await get_user(request)
    friend_ids = await friends.list(user['_id'])
    friend_items = await users.get(friend_ids)

    # get friend request notifications
    notification_items = await notifications.list(user['_id'], ['friend request', 'friend accept'], populate=True)
    return {'friends': friend_items, 'notifications': notification_items, 'breadcrumb': [Breadcrumb.HOME(), Breadcrumb.FRIENDS()]}

#POST /friend/request (email) => send friend request to user identified by email address
@routes.post('/friend/request')
@login_required
async def request_friend(request):
    user = await get_user(request)
    data = await request.post()
    if 'email' in data:
        other = await users.list({'email': data['email']})
        if len(other) == 1:
            await friends.add(user['_id'], other[0]['_id'], request=True)
        else:
            raise web.HTTPBadRequest()
    else:
        raise web.HTTPBadRequest()
    raise web.HTTPFound('/friends')

#POST /friend/accept/{friend_id} => accept friend request
@routes.post('/friend/accept/{request_id}')
@login_required
async def accept_friend(request):
    user = await get_user(request)
    request_id = ObjectId(request.match_info['request_id'])
    data = await request.post()
    if 'notification' in data:
        notification_id = ObjectId(data['notification'])
        notification = await notifications.get(notification_id)
        if notification is not None and notification['data']['friend_id'] == request_id:
            await notifications.dismiss(user['_id'], notification_id)
    await friends.accept(request_id)
    raise web.HTTPFound('/friends')

