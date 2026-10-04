import json
import requests

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Netflix Cookie Checker</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #141414; color: #fff; padding: 20px; margin: 0; }
        .container { max-width: 700px; margin: 0 auto; padding-top: 20px; }
        h1 { text-align: center; color: #e50914; }
        textarea { width: 100%; height: 150px; background: #333; color: #fff; border: 1px solid #555; border-radius: 5px; padding: 15px; font-size: 14px; box-sizing: border-box; }
        button { background: #e50914; color: white; border: none; padding: 12px 24px; cursor: pointer; margin-top: 15px; width: 100%; font-size: 16px; border-radius: 4px; font-weight: bold; }
        button:hover { background: #b20710; }
        button:disabled { background: #666; cursor: not-allowed; }
        .result-container { margin-top: 20px; }
        .result-item { background: #222; padding: 15px; margin-bottom: 10px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
        .valid { color: #4cd137; font-weight: bold; }
        .invalid { color: #e84118; font-weight: bold; }
        .loading { text-align: center; color: #fbc531; display: none; margin-top: 10px; }
        .cookie-text { font-family: monospace; font-size: 12px; color: #aaa; word-break: break-all; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Netflix Cookie Checker</h1>
        <textarea id="cookies" placeholder="Paste your cookies here (nfln=...; uiv=...)"></textarea>
        <button id="checkBtn" onclick="checkCookies()">Check Cookies</button>
        <p class="loading" id="loading">Checking...</p>
        <div class="result-container" id="results"></div>
    </div>
    <script>
        async function checkCookies() {
            const cookieInput = document.getElementById('cookies').value;
            const loading = document.getElementById('loading');
            const resultsDiv = document.getElementById('results');
            const btn = document.getElementById('checkBtn');
            
            if (!cookieInput.trim()) { alert("Please enter at least one cookie."); return; }
            
            const cookies = cookieInput.split('\\n').filter(c => c.trim() !== '');
            loading.style.display = 'block';
            resultsDiv.innerHTML = '';
            btn.disabled = true;
            
            const batchSize = 5; 
            for (let i = 0; i < cookies.length; i += batchSize) {
                const batch = cookies.slice(i, i + batchSize);
                try {
                    const response = await fetch('/api/check', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({cookies: batch})
                    });
                    const data = await response.json();
                    data.results.forEach(res => {
                        const div = document.createElement('div');
                        div.className = 'result-item';
                        div.innerHTML = `<span class="cookie-text">${res.cookie}</span><span class="${res.status ? 'valid' : 'invalid'}">${res.message}</span>`;
                        resultsDiv.appendChild(div);
                    });
                } catch (error) { console.error(error); }
            }
            loading.style.display = 'none';
            btn.disabled = false;
        }
    </script>
</body>
</html>"""

class NetflixChecker:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Origin': 'https://www.netflix.com',
            'Referer': 'https://www.netflix.com/'
        }

    def check_cookie(self, cookie_string):
        cookies = {}
        for line in cookie_string.split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
        
        self.session.cookies.clear()
        self.session.cookies.update(cookies)
        
        try:
            response = self.session.get(
                'https://www.netflix.com/browse',
                headers={'User-Agent': self.headers['User-Agent']}
            )
            if response.status_code == 200 and '/login' not in response.url:
                return True, "Active"
            elif response.status_code == 401:
                return False, "Unauthorized"
            else:
                return False, f"Error: {response.status_code}"
        except Exception as e:
            return False, str(e)

def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    if method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html'},
            'body': HTML_TEMPLATE
        }
    
    if method == 'POST':
        body = json.loads(event.get('body', '{}'))
        cookies_to_check = body.get('cookies', [])
        checker = NetflixChecker()
        results = []
        
        for cookie_str in cookies_to_check:
            status, message = checker.check_cookie(cookie_str)
            results.append({'cookie': cookie_str[:50] + '...', 'status': status, 'message': message})
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'results': results})
        }
    
    return {'statusCode': 405, 'body': 'Method Not Allowed'}
