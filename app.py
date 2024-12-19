from flask import Flask, render_template, request, session, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
from urllib3.exceptions import InsecureRequestWarning
import time
import socks
import socket
from requests.auth import HTTPProxyAuth
import json
from datetime import datetime

# Deaktiviere Warnungen für unsichere HTTPS-Requests
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Wichtig für Sessions
logging.basicConfig(level=logging.INFO)

class ProxyLogger:
    @staticmethod
    def log_to_response(response, log_entry):
        if not hasattr(response, '_proxy_logs'):
            response._proxy_logs = []
        response._proxy_logs.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': log_entry
        })
        return response

def create_proxy_session(protocol, host, port, username=None, password=None):
    session = requests.Session()
    
    if protocol in ['http', 'https']:
        proxy_url = f"{protocol}://{host}:{port}"
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        session.proxies = proxies
        if username and password:
            session.auth = HTTPProxyAuth(username, password)
    
    elif protocol in ['socks4', 'socks5']:
        socks_type = socks.SOCKS4 if protocol == 'socks4' else socks.SOCKS5
        socks.set_default_proxy(
            socks_type,
            host,
            int(port),
            username=username if username else None,
            password=password if password else None
        )
        socket.socket = socks.socksocket
    
    return session

def modify_links(content, base_url, proxy_settings):
    """Modifiziert alle Links in der HTML-Seite, damit sie über den Proxy geleitet werden"""
    soup = BeautifulSoup(content, 'html.parser')
    
    # Proxy-Parameter für die URLs
    modified_count = 0
    proxy_params = {
        'proxy_host': proxy_settings['host'],
        'proxy_port': proxy_settings['port'],
        'protocol': proxy_settings['protocol']
    }
    if proxy_settings.get('username'):
        proxy_params['proxy_username'] = proxy_settings['username']
        proxy_params['proxy_password'] = proxy_settings['password']
    
    # Relative URLs in absolute URLs umwandeln
    for tag in soup.find_all(['a', 'img', 'link', 'script']):
        for attr in ['href', 'src']:
            if tag.get(attr):
                url = tag.get(attr)
                if not url.startswith(('javascript:', 'data:', '#', 'mailto:')):
                    if not url.startswith(('http://', 'https://')):
                        url = urllib.parse.urljoin(base_url, url)
                    
                    # Erstelle Query-String für Proxy-Parameter
                    query_params = urllib.parse.urlencode({
                        'url': url,
                        **proxy_params
                    })
                    tag[attr] = f"/browse?{query_params}"
    
    return str(soup)

@app.route('/')
def index():
    return render_template('index.html')

def test_proxy_connection(session, protocol):
    """Testet die Proxy-Verbindung mit verschiedenen URLs"""
    test_urls = [
        'http://google.com',
        'https://google.com',
        #'http://httpbin.org/ip',
        #'https://httpbin.org/ip'
    ]
    
    # Wähle die passende Test-URL basierend auf dem Protokoll
    if protocol.startswith('http'):
        urls_to_try = test_urls
    else:
        # Für SOCKS nur HTTPS verwenden
        urls_to_try = [url for url in test_urls if url.startswith('https')]

    for test_url in urls_to_try:
        try:
            response = session.get(test_url, timeout=5, verify=False)
            if response.status_code == 200:
                return response, None
        except requests.exceptions.RequestException as e:
            continue
    
    return None, "Keine der Test-URLs war erreichbar"

