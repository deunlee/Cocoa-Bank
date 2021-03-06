import os
import logging
import atexit
import pickle
import traceback
from os.path import isfile
from Crypto.PublicKey import RSA
from flask import Flask, request
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from user import User
from digital_envelope import DigitalEnvelope

SERVER_IP   = '0.0.0.0'
SERVER_PORT = 5000

PRIVATE_KEY_PATH = 'server-private.pem'
PUBLIC_KEY_PATH  = 'server-public.pem'
DATABASE_FILE    = 'server-database.db'

class Server:
    def __init__(self):
        self.private_key = ''
        self.public_key  = ''
        self.users       = {}
        if not isfile(PRIVATE_KEY_PATH) or not isfile(PUBLIC_KEY_PATH):
            self.gen_cert()
        else:
            self.load_cert()
        self.load_database() # 데이터베이스 로드

    def gen_cert(self, bits=2048):
        print('[SERVER] 인증서를 생성합니다.')
        key = RSA.generate(bits)
        self.private_key = key.export_key().decode('utf8')
        self.public_key  = key.publickey().export_key().decode('utf8')
        with open(PRIVATE_KEY_PATH, 'w') as f:
            f.write(self.private_key)
        with open(PUBLIC_KEY_PATH, 'w') as f:
            f.write(self.public_key)
        print('[SERVER] 인증서 생성 완료!')

    def load_cert(self):
        self.private_key = open(PRIVATE_KEY_PATH, 'r').read()
        self.public_key  = open(PUBLIC_KEY_PATH, 'r').read()
        print('[SERVER] 인증서 로드 완료!')

    def load_database(self):
        if isfile(DATABASE_FILE):
            with open(DATABASE_FILE, 'rb') as f:
                self.users = pickle.load(f)
            print('[SERVER] 사용자 데이터베이스를 로드했습니다.')

    def save_database(self):
        with open(DATABASE_FILE, 'wb') as f:
            pickle.dump(self.users, f)

    # 전자봉투 암호화
    def encrypt_digital_envelope(self, plain_data: dict, client_public_key: str) -> str:
        envelope = DigitalEnvelope()
        envelope.set_sender_certificate(self.public_key)
        envelope.set_sender_private_key(self.private_key)
        envelope.set_receiver_public_key(client_public_key)
        return envelope.encrypt(plain_data)

    # 전자봉투 복호화
    def decrypt_digital_envelope(self, encrypted_data: str):
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(self.private_key)
        data, client_public_key = envelope.decrypt(encrypted_data)
        return (data, client_public_key)

    # 사용자 정보 가져오기
    def get_user_info(self, account_num: str, public_key: str) -> User:
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('가입된 사용자가 아닙니다.')
        if user.public_key != public_key:
            raise Exception('공개키가 다릅니다. 해킹 시도일 수 있습니다.')
        return user
    
    # 회원 가입 (계좌 개설)
    def register(self, name: str, public_key: str) -> User:
        account_num = f'1111-{len(self.users)+1:04}'
        new_user    = User(name, account_num, 100000)
        new_user.set_public_key(public_key)
        self.users[account_num] = new_user
        self.save_database()
        return new_user
    
    # 입금 (ATM -> User)
    def deposit(self, account_num: str, amount: int):
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('계좌를 찾을 수 없습니다.')
        user.deposit('ATM', amount)
        self.save_database()

    # 출금 (User -> ATM)
    def withdraw(self, account_num: str, amount: int):
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('계좌를 찾을 수 없습니다.')
        user.withdraw('ATM', amount)
        self.save_database()

    # 송금 (User -> User)
    def transfer(self, account_from: str, account_to: str, amount: int, timestamp: int):
        if account_from == account_to:
            raise Exception('본인에게 이체할 수 없습니다.')
        user_from: User = self.users.get(account_from)
        user_to: User   = self.users.get(account_to)
        if not user_from:
            raise Exception('보내는 사람 계좌를 찾을 수 없습니다.')
        if not user_to:
            raise Exception('받는 사람 계좌를 찾을 수 없습니다.')
        user_from.withdraw(user_to.name, amount, timestamp) # 보내는 사람 계좌에서 금액 차감
        user_to.deposit(user_from.name, amount, timestamp)  # 받는 사람 계좌에 해당 금액 추가
        self.save_database()


if __name__ == '__main__':
    # 서버 객체 생성
    server = Server()

    # 종료시 데이터베이스 저장
    def close_handler():
        print('[SERVER] 데이터베이스를 저장합니다.')
        server.save_database()
    atexit.register(close_handler)

    # 플라스크 웹 서버 생성
    os.environ['FLASK_ENV'] = 'development'
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    def res_ok(data):
        return { 'success': True, 'data': data }
    def res_fail(message):
        return { 'success': False, 'data': message }


    # 회원 가입 (계좌 개설)
    @app.route('/register', methods=['POST'])
    def route_register():
        try:
            encrypted_data = request.form.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.register(data['name'], client_public_key) # 사용자 등록
            print(f'[SERVER] 회원가입 // {user.name}: {user.account_num}')
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'account_num': user.account_num
            }, client_public_key))
        except Exception as e:
            print(f'[SERVER] 회원가입 오류: {str(e)}')
            # traceback.print_exc()
            return res_fail(str(e))


    # 계좌 조회
    @app.route('/check', methods=['POST'])
    def route_check():
        try:
            encrypted_data = request.form.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.get_user_info(data['account_num'], client_public_key)
            print(f'[SERVER] 계좌 조회 // {user.name}: {user.account_num} // 잔액 {user.balance}원')
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'name'    : user.name,
                'balance' : user.balance,
                'logs'    : user.logs
            }, client_public_key))
        except Exception as e:
            print(f'[SERVER] 계좌 조회 오류: {str(e)}')
            # traceback.print_exc()
            return res_fail(str(e))


    # 이체 (입금/출금/송금)
    @app.route('/transfer', methods=['POST'])
    def route_transfer():
        try:
            encrypted_data = request.form.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.get_user_info(data['account_num'], client_public_key)
            server.transfer(user.account_num, data['account_to'], int(data['amount']), int(data['timestamp']))
            user_to = server.users.get(data['account_to'])
            print(f'[SERVER] 이체 // ({user.name}: {user.account_num}) ==> ({user_to.name}: {user_to.account_num}) // {data["amount"]}원')
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'balance' : user.balance,
                'logs'    : user.logs
            }, client_public_key))
        except Exception as e:
            print(f'[SERVER] 이체 오류: {str(e)}')
            # traceback.print_exc()
            return res_fail(str(e))

    @app.route('/log_count', methods=['POST'])
    def route_log_count():
        try:
            account_num = request.form.get('account_num')
            user        = server.users.get(account_num)
            if not user:            
                return res_fail('가입된 사용자가 아닙니다.')
            return res_ok(len(user.logs))
        except Exception as e:
            # traceback.print_exc()
            return res_fail(str(e))


    print(f'[SERVER] 서버를 시작합니다 ({SERVER_IP}:{SERVER_PORT})')
    app.run(host=SERVER_IP, port=SERVER_PORT, use_reloader=False)
