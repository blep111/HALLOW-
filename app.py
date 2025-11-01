from flask import Flask, request, jsonify, render_template
import requests, re, random, os

app = Flask(__name__)

# ✅ Random mobile user-agents for realism
ua_list = [
    "Mozilla/5.0 (Linux; Android 10; Wildfire E Lite) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/105.0.5195.136 Mobile Safari/537.36 [FBAN/EMA;FBLC/en_US;FBAV/298.0.0.10.115;]",
    "Mozilla/5.0 (Linux; Android 11; KINGKONG 5 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36 [FBAN/EMA;FBLC/fr_FR;FBAV/320.0.0.12.108;]",
    "Mozilla/5.0 (Linux; Android 11; G91 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36 [FBAN/EMA;FBLC/fr_FR;FBAV/325.0.1.4.108;]"
]

# ✅ Extract token from cookie (with backup API)
def extract_token(cookie, ua):
    try:
        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}

        # First, try Facebook business location method
        res = requests.get(
            "https://business.facebook.com/business_locations",
            headers={"user-agent": ua, "referer": "https://www.facebook.com/"},
            cookies=cookies,
            timeout=10
        )
        token_match = re.search(r'(EAAG\w+)', res.text)
        if token_match:
            return token_match.group(1)

        # Fallback → use external API (c2t.lara.rest)
        api_res = requests.post("https://c2t.lara.rest/", json={"cookie": cookie})
        if api_res.status_code == 200:
            data = api_res.json()
            return data.get("access_token")
    except Exception as e:
        print("Token extraction error:", e)
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/share", methods=["POST"])
def share():
    try:
        data = request.get_json()
        cookie = data.get("cookie")
        post_link = data.get("link")
        limit = int(data.get("limit", 0))

        if not cookie or not post_link or not limit:
            return jsonify({"status": False, "message": "⚠️ Missing input fields."})

        ua = random.choice(ua_list)
        token = extract_token(cookie, ua)
        if not token:
            return jsonify({"status": False, "message": "❌ Token extraction failed. Please check your cookie."})

        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}

        success = 0
        for _ in range(limit):
            res = requests.post(
                "https://graph.facebook.com/v18.0/me/feed",
                params={"link": post_link, "access_token": token, "published": 0},
                headers={"user-agent": ua},
                cookies=cookies,
                timeout=10
            )
            if "id" in res.text:
                success += 1

        return jsonify({
            "status": True,
            "message": f"✅ Successfully shared {success} times!",
            "success_count": success
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": False, "message": "👻 Server error. Please try again later."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
