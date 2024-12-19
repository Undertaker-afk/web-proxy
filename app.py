from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import socks
import socket
import logging
from urllib.parse import urlparse
import base64

app = Flask(__name__)
CORS(app)  # Aktiviert CORS für alle Routen

# Logging Konfiguration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyConnection:
    def __init__(self):
        self.default_socket = socket.socket
        
    def setup_socks_proxy(self, proxy_type, host, port, username=None, password=None):
        """Konfiguriert SOCKS Proxy"""
        if proxy_type.lower() == 'socks4':
            socks_type = socks.SOCKS4
        elif proxy_type.lower() == 'socks5':
            socks_type = socks.SOCKS5
        else:
            return False
            
        socks.set_default_proxy(
            socks_type,
            host,
            int(port),
            username=username,
            password=password
        )
        socket.socket = socks.socksocket
        return True
        
    def reset_connection(self):
        """Setzt die Socket-Verbindung zurück"""
        socket.socket = self.default_socket

proxy_connection = ProxyConnection()

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

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        protocol = data.get('protocol', '').lower()
        host = data.get('hostname')
        port = data.get('port')
        username = data.get('username')
        password = data.get('password')
        auth_required = data.get('authRequired', False)

        if not all([protocol, host, port]):
            return jsonify({
                'success': False,
                'message': 'Protokoll, Host und Port sind erforderlich'
            }), 400

        # Test URL für die Verbindungsprüfung
        test_url = 'http://example.com'

        try:
            if protocol in ['socks4', 'socks5']:
                proxy_connection.setup_socks_proxy(
                    protocol,
                    host,
                    port,
                    username if auth_required else None,
                    password if auth_required else None
                )
                response = requests.get(test_url, timeout=10)
            else:
                proxies = create_proxy_dict(
                    protocol,
                    host,
                    port,
                    username if auth_required else None,
                    password if auth_required else None
                )
                response = requests.get(test_url, proxies=proxies, timeout=10)

            return jsonify({
                'success': True,
                'message': 'Verbindungstest erfolgreich',
                'status_code': response.status_code
            })

        except requests.exceptions.RequestException as e:
            logger.error(f"Verbindungsfehler: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Verbindungsfehler: {str(e)}'
            }), 500

        finally:
            if protocol in ['socks4', 'socks5']:
                proxy_connection.reset_connection()

    except Exception as e:
        logger.error(f"Serverfehler: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Serverfehler: {str(e)}'
        }), 500

@app.route('/api/proxy', methods=['POST'])
def proxy_request():
    try:
        data = request.json
        target_url = data.get('targetUrl')
        protocol = data.get('protocol', '').lower()
        host = data.get('hostname')
        port = data.get('port')
        username = data.get('username')
        password = data.get('password')
        auth_required = data.get('authRequired', False)

        if not all([target_url, protocol, host, port]):
            return jsonify({
                'success': False,
                'message': 'Ziel-URL, Protokoll, Host und Port sind erforderlich'
            }), 400

        if not validate_url(target_url):
            return jsonify({
                'success': False,
                'message': 'Ungültige Ziel-URL'
            }), 400

        try:
            if protocol in ['socks4', 'socks5']:
                proxy_connection.setup_socks_proxy(
                    protocol,
                    host,
                    port,
                    username if auth_required else None,
                    password if auth_required else None
                )
                response = requests.get(target_url, timeout=30)
            else:
                proxies = create_proxy_dict(
                    protocol,
                    host,
                    port,
                    username if auth_required else None,
                    password if auth_required else None
                )
                response = requests.get(target_url, proxies=proxies, timeout=30)

            # Versuche den Content-Type zu bestimmen
            content_type = response.headers.get('content-type', '')
            
            # Bei Textinhalten, sende den Text zurück
            if 'text' in content_type or 'json' in content_type:
                return jsonify({
                    'success': True,
                    'content_type': content_type,
                    'content': response.text,
                    'status_code': response.status_code
                })
            # Bei Binärdaten, kodiere sie als Base64
            else:
                encoded_content = base64.b64encode(response.content).decode('utf-8')
                return jsonify({
                    'success': True,
                    'content_type': content_type,
                    'content': encoded_content,
                    'is_base64': True,
                    'status_code': response.status_code
                })

        except requests.exceptions.RequestException as e:
            logger.error(f"Proxy-Fehler: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Proxy-Fehler: {str(e)}'
            }), 500

        finally:
            if protocol in ['socks4', 'socks5']:
                proxy_connection.reset_connection()

    except Exception as e:
        logger.error(f"Serverfehler: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Serverfehler: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
