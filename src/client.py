import json
from os.path import isfile
from Crypto.PublicKey import RSA

from digital_envelope import *

class Client:
    PRIVATE_KEY_PATH = 'user_private.pem'
    PUBLIC_KEY_PATH  = 'user_public.pem'

    def __init__(self, name: str, account_num: str):
        self.name              = name
        self.account_num       = account_num
        self.private_key       = None
        self.public_key        = None
        self.server_public_key = None
        if not isfile(self.PRIVATE_KEY_PATH) or not isfile(self.PUBLIC_KEY_PATH):
            print('[CLIENT] 인증서가 없습니다. 인증서를 생성합니다.')
            self.gen_cert()
            print('[CLIENT] 인증서 생성 완료!')
        else:
            self.load_cert()
            print('[CLIENT] 인증서 로드 완료!')

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

    def create_digital_envelope(self):
        envelope = DigitalEnvelope()
        envelope.set_sender_certificate(self.public_key)
        envelope.set_sender_private_key(self.private_key)
        envelope.set_receiver_public_key(self.server_public_key)
        return envelope

    def transfer(self, receiver_account_number, amount):
        envelope = DigitalEnvelope()

        envelope.set_sender_certificate(self.public_key)
        envelope.set_sender_private_key(self.private_key)
        envelope.set_receiver_public_key(open('server_public.pem').read())

        data = {
            'sender': self.account_number,
            'receiver': receiver_account_number,
            'amount': amount
        }
        encrypted = envelope.encrypt(json.dumps(data))

        envelope = DigitalEnvelope()
        envelope.set_receiver_private_key(open('server_private.pem').read())
        print(envelope.decrypt(encrypted))



if __name__ == '__main__':
    # 사용자 객체 생성
    user = Client('철수', '1000-1234')


    user.transfer('1000-5555', 1000)

