import os, atexit, pickle
from os.path import isfile
from Crypto.PublicKey import RSA
from flask import Flask, request, abort

from user import *
from digital_envelope import *

class Server:
    PRIVATE_KEY_PATH = 'server_private.pem'
    PUBLIC_KEY_PATH  = 'server_public.pem'
    DATABASE_FILE    = 'server_database.db'

    def __init__(self):
        self.private_key = ''
        self.public_key  = ''
        self.users       = {} # TODO: SQL로 구현할 것

        if not isfile(self.PRIVATE_KEY_PATH) or not isfile(self.PUBLIC_KEY_PATH):
            print('[SERVER] 인증서가 없습니다. 인증서를 생성합니다.')
            self.gen_cert()
            print('[SERVER] 인증서 생성 완료!')
        else:
            self.load_cert()
            print('[SERVER] 인증서 로드 완료!')
        
        self.load_database()

    def gen_cert(self, bits=2048):
        key = RSA.generate(bits)
        private_key = key.export_key()
        with open(self.PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_key)
        public_key = key.publickey().export_key()
        with open(self.PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_key)

    def load_cert(self):
        self.private_key = open(self.PRIVATE_KEY_PATH).read()
        self.public_key  = open(self.PUBLIC_KEY_PATH).read()

    def load_database(self):
        if isfile(self.DATABASE_FILE):
            with open(self.DATABASE_FILE, 'rb') as f:
                self.users = pickle.load(f)
            print('[SERVER] 사용자 데이터베이스를 로드했습니다.')

    def save_database(self):
        with open(self.DATABASE_FILE, 'wb') as f:
            pickle.dump(self.users, f)

    def register_user(self, name, public_key):
        account_num = f'1111-{len(self.users):04}'
        new_user    = User(name, account_num, 0, public_key) # 초기 금액은 0원
        self.users.append(new_user)
        return new_user


if __name__ == '__main__':
    # 서버 객체 생성
    server = Server()

    # 종료시 데이터베이스 저장
    def close_handler():
        print('[SERVER] 데이터베이스를 저장하는 중...')
        server.save_database()
    atexit.register(close_handler)

    # 플라스크 웹 서버 생성
    app = Flask(__name__)

    @app.route('/register')
    def register():
        try:
            name       = request.args.get('name', '').strip()
            public_key = request.args.get('public_key')
        except:
            abort(403)

    app.run(host='0.0.0.0', port=5000)