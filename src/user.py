import uuid
import os

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
    reader = await request.multipart()
    data = {}

    while True: # handle file upload and other fields
        field = await reader.next()
        if not field:
            break
        if field.name in ['email', 'name', 'password']:
            data[field.name] = (await field.read(decode=True)).decode('utf8')
        elif field.name == 'picture':
            if field.filename == '': # skip if no file was provided
                continue
            # TODO: should check content for actual picture; should also limit size on the client side
            extension = field.filename.split('.')[-1].lower()
            if extension not in ['jpg', 'jpeg', 'png', 'gif']:
                raise web.HTTPBadRequest(reason='Picture file type not allowed, please use jpg, jpeg, png or gif')
            filename = str(uuid.uuid4()) + '.' + extension
            size = 0
            with open('./data/pictures/' + filename, 'wb') as f:
                while True:
                    chunk = await field.read_chunk()  # 8192 bytes by default.
                    if not chunk:
                        break
                    size += len(chunk)
                    f.write(chunk)
                    if size > 1024 * 1024 * 10: # max 10M 
                        fp.close()
                        os.unlink('./data/pictures/' + filename)
                        raise web.HTTPBadRequest(reason='Picture file too large')
            data['picture'] = '/pictures/' + filename
        else:
            raise web.HTTPBadRequest()

    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    picture = data.get('picture', '')

    if picture.strip() == '':
        picture = 'https://api.adorable.io/avatars/512/' + email
    error = None
    if 'email' == '' or password == '':
        error = 'invalid request'
    user_id = await users.add(password=password, email=email, name=name, picture=picture)
    if user_id is None:
        error = 'email already exists'
    if error is not None:
        if os.path.exists('./data/' + picture):
            os.unlink('./data/' + picture)
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

