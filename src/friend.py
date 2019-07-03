import sys
from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, login_required, get_user, to_objectid, redirect
from backend import friends, users, notifications, history, comments

@routes.get('/friends')
@login_required
@aiohttp_jinja2.template('friends.html')
async def show_friends(request):
    user = await get_user(request)
    friend_items = await friends.list(user['_id'], populate=True)
    for item in friend_items:
        item['href'] = '/friend/%s' % str(item['_id'])
    await history.add(user['_id'], 'list-friends')
    return {'friends': friend_items, 'nav': 'friends'}

@routes.get('/add-friend')
@aiohttp_jinja2.template('add_friend.html')
@login_required
async def add_playlist(request):
    user = await get_user(request)
    await history.add(user['_id'], 'add-friend-form')
    return {'nav': 'friends'}

@routes.get('/friend/{friend_id}')
@login_required
@aiohttp_jinja2.template('friend.html')
async def show_friend(request):
    user = await get_user(request)
    friend_id = to_objectid(request.match_info['friend_id'])
    if await friends.exists(user['_id'], friend_id):
        friend = await users.get(friend_id)
        shared_by_myself = await comments.list(owner_id=user['_id'], recipient_id=friend['_id'], populate=True) 
        shared_with_me = await comments.list(recipient_id=user['_id'], owner_id=friend_id, populate=True)
        all_items = sorted(shared_by_myself + shared_with_me, key=lambda item: item['date'], reverse=True)
        await history.add(user['_id'], 'show-friend', {'friend_id': friend_id, 'name': friend['name']})
        return {'friend': friend, 'nav': 'friends', 'comments': all_items, 'show_video': True}
    raise web.HTTPBadRequest(reason='Not a friend')

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
        friend = await users.get(request['user_id'])
        await history.add(user['_id'], 'view-friend-request', {'request': request})
        return {'friend': friend, 'request_id': request_id, 'nav': 'notifications'}
    raise web.HTTPBadRequest()

@routes.get('/friend/accept/{request_id}')
@login_required
async def accept_friend(request):
    user = await get_user(request)
    request_id = to_objectid(request.match_info['request_id'])
    await friends.accept(request_id)
    request = await friends.get(request_id)
    await history.add(user['_id'], 'accept-friend-request', {'request': request})
    raise web.HTTPFound('/friends')

@routes.post('/unfriend/{friend_id}')
@login_required
async def unfriend(request):
    user = await get_user(request)
    friend_id = to_objectid(request.match_info['friend_id'])
    if await friends.remove(user['_id'], friend_id):
        friend = await users.get(friend_id)
        await history.add(user['_id'], 'unfriend', {'friend_id': friend['_id'], 'name': friend['name']})
        # TODO: send notificaiton to other user
        await redirect(request, '/friends', info='Unfriended %s' % friend['name'])
    raise web.HTTPBadRequest(reason='Not friend')