@app.route('/test_connection', methods=['POST'])
def test_connection():
    try:
        protocol = request.form.get('protocol', 'http')
        host = request.form.get('proxy_host')
        port = request.form.get('proxy_port')
        use_auth = request.form.get('use_auth') == 'on'
        username = request.form.get('proxy_username') if use_auth else None
        password = request.form.get('proxy_password') if use_auth else None

        logging.info(f"Testing connection to proxy {protocol}://{host}:{port}")

        # Validiere Port
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return jsonify({'success': False, 'error': 'Ungültiger Port (muss zwischen 1 und 65535 liegen)'})
        except ValueError:
            return jsonify({'success': False, 'error': 'Port muss eine Zahl sein'})

        # Validiere Host
        if not host:
            return jsonify({'success': False, 'error': 'Proxy-Host ist erforderlich'})

        start_time = time.time()
        try:
            session = create_proxy_session(protocol, host, port, username, password)
            response, error = test_proxy_connection(session, protocol)
            
            if error:
                return jsonify({'success': False, 'error': error})
            
            if response:
                end_time = time.time()
                latency = round((end_time - start_time) * 1000)
                
                # Versuche die externe IP zu ermitteln
                try:
                    if 'httpbin.org' in response.url:
                        ip_info = response.json()
                        external_ip = ip_info.get('origin', 'Unbekannt')
                    else:
                        external_ip = 'Nicht verfügbar'
                except:
                    external_ip = 'Nicht verfügbar'

                return jsonify({
                    'success': True,
                    'latency': latency,
                    'details': {
                        'status_code': response.status_code,
                        'response_size': len(response.content),
                        'server': response.headers.get('Server', 'Unknown'),
                        'external_ip': external_ip,
                        'protocol_used': protocol
                    }
                })
            
            return jsonify({'success': False, 'error': 'Keine erfolgreiche Verbindung möglich'})

        except requests.exceptions.ProxyError as e:
            error_msg = f"Proxy-Verbindungsfehler: Verbindung zum Proxy-Server nicht möglich. Bitte überprüfen Sie:\n" \
                       f"1. Ist der Proxy-Server aktiv?\n" \
                       f"2. Sind Host und Port korrekt?\n" \
                       f"3. Ist das richtige Protokoll ausgewählt?\n" \
                       f"4. Sind die Authentifizierungsdaten korrekt?"
            logging.error(f"Proxy error: {str(e)}")
            return jsonify({'success': False, 'error': error_msg})
            
        except requests.exceptions.SSLError as e:
            error_msg = "SSL/TLS Fehler: Verschlüsselungsfehler bei der Verbindung"
            logging.error(f"SSL error: {str(e)}")
            return jsonify({'success': False, 'error': error_msg})
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Verbindungsfehler: Server nicht erreichbar oder falsches Protokoll"
            logging.error(f"Connection error: {str(e)}")
            return jsonify({'success': False, 'error': error_msg})
            
        except requests.exceptions.Timeout as e:
            error_msg = "Zeitüberschreitung: Der Server antwortet nicht"
            logging.error(f"Timeout error: {str(e)}")
            return jsonify({'success': False, 'error': error_msg})
            
        except Exception as e:
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            logging.error(f"Unexpected error: {str(e)}")
            return jsonify({'success': False, 'error': error_msg})

    except Exception as e:
        error_msg = f"Fehler beim Testen der Verbindung: {str(e)}"
        logging.error(error_msg)
        return jsonify({'success': False, 'error': error_msg})

@app.route('/browse', methods=['GET', 'POST'])
def browse():
    try:
        if request.method == 'POST':
            # Hole alle Proxy-Einstellungen aus dem Formular
            proxy_settings = {
                'protocol': request.form.get('protocol', 'http'),
                'host': request.form.get('proxy_host'),
                'port': request.form.get('proxy_port'),
                'use_auth': request.form.get('use_auth') == 'on'
            }
            
            if proxy_settings['use_auth']:
                proxy_settings['username'] = request.form.get('proxy_username')
                proxy_settings['password'] = request.form.get('proxy_password')
            
            url = request.form.get('url')
            session['proxy_settings'] = proxy_settings
        else:
            url = request.args.get('url')
            proxy_settings = {
                'protocol': request.args.get('protocol'),
                'host': request.args.get('proxy_host'),
                'port': request.args.get('proxy_port'),
                'username': request.args.get('proxy_username'),
                'password': request.args.get('proxy_password')
            }

        if not url:
            return render_template('index.html', error="Bitte geben Sie eine URL ein.")

        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        # Request-Header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Erstelle Proxy-Session und sende Request
        session = create_proxy_session(
            proxy_settings['protocol'],
            proxy_settings['host'],
            proxy_settings['port'],
            proxy_settings.get('username'),
            proxy_settings.get('password')
        )
        
        response = session.get(url, headers=headers, verify=False, timeout=10)
        
        # Content-Type überprüfen
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            modified_content, modified_links = modify_links(response.text, url, proxy_settings)
            success_message = (
                f"Seite erfolgreich geladen in {request_time}ms. "
                f"Größe: {response_size/1024:.1f}KB. "
                f"{modified_links} Links modifiziert."
            )
            return render_template('index.html', 
                                content=modified_content,
                                success=success_message)
        else:
            # Für nicht-HTML Inhalte (Bilder, PDFs, etc.)
            return response.content, 200, {'Content-Type': response.headers['Content-Type']}

    except requests.exceptions.ProxyError:
        error_message = "Fehler bei der Verbindung zum Proxy-Server. Bitte überprüfen Sie die Proxy-Einstellungen."
        return render_template('index.html', error=error_message)
    except requests.exceptions.ConnectionError:
        error_message = "Verbindungsfehler. Bitte überprüfen Sie die URL und Proxy-Einstellungen."
        return render_template('index.html', error=error_message)
    except requests.exceptions.Timeout:
        error_message = "Zeitüberschreitung bei der Anfrage. Bitte versuchen Sie es erneut."
        return render_template('index.html', error=error_message)
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {str(e)}")
        error_message = f"Ein Fehler ist aufgetreten: {str(e)}"
        return render_template('index.html', error=error_message)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
