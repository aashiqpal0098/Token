import random
import string
import json
import time
import uuid
import sys
import os
import threading

from flask import Flask, render_template_string, request, jsonify, session


# ============================================================
# AASHIQ HATELA - SAFE FACEBOOK LOGIN DEMO
# ============================================================

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "aashiq_hatela_demo_secret_key_2026"
)

login_sessions = {}


# ============================================================
# DEMO AUTHENTICATION
# ============================================================

class DemoFacebookLogin:

    DEMO_EMAIL = "demo@example.com"
    DEMO_PASSWORD = "demo123"

    def __init__(self, uid_phone_mail, password):
        self.uid_phone_mail = uid_phone_mail
        self.password = password

        self.device_id = str(uuid.uuid4())
        self.machine_id = self._generate_machine_id()

    @staticmethod
    def _generate_machine_id():
        return "".join(
            random.choices(
                string.ascii_letters + string.digits,
                k=24
            )
        )

    def login(self):

        # Demo account
        if (
            self.uid_phone_mail == self.DEMO_EMAIL
            and self.password == self.DEMO_PASSWORD
        ):
            return self._success_result()

        # Demo 2FA account
        if (
            self.uid_phone_mail == "2fa@example.com"
            and self.password == "demo123"
        ):
            return {
                "requires_2fa": True,
                "login_first_factor": str(uuid.uuid4()),
                "uid": "demo-user-2fa"
            }

        return {
            "success": False,
            "error": "Invalid demo email or password."
        }

    def verify_otp(self, otp_code):

        # Demo OTP only
        if otp_code == "123456":
            return self._success_result()

        return {
            "success": False,
            "error": "Invalid demo OTP."
        }

    def _success_result(self):

        demo_session = str(uuid.uuid4())

        return {
            "success": True,
            "message": "Demo login successful.",
            "user": {
                "id": "demo-user-001",
                "email": self.uid_phone_mail
            },
            "demo_session": demo_session
        }


# ============================================================
# HTML
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Aashiq Hatela Facebook Tool</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    min-height: 100vh;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #071a0f,
            #123d21,
            #071a0f
        );

    color: white;

    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    width: 92%;
    max-width: 430px;

    background: rgba(0, 0, 0, 0.45);

    border: 1px solid rgba(255,255,255,0.12);

    border-radius: 22px;

    padding: 25px;

    box-shadow:
        0 15px 50px rgba(0,0,0,0.5);

    backdrop-filter: blur(12px);
}

.logo {
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: #55ff88;

    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #b8cdbd;
    font-size: 14px;
    margin-bottom: 25px;
}

h2 {
    text-align: center;
    margin-bottom: 20px;
}

input {
    width: 100%;

    padding: 14px;

    margin-top: 10px;
    margin-bottom: 14px;

    border: none;
    outline: none;

    border-radius: 10px;

    background: #102719;
    color: white;

    font-size: 15px;
}

input::placeholder {
    color: #8ea494;
}

button {
    width: 100%;

    padding: 14px;

    border: none;
    border-radius: 10px;

    background: #25d366;

    color: #071a0f;

    font-size: 16px;
    font-weight: bold;

    cursor: pointer;

    margin-top: 5px;
}

button:hover {
    opacity: 0.9;
}

.secondary {
    background: #334b3b;
    color: white;
}

.hidden {
    display: none;
}

.message {
    margin-top: 15px;

    padding: 12px;

    border-radius: 10px;

    background: rgba(255,255,255,0.08);

    font-size: 14px;

    word-break: break-word;
}

.success {
    border-left: 4px solid #25d366;
}

.error {
    border-left: 4px solid #ff5555;
}

.info {
    border-left: 4px solid #55aaff;
}

.demo-info {
    margin-top: 20px;

    padding: 12px;

    background: rgba(37,211,102,0.08);

    border-radius: 10px;

    font-size: 12px;

    color: #b8cdbd;
}

.result-box {
    margin-top: 15px;

    padding: 14px;

    background: #0d2114;

    border-radius: 10px;

    word-break: break-word;
}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        🌿 AASHIQ HATELA 🌿
    </div>

    <div class="subtitle">
        Facebook Login Tool | Safe Demo Version
    </div>


    <!-- LOGIN -->

    <div id="loginSection">

        <h2>Login to Facebook</h2>

        <input
            id="email"
            type="text"
            placeholder="Email / Phone"
            autocomplete="off"
        >

        <input
            id="password"
            type="password"
            placeholder="Password"
            autocomplete="off"
        >

        <button onclick="login()">
            🔐 Login
        </button>

        <div class="demo-info">
            <b>Demo account</b><br><br>

            Normal login:<br>
            Email: demo@example.com<br>
            Password: demo123<br><br>

            2FA login:<br>
            Email: 2fa@example.com<br>
            Password: demo123<br>
            OTP: 123456
        </div>

    </div>


    <!-- 2FA -->

    <div id="twoFASection" class="hidden">

        <h2>🔐 2FA Required</h2>

        <p>
            Enter the demo OTP:
        </p>

        <input
            id="otp"
            type="text"
            inputmode="numeric"
            maxlength="6"
            placeholder="Enter 6-digit OTP"
        >

        <button onclick="verify2FA()">
            Verify
        </button>

        <button
            class="secondary"
            onclick="cancel2FA()"
        >
            Cancel
        </button>

    </div>


    <!-- RESULT -->

    <div
        id="resultSection"
        class="hidden"
    >

        <h2>✅ Login Successful!</h2>

        <div
            id="result"
            class="result-box"
        ></div>

        <button onclick="location.reload()">
            Login Again
        </button>

    </div>


    <div id="message"></div>

