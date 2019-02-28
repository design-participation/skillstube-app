
SERVER_COOKIE_KEY = b'' # generate by running this script

YOUTUBE_DEVELOPER_KEY = '' # get one from google
YOUTUBE_CHANNEL = '' # target youtube channel

DB_NAME = 'howtoapp'
DB_URL = 'mongodb://localhost:27018'

HOST = 'localhost'
PORT = 8787

# for use over localhost, use the ssl/generate.sh script
SSL_CRT = 'ssl/localhost.crt'
SSL_KEY = 'ssl/localhost.key'
USE_SSL = True

if __name__ == '__main__':
    # generate server cookie key
    from cryptography import fernet
    import base64
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    print('SERVER_COOKIE_KEY =', secret_key)

