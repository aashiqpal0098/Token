import random
import string
import json
import time
import requests
import uuid
import base64
import io
import struct
import sys
import os
from flask import Flask, render_template_string, request, jsonify, session
import threading

# Crypto libraries check
try:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Error: 'pycryptodome' module not found.")
    print("Run: pip install pycryptodome")
    sys.exit()

# ===========================================
# AASHIQ HATELA FACEBOOK LOGIN CLASSES
# ===========================================

class FacebookPasswordEncryptor:
    @staticmethod
    def get_public_key():
        try:
            url = 'https://b-graph.facebook.com/pwd_key_fetch'
            params = {
                'version': '2',
                'flow': 'CONTROLLER_INITIALIZATION',
                'method': 'GET',
                'fb_api_req_friendly_name': 'pwdKeyFetch',
                'fb_api_caller_class': 'com.facebook.auth.login.AuthOperations',
                'access_token': '438142079694454|fc0a7caa49b192f64f6f5a6d9643bb28'
            }
            response = requests.post(url, params=params).json()
            return response.get('public_key'), str(response.get('key_id', '25'))
        except Exception as e:
            raise Exception(f"Public key fetch error: {e}")

    @staticmethod
    def encrypt(password, public_key=None, key_id="25"):
        if public_key is None:
            public_key, key_id = FacebookPasswordEncryptor.get_public_key()

        try:
            rand_key = get_random_bytes(32)
            iv = get_random_bytes(12)
            
            pubkey = RSA.import_key(public_key)
            cipher_rsa = PKCS1_v1_5.new(pubkey)
            encrypted_rand_key = cipher_rsa.encrypt(rand_key)
            
            cipher_aes = AES.new(rand_key, AES.MODE_GCM, nonce=iv)
            current_time = int(time.time())
            cipher_aes.update(str(current_time).encode("utf-8"))
            encrypted_passwd, auth_tag = cipher_aes.encrypt_and_digest(password.encode("utf-8"))
            
            buf = io.BytesIO()
            buf.write(bytes([1, int(key_id)]))
            buf.write(iv)
            buf.write(struct.pack("<h", len(encrypted_rand_key)))
            buf.write(encrypted_rand_key)
            buf.write(auth_tag)
            buf.write(encrypted_passwd)
            
            encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"#PWD_FB4A:2:{current_time}:{encoded}"
        except Exception as e:
            raise Exception(f"Encryption error: {e}")


class FacebookAppTokens:
    APPS = {
        'FB_ANDROID': {'name': 'Facebook For Android', 'app_id': '350685531728'},
        'MESSENGER_ANDROID': {'name': 'Facebook Messenger For Android', 'app_id': '256002347743983'},
        'FB_LITE': {'name': 'Facebook For Lite', 'app_id': '275254692598279'},
        'MESSENGER_LITE': {'name': 'Facebook Messenger For Lite', 'app_id': '200424423651082'},
        'ADS_MANAGER_ANDROID': {'name': 'Ads Manager App For Android', 'app_id': '438142079694454'},
        'PAGES_MANAGER_ANDROID': {'name': 'Pages Manager For Android', 'app_id': '121876164619130'}
    }
    
    @staticmethod
    def get_app_id(app_key):
        app = FacebookAppTokens.APPS.get(app_key)
        return app['app_id'] if app else None
    
    @staticmethod
    def get_all_app_keys():
        return list(FacebookAppTokens.APPS.keys())
    
    @staticmethod
    def extract_token_prefix(token):
        for i, char in enumerate(token):
            if char.islower():
                return token[:i]
        return token


