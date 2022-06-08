import sys, glob
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from client import *
client = None

class LoginDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/client_login.ui', self)
    
        cert_list = glob.glob(PRIVATE_KEY_PATH.format('*', '*'))
        def conv(x):
            x = x[5:-12].split('-')
            return f'{x[2]}: {x[0]}-{x[1]}'
        account_list = list(map(conv, cert_list))
        self.btn_login.clicked.connect(self.on_click_login)
        self.btn_register.clicked.connect(self.on_click_register)
        self.combo_account.addItems(account_list)

    def on_click_login(self):
        if self.combo_account.count() == 0:
            QMessageBox.warning(self, self.windowTitle(), '회원가입을 먼저 해주세요.')
            return
        global client
        name, account_num = self.combo_account.currentText().split(': ')
        private_key = open(PRIVATE_KEY_PATH.format(account_num, name)).read()
        public_key  = open(PUBLIC_KEY_PATH.format(account_num, name)).read()
        client = Client(account_num, private_key, public_key)
        print(client)
        self.close()

    def on_click_register(self):
        RegisterDialog().show()
        self.close()


class RegisterDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/client_register.ui', self)
        self.btn_register.clicked.connect(self.on_click_register)

    def on_click_register(self):
        name     = self.txt_name.text().strip().replace(':', '')
        password = self.txt_name.text()
        if not name:
            QMessageBox.warning(self, self.windowTitle(), '이름을 입력해 주세요.')
            return
        if not password:
            QMessageBox.warning(self, self.windowTitle(), '비밀번호를 입력해 주세요.')
            return
        try:
            account_num = Client.register(name, password)
            QMessageBox.information(self, self.windowTitle(), f'성공적으로 회원가입되었습니다.\n\n계좌 번호: {account_num}')
            LoginDialog().show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, self.windowTitle(), str(e))




if __name__ == '__main__':
    app = QApplication(sys.argv)
    LoginDialog().show()
    sys.exit(app.exec_())

