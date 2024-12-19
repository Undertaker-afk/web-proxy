from flask import Flask, render_template, request, Response
import requests
from urllib.parse import urljoin
import os
import socks
import socket
from requests.auth import HTTPProxyAuth

app = Flask(__name__)

def create_proxy_session(proxy_type, host, port, username=None, password=None):
    session = requests.Session()
    
    if proxy_type in ['http', 'https']:
        proxies = {
            'http': f'{proxy_type}://{host}:{port}',
            'https': f'{proxy_type}://{host}:{port}'
        }
        
        if username and password:
            auth = HTTPProxyAuth(username, password)
            session.auth = auth
            
        session.proxies = proxies
        
    elif proxy_type in ['socks4', 'socks5']:
        socks_type = socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4
        
        if username and password and proxy_type == 'socks5':
            socks.set_default_proxy(socks_type, host, int(port), username=username, password=password)
        else:
            socks.set_default_proxy(socks_type, host, int(port))
            
        socket.socket = socks.socksocket
        
    return session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/browse', methods=['POST'])
def browse():
    proxy_type = request.form['proxy_type']
    proxy_host = request.form['proxy_host']
    proxy_port = request.form['proxy_port']
    proxy_username = request.form.get('proxy_username')
    proxy_password = request.form.get('proxy_password')
    url = request.form['url']

    try:
        # Erstelle eine neue Session mit den Proxy-Einstellungen
        session = create_proxy_session(
            proxy_type,
            proxy_host,
            proxy_port,
            proxy_username,
            proxy_password
        )

        # Request über den Proxy ausführen
        response = session.get(
            url,
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

    except Exception as e:
        error_message = f'Fehler beim Verbinden: {str(e)}'
        return error_message, 500

    finally:
        # Wenn SOCKS verwendet wurde, setzen wir den Socket zurück
        if proxy_type in ['socks4', 'socks5']:
            socket.socket = socket._real_socket

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)