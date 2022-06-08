import json, requests
from os.path import isfile
from Crypto.PublicKey import RSA

from user import User
from digital_envelope import DigitalEnvelope

SERVER_IP   = '127.0.0.1'
SERVER_PORT = 5000


PRIVATE_KEY_PATH = 'user-{0}-private.pem'
PUBLIC_KEY_PATH  = 'user-{0}-public.pem'

class Client:
    def __init__(self, account_num: str):
        self.name        : str  = None
        self.private_key : str  = None
        self.public_key  : str  = None
        self.account_num : str  = account_num
        self.user        : User = None
        self.load_cert()
        self.load_user_info()

    def load_cert(self):
        self.private_key = open(PRIVATE_KEY_PATH.format(self.account_num)).read()
        self.public_key  = open(PUBLIC_KEY_PATH.format(self.account_num)).read()
        print('[CLIENT] 인증서 로드 완료!')

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
        envelope.set_receiver_public_key(SERVER_PUBLIC)
        # 서버에 회원가입 요청
        data     = envelope.encrypt({ 'name': name }) # 전자봉투 암호화
        response = Client.send_request('register', data)
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(private_key)
        data, server_public_key = envelope.decrypt(response) # 전자봉투 복호화
        if server_public_key != SERVER_PUBLIC:
            raise Exception('공개키가 다릅니다. 해킹 시도일 수 있습니다.')
        account_num = data['account_num']
        print(f'[CLIENT] 회원가입 완료! 발급된 계좌번호는 {account_num} 입니다.')
        with open(PRIVATE_KEY_PATH.format(account_num), 'w') as f:
            f.write(private_key)
        with open(PUBLIC_KEY_PATH.format(account_num), 'w') as f:
            f.write(public_key)
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
        envelope.set_receiver_public_key(SERVER_PUBLIC)
        return envelope.encrypt(plain_data)

    # 전자봉투 복호화
    def decrypt_digital_envelope(self, encrypted_data: str) -> str:
        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(self.private_key)
        data, server_public_key = envelope.decrypt(encrypted_data)
        if SERVER_PUBLIC != server_public_key:
            raise Exception('서버의 공개키가 다릅니다.')
        return data

    # 서버로부터 사용자 정보 불러오기
    def load_user_info(self):
        print('[CLIENT] 서버로부터 사용자 정보를 불러옵니다.')
        data     = self.encrypt_digital_envelope({ 'account_num': self.account_num }) # 전자봉투 암호화
        response = Client.send_request('check', data)
        data     = self.decrypt_digital_envelope(response) # 전자봉투 복호화
        self.user = User(data['name'], self.account_num, data['balance'])
        self.user.log
        print(f'[CLIENT] 로그인되었습니다. ({self.user.name}: {self.account_num})')
        print(f'[CLIENT] 현재까지 거래내역은 {len(self.user.log)}건, 잔액은 {self.user.balance}원 입니다.')



if __name__ == '__main__':
    # 회원 가입 (계좌 개설)
    name = '김철수'
    password = '1q2w3e4r'
    # account_num = Client.register(name, password)


    # 사용자 객체 생성
    # user = Client(account_num)
    user = Client('1111-0003')


    # user.transfer('1000-5555', 1000)

