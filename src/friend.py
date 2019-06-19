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
    await history.add(user['_id'], 'list-friends')
    return {'friends': friend_items, 'nav': 'friends'}

#POST /friend/request (email) => send friend request to user identified by email address
@routes.post('/friend/request')
@login_required
@aiohttp_jinja2.template('friends.html')
async def request_friend(request):
    user = await get_user(request)
    friend_items = await friends.list(user['_id'], populate=True)

    data = await request.post()
    qrcode = data.get('qrcode', '')
    email = data.get('email', '').lower().strip()
    other = []
    await history.add(user['_id'], 'send-friend-request', {'email': email, 'qrcode': qrcode})
    if qrcode != '':
        request = False
        other = await users.list({'qrcode': qrcode})
    elif email != '':
        other = await users.list({'email': email})
        requrest = True

    info = error = None
    if len(other) == 1:
        if await friends.exists(user['_id'], other[0]['_id']):
            info = 'Already friend with %s' % other[0]['name']
        elif user['_id'] == other[0]['_id']:
            error = 'You cannot friend yourself'
        else:
            await friends.add(user['_id'], other[0]['_id'], request=request)
            if request:
                info = 'Sent request to %s' % other[0]['name']
            else:
                info = '%s is now a friend' % other[0]['name']
                friend_items.insert(0, other[0])
    else:
        error = 'User not found'

    #raise web.HTTPFound('/friends')
    return {'friends': friend_items, 'info_message': info, 'error_message': error, 'nav': 'friends'}

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

