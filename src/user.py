from datetime import datetime

class User:
    def __init__(self, name: str, account_num: str, balance: int):
        self.name        = name.strip()
        self.account_num = account_num
        self.balance     = balance
        self.public_key  = None
        self.last_time   = 0 # replay attack 방지용
        self.logs        = []

    def get_time_str(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def set_public_key(self, public_key: str):
        self.public_key = public_key

    def deposit(self, name_from: str, amount: int, timestamp: int):
        if self.last_time >= timestamp:
            raise Exception('재전송 공격 감지됨! 해킹 시도일 수 있습니다')
        self.last_time = timestamp
        if amount <= 0 or type(amount) is not int:
            raise Exception('금액은 자연수이어야 합니다.')
        self.balance += amount
        self.logs.append({
            'type'    : 'deposit',
            'message' : name_from,
            'amount'  : amount,
            'time'    : self.get_time_str()
        })

    def withdraw(self, name_to: str, amount: int, timestamp: int):
        if self.last_time >= timestamp:
            raise Exception('재전송 공격 감지됨! 해킹 시도일 수 있습니다')
        self.last_time = timestamp
        if amount <= 0 or type(amount) is not int:
            raise Exception('금액은 자연수이어야 합니다.')
        if self.balance < amount and not self.is_atm():
            raise Exception('잔액이 부족합니다.')
        self.balance -= amount
        self.logs.append({
            'type'    : 'withdraw',
            'message' : name_to,
            'amount'  : amount,
            'time'    : self.get_time_str()
        })

    def is_atm(self):
        # 9999로 시작하는 계좌는 ATM 계좌
        return self.account_num.startswith('9999-')

    @staticmethod
    def get_timestamp():
        return int(datetime.now().timestamp() * 1000)
