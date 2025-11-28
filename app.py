from flask import Flask, request, jsonify, render_template
import requests, re, random, os, time, threading

app = Flask(__name__)

# ✅ Expanded list of random mobile user-agents for better realism and rotation
ua_list = [
    "Mozilla/5.0 (Linux; Android 10; Wildfire E Lite) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/105.0.5195.136 Mobile Safari/537.36 [FBAN/EMA;FBLC/en_US;FBAV/298.0.0.10.115;]",
    "Mozilla/5.0 (Linux; Android 11; KINGKONG 5 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36 [FBAN/EMA;FBLC/fr_FR;FBAV/320.0.0.12.108;]",
    "Mozilla/5.0 (Linux; Android 11; G91 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/106.0.5249.126 Mobile Safari/537.36 [FBAN/EMA;FBLC/fr_FR;FBAV/325.0.1.4.108;]",
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 [FBAN/EMA;FBLC/en_US;FBAV/330.0.0.15.113;]",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36 [FBAN/EMA;FBLC/en_US;FBAV/335.0.0.12.119;]",
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 9) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/88.0.4324.152 Mobile Safari/537.36 [FBAN/EMA;FBLC/it_IT;FBAV/310.0.0.8.109;]",
    "Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.120 Mobile Safari/537.36 [FBAN/EMA;FBLC/de_DE;FBAV/315.0.0.9.110;]",
    "Mozilla/5.0 (Linux; Android 12; Samsung Galaxy S22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36 [FBAN/EMA;FBLC/es_ES;FBAV/325.0.1.4.108;]"
]

# ✅ Extract token from cookie (with backup API and improved error handling)
def extract_token(cookie, ua):
    try:
        cookies = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}

        # First, try Facebook business location method
        res = requests.get(
            "https://business.facebook.com/business_locations",
            headers={"user-agent": ua, "referer": "https://www.facebook.com/"},
            cookies=cookies,
            timeout=15  # Increased timeout for reliability
        )
        token_match = re.search(r'(EAAG\w+)', res.text)
        if token_match:
            return token_match.group(1)

        # Fallback → use external API (c2t.lara.rest)
        api_res = requests.post("https://c2t.lara.rest/", json={"cookie": cookie}, timeout=15)
        if api_res.status_code == 200:
            data = api_res.json()
            return data.get("access_token")
    except Exception as e:
        print(f"Token extraction error for cookie: {e}")
    return None

# ✅ Function to perform a single share with retry logic
def perform_share(token, cookies, post_link, ua, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            res = requests.post(
                "https://graph.facebook.com/v18.0/me/feed",
                params={"link": post_link, "access_token": token, "published": 0},
                headers={"user-agent": ua},
                cookies=cookies,
                timeout=15
            )
            if "id" in res.text:
                return True
            elif attempt < max_retries:
                time.sleep(1)  # Short delay before retry
        except Exception as e:
            print(f"Share attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(1)
    return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/share", methods=["POST"])
def share():
    try:
        data = request.get_json()
        cookies_input = data.get("cookies")  # Now accepts multiple cookies as a string (newline-separated) or list
        post_link = data.get("link")
        limit = int(data.get("limit", 0))

        if not cookies_input or not post_link or not limit:
            return jsonify({"status": False, "message": "⚠️ Missing input fields."})

        # Parse cookies: if string, split by newlines; if list, use as is
        if isinstance(cookies_input, str):
            cookies_list = [c.strip() for c in cookies_input.split('\n') if c.strip()]
        elif isinstance(cookies_input, list):
            cookies_list = cookies_input
        else:
            return jsonify({"status": False, "message": "⚠️ Cookies must be a string (newline-separated) or list."})

        if not cookies_list:
            return jsonify({"status": False, "message": "⚠️ No valid cookies provided."})

        # Limit to 60 shares max for safety
        limit = min(limit, 60)

        # Extract tokens for each cookie
        token_data = []
        for cookie in cookies_list:
            ua = random.choice(ua_list)
            token = extract_token(cookie, ua)
            if token:
                cookies_dict = {i.split('=')[0]: i.split('=')[1] for i in cookie.split('; ') if '=' in i}
                token_data.append({"token": token, "cookies": cookies_dict, "ua": ua})
            else:
                print(f"Failed to extract token for cookie: {cookie[:50]}...")

        if not token_data:
            return jsonify({"status": False, "message": "❌ No valid tokens extracted from cookies."})

        success = 0
        for i in range(limit):
            # Select a random token/cookie combo to distribute load
            selected = random.choice(token_data)
            if perform_share(selected["token"], selected["cookies"], post_link, selected["ua"]):
                success += 1
            # 3-second cooldown between shares to avoid suspension
            if i < limit - 1:
                time.sleep(3)

        return jsonify({
            "status": True,
            "message": f"✅ Successfully shared {success}/{limit} times!",
            "success_count": success
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({"status": False, "message": "👻 Server error. Please try again later."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
