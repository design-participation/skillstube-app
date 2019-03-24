import sys
from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, login_required, get_user, to_objectid
from backend import friends, users, notifications, history

#GET /personal => show personal information
@routes.get('/friends')
@login_required
@aiohttp_jinja2.template('friends.html')
async def show_friends(request):
    user = await get_user(request)
    friend_items = await friends.list(user['_id'], populate=True)
    # TODO: remove
    if '-debug' in sys.argv:
        for item in friend_items:
            item['href'] = '/shared/' + str(item['_id'])

    # get friend request notifications
    notification_items = await notifications.list(user['_id'], ['friend request', 'friend accept'], populate=True)
    await history.add(user['_id'], 'list-friends')
    return {'friends': friend_items, 'notifications': notification_items, 'nav': 'friends'}

#POST /friend/request (email) => send friend request to user identified by email address
@routes.post('/friend/request')
@login_required
async def request_friend(request):
    user = await get_user(request)
    data = await request.post()
    if 'email' in data:
        email = data['email'].lower().strip()
        other = await users.list({'email': email})
        if len(other) == 1:
            await friends.add(user['_id'], other[0]['_id'], request=True)
        else:
            raise web.HTTPBadRequest(reason='User not found')
        await history.add(user['_id'], 'friend-request', {'email': data['email']})
    else:
        raise web.HTTPBadRequest(reason='Email missing')
    raise web.HTTPFound('/friends')

@routes.get('/friend/request/{request_id}')
@login_required
@aiohttp_jinja2.template('friend_request.html')
async def view_friend_request(request):
    user = await get_user(request)
    request_id = to_objectid(request.match_info['request_id'])
    request = await friends.get(request_id)
    if request is not None and request['other_id'] == user['_id']:
        #TODO: finish
        friend = await users.get(request['user_id'])
        await history.add(user['_id'], 'view-friend-request', {'request': request})
        return {'friend': friend, 'request_id': request_id, 'nav': 'notifications'}
    raise web.HTTPBadRequest()

#GET /friend/accept/{friend_id} => accept friend request
@routes.get('/friend/accept/{request_id}')
@login_required
async def accept_friend(request):
    user = await get_user(request)
    request_id = to_objectid(request.match_info['request_id'])
    await friends.accept(request_id)
    request = await friends.get(request_id)
    await history.add(user['_id'], 'accept-friend-request', {'request': request})
    raise web.HTTPFound('/friends')

