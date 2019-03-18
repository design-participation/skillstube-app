from aiohttp import web
from aiohttp_session import get_session, new_session
import aiohttp_jinja2

from util import routes, login_required
from backend import users, history

#GET /user => new user form
@routes.get('/user')
@aiohttp_jinja2.template('new_user.html')
async def new_user_form(request):
    return {}

#POST /user (email, password) => create user
@routes.post('/user')
@aiohttp_jinja2.template('new_user.html')
async def new_user(request):
    data = await request.post()
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    picture = data.get('picture', '')
    #TODO: need to check that picture exists
    if picture.strip() == '':
        picture = 'https://api.adorable.io/avatars/512/' + email
    error = None
    if 'email' == '' or password == '':
        error = 'invalid request'
    user_id = await users.add(password=password, email=email, name=name, picture=picture)
    if user_id is None:
        error = 'email already exists'
    if error is not None:
        return {'email': email, 'name': name, 'picture': picture, 'error': error}
    else:
        session = await new_session(request)
        session['user_id'] = str(user_id)
        await history.add(user_id, 'created')
        raise web.HTTPFound('/')

#GET /login => login form
@routes.get('/login')
@aiohttp_jinja2.template('login.html')
async def login_form(request):
    import sys
    if '-debug' in sys.argv:
        result = []
        for user in await users.list():
            user['href'] = '/debug:login/' + str(user['_id'])
            result.append(user)
        import random
        random.shuffle(result)
        return {'users': result}
    return {}

#GET /logout => show logout screen
@routes.get('/logout')
@login_required
@aiohttp_jinja2.template('logout.html')
async def logout(request):
    return {}

#POST /logout => remove user_id from session
@routes.post('/logout')
@login_required
async def logout(request):
    session = await get_session(request)
    if 'user_id' in session:
        del session['user_id']
    raise web.HTTPFound('/login')

#POST /login (email, password) => login as existing user
@routes.post('/login')
@aiohttp_jinja2.template('login.html')
async def login(request):
    data = await request.post()
    email = data.get('email', '')
    password = data.get('password', '')
    user_id = await users.login(email, password)
    if user_id is not None:
        session = await new_session(request)
        session['user_id'] = str(user_id)
        await history.add(user_id, 'login')
        raise web.HTTPFound('/')
    else:
        return {'email': email, 'error': 'invalid credentials'}

