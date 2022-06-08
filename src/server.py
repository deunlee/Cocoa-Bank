import atexit, json, pickle
from os.path import isfile
from Crypto.PublicKey import RSA
from flask import Flask, request

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
        self.load_database() # 데이터베이스 로드

    def gen_cert(self, bits=2048):
        key = RSA.generate(bits)
        self.private_key = key.export_key()
        with open(self.PRIVATE_KEY_PATH, 'wb') as f:
            f.write(self.private_key)
        self.public_key = key.publickey().export_key()
        with open(self.PUBLIC_KEY_PATH, 'wb') as f:
            f.write(self.public_key)

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

    # 전자봉투 암호화
    def encrypt_digital_envelope(self, plain_data: dict, client_public_key: str) -> str:
        envelope = DigitalEnvelope()
        envelope.set_sender_certificate(self.public_key)
        envelope.set_sender_private_key(self.private_key)
        envelope.set_receiver_public_key(client_public_key)
        return envelope.encrypt(json.dumps(plain_data))

    # 전자봉투 복호화
    def decrypt_digital_envelope(self, encrypted_data: str):
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(self.private_key)
        data, client_public_key = envelope.decrypt(encrypted_data)
        return (json.loads(data), client_public_key)

    # 사용자 정보 가져오기
    def get_user_info(self, account_num: str, public_key: str) -> User:
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('가입된 사용자가 아닙니다.')
        if user.public_key != public_key:
            raise Exception('공개키가 다릅니다.')
        return user
    
    # 회원 가입 (계좌 개설)
    def register_user(self, name: str, public_key: str) -> User:
        account_num = f'1111-{len(self.users):04}'
        new_user    = User(name, account_num, 1100, public_key) # 초기 금액은 0원
        self.users[account_num] = new_user
        return new_user
    
    # 입금 (ATM -> User)
    def deposit(self, account_num: str, amount: int):
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('계좌를 찾을 수 없습니다.')
        user.deposit('ATM', amount)

    # 출금 (User -> ATM)
    def withdraw(self, account_num: str, amount: int):
        user: User = self.users.get(account_num)
        if not user:
            raise Exception('계좌를 찾을 수 없습니다.')
        user.withdraw('ATM', amount)

    # 송금 (User -> User)
    def transfer(self, account_from: str, account_to: str, amount: int):
        user_from: User = self.users.get(account_from)
        user_to: User   = self.users.get(account_to)
        if not user_from:
            raise Exception('보내는 사람 계좌를 찾을 수 없습니다.')
        if not user_from:
            raise Exception('받는 사람 계좌를 찾을 수 없습니다.')
        user_from.withdraw(user_to.name, amount) # 보내는 사람 계좌에서 금액 차감
        user_to.deposit(user_from.name, amount)  # 받는 사람 계좌에 해당 금액 추가


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
    flask_ip   = '0.0.0.0'
    flask_port = 5000

    def res_ok(data):
        return { 'success': False, 'data': data }
    def res_fail(message):
        return { 'success': False, 'data': message }


    # 회원 가입 (계좌 개설)
    @app.route('/register', methods=['POST'])
    def route_register():
        try:
            encrypted_data = request.args.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.register_user(data['name'], client_public_key) # 사용자 등록
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'name'        : user.name,
                'account_num' : user.account_num
            }, client_public_key))
        except:
            return res_fail('알 수 없는 오류가 발생하였습니다.')


    # 계좌 조회
    @app.route('/check', methods=['POST'])
    def route_check():
        try:
            encrypted_data = request.args.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.get_user_info(data['account_num'], client_public_key)
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'balance' : user.balance,
                'log'     : user.log
            }, client_public_key))
        except:
            return res_fail('알 수 없는 오류가 발생하였습니다.')


    # 이체 (입금/출금/송금)
    @app.route('/transfer', methods=['POST'])
    def route_transfer():
        try:
            encrypted_data = request.args.get('data')
            data, client_public_key = server.decrypt_digital_envelope(encrypted_data) # 전자봉투 복호화
            user = server.get_user_info(data['account_num'], client_public_key)
            server.transfer(user.account_num, data['account_to'], data['amount'])
            return res_ok(server.encrypt_digital_envelope({ # 전자봉투로 암호화해서 전송
                'balance' : user.balance
            }, client_public_key))
        except:
            return res_fail('알 수 없는 오류가 발생하였습니다.')


    # 서버 공개키
    @app.route('/server_public', methods=['POST'])
    def route_server_public():
        # TODO: CA를 구현해서 공개키 변조여부도 확인해야 함
        return res_ok(server.public_key)


    # 변경내역 확인용
    @app.route('/log_count', methods=['POST'])
    def route_log_count():
        try:
            account_num = request.args.get('account_num')
            user        = server.users.get(account_num)
            if not user:            
                return res_fail('가입된 사용자가 아닙니다.')
            return res_ok(len(user.log))
        except:
            return res_fail('알 수 없는 오류가 발생하였습니다.')


    print(f'[SERVER] 서버를 시작합니다 ({flask_ip}:{flask_port})')
    app.run(host=flask_ip, port=flask_port)
