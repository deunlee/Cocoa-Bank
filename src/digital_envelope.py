import json
from Crypto.Hash import SHA256
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

class DigitalEnvelope:
    def __init__(self):
        self.sender_certificate   = None # pem 파일 내용
        self.sender_private_key   = None
        self.receiver_public_key  = None
        self.receiver_private_key = None

    def set_sender_certificate(self, cert: str):  # 송신자 인증서
        self.sender_certificate = cert
    def set_sender_private_key(self, key: str):   # 송신자 개인키
        self.sender_private_key = key
    def set_receiver_public_key(self, key: str):  # 수신자 공개키
        self.receiver_public_key = key
    def set_receiver_private_key(self, key: str): # 수신자 개인키
        self.receiver_private_key = key

    def encrypt(self, plain_data: str) -> str:
        if not self.sender_certificate:  raise Exception('송신자 인증서가 필요합니다.')
        if not self.sender_private_key:  raise Exception('송신자 개인키가 필요합니다.')
        if not self.receiver_public_key: raise Exception('수신자 공개키가 필요합니다.')
            
        # 데이터의 해시를 계산 => 무결성
        hash = SHA256.new(plain_data.encode('utf8'))

        # 해시를 송신자의 개인키로 암호화 (부인방지) => 전자 서명
        rsa_key   = RSA.import_key(self.sender_private_key)
        signature = PKCS1_v1_5.new(rsa_key).sign(hash)

        # 비밀키(대칭키) 생성
        session_key = get_random_bytes(16)
        # print('session_key=' + session_key.hex())

        # 원본 데이터, 암호화된 해시, 송신자 인증서를 비밀키(대칭키)로 암호화 => 기밀성
        new_data = {
            'plain_data'    : plain_data,
            'encryptd_hash' : signature.hex(),
            'sender_cert'   : self.sender_certificate
        }
        new_data   = json.dumps(new_data).encode('utf8')
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        cipher_text, cipher_tag = cipher_aes.encrypt_and_digest(new_data)
        encrypted = cipher_text.hex() + '/' + cipher_tag.hex() + '/' + cipher_aes.nonce.hex()

        # 비밀키(대칭키)를 수신자의 공개키로 암호화
        rsa_key         = RSA.import_key(self.receiver_public_key)
        cipher_rsa      = PKCS1_OAEP.new(rsa_key)
        enc_session_key = cipher_rsa.encrypt(session_key)

        # 암호화된 데이터 리턴
        return encrypted + '/' + enc_session_key.hex()


    def decrypt(self, encrypted_data: str):
        if not self.receiver_private_key: raise Exception('수신자 개인키가 필요합니다.')

        # 데이터 분리
        cipher_text, cipher_tag, aes_nonce, enc_session_key = encrypted_data.split('/')
        cipher_text     = bytes.fromhex(cipher_text)
        cipher_tag      = bytes.fromhex(cipher_tag)
        aes_nonce       = bytes.fromhex(aes_nonce)
        enc_session_key = bytes.fromhex(enc_session_key)

        # 비밀키(대칭키)를 수신자의 비밀키로 복호화
        rsa_key     = RSA.import_key(self.receiver_private_key)
        cipher_rsa  = PKCS1_OAEP.new(rsa_key)
        session_key = cipher_rsa.decrypt(enc_session_key)
        # print('session_key=' + session_key.hex())

        # 비밀키로 데이터를 복호화 => 원본 데이터, 암호화된 해시, 송신자의 인증서 획득
        cipher_aes = AES.new(session_key, AES.MODE_EAX, aes_nonce)
        data = cipher_aes.decrypt_and_verify(cipher_text, cipher_tag)
        data = json.loads(data)
        plain_data  = data['plain_data']
        signature   = bytes.fromhex(data['encryptd_hash'])
        sender_cert = data['sender_cert']

        # 데이터의 해시를 계산
        hash = SHA256.new(plain_data.encode('utf8'))

        # 암호화된 해시값을 송신자의 공개키로 복호화하고 비교
        rsa_key = RSA.import_key(sender_cert)
        try:
            PKCS1_v1_5.new(rsa_key).verify(hash, signature)
        except (ValueError, TypeError):
            raise Exception('해시 값이 다릅니다.')

        return (plain_data, sender_cert)
