from flask import Flask, request, render_template, jsonify
import requests
from urllib.parse import urlparse
import re

app = Flask(__name__)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_proxy(proxy):
    # Einfache Validierung für IP:Port Format
    proxy_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$')
    return bool(proxy_pattern.match(proxy))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    proxy = request.form.get('proxy')
    url = request.form.get('url')
    
    # Validierung der Eingaben
    if not url or not proxy:
        return jsonify({'error': 'URL und Proxy-Adresse sind erforderlich'}), 400
    
    if not is_valid_url(url):
        return jsonify({'error': 'Ungültige URL'}), 400
    
    if not is_valid_proxy(proxy):
        return jsonify({'error': 'Ungültiges Proxy-Format (verwende IP:Port)'}), 400

    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        response = requests.get(
            url, 
            proxies=proxies, 
            timeout=10,
            verify=False  # Deaktiviert SSL-Verifizierung
        )
        
        return jsonify({
            'status': response.status_code,
            'content': response.text,
            'headers': dict(response.headers)
        })
    
    except requests.exceptions.ProxyError:
        return jsonify({'error': 'Proxy-Verbindungsfehler'}), 500
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Zeitüberschreitung der Anfrage'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Fehler: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
