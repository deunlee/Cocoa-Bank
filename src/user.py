class User:
    def __init__(self, name, account_num, amount, public_key):
        self.name        = name
        self.account_num = account_num
        self.amount      = amount
        self.public_key  = public_key
        self.log         = []

    def add_log(self, message):
        self.log.append(message)
        