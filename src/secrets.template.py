import os

SERVER_COOKIE_KEY = b'' # generate by running this script

YOUTUBE_DEVELOPER_KEY = '' # get one from google
YOUTUBE_CHANNEL_ID = '' # youtube channel id selectable for search
YOUTUBE_CHANNEL_NAME = '' # display name for channel

DB_NAME = 'howtoapp'
DB_URL = 'mongodb://localhost:27018'
EXPORT_PASSWORD = '' # fill with a secure password for exporting database content

HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', 8787))

# for use over https://localhost:8787, use the ssl/generate.sh script to make a trust a new SSL certificate
SSL_CRT = 'ssl/localhost.crt'
SSL_KEY = 'ssl/localhost.key'
USE_SSL = True # note that youtube disallow playing some videos without HTTPS

if __name__ == '__main__':
    # generate server cookie key
    from cryptography import fernet
    import base64
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    print('SERVER_COOKIE_KEY =', secret_key)

