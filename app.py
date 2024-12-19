from flask import Flask, render_template, request, Response
import requests
from urllib.parse import urljoin
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/browse', methods=['POST'])
def browse():
    proxy_host = request.form['proxy_host']
    proxy_port = request.form['proxy_port']
    url = request.form['url']

    # Proxy-Konfiguration
    proxies = {
        'http': f'http://{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_host}:{proxy_port}'
    }

    try:
        # Request über den Proxy ausführen
        response = requests.get(
            url,
            proxies=proxies,
            verify=False  # SSL-Verifizierung deaktivieren (nur für Testzwecke)
        )

        # Links im HTML-Content anpassen
        content = response.text
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Relative URLs zu absoluten URLs umwandeln
            content = content.replace('href="/', f'href="{urljoin(url, "/")}')
            content = content.replace('src="/', f'src="{urljoin(url, "/")}')

        # Response mit Original-Headers zurückgeben
        return Response(
            content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )

    except requests.RequestException as e:
        return f'Fehler beim Verbinden: {str(e)}', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)