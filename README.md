# Cocoa-Bank


## 환경 구성 및 실행
1. Python 3.8 이상 설치
1. 필요한 패키지 설치
   - `pip install -r requirements.txt`
1. 서버 실행 (포트: 5000)
   - `python src/server.py`
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
