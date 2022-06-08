import json
from Crypto.PublicKey import RSA

from digital_envelope import *


class Client:
    PRIVATE_KEY_PATH = 'user_private.pem'
    PUBLIC_KEY_PATH  = 'user_public.pem'

    def __init__(self, name, account_number):
        self.name = name                     # 이름
        self.account_number = account_number # 계좌 번호
        self.private_key = None
        self.public_key  = None
        
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


    user = Client('철수', '1000-1234')
    # user.gen_cert()
    user.load_cert()

    user.transfer('1000-5555', 1000)

