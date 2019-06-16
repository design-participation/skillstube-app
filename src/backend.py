from datetime import datetime, timezone
import collections
import uuid

import asyncio
import motor.motor_asyncio
import pymongo

from bson.objectid import ObjectId
from passlib.hash import pbkdf2_sha256

import util
import secrets

client = motor.motor_asyncio.AsyncIOMotorClient(secrets.DB_URL)
db = client[secrets.DB_NAME]

class DB:
    def __init__(self, db_name):
        self.db = db[db_name]

    def check_type(self, _id):
        if type(_id) is not list:
            _id = [_id]
        for item in _id:
            if item is not None and type(item) is not ObjectId:
                raise Exception('need to use ObjectId()')

    async def add(self, _key=None, **kwargs):
        result = await self.db.replace_one(_key if _key is not None else kwargs, kwargs, upsert=True)
        return result.upserted_id

    async def get(self, _id, projection=None):
        self.check_type(_id)
        if type(_id) is list:
            return await self.db.find({'_id': {'$in': _id}}, projection).to_list(None)
        else:
            return await self.db.find_one({'_id': _id})

    async def update(self, _id, value):
        self.check_type(_id)
        result = await self.db.replace_one({'_id': _id}, value)
        return result.inserted_id

    async def list(self, *args, **kwargs):
        return await self.db.find(*args, **kwargs).to_list(None)

    async def find(self, *args, **kwargs):
        return await self.db.find_one(*args, **kwargs)

    async def delete(self, _id):
        self.check_type(_id)
        if type(_id) is list:
            await self.db.delete_many({_id: {'$in': _id}})
        else:
            await self.db.delete_one({_id: _id})

    async def count(self):
        return await self.db.count_documents()

    async def clear(self):
        await self.db.drop()


# TODO: redact passwords in queries
class Users(DB):
    def __init__(self):
        super().__init__('users')
        self.db.create_index('email', unique=True)

    async def get(self, _id):
        user = await super().get(_id, {'password': False})
        # upgrade users who don't have yet a qrcode
        if type(user) is dict and 'qrcode' not in user: 
            user['qrcode'] = str(uuid.uuid4())
            await self.db.find_one_and_update({'_id': _id}, {'$set': {'qrcode': user['qrcode']}})
        return user

    async def add(self, email, password, name='', picture='', origin='genuine'):
        if await self.db.find_one({'email': email}):
            return None
        return await super().add(
                email=email,
                password=pbkdf2_sha256.hash(password),
                name=name,
                picture=picture,
                qrcode=str(uuid.uuid4()),
                origin=origin
                )

    async def change_password(self, _id, old_password, new_password): 
        user = await super().find({'_id': _id})
        if user is not None and pbkdf2_sha256.verify(old_password, user['password']):
            await self.db.find_one_and_update({'_id': _id}, {'$set': {'password': pbkdf2_sha256.hash(new_password), 'qrcode': str(uuid.uuid4())}})
            return True
        return False

    async def change_picture(self, _id, picture): 
        await self.db.find_one_and_update({'_id': _id}, {'$set': {'picture': picture}})

    async def login(self, email, password):
        user = await super().find({'email': email})
        if user is not None and pbkdf2_sha256.verify(password, user['password']):
            return user['_id']
        return None

    async def login_from_qrcode(self, qrcode):
        user = await super().find({'qrcode': qrcode})
        if user is not None:
            return user['_id']
        return None


class Videos(DB):
    def __init__(self):
        super().__init__('videos')

    async def add(self, video_id, title, thumbnail): 
        return await super().add(video_id=video_id, title=title, thumbnail=thumbnail)

    async def get(self, video_id):
        if type(video_id) is list:
            return await self.db.find({'video_id': {'$in': video_id}}).to_list(None)
        else:
            return await self.db.find_one({'video_id': video_id})
         

class History(DB):
    def __init__(self):
        super().__init__('history')
        self.db.create_index('user_id')

    async def add(self, user_id, type, data=None):
        return await super().add(user_id=user_id, type=type, data=data, date=util.now())

    async def list(self, user_id, type=None, limit=0):
        filter = {'user_id': user_id}
        if type:
            filter['type'] = type
        return await super().list(filter, limit=limit, sort=[('date', pymongo.DESCENDING)])


