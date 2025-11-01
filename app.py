from flask import Flask, request, jsonify, render_template
import requests
import re
import random
import os

app = Flask(__name__)

# User-Agent list for realism
ua_list = [
    "Mozilla/5.0 (Linux; Android 10; Wildfire E Lite) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/105.0.5195.136 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; KINGKONG 5 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; G91 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36"
]

# 🧠 Improved Token Extraction
def extract_token(cookie, ua):
    try:
        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}
        res = requests.get(
            "https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed",
            headers={
                "user-agent": ua,
                "referer": "https://m.facebook.com/",
            },
            cookies=cookies
        )
        token_match = re.search(r'{"accessToken":"(EAA\w+)"', res.text)
        if token_match:
            print("[✅] Token extracted successfully")
            return token_match.group(1)
        else:
            print("[❌] Token not found in response.")
            return None
    except Exception as e:
        print("Token extraction error:", e)
        return None

# 🕸️ Homepage
@app.route("/")
def index():
    return render_template("index.html")

# ⚡ Share Endpoint
@app.route("/api/share", methods=["POST"])
def share():
    data = request.get_json()
    cookie = data.get("cookie")
    post_link = data.get("link")
    limit = int(data.get("limit", 0))

    # Validate input
    if not cookie or not post_link or not limit:
        return jsonify({"status": False, "message": "⚠️ Missing required input."})

    ua = random.choice(ua_list)
    token = extract_token(cookie, ua)

    if not token:
        return jsonify({"status": False, "message": "❌ Failed to extract token. Invalid cookie or expired session."})

    try:
        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}
        success = 0

        for _ in range(limit):
            res = requests.post(
                "https://graph.facebook.com/v18.0/me/feed",
                params={
                    "link": post_link,
                    "access_token": token,
                    "published": 0
                },
                headers={"user-agent": ua},
                cookies=cookies
            )

            if "id" in res.text:
                success += 1
            else:
                break

        return jsonify({
            "status": True,
            "message": f"✅ Successfully shared {success} times!",
            "count": success
        })

    except Exception as e:
        print("Share error:", e)
        return jsonify({"status": False, "message": "💀 An error occurred while sharing."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)