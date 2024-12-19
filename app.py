from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import requests
import logging
from urllib.parse import urlparse
import socks
import socket
import time

app = Flask(__name__)
socketio = SocketIO(app)

# Logging Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.default_socket = socket.socket
        self.default_create_connection = socket.create_connection

    def setup_proxy(self, host, port, protocol, auth=None):
        if protocol.lower() in ['socks4', 'socks5']:
            socks_version = socks.SOCKS4 if protocol.lower() == 'socks4' else socks.SOCKS5
            socks.set_default_proxy(
                socks_version,
                host,
                int(port),
                username=auth.get('username') if auth else None,
                password=auth.get('password') if auth else None
            )
            socket.socket = socks.socksocket
            socket.create_connection = socks.create_connection
        return {
            'http': f'{protocol}://{host}:{port}',
            'https': f'{protocol}://{host}:{port}'
        }

    def reset_proxy(self):
        socket.socket = self.default_socket
        socket.create_connection = self.default_create_connection

proxy_manager = ProxyManager()

def emit_log(message, type='info'):
    socketio.emit('proxyLog', {'message': message, 'type': type})

def create_proxy_dict(protocol, host, port, username=None, password=None):
    """Erstellt das Proxy-Dictionary für requests"""
    auth_string = f"{username}:{password}@" if username and password else ""
    proxy_url = f"{protocol}://{auth_string}{host}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def validate_url(url):
    """Überprüft, ob eine URL gültig ist"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-proxy', methods=['POST'])
def test_proxy():
    data = request.json
    try:
        proxies = proxy_manager.setup_proxy(
            data['host'],
            data['port'],
            data['protocol'],
            data['auth']
        )
        
        # Test-URL (Google)
        test_url = 'https://www.google.com'
        start_time = time.time()
        
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            emit_log(f'Proxy-Test erfolgreich! Antwortzeit: {response_time:.2f}s', 'success')
            return jsonify({'success': True})
        else:
            emit_log(f'Proxy-Test fehlgeschlagen: Status {response.status_code}', 'error')
            return jsonify({'success': False, 'error': f'Status {response.status_code}'})
            
    except Exception as e:
        emit_log(f'Proxy-Test fehlgeschlagen: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)})
    finally:
        proxy_manager.reset_proxy()

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    try:
        proxies = proxy_manager.setup_proxy(
            data['host'],
            data['port'],
            data['protocol'],
            data['auth']
        )
        
        target_url = data['targetUrl']
        emit_log(f'Verbinde mit {target_url}...', 'info')
        
        response = requests.get(target_url, proxies=proxies, timeout=15)
        
        if response.status_code == 200:
            # Modifiziere Links im HTML-Content für relative URLs
            content = response.text
            base_url = urlparse(target_url)
            content = content.replace('href="/', f'href="{base_url.scheme}://{base_url.netloc}/')
            content = content.replace('src="/', f'src="{base_url.scheme}://{base_url.netloc}/')
            
            emit_log('Verbindung erfolgreich hergestellt!', 'success')
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            emit_log(f'Verbindung fehlgeschlagen: Status {response.status_code}', 'error')
            return jsonify({
                'success': False,
                'error': f'Status {response.status_code}'
            })
            
    except Exception as e:
        emit_log(f'Verbindungsfehler: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'error': str(e)
        })
    finally:
        proxy_manager.reset_proxy()

if __name__ == '__main__':
    socketio.run(app, debug=True)