class Notifications(DB):
    def __init__(self):
        super().__init__('notifications')
        self.db.create_index('user_id')

    async def add(self, user_id, type, data=None):
        return await super().add(user_id=user_id, new=True, data=data, type=type, date=util.now())

    async def dismiss(self, user_id, _id):
        await self.db.find_one_and_update({'_id': _id, 'user_id': user_id}, {'$set': {'new': False}})

    async def list(self, user_id, notification_type=None, return_old=False, return_all=False, populate=False, limit=0):
        filter = {'user_id': user_id}
        if notification_type:
            if type(notification_type) == list:
                filter['$or'] = [{'type': x} for x in notification_type]
            else:
                filter['type'] = notification_type
        if return_old:
            filter['new'] = False
        elif not return_all:
            filter['new'] = True
        result = await super().list(filter, limit=limit, sort=[('date', pymongo.DESCENDING)])
        if populate:
            sender_ids = [item['data']['sender_id'] for item in result if 'sender_id' in item['data']]
            senders = {item['_id']: item for item in await users.get(sender_ids)}
            share_ids = [item['data']['share_id'] for item in result if 'share_id' in item['data']]
            share_items = {item['_id']: item for item in await shares.get(share_ids)}
            for item in result:
                if 'sender_id' in item['data']:
                    item['data']['sender'] = senders[item['data']['sender_id']]
                if 'share_id' in item['data']:
                    item['data']['share'] = share_items[item['data']['share_id']]
        return result

    async def count(self, user_id):
        return await self.db.count_documents({'user_id': user_id, 'new': True})


class Friends(DB):
    def __init__(self):
        super().__init__('friends')
        self.db.create_index('pair', unique=True)
        self.db.create_index('user_id')
        self.db.create_index('other_id')

    async def add(self, user_id, other_id, request=False):
        if user_id == other_id:
            return None
        pair = '|'.join(tuple(set([str(user_id), str(other_id)])))
        if await self.db.find_one({'pair': pair}):
            # TODO: resend notification if already exists?
            return None
        status = 'accepted'
        if request:
            status = 'requested'
        friend_id = await super().add(pair=pair, user_id=user_id, other_id=other_id, status=status, date=util.now())
        if request:
            # TODO: discard older notifications for the same relationship
            await notifications.add(other_id, 'friend request', {'sender_id': user_id, 'friend_id': friend_id})
        return friend_id

    async def accept(self, _id):
        # TODO: check whether it was already accepted
        friendship = await self.get(_id)
        print(friendship)
        await notifications.add(friendship['user_id'], 'friend accept', {'sender_id': friendship['other_id'], 'friend_id': friendship['_id']})
        await self.db.find_one_and_update({'_id': _id}, {'$set': {'status': 'accepted', 'date': util.now()}})

    async def list(self, user_id, populate=False, limit=0):
        filter = {'$or': [{'user_id': user_id}, {'other_id': user_id}], 'status': 'accepted'}
        found = await super().list(filter, limit=limit, sort=[('date', pymongo.DESCENDING)])
        order = {}
        result = []
        for i, item in enumerate(found):
            result.append(item['other_id'] if item['user_id'] == user_id else item['user_id'])
            order[result[-1]] = i
        if populate:
            result = await users.get(result)
            result.sort(key=lambda item: order[item['_id']]) # need to reenforce sorting order
        return result


class Comments(DB):
    def __init__(self):
        super().__init__('comments')

    async def list(self, user_id, video_id=None, populate=False, shared_with_me=False, owner_id=None, limit=0):
        filter = {'user_id': user_id}
        if video_id is not None:
            filter['video_id'] = video_id
        if shared_with_me:
            shared_comment_ids = [item['comment_id'] for item in await shares.list(recipient_id=user_id, owner_id=owner_id)]
            found = await super().get(shared_comment_ids)
        else:
            found = await super().list(filter, limit=limit, sort=[('date', pymongo.ASCENDING)])

        if video_id is not None:
            shared_comment_ids = [item['comment_id'] for item in await shares.list(video_id, user_id)]
            found += await super().get(shared_comment_ids)

        if populate:
            comment_ids = [item['_id'] for item in found]
            user_ids = [item['user_id'] for item in found]
            user_ids += [item['recipient_id'] for item in await shares.list(comment_id=comment_ids)]
            user_items = {item['_id']: item for item in await users.get(user_ids)}

        # augment comments with list of children, also index by id
        by_id = {item['_id']: dict(item, **{'children': []}) for item in found}
        # reorganize as tree
        roots = []
        for item in by_id.values():
            if populate:
                item['user'] = user_items[item['user_id']]
                item['shared_with'] = [user_items[item['recipient_id']] for item in await shares.list(video_id, comment_id=item['_id'])]
            if item['parent_id'] is None:
                roots.append(item)
            elif item['parent_id'] in found:
                found[item['parent_id']].children.append(item)
            else:
                # note: this could be a feature to cheaply delete comments
                raise Exception('Inconsistent comment tree in db')
        return sorted(roots, key=lambda x: x['date'])

    async def add(self, user_id, video_id, text, parent_id=None):
        return await super().add(user_id=user_id, video_id=video_id, text=text, parent_id=parent_id, date=util.now())


