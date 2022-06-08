class User:
    def __init__(self, name: str, account_num: str, balance: int):
        self.name        = name.strip()
        self.account_num = account_num
        self.balance     = balance
        self.public_key  = None
        self.log         = []

    def add_log(self, message: str):
        self.log.append(message)
    
    def set_public_key(self, public_key: str):
        self.public_key = public_key

    def deposit(self, name_from: str, amount: int) -> bool:
        if amount <= 0 or type(amount) is not int:
            raise Exception('금액은 자연수이어야 합니다.')
        self.balance += amount
        self.add_log(f'입금: {name_from} ({amount}원)')
        return True

    def withdraw(self, name_to: str, amount: int):
        if amount <= 0 or type(amount) is not int:
            raise Exception('금액은 자연수이어야 합니다.')
        if self.balance < amount and not self.is_atm():
            raise Exception('잔액이 부족합니다.')
        self.balance -= amount
        self.add_log(f'출금: {name_to} ({amount}원)')
        return True

    def is_atm(self):
        # 9999로 시작하는 계좌는 ATM 계좌
        return self.account_num.startswith('9999-')