class FacebookLogin:
    API_URL = "https://b-graph.facebook.com/auth/login"
    ACCESS_TOKEN = "350685531728|62f8ce9f74b12f84c123cc23437a4a32"
    API_KEY = "882a8490361da98702bf97a021ddc14d"
    SIG = "214049b9f17c38bd767de53752b53946"
    
    BASE_HEADERS = {
        "content-type": "application/x-www-form-urlencoded",
        "x-fb-net-hni": "45201",
        "zero-rated": "0",
        "x-fb-sim-hni": "45201",
        "x-fb-connection-quality": "EXCELLENT",
        "x-fb-friendly-name": "authenticate",
        "x-fb-connection-bandwidth": "78032897",
        "x-tigon-is-retry": "False",
        "authorization": "OAuth null",
        "x-fb-connection-type": "WIFI",
        "x-fb-device-group": "3342",
        "priority": "u=3,i",
        "x-fb-http-engine": "Liger",
        "x-fb-client-ip": "True",
        "x-fb-server-cluster": "True"
    }
    
    def __init__(self, uid_phone_mail, password, machine_id=None, convert_token_to=None, convert_all_tokens=False):
        self.uid_phone_mail = uid_phone_mail
        
        if password.startswith("#PWD_FB4A"):
            self.password = password
        else:
            self.password = FacebookPasswordEncryptor.encrypt(password)
        
        if convert_all_tokens:
            self.convert_token_to = FacebookAppTokens.get_all_app_keys()
        elif convert_token_to:
            self.convert_token_to = convert_token_to if isinstance(convert_token_to, list) else [convert_token_to]
        else:
            self.convert_token_to = []
        
        self.session = requests.Session()
        
        self.device_id = str(uuid.uuid4())
        self.adid = str(uuid.uuid4())
        self.secure_family_device_id = str(uuid.uuid4())
        self.machine_id = machine_id if machine_id else self._generate_machine_id()
        self.jazoest = ''.join(random.choices(string.digits, k=5))
        self.sim_serial = ''.join(random.choices(string.digits, k=20))
        
        self.headers = self._build_headers()
        self.data = self._build_data()
    
    @staticmethod
    def _generate_machine_id():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    
    def _build_headers(self):
        headers = self.BASE_HEADERS.copy()
        headers.update({
            "x-fb-request-analytics-tags": '{"network_tags":{"product":"350685531728","retry_attempt":"0"},"application_tags":"unknown"}',
            "user-agent": "Dalvik/2.1.0 (Linux; U; Android 9; 23113RKC6C Build/PQ3A.190705.08211809) [FBAN/FB4A;FBAV/417.0.0.33.65;FBPN/com.facebook.katana;FBLC/vi_VN;FBBV/480086274;FBCR/MobiFone;FBMF/Redmi;FBBD/Redmi;FBDV/23113RKC6C;FBSV/9;FBCA/x86:armeabi-v7a;FBDM/{density=1.5,width=1280,height=720};FB_FW/1;FBRV/0;]"
        })
        return headers
    
    def _build_data(self):
        base_data = {
            "format": "json",
            "email": self.uid_phone_mail,
            "password": self.password,
            "credentials_type": "password",
            "generate_session_cookies": "1",
            "locale": "vi_VN",
            "client_country_code": "VN",
            "api_key": self.API_KEY,
            "access_token": self.ACCESS_TOKEN
        }
        
        base_data.update({
            "adid": self.adid,
            "device_id": self.device_id,
            "generate_analytics_claim": "1",
            "community_id": "",
            "linked_guest_account_userid": "",
            "cpl": "true",
            "try_num": "1",
            "family_device_id": self.device_id,
            "secure_family_device_id": self.secure_family_device_id,
            "sim_serials": f'["{self.sim_serial}"]',
            "openid_flow": "android_login",
            "openid_provider": "google",
            "openid_tokens": "[]",
            "account_switcher_uids": f'["{self.uid_phone_mail}"]',
            "fb4a_shared_phone_cpl_experiment": "fb4a_shared_phone_nonce_cpl_at_risk_v3",
            "fb4a_shared_phone_cpl_group": "enable_v3_at_risk",
            "enroll_misauth": "false",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "machine_id": self.machine_id,
            "jazoest": self.jazoest,
            "meta_inf_fbmeta": "V2_UNTAGGED",
            "advertiser_id": self.adid,
            "encrypted_msisdn": "",
            "currently_logged_in_userid": "0",
            "fb_api_req_friendly_name": "authenticate",
            "fb_api_caller_class": "Fb4aAuthHandler",
            "sig": self.SIG
        })
        
        return base_data
    
    def _convert_token(self, access_token, target_app):
        try:
            app_id = FacebookAppTokens.get_app_id(target_app)
            if not app_id:
                return None
            
            response = requests.post(
                'https://api.facebook.com/method/auth.getSessionforApp',
                data={
                    'access_token': access_token,
                    'format': 'json',
                    'new_app_id': app_id,
                    'generate_session_cookies': '1'
                }
            )
            
            result = response.json()
            
            if 'access_token' in result:
                token = result['access_token']
                prefix = FacebookAppTokens.extract_token_prefix(token)
                
                cookies_dict = {}
                cookies_string = ""
                
                if 'session_cookies' in result:
                    for cookie in result['session_cookies']:
                        cookies_dict[cookie['name']] = cookie['value']
                        cookies_string += f"{cookie['name']}={cookie['value']}; "
                
                return {
                    'token_prefix': prefix,
                    'access_token': token,
                    'cookies': {
                        'dict': cookies_dict,
                        'string': cookies_string.rstrip('; ')
                    }
                }
            return None     
        except:
            return None
    
    def _parse_success_response(self, response_json):
        original_token = response_json.get('access_token')
        original_prefix = FacebookAppTokens.extract_token_prefix(original_token)
        
        result = {
            'success': True,
            'original_token': {
                'token_prefix': original_prefix,
                'access_token': original_token
            },
            'cookies': {}
        }
        
        if 'session_cookies' in response_json:
            cookies_dict = {}
            cookies_string = ""
            for cookie in response_json['session_cookies']:
                cookies_dict[cookie['name']] = cookie['value']
                cookies_string += f"{cookie['name']}={cookie['value']}; "
            result['cookies'] = {
                'dict': cookies_dict,
                'string': cookies_string.rstrip('; ')
            }
        
        if self.convert_token_to:
            result['converted_tokens'] = {}
            for target_app in self.convert_token_to:
                converted = self._convert_token(original_token, target_app)
                if converted:
                    result['converted_tokens'][target_app] = converted
        
        return result
    
    def _handle_2fa_manual(self, error_data):
        return {
            'requires_2fa': True,
            'login_first_factor': error_data['login_first_factor'],
            'uid': error_data['uid']
        }
    
    def login(self):
        try:
            response = self.session.post(self.API_URL, headers=self.headers, data=self.data)
            response_json = response.json()
            
            if 'access_token' in response_json:
                return self._parse_success_response(response_json)
            
            if 'error' in response_json:
                error_data = response_json.get('error', {}).get('error_data', {})
                
                if 'login_first_factor' in error_data and 'uid' in error_data:
                    return self._handle_2fa_manual(error_data)
                
                return {
                    'success': False,
                    'error': response_json['error'].get('message', 'Unknown error'),
                    'error_user_msg': response_json['error'].get('error_user_msg')
                }
            
            return {'success': False, 'error': 'Unknown response format'}
            
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Invalid JSON response'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aashiq_hatela_secret_key_2024')
login_sessions = {}