</div>


<script>

let sessionId = null;


function showMessage(text, type="info") {

    const box =
        document.getElementById("message");

    box.className =
        "message " + type;

    box.innerHTML = text;
}


async function login() {

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    if (!email || !password) {

        showMessage(
            "Email and password required.",
            "error"
        );

        return;
    }

    showMessage(
        "Logging in...",
        "info"
    );

    try {

        const response =
            await fetch("/login", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })

            });


        const data =
            await response.json();


        if (data.requires_2fa) {

            sessionId =
                data.session_id;

            document
                .getElementById("loginSection")
                .classList.add("hidden");

            document
                .getElementById("twoFASection")
                .classList.remove("hidden");

            showMessage(
                "2FA verification required.",
                "info"
            );

            return;
        }


        if (!data.success) {

            showMessage(
                data.error || "Login failed.",
                "error"
            );

            return;
        }


        showResult(data);

    } catch (error) {

        showMessage(
            "Connection error: " +
            error.message,
            "error"
        );
    }
}


async function verify2FA() {

    const otp =
        document.getElementById("otp")
        .value
        .trim();


    if (!otp) {

        showMessage(
            "OTP required.",
            "error"
        );

        return;
    }


    if (!sessionId) {

        showMessage(
            "Session expired.",
            "error"
        );

        return;
    }


    showMessage(
        "Verifying OTP...",
        "info"
    );


    try {

        const response =
            await fetch("/verify_2fa", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    session_id:
                        sessionId,

                    otp_code:
                        otp

                })

            });


        const data =
            await response.json();


        if (!data.success) {

            showMessage(
                data.error || "OTP failed.",
                "error"
            );

            return;
        }


        showResult(data);


    } catch (error) {

        showMessage(
            "Connection error: " +
            error.message,
            "error"
        );
    }
}


function showResult(data) {

    document
        .getElementById("loginSection")
        .classList.add("hidden");

    document
        .getElementById("twoFASection")
        .classList.add("hidden");

    document
        .getElementById("resultSection")
        .classList.remove("hidden");


    const result =
        document.getElementById("result");


    result.innerHTML = `

        <b>Message:</b>
        ${escapeHtml(data.message || "")}

        <br><br>

        <b>User ID:</b>
        ${escapeHtml(
            data.user?.id || "demo-user"
        )}

        <br><br>

        <b>Email:</b>
        ${escapeHtml(
            data.user?.email || ""
        )}

        <br><br>

        <b>Demo Session:</b>
        ${escapeHtml(
            data.demo_session || ""
        )}

    `;

    showMessage(
        "Demo login successful.",
        "success"
    );
}


function cancel2FA() {

    sessionId = null;

    document
        .getElementById("twoFASection")
        .classList.add("hidden");

    document
        .getElementById("loginSection")
        .classList.remove("hidden");

    document
        .getElementById("otp")
        .value = "";

    showMessage(
        "2FA cancelled.",
        "info"
    );
}


function escapeHtml(value) {

    return String(value)

        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

</script>

</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template_string(
        HTML_TEMPLATE
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        email = (
            data.get("email") or ""
        ).strip()

        password = (
            data.get("password") or ""
        )


        if not email or not password:

            return jsonify({
                "success": False,
                "error":
                    "Email and password required."
            })


        fb_login = DemoFacebookLogin(
            uid_phone_mail=email,
            password=password
        )


        result = fb_login.login()


        if result.get("requires_2fa"):

            session_id = str(
                uuid.uuid4()
            )


            login_sessions[
                session_id
            ] = {

                "fb_login":
                    fb_login,

                "data":
                    result,

                "timestamp":
                    time.time()

            }


            result[
                "session_id"
            ] = session_id


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                "Server error: " +
                str(e)

        })


# ============================================================
# VERIFY 2FA
# ============================================================

@app.route(
    "/verify_2fa",
    methods=["POST"]
)
def verify_2fa():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        session_id = (
            data.get("session_id")
            or ""
        )

        otp_code = (
            data.get("otp_code")
            or ""
        ).strip()


        if not session_id or not otp_code:

            return jsonify({

                "success": False,

                "error":
                    "Session ID and OTP required."

            })


        if session_id not in login_sessions:

            return jsonify({

                "success": False,

                "error":
                    "Session expired."

            })


        session_data = \
            login_sessions[session_id]


        fb_login = \
            session_data["fb_login"]


        result = fb_login.verify_otp(
            otp_code
        )


        if result.get("success"):

            del login_sessions[
                session_id
            ]


        return jsonify(result)


    except Exception as e:

        return jsonify({

            "success": False,

            "error":
                "Server error: " +
                str(e)

        })


# ============================================================
# SESSION CLEANUP
# ============================================================

def cleanup_sessions():

    while True:

        time.sleep(300)

        current_time = time.time()


        for sid in list(
            login_sessions.keys()
        ):

            try:

                if (
                    current_time -
                    login_sessions[sid]["timestamp"]
                    > 600
                ):

                    del login_sessions[sid]

            except KeyError:

                pass


cleanup_thread = threading.Thread(
    target=cleanup_sessions,
    daemon=True
)

cleanup_thread.start()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
