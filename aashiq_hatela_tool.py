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

# ===========================================
# FLASK APP - AASHIQ HATELA EDITION
# ===========================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aashiq_hatela_secret_key_2024')
login_sessions = {}

# HTML Template - Hari Badiyo Wala Nature Theme
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>𝕬𝖆𝖘𝖍𝖎𝖖 𝕳𝖆𝖙𝖊𝖑𝖆 | 𝕱𝖆𝖈𝖊𝖇𝖔𝖔𝖐 𝕿𝖔𝖔𝖑</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }

        :root {
            --primary-green: #2e7d32;
            --secondary-green: #1b5e20;
            --light-green: #66bb6a;
            --dark-green: #0d3b0f;
            --accent-gold: #ffd54f;
            --text-light: #ffffff;
            --text-dark: #1a2e1a;
            --glass-bg: rgba(255, 255, 255, 0.12);
            --card-bg: rgba(30, 60, 30, 0.6);
        }

        body {
            background: linear-gradient(135deg, #0a3b0a 0%, #1a6b1a 50%, #0d4d0d 100%);
            min-height: 100vh;
            color: var(--text-light);
            overflow-x: hidden;
            position: relative;
        }

        /* Falling Leaves Animation */
        .leaf {
            position: fixed;
            top: -20px;
            pointer-events: none;
            z-index: 999;
            animation: fall linear forwards;
        }

        @keyframes fall {
            0% {
                transform: translateY(-20px) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }

        /* Forest Pattern Overlay */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" opacity="0.08"><path fill="white" d="M20,70 L30,40 L40,70 L35,70 L45,45 L55,70 L50,70 L60,50 L70,70 L65,70 L75,55 L85,70 Z M50,20 L55,35 L65,35 L58,45 L62,58 L50,50 L38,58 L42,45 L35,35 L45,35 Z"/></svg>');
            background-repeat: repeat;
            background-size: 80px;
            pointer-events: none;
        }

        .container {
            max-width: 1300px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            min-height: 100vh;
            align-items: center;
            position: relative;
            z-index: 1;
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }

        /* Hero Section - Aashiq Hatela Style */
        .hero-section {
            text-align: center;
            padding: 50px 30px;
            background: var(--card-bg);
            backdrop-filter: blur(15px);
            border-radius: 50px 20px 50px 20px;
            border: 2px solid rgba(255, 213, 79, 0.3);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }

        .hero-section::before {
            content: '🌿🌻🌸';
            position: absolute;
            bottom: 10px;
            right: 10px;
            font-size: 60px;
            opacity: 0.15;
            pointer-events: none;
        }

        .hero-section::after {
            content: '🍃🌱🍂';
            position: absolute;
            top: 10px;
            left: 10px;
            font-size: 50px;
            opacity: 0.15;
            pointer-events: none;
        }

        .logo {
            font-size: 5rem;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 20px rgba(255, 213, 79, 0.5));
            animation: bounce 2s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .title {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-gold), var(--light-green), white);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
            font-size: 1rem;
            color: var(--accent-gold);
            margin-bottom: 30px;
            font-weight: 500;
            letter-spacing: 1px;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 30px;
        }

        .feature {
            background: rgba(0, 0, 0, 0.3);
            padding: 18px;
            border-radius: 20px;
            border: 1px solid rgba(255, 213, 79, 0.2);
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }

        .feature:hover {
            transform: translateY(-5px);
            border-color: var(--accent-gold);
            background: rgba(0, 0, 0, 0.4);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .feature i {
            font-size: 2rem;
            color: var(--accent-gold);
            margin-bottom: 10px;
        }

        .feature h3 {
            font-size: 1rem;
            margin-bottom: 5px;
        }

        .feature p {
            font-size: 0.75rem;
            opacity: 0.8;
        }

        /* Login Form */
        .login-form {
            background: var(--card-bg);
            backdrop-filter: blur(15px);
            padding: 45px 35px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }

        .form-title {
            font-size: 1.8rem;
            margin-bottom: 30px;
            text-align: center;
            position: relative;
            padding-bottom: 15px;
            color: var(--accent-gold);
        }

        .form-title::after {
            content: '🌸';
            position: absolute;
            bottom: -5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 20px;
        }

        .form-group {
            position: relative;
            margin-bottom: 30px;
        }

        .form-group input {
            width: 100%;
            padding: 16px 20px;
            background: rgba(0, 0, 0, 0.5);
            border: 2px solid rgba(255, 255, 255, 0.15);
            border-radius: 50px;
            color: var(--text-light);
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .form-group input:focus {
            outline: none;
            border-color: var(--accent-gold);
            background: rgba(0, 0, 0, 0.7);
            box-shadow: 0 0 0 3px rgba(255, 213, 79, 0.2);
        }

        .form-group label {
            position: absolute;
            left: 25px;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(255, 255, 255, 0.7);
            transition: all 0.3s ease;
            pointer-events: none;
        }

        .form-group input:focus + label,
        .form-group input:not(:placeholder-shown) + label {
            top: -10px;
            left: 20px;
            font-size: 0.75rem;
            color: var(--accent-gold);
            background: var(--dark-green);
            padding: 0 10px;
            border-radius: 20px;
        }

        .form-group i {
            position: absolute;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--accent-gold);
        }

        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, var(--primary-green), var(--secondary-green));
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 2px;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(46, 125, 50, 0.5);
            background: linear-gradient(135deg, var(--light-green), var(--primary-green));
        }

        .btn:active {
            transform: translateY(0);
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .results-section {
            display: none;
            margin-top: 30px;
            padding: 20px;
            background: rgba(46, 125, 50, 0.3);
            border-radius: 20px;
            border: 1px solid var(--accent-gold);
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .token-box {
            background: rgba(0, 0, 0, 0.4);
            padding: 15px;
            border-radius: 15px;
            margin: 10px 0;
            word-break: break-all;
            font-family: monospace;
            font-size: 0.85rem;
            border: 1px solid rgba(255, 213, 79, 0.3);
            transition: all 0.3s ease;
        }

        .token-box:hover {
            border-color: var(--accent-gold);
        }

        .token-title {
            color: var(--accent-gold);
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .copy-btn {
            background: rgba(255, 213, 79, 0.2);
            border: 1px solid var(--accent-gold);
            color: var(--accent-gold);
            padding: 5px 15px;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.75rem;
        }

        .copy-btn:hover {
            background: var(--accent-gold);
            color: var(--dark-green);
        }

        .alert {
            padding: 12px 20px;
            border-radius: 50px;
            margin: 20px 0;
            display: none;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .alert-success {
            background: rgba(102, 187, 106, 0.3);
            border: 1px solid #66bb6a;
            color: #a5d6a7;
        }

        .alert-error {
            background: rgba(255, 71, 87, 0.2);
            border: 1px solid #ff4757;
            color: #ff8a92;
        }

        .alert-warning {
            background: rgba(255, 213, 79, 0.2);
            border: 1px solid var(--accent-gold);
            color: var(--accent-gold);
        }

        .twofa-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .twofa-content {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            padding: 40px;
            border-radius: 30px;
            border: 2px solid var(--accent-gold);
            max-width: 500px;
            width: 90%;
            animation: modalIn 0.4s ease;
        }

        @keyframes modalIn {
            from { opacity: 0; transform: scale(0.9) translateY(-30px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .toggle-password {
            position: absolute;
            right: 55px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            color: var(--accent-gold);
        }

        .footer-badge {
            text-align: center;
            margin-top: 20px;
            font-size: 0.8rem;
            opacity: 0.7;
        }
    </style>
</head>
<body>

    <div class="container">
        <div class="hero-section">
            <div class="logo">
                <i class="fas fa-user-secret"></i>
            </div>
            <h1 class="title">𝕬𝖆𝖘𝖍𝖎𝖖 𝕳𝖆𝖙𝖊𝖑𝖆</h1>
            <p class="subtitle">🌿 𝕱𝖆𝖈𝖊𝖇𝖔𝖔𝖐 𝕷𝖔𝖌𝖎𝖓 𝕿𝖔𝖔𝖑 🌿</p>
            
            <div class="features">
                <div class="feature">
                    <i class="fas fa-shield-alt"></i>
                    <h3>Secure Login</h3>
                    <p>End-to-end encryption</p>
                </div>
                <div class="feature">
                    <i class="fas fa-sync-alt"></i>
                    <h3>Token Converter</h3>
                    <p>6+ app tokens</p>
                </div>
                <div class="feature">
                    <i class="fas fa-mobile-alt"></i>
                    <h3>2FA Support</h3>
                    <p>OTP verification</p>
                </div>
                <div class="feature">
                    <i class="fas fa-leaf"></i>
                    <h3>Nature Theme</h3>
                    <p>Hari Badiyo wala</p>
                </div>
            </div>
        </div>

        <div class="login-form">
            <h2 class="form-title">🌻 𝕷𝖔𝖌𝖎𝖓 𝖙𝖔 𝕱𝖆𝖈𝖊𝖇𝖔𝖔𝖐 🌻</h2>
            
            <div class="alert" id="alert"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <input type="text" id="email" placeholder=" " required>
                    <label for="email"><i class="fas fa-envelope"></i> Email / Phone Number</label>
                    <i class="fas fa-user-circle"></i>
                </div>
                
                <div class="form-group">
                    <input type="password" id="password" placeholder=" " required>
                    <label for="password"><i class="fas fa-lock"></i> Password</label>
                    <i class="fas fa-lock"></i>
                    <span class="toggle-password" onclick="togglePassword()">
                        <i class="fas fa-eye"></i>
                    </span>
                </div>
                
                <button type="submit" class="btn" id="loginBtn">
                    <span id="btnText">🌿 Login to Facebook 🌿</span>
                    <span id="btnLoading" class="loading" style="display: none;"></span>
                </button>
            </form>

            <div class="results-section" id="results">
                <h3 style="color: var(--accent-gold); margin-bottom: 20px;">
                    <i class="fas fa-check-circle"></i> ✅ Login Successful!
                </h3>
                
                <div class="token-box" id="originalToken">
                    <div class="token-title">
                        <i class="fas fa-key"></i> 🔑 Original Token
                        <button class="copy-btn" onclick="copyToken('originalTokenText')">📋 Copy</button>
                    </div>
                    <div id="originalTokenText"></div>
                </div>
                
                <div class="token-box" id="cookies">
                    <div class="token-title">
                        <i class="fas fa-cookie-bite"></i> 🍪 Cookies
                        <button class="copy-btn" onclick="copyToken('cookiesText')">📋 Copy</button>
                    </div>
                    <div id="cookiesText"></div>
                </div>
                
                <div id="convertedTokens"></div>
            </div>
            
            <div class="footer-badge">
                <i class="fas fa-heart" style="color: #ff6b6b;"></i> Made with Nature by Aashiq Hatela <i class="fas fa-leaf" style="color: #66bb6a;"></i>
            </div>
        </div>
    </div>

    <div class="twofa-modal" id="twofaModal">
        <div class="twofa-content">
            <h2 style="color: var(--accent-gold); margin-bottom: 20px;">
                <i class="fas fa-shield-alt"></i> 🔐 2FA Required
            </h2>
            <p style="margin-bottom: 30px; color: var(--text-light);">
                📱 Facebook has sent an OTP to your mobile/WhatsApp.<br>
                Please enter the code below.
            </p>
            
            <div class="form-group">
                <input type="text" id="otpCode" placeholder=" " maxlength="6" autocomplete="off">
                <label for="otpCode"><i class="fas fa-keyboard"></i> Enter 6-digit OTP</label>
                <i class="fas fa-sms"></i>
            </div>
            
            <div style="display: flex; gap: 15px; margin-top: 30px;">
                <button class="btn" onclick="submitOTP()" style="flex: 1; background: var(--accent-gold); color: var(--dark-green);">
                    ✅ Verify OTP
                </button>
                <button class="btn" onclick="close2FAModal()" 
                        style="background: rgba(255, 71, 87, 0.2); color: #ff8a92; border: 1px solid #ff4757; flex: 1;">
                    ❌ Cancel
                </button>
            </div>
        </div>
    </div>

    <script>
        // Falling leaves animation
        function createLeaf() {
            const leaf = document.createElement('div');
            leaf.className = 'leaf';
            const leafIcons = ['🍃', '🌿', '🍂', '🌱', '🌸', '🌻'];
            leaf.innerHTML = leafIcons[Math.floor(Math.random() * leafIcons.length)];
            leaf.style.left = Math.random() * 100 + '%';
            leaf.style.fontSize = (Math.random() * 20 + 15) + 'px';
            leaf.style.animationDuration = Math.random() * 5 + 5 + 's';
            leaf.style.animationDelay = Math.random() * 5 + 's';
            document.body.appendChild(leaf);
            
            setTimeout(() => {
                leaf.remove();
            }, 10000);
        }

        setInterval(createLeaf, 800);

        function showAlert(message, type = 'error') {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert alert-${type}`;
            alert.style.display = 'block';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }

        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const eyeIcon = document.querySelector('.toggle-password i');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                eyeIcon.className = 'fas fa-eye';
            }
        }

        function copyToken(elementId) {
            const text = document.getElementById(elementId).textContent;
            navigator.clipboard.writeText(text).then(() => {
                showAlert('📋 Copied to clipboard!', 'success');
            });
        }

        let twofaData = null;
        function show2FAModal(data) {
            twofaData = data;
            document.getElementById('twofaModal').style.display = 'flex';
            document.getElementById('otpCode').focus();
        }

        function close2FAModal() {
            document.getElementById('twofaModal').style.display = 'none';
            twofaData = null;
        }

        function submitOTP() {
            const otpCode = document.getElementById('otpCode').value.trim();
            if (!otpCode || otpCode.length !== 6) {
                showAlert('⚠️ Please enter valid 6-digit OTP', 'error');
                return;
            }

            document.getElementById('loginBtn').disabled = true;
            document.getElementById('btnText').style.display = 'none';
            document.getElementById('btnLoading').style.display = 'inline-block';

            fetch('/verify_2fa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: twofaData.session_id,
                    otp_code: otpCode
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showResults(data);
                    close2FAModal();
                    showAlert('✅ Login successful!', 'success');
                } else {
                    showAlert('❌ ' + (data.error || 'OTP verification failed'), 'error');
                }
            })
            .catch(error => {
                showAlert('🌐 Network error: ' + error, 'error');
            })
            .finally(() => {
                document.getElementById('loginBtn').disabled = false;
                document.getElementById('btnText').style.display = 'block';
                document.getElementById('btnLoading').style.display = 'none';
            });
        }

        function showResults(data) {
            document.getElementById('originalTokenText').textContent = data.original_token.access_token;
            document.getElementById('cookiesText').textContent = data.cookies.string || 'No cookies available';
            
            const convertedTokensDiv = document.getElementById('convertedTokens');
            if (data.converted_tokens && Object.keys(data.converted_tokens).length > 0) {
                let html = '<h4 style="color: var(--accent-gold); margin: 20px 0 10px 0;"><i class="fas fa-exchange-alt"></i> 🔄 Converted Tokens</h4>';
                
                const appNames = {
                    'FB_ANDROID': '📱 Facebook Android',
                    'MESSENGER_ANDROID': '💬 Messenger Android',
                    'FB_LITE': '⚡ Facebook Lite',
                    'MESSENGER_LITE': '📨 Messenger Lite',
                    'ADS_MANAGER_ANDROID': '📊 Ads Manager',
                    'PAGES_MANAGER_ANDROID': '📄 Pages Manager'
                };
                
                for (const [app, tokenData] of Object.entries(data.converted_tokens)) {
                    const appName = appNames[app] || app;
                    html += `
                        <div class="token-box">
                            <div class="token-title">
                                <i class="fas fa-mobile-alt"></i> ${appName}
                                <button class="copy-btn" onclick="copyToken('token_${app}')">📋 Copy</button>
                            </div>
                            <div id="token_${app}">${tokenData.access_token}</div>
                        </div>
                    `;
                }
                convertedTokensDiv.innerHTML = html;
            } else {
                convertedTokensDiv.innerHTML = '';
            }
            
            document.getElementById('results').style.display = 'block';
        }

        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();
            
            if (!email || !password) {
                showAlert('❌ Please fill in all fields', 'error');
                return;
            }

            document.getElementById('loginBtn').disabled = true;
            document.getElementById('btnText').style.display = 'none';
            document.getElementById('btnLoading').style.display = 'inline-block';

            fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showResults(data);
                    showAlert('✅ Welcome to Aashiq Hatela Tool!', 'success');
                } else if (data.requires_2fa) {
                    show2FAModal(data);
                    showAlert('🔐 2FA required. Enter OTP code.', 'warning');
                } else {
                    showAlert('❌ ' + (data.error || 'Login failed'), 'error');
                }
            })
            .catch(error => {
                showAlert('🌐 Network error: ' + error, 'error');
            })
            .finally(() => {
                document.getElementById('loginBtn').disabled = false;
                document.getElementById('btnText').style.display = 'block';
                document.getElementById('btnLoading').style.display = 'none';
            });
        });

        document.getElementById('otpCode').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitOTP();
        });
    </script>
</body>
</html>
'''

# ===========================================
# FLASK ROUTES - AASHIQ HATELA EDITION
# ===========================================

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
            return jsonify({'success': False, 'error': 'Email and password are required'})
        
        fb_login = FacebookLogin(
            uid_phone_mail=email,
            password=password,
            convert_all_tokens=True
        )
        
        result = fb_login.login()
        
        if result.get('requires_2fa'):
            session_id = str(uuid.uuid4())
            login_sessions[session_id] = {
                'fb_login': fb_login,
                'data': result,
                'timestamp': time.time()
            }
            
            # Clean old sessions
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
            return jsonify({'success': False, 'error': 'Session ID and OTP code are required'})
        
        if session_id not in login_sessions:
            return jsonify({'success': False, 'error': 'Session expired or invalid'})
        
        session_data = login_sessions[session_id]
        fb_login = session_data['fb_login']
        twofa_data = session_data['data']
        
        data_2fa = {
            'locale': 'vi_VN',
            'format': 'json',
            'email': fb_login.uid_phone_mail,
            'device_id': fb_login.device_id,
            'access_token': fb_login.ACCESS_TOKEN,
            'generate_session_cookies': 'true',
            'generate_machine_id': '1',
            'twofactor_code': otp_code,
            'credentials_type': 'two_factor',
            'error_detail_type': 'button_with_disabled',
            'first_factor': twofa_data['login_first_factor'],
            'password': fb_login.password,
            'userid': twofa_data['uid'],
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
            return jsonify({
                'success': False,
                'error': response_json.get('error', {}).get('message', 'OTP Verification Failed')
            })
            
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

if __name__ == '__main__':
    print("=" * 60)
    print("  🌿 AASHIQ HATELA FACEBOOK TOOL 🌿")
    print("  Hari Badiyo wala version | Deploy Ready")
    print("=" * 60)
    
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"\n🚀 Server running on http://{host}:{port}")
    print("🍃 Press Ctrl+C to stop\n")
    
    if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
# For gunicorn
app = app