# HTML Template (short version for deploy - main HTML wahi hai jo pehle diya tha)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aashiq Hatela Facebook Tool</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', sans-serif;
        }
        body {
            background: linear-gradient(135deg, #0a3b0a 0%, #1a6b1a 50%, #0d4d0d 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            min-height: 100vh;
            align-items: center;
        }
        @media (max-width: 768px) {
            .container { grid-template-columns: 1fr; }
        }
        .hero-section {
            text-align: center;
            padding: 40px;
            background: rgba(0,0,0,0.3);
            border-radius: 30px;
            backdrop-filter: blur(10px);
        }
        .title {
            font-size: 2.5rem;
            color: #ffd54f;
            margin-bottom: 10px;
        }
        .login-form {
            background: rgba(0,0,0,0.4);
            padding: 40px;
            border-radius: 30px;
            backdrop-filter: blur(10px);
        }
        .form-group {
            position: relative;
            margin-bottom: 25px;
        }
        .form-group input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255,255,255,0.1);
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 50px;
            color: white;
            font-size: 1rem;
        }
        .form-group input:focus {
            outline: none;
            border-color: #ffd54f;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #2e7d32, #1b5e20);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
        }
        .btn:hover {
            background: linear-gradient(135deg, #1b5e20, #0d3b0f);
        }
        .token-box {
            background: rgba(0,0,0,0.5);
            padding: 15px;
            border-radius: 15px;
            margin: 10px 0;
            word-break: break-all;
        }
        .copy-btn {
            background: #ffd54f;
            color: #1a5a1a;
            padding: 5px 15px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            margin-left: 10px;
        }
        .results-section {
            display: none;
            margin-top: 20px;
        }
        .alert {
            padding: 10px;
            border-radius: 25px;
            margin: 15px 0;
            display: none;
        }
        .alert-success { background: rgba(0,214,143,0.3); border: 1px solid #00d68f; }
        .alert-error { background: rgba(255,71,87,0.3); border: 1px solid #ff4757; }
        .twofa-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .twofa-content {
            background: rgba(0,0,0,0.8);
            padding: 40px;
            border-radius: 30px;
            max-width: 500px;
            width: 90%;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero-section">
            <h1 class="title">🌿 AASHIQ HATELA 🌿</h1>
            <p>Facebook Login Tool | Hari Badiyo Wala Version</p>
        </div>
        <div class="login-form">
            <h2>Login to Facebook</h2>
            <div class="alert" id="alert"></div>
            <form id="loginForm">
                <div class="form-group">
                    <input type="text" id="email" placeholder="Email / Phone Number" required>
                </div>
                <div class="form-group">
                    <input type="password" id="password" placeholder="Password" required>
                </div>
                <button type="submit" class="btn" id="loginBtn">
                    <span id="btnText">🔐 Login</span>
                    <span id="btnLoading" class="loading" style="display:none;"></span>
                </button>
            </form>
            <div class="results-section" id="results">
                <h3>✅ Login Successful!</h3>
                <div class="token-box">
                    <div>🔑 Token: <button class="copy-btn" onclick="copyToken('originalTokenText')">Copy</button></div>
                    <div id="originalTokenText"></div>
                </div>
                <div class="token-box">
                    <div>🍪 Cookies: <button class="copy-btn" onclick="copyToken('cookiesText')">Copy</button></div>
                    <div id="cookiesText"></div>
                </div>
                <div id="convertedTokens"></div>
            </div>
        </div>
    </div>
    <div class="twofa-modal" id="twofaModal">
        <div class="twofa-content">
            <h2>🔐 2FA Required</h2>
            <p>Enter OTP sent to your phone:</p>
            <div class="form-group">
                <input type="text" id="otpCode" placeholder="6-digit OTP" maxlength="6">
            </div>
            <button class="btn" onclick="submitOTP()">Verify</button>
            <button class="btn" onclick="close2FAModal()" style="margin-top:10px; background:#555;">Cancel</button>
        </div>
    </div>
    <script>
        let twofaData = null;
        function showAlert(msg, type) {
            const alert = document.getElementById('alert');
            alert.textContent = msg;
            alert.className = `alert alert-${type}`;
            alert.style.display = 'block';
            setTimeout(() => alert.style.display = 'none', 5000);
        }
        function copyToken(id) {
            navigator.clipboard.writeText(document.getElementById(id).textContent);
            showAlert('Copied!', 'success');
        }
        function show2FAModal(data) { twofaData = data; document.getElementById('twofaModal').style.display = 'flex'; }
        function close2FAModal() { document.getElementById('twofaModal').style.display = 'none'; twofaData = null; }
        function submitOTP() {
            const otp = document.getElementById('otpCode').value;
            if(!otp) return showAlert('Enter OTP', 'error');
            fetch('/verify_2fa', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: twofaData.session_id, otp_code: otp})
            }).then(r=>r.json()).then(data=>{
                if(data.success) { showResults(data); close2FAModal(); showAlert('Login Success!','success'); }
                else showAlert(data.error,'error');
            });
        }
        function showResults(data) {
            document.getElementById('originalTokenText').textContent = data.original_token.access_token;
            document.getElementById('cookiesText').textContent = data.cookies.string || 'No cookies';
            document.getElementById('results').style.display = 'block';
        }
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            if(!email || !password) return showAlert('Fill all fields','error');
            document.getElementById('loginBtn').disabled = true;
            document.getElementById('btnText').style.display = 'none';
            document.getElementById('btnLoading').style.display = 'inline-block';
            fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email, password: password})
            }).then(r=>r.json()).then(data=>{
                if(data.success) showResults(data);
                else if(data.requires_2fa) show2FAModal(data);
                else showAlert(data.error,'error');
            }).finally(()=>{
                document.getElementById('loginBtn').disabled = false;
                document.getElementById('btnText').style.display = 'block';
                document.getElementById('btnLoading').style.display = 'none';
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'})
        fb_login = FacebookLogin(uid_phone_mail=email, password=password, convert_all_tokens=True)
        result = fb_login.login()
        if result.get('requires_2fa'):
            session_id = str(uuid.uuid4())
            login_sessions[session_id] = {'fb_login': fb_login, 'data': result, 'timestamp': time.time()}
            for sid in list(login_sessions.keys()):
                if time.time() - login_sessions[sid]['timestamp'] > 600:
                    del login_sessions[sid]
            result['session_id'] = session_id
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        otp_code = data.get('otp_code')
        if not session_id or not otp_code:
            return jsonify({'success': False, 'error': 'Session ID and OTP required'})
        if session_id not in login_sessions:
            return jsonify({'success': False, 'error': 'Session expired'})
        session_data = login_sessions[session_id]
        fb_login = session_data['fb_login']
        twofa_data = session_data['data']
        data_2fa = {
            'locale': 'vi_VN', 'format': 'json', 'email': fb_login.uid_phone_mail,
            'device_id': fb_login.device_id, 'access_token': fb_login.ACCESS_TOKEN,
            'generate_session_cookies': 'true', 'generate_machine_id': '1',
            'twofactor_code': otp_code, 'credentials_type': 'two_factor',
            'error_detail_type': 'button_with_disabled', 'first_factor': twofa_data['login_first_factor'],
            'password': fb_login.password, 'userid': twofa_data['uid'],
            'machine_id': twofa_data['login_first_factor']
        }
        response = fb_login.session.post(fb_login.API_URL, data=data_2fa, headers=fb_login.headers)
        response_json = response.json()
        if 'access_token' in response_json:
            result = fb_login._parse_success_response(response_json)
            if session_id in login_sessions:
                del login_sessions[session_id]
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': response_json.get('error', {}).get('message', 'OTP Failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def cleanup_sessions():
    while True:
        time.sleep(300)
        current_time = time.time()
        for sid in list(login_sessions.keys()):
            if current_time - login_sessions[sid]['timestamp'] > 600:
                del login_sessions[sid]

cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()

# IMPORTANT - For Render/Gunicorn
application = app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
