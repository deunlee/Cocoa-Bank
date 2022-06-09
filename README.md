# Cocoa-Bank


## 환경 구성 및 실행
1. Python 3.8 이상 설치
1. 필요한 패키지 설치
   - `pip install -r requirements.txt`
1. 서버 실행 (포트: 5000)
   - `python src/server.py`
   - **중요:** 서버 종료시 Ctrl+C 키를 사용할 것 (콘솔 창의 X버튼 누르면 데이터가 저장되지 않음)
1. 클라이언트에 서버 공개키 등록
   - `src/client.py` 코드 열기
   - `server-public.pem` 파일 내용으로 `SERVER_PUBLIC_KEY` 변수 수정
1. 클라이언트 실행
   - `python src/client_ui.py`

## 로그인 오류 메시지
- RSA key format is not supported
  - 클라이언트에 서버 공개키 등록 안됨
- Incorrect decryption.
  - 패킷이 변조되었거나, 서버 공개키가 변경됨

## TODO
- 변경내역 발생시 자동 새로고침
- 사용자 데이터베이스 MariaDB로 변경
- 오류 메시지 암호화해서 전송
- ATM 입금/출금 구현
- UI 디자인 개선

## 배포용 실행파일 빌드
```sh
pip install pyinstaller
easy_install pyinstaller
pyinstaller --onefile src/server.py
pyinstaller --onefile --add-data "ui;ui" src/client_ui.py
```

<!-- pyi-makespec --onefile src/client_ui.py # --noconsole -->
<!-- pyinstaller client_ui.spec -->
<!-- https://stackoverflow.com/questions/41870727/pyinstaller-adding-data-files -->

<!-- openssl rsa -in server-private.pem -text -inform PEM -noout -->
