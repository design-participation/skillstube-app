import asyncio
import datetime
from aiohttp import web
import aiohttp_jinja2

from backend import users, videos, history, notifications, friends, comments, shares, playlists
from util import routes, login_required, get_user

import secrets

async def export_all(filename='export.xlsx'):
    # redact sensitive information
    projection={'password': False}
    import xlsxwriter
    print('exporting to "%s"' % filename)
    workbook = xlsxwriter.Workbook(filename)
    title_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss.000', 'align': 'left'})
    for name, collection in [('users', users), ('videos', videos), ('history', history), ('notifications', notifications), ('friends', friends), ('comments', comments), ('shares', shares), ('playlists', playlists)]:
        worksheet = workbook.add_worksheet(name)
        # pass 1: gather keys
        def record_keys(keys, doc, path=[]):
            for key, value in doc.items():
                if type(value) is dict:
                    record_keys(keys, value, path + [key])
                else:
                    identifier = '/'.join(path + [key])
                    if identifier not in keys:
                        keys[identifier] = len(keys)

        keys = {}
        cursor = collection.db.find({}, projection)
        while True:
            docs = await cursor.to_list(length=100)
            if len(docs) == 0:
                break
            for doc in docs:
                record_keys(keys, doc)

        for key, num in keys.items():
            worksheet.write(0, num, key, title_format)

        # store data
        def record_doc(row, doc, path=[]):
            for key, value in doc.items():
                if type(value) is dict:
                    record_doc(row, value, path + [key])
                else:
                    row[keys['/'.join(path + [key])]] = value

        doc_num = 1
        cursor = collection.db.find({}, projection)
        while True:
            docs = await cursor.to_list(length=100)
            if len(docs) == 0:
                break
            for doc in docs:
                row = ['' for i in keys]
                record_doc(row, doc)
                for num, value in enumerate(row):
                    if type(value) is datetime.datetime:
                        worksheet.write_datetime(doc_num, num, value, date_format)
                    else:
                        worksheet.write(doc_num, num, str(value))
                doc_num += 1

    workbook.close()

#GET /export => export form
@routes.get('/export')
@aiohttp_jinja2.template('export.html')
async def export_form(request):
    return {}

#GET /export => actual export
@routes.post('/export')
@aiohttp_jinja2.template('export.html')
async def export(request):
    data = await request.post()
    password = data.get('password', '')
    if password == secrets.EXPORT_PASSWORD:
        filename = '/export/export_%s.xlsx' % datetime.datetime.utcnow()
        await export_all('data' + filename)
        raise web.HTTPFound(filename)
    else:
        return {'error_message': 'invalid credentials'}

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print('usage: %s <output-filename>', file=sys.stderr)
        sys.exit(1)
    asyncio.get_event_loop().run_until_complete(export_all(sys.argv[1]))
