import json
import bcrypt
import requests
from Crypto.PublicKey import RSA

from aes import AESCryptoCBC
from user import User
from digital_envelope import DigitalEnvelope

SERVER_IP   = '127.0.0.1'
SERVER_PORT = 5000

SERVER_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
-----END PUBLIC KEY-----""" # 여기 수정해야 함
# TODO: CA를 구현하면 서버 공개키를 하드코딩하지 않아도 됨

PRIVATE_KEY_PATH = 'user-{0}-{1}-private.pem'
PUBLIC_KEY_PATH  = 'user-{0}-{1}-public.pem'

class Client:
    def __init__(self, account_num: str, name: str, password: str):
        self.private_key = open(PRIVATE_KEY_PATH.format(account_num, name), 'r').read().split('**')
        self.public_key  = open(PUBLIC_KEY_PATH.format(account_num, name), 'r').read()
        self.account_num = account_num
        self.user: User  = None
        # 비밀번호 확인 후 개인키 파일 복호화
        if not bcrypt.checkpw(password.encode('utf8'), self.private_key[0].encode('utf8')):
            raise Exception('비밀번호가 일치하지 않습니다.')
        crypto = AESCryptoCBC(password)
        self.private_key = crypto.decrypt(self.private_key[1])
        self.load_user_info()

    @staticmethod
    def register(name: str, password: str, bits=2048) -> str:
        print('[CLIENT] 회원가입을 위해 인증서를 생성합니다.')
        key = RSA.generate(bits)
        private_key = key.export_key().decode('utf8')
        public_key  = key.publickey().export_key().decode('utf8')
        print('[CLIENT] 서버에 회원가입을 요청합니다.')
        envelope = DigitalEnvelope() # 전자봉투 생성
        envelope.set_sender_certificate(public_key)
        envelope.set_sender_private_key(private_key)
        envelope.set_receiver_public_key(SERVER_PUBLIC_KEY)
        # 서버에 회원가입 요청
        data     = envelope.encrypt({ 'name': name }) # 전자봉투 암호화
        response = Client.send_request('register', data)
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(private_key)
        data, server_public_key = envelope.decrypt(response) # 전자봉투 복호화
        if server_public_key != SERVER_PUBLIC_KEY:
            raise Exception('공개키가 다릅니다. 해킹 시도일 수 있습니다.')
        account_num = data['account_num']
        print(f'[CLIENT] 회원가입 완료! 발급된 계좌번호는 {account_num} 입니다.')
        # 개인키 파일은 암호화해서 저장 (AES + bcrypt)
        hash        = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')
        crypto      = AESCryptoCBC(password)
        private_key = hash + '**' + crypto.encrypt(private_key)
        with open(PRIVATE_KEY_PATH.format(account_num, name), 'w') as f:
            f.write(private_key)
        with open(PUBLIC_KEY_PATH.format(account_num, name), 'w') as f:
            f.write(public_key)
        print('[CLIENT] 인증서 및 비밀번호가 저장되었습니다.')
        return account_num

    @staticmethod
    def send_request(route, data=None):
        response = None
        try:
            response = requests.post(f'http://{SERVER_IP}:{SERVER_PORT}/{route}', { 'data': data })
        except Exception as e:
            raise Exception('서버에 요청할 수 없습니다.')
        if response.status_code != 200:
            raise Exception('서버에 요청하는데 오류가 발생했습니다.')
        data = json.loads(response.content.decode('utf8'))
        if data['success'] != True:
            raise Exception(data['data'])
        return data['data']

    # 전자봉투 암호화
    def encrypt_digital_envelope(self, plain_data: dict) -> str:
        envelope = DigitalEnvelope()
        envelope.set_sender_certificate(self.public_key)
        envelope.set_sender_private_key(self.private_key)
        envelope.set_receiver_public_key(SERVER_PUBLIC_KEY)
        return envelope.encrypt(plain_data)

    # 전자봉투 복호화
    def decrypt_digital_envelope(self, encrypted_data: str) -> str:
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(self.private_key)
        data, server_public_key = envelope.decrypt(encrypted_data)
        if SERVER_PUBLIC_KEY != server_public_key:
            raise Exception('서버의 공개키가 다릅니다.')
        return data

    # 서버로부터 사용자 정보 불러오기
    def load_user_info(self):
        print('[CLIENT] 서버로부터 사용자 정보를 불러옵니다.')
        try:
            encrypted = self.encrypt_digital_envelope({ 'account_num': self.account_num }) # 전자봉투 암호화
            response  = Client.send_request('check', encrypted) # 서버에 요청
            decrypted = self.decrypt_digital_envelope(response) # 전자봉투 복호화
            self.user = User(decrypted['name'], self.account_num, decrypted['balance'])
            self.user.logs = decrypted['logs']
            print(f'[CLIENT] 로그인된 사용자: ({self.user.name}: {self.account_num})')
            print(f'[CLIENT] 현재까지 거래내역은 {len(self.user.logs)}건, 잔액은 {self.user.balance}원 입니다.')
        except Exception as e:
            print(f'[CLIENT] 사용자 정보 불러오기 실패: {str(e)}')
            raise e

    # 송금 요청
    def transfer(self, account_to: str, amount: int):
        print(f'[CLIENT] {account_to}에게 {amount}원을 송금합니다.')
        try:
            encrypted = self.encrypt_digital_envelope({ # 전자봉투 암호화
                'account_num' : self.account_num,
                'account_to'  : account_to,
                'amount'      : amount,
            })
            response  = Client.send_request('transfer', encrypted) # 서버에 요청
            decrypted = self.decrypt_digital_envelope(response)    # 전자봉투 복호화
            self.user.balance = decrypted['balance']
            self.user.logs    = decrypted['logs']
            # print(self.user.logs)
            print(f'[CLIENT] 성공적으로 송금되었습니다. (잔액 {self.user.balance}원)')
        except Exception as e:
            print(f'[CLIENT] 송금 실패: {str(e)}')
            raise e




if __name__ == '__main__':
    password = 'secret'
    hash = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode('utf8')
    print(hash)
    print(bcrypt.checkpw(password.encode('utf8'), hash.encode('utf8')))
