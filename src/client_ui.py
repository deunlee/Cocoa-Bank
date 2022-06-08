import sys, glob
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtWidgets import *

from client import *

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/ui_login.ui', self)
    
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
        password = self.txt_password.text()
        if not password:
            QMessageBox.warning(self, self.windowTitle(), '비밀번호를 입력해 주세요.')
            return
        name, account_num = self.combo_account.currentText().split(': ')
        window = MainWindow()
        window.set_info(name, account_num)
        window.show()
        self.close()

    def on_click_register(self):
        RegisterWindow().show()
        self.close()



class RegisterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/ui_register.ui', self)
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
            LoginWindow().show()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, self.windowTitle(), str(e))



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ui/ui_main.ui', self)
        self.btn_transfer.clicked.connect(self.on_click_transfer)
        self.btn_refresh.clicked.connect(self.on_click_refresh)
        self.client = None
        # self.timer = QTimer(self)
        # self.timer.setInterval(1000)
        # self.timer.timeout.connect(self.on_click_refresh)
        # self.timer.start()    

    def set_info(self, name, account_num):
        try:
            private_key = open(PRIVATE_KEY_PATH.format(account_num, name)).read()
            public_key  = open(PUBLIC_KEY_PATH.format(account_num, name)).read()
            self.client = Client(account_num, private_key, public_key)
        except Exception as e:
            QMessageBox.critical(self, self.windowTitle(), str(e))
            self.close()
        self.label_info.setText(f'{name} {account_num}')
        self.on_click_refresh()

    def on_click_refresh(self):
        self.client.load_user_info()
        self.label_balance.setText(f'{format(self.client.user.balance, ",")}원')
        print(self.client.user.log)

    def on_click_transfer(self):
        window = TransferWindow(self.client)
        window.show()
        window.exec_()
        self.on_click_refresh()



class TransferWindow(QDialog):
    def __init__(self, client: Client):
        super().__init__()
        self.ui = uic.loadUi('ui/ui_transfer.ui', self)
        self.client = client
        self.btn_transfer.clicked.connect(self.on_click_transfer)

    def on_click_transfer(self):
        self.btn_transfer.setEnabled(False)
        account_to = self.txt_account.text()
        amount     = int(self.txt_amount.text())
        if not account_to:
            QMessageBox.warning(self, self.windowTitle(), '받는 사람 계좌 번호를 입력해 주세요.')
            return
        if amount <= 0:
            QMessageBox.warning(self, self.windowTitle(), '금액을 정확히 입력해 주세요.')
            return
        try:
            self.client.transfer(account_to, amount)
            QMessageBox.information(self, self.windowTitle(), '성공적으로 이체되었습니다.')
            self.close()
        except Exception as e:
            QMessageBox.critical(self, self.windowTitle(), str(e))
        self.btn_transfer.setEnabled(True)





if __name__ == '__main__':
    app = QApplication(sys.argv)
    LoginWindow().show()
    sys.exit(app.exec_())
