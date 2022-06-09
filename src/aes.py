import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

class AESCryptoCBC():
    BLOCK_SIZE = 16

    def __init__(self, key: str):
        self.key = hashlib.sha256(key.encode('utf8')).digest()

    def _pad(self, s):
        t = self.BLOCK_SIZE - len(s) % self.BLOCK_SIZE
        return s + bytes([t]) * t

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    def encrypt(self, plain_data: str) -> str:
        plain_data = self._pad(plain_data.encode('utf8'))
        iv     = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(plain_data)).decode('utf-8')

    def decrypt(self, encrypted_data: str):
        data = base64.b64decode(encrypted_data)
        iv   = data[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(data[AES.block_size:])).decode('utf-8')



if __name__ == '__main__':
    crypto = AESCryptoCBC('secret-key')
    enc = crypto.encrypt('some message')
    print(enc)

    crypto = AESCryptoCBC('secret-key')
    dec = crypto.decrypt(enc)
    print(dec)