class Shares(DB):
    def __init__(self):
        super().__init__('shares')

    async def add(self, video_id, comment_id, preview, owner_id, recipient_id):
        # can only share once
        if await self.db.count_documents({'video_id': video_id, 'comment_id': comment_id, 'owner_id': owner_id, 'recipient_id': recipient_id}) == 0:
            share_id = await super().add(video_id=video_id, comment_id=comment_id, owner_id=owner_id, recipient_id=recipient_id, date=util.now())
            preview.update({'video_id': video_id, 'comment_id': comment_id})
            await notifications.add(recipient_id, 'shared content', {'sender_id': owner_id, 'share_id': share_id, 'preview': preview})
            return share_id
        return None

    # note: comment_id can be a list
    async def list(self, video_id=None, recipient_id=None, comment_id=None, owner_id=None, limit=0):
        self.check_type(recipient_id)
        self.check_type(comment_id)
        filter = {}
        if video_id is not None:
            filter['video_id'] = video_id
        if recipient_id is not None:
            filter['recipient_id'] = recipient_id
        if owner_id is not None:
            filter['owner_id'] = owner_id
        if comment_id is not None:
            filter['comment_id'] = {'$in': comment_id} if type(comment_id) is list else comment_id
        return await super().list(filter, limit=limit)


class Playlists(DB):
    def __init__(self):
        super().__init__('playlists')
        self.db.create_index('user_id')

    async def get_for_video(self, user_id, video_id):
        item = await self.db.find_one({'user_id': user_id, 'type': 'video', 'video_id': video_id})
        if item is not None:
            return await self.get(item['folder_id'])

    async def add_folder(self, user_id, name):
        return await super().add(user_id=user_id, type='folder', name=name)

    async def add(self, user_id, folder_id, video_id):
        return await super().add(_key={'user_id': user_id, 'video_id': video_id}, user_id=user_id, type='video', video_id=video_id, folder_id=folder_id)

    async def list_folders(self, user_id):
        return await super().list({'user_id': user_id, 'type': 'folder'})

    async def list(self, user_id, folder_id=None, limit=0):
        filter = {'user_id': user_id, 'type': 'video'}
        if folder_id is not None:
            filter['folder_id'] = folder_id
        return await super().list(filter, limit=limit)

    async def count(self, folder_id):
        return await self.db.count_documents({'folder_id': folder_id})



async def clear_all():
    await asyncio.gather(
        users.clear(),
        videos.clear(),
        history.clear(),
        notifications.clear(),
        friends.clear(),
        comments.clear(),
        shares.clear(),
        playlists.clear(),
        )
    import os
    os.system('rm data/pictures/*') # also remove all uploaded pictures

users = Users()
videos = Videos()
history = History()
notifications = Notifications()
friends = Friends()
comments = Comments()
shares = Shares()
playlists = Playlists()

#TODO write proper separate tests
#TODO documentation

if __name__ == '__main__':
    async def main():
        await clear_all()

        # Users
        for c in 'ABCDEF':
            print(await users.add(name=c, email=c + '@example.com', picture='', password=c))

        print('DUP', await users.add(name='A', email='A@example.com', picture='', password='A'))

        for user in await users.list():
            print(user)

        print(await users.login('X@example.com', 'A'))
        print(await users.login('A@example.com', 'A'))
        print(await users.login('A@example.com', 'X'))

        A = await users.find({'email': 'A@example.com'})
        user_id = A['_id']
        print(await users.get(user_id))

        # History
        import random, time
        for i in range(5):
            await history.add(user_id, 'query', {'a': random.random()})
            time.sleep(random.random() * 0.1)
        for i in range(5):
            await history.add(user_id, 'doc', {'b': random.random()})
            time.sleep(random.random() * 0.1)

        for item in await history.list():
            print(item['date'])
        print(await history.list(type='doc', limit=3))

        # Notifications
        for i in range(5):
            notif_id = await notifications.add(user_id, 'friend request', {'a': random.random()})

        print(repr(notif_id))
        print(await notifications.count(user_id))
        await notifications.dismiss(user_id, notif_id)
        print(await notifications.count(user_id))
        for notif in await notifications.list(user_id):
            print(notif)

        # Friends
        user_ids = [x['_id'] for x in await users.list()]
        for i in range(4):
            id = await friends.add(user_id, random.choice(user_ids))
            await friends.accept(id)

        for friend in await friends.list(user_id):
            print(friend)


    asyncio.get_event_loop().run_until_complete(main())

