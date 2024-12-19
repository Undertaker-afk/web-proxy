from flask import Flask, render_template, request, Response, jsonify
import requests
from urllib.parse import urljoin
import os
import socks
import socket
from requests.auth import HTTPProxyAuth
from urllib3.exceptions import InsecureRequestWarning

# Unterdrücke SSL-Warnungen (nur für Entwicklungszwecke)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

app = Flask(__name__)

# Speicher für die aktuelle Sitzung
session_data = {
    'history': [],
    'current_index': -1
}

def create_proxy_session(proxy_type, host, port, username=None, password=None):
    session = requests.Session()
    
    if proxy_type in ['http', 'https']:
        proxies = {
            'http': f'{proxy_type}://{host}:{port}',
            'https': f'{proxy_type}://{host}:{port}'
        }
        if username and password:
            session.auth = HTTPProxyAuth(username, password)
        session.proxies = proxies
    
    elif proxy_type in ['socks4', 'socks5']:
        socks_type = socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4
        
        def create_connection(address, timeout=None, source_address=None):
            sock = socks.create_connection(
                address,
                timeout=timeout,
                source_address=source_address,
                proxy_type=socks_type,
                proxy_addr=host,
                proxy_port=int(port),
                proxy_username=username if username else None,
                proxy_password=password if password else None
            )
            return sock

        session.proxies = {}
        socket.create_connection = create_connection
    
    return session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test_proxy', methods=['POST'])
def test_proxy():
    try:
        data = request.json
        session = create_proxy_session(
            data['proxy_type'],
            data['proxy_host'],
            data['proxy_port'],
            data.get('proxy_user'),
            data.get('proxy_pass')
        )
        
        # Wähle die Test-URL basierend auf dem Proxy-Typ
        test_url = 'http://www.google.com' if data['proxy_type'] == 'http' else 'https://www.google.com'
        
        # Teste die Verbindung
        test_response = session.get(test_url, timeout=10, verify=False)
        if test_response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': f'Status Code: {test_response.status_code}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/browse', methods=['POST'])
def browse():
    try:
        proxy_type = request.form['proxy_type']
        proxy_host = request.form['proxy_host']
        proxy_port = request.form['proxy_port']
        proxy_user = request.form.get('proxy_user')
        proxy_pass = request.form.get('proxy_pass')
        url = request.form['url']

        session = create_proxy_session(
            proxy_type, 
            proxy_host, 
            proxy_port,
            proxy_user,
            proxy_pass
        )

        response = session.get(url, verify=False)
        
        # Füge URL zum Verlauf hinzu
        session_data['history'].append(url)
        session_data['current_index'] = len(session_data['history']) - 1

        # Links im HTML-Content anpassen
        content = response.text
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Relative URLs zu absoluten URLs umwandeln
            content = content.replace('href="/', f'href="{urljoin(url, "/")}')
            content = content.replace('src="/', f'src="{urljoin(url, "/")}')

        return Response(
            content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )

    except Exception as e:
        return str(e), 500

@app.route('/navigate', methods=['POST'])
def navigate():
    url = request.json.get('url')
    if url:
        # Lösche Forward-History wenn eine neue URL eingegeben wird
        session_data['history'] = session_data['history'][:session_data['current_index'] + 1]
        session_data['history'].append(url)
        session_data['current_index'] = len(session_data['history']) - 1
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No URL provided'})

@app.route('/back')
def go_back():
    if session_data['current_index'] > 0:
        session_data['current_index'] -= 1
        return jsonify({
            'success': True,
            'url': session_data['history'][session_data['current_index']]
        })
    return jsonify({'success': False, 'error': 'No previous page'})

@app.route('/forward')
def go_forward():
    if session_data['current_index'] < len(session_data['history']) - 1:
        session_data['current_index'] += 1
        return jsonify({
            'success': True,
            'url': session_data['history'][session_data['current_index']]
        })
    return jsonify({'success': False, 'error': 'No next page'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)