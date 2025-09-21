from flask import Flask, request, render_template_string, redirect, url_for, session
import logging
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for session management

# Configure logging
logger = logging.getLogger('user_activity')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('user_activity.log')
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# HTML Templates

login_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Login Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
            display: flex;
            height: 100vh;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .login-container {
            background: rgba(0,0,0,0.6);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
            width: 300px;
            text-align: center;
        }
        input[type="text"] {
            width: 100%;
            padding: 0.5rem;
            border: none;
            border-radius: 5px;
            margin: 1rem 0;
            font-size: 1rem;
        }
        input[type="submit"] {
            background-color: #6c63ff;
            border: none;
            padding: 0.7rem 1.5rem;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        input[type="submit"]:hover {
            background-color: #5751d1;
        }
        h2 {
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form method="post" action="{{ url_for('login') }}">
            <input type="text" name="login_id" placeholder="Enter your Login ID" required />
            <input type="submit" value="Login" />
        </form>
        {% if error %}
        <p style="color:#ff8080;">{{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

main_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Main Page</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(120deg, #f6d365, #fda085);
            color: #333;
            display: flex;
            height: 100vh;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .main-container {
            background: #fff;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0px 15px 30px rgba(0,0,0,0.1);
            text-align: center;
            width: 400px;
        }
        h1 {
            margin-bottom: 1rem;
            color: #764ba2;
        }
        p {
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        a.logout {
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #764ba2;
            color: white;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        a.logout:hover {
            background-color: #5a3578;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <h1>Welcome, {{ login_id }}!</h1>
        <p>You have successfully logged in to the main page.</p>
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
    </div>
</body>
</html>
"""

# Helper function to get client IP
def get_client_ip():
    # Try to get real IP if behind proxy
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For may contain multiple IPs, take the first one
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

# Helper function to get location from IP using ip-api.com
def get_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                city = data.get('city', '')
                region = data.get('regionName', '')
                country = data.get('country', '')
                return f"{city}, {region}, {country}".strip(', ')
    except Exception as e:
        logger.error(f"Error fetching location for IP {ip}: {e}")
    return "Unknown Location"

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        if not login_id:
            error = 'Please enter a valid Login ID.'
        else:
            ip = get_client_ip()
            location = get_location(ip)
            session['login_id'] = login_id
            session['ip'] = ip
            session['location'] = location

            # Log the login event
            logger.info(f"LOGIN - ID: {login_id} | IP: {ip} | Location: {location}")

            return redirect(url_for('main'))

    return render_template_string(login_page_html, error=error)

@app.route('/main')
def main():
    login_id = session.get('login_id')
    ip = session.get('ip')
    location = session.get('location')

    if not login_id:
        return redirect(url_for('login'))

    # Log page visit activity
    logger.info(f"ACTIVITY - User: {login_id} visited main page | IP: {ip} | Location: {location}")

    return render_template_string(main_page_html, login_id=login_id)

@app.route('/logout')
def logout():
    login_id = session.get('login_id', 'Unknown')
    ip = session.get('ip', 'Unknown IP')
    location = session.get('location', 'Unknown Location')

    logger.info(f"LOGOUT - User: {login_id} logged out | IP: {ip} | Location: {location}")

    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Run on 0.0.0.0 to allow external access if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
