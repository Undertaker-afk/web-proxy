<!DOCTYPE html>
<html>
<head>
    <title>Proxy Configuration</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            display: flex;
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .config-panel {
            flex: 1;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .log-panel {
            flex: 1;
            background: #1e1e1e;
            color: #fff;
            padding: 20px;
            border-radius: 8px;
            min-height: 400px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="password"],
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .test-btn {
            background-color: #4CAF50;
            color: white;
        }
        .connect-btn {
            background-color: #2196F3;
            color: white;
        }
        .clear-btn {
            background-color: #f44336;
            color: white;
        }
        .auth-fields {
            padding: 10px;
            margin-top: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            display: none;
        }
        .log-entry {
            margin: 5px 0;
            font-family: monospace;
        }
        .success { color: #4CAF50; }
        .error { color: #f44336; }
        .info { color: #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="config-panel">
            <h2>Proxy Configuration</h2>
            <form id="proxyForm">
                <div class="form-group">
                    <label for="protocol">Protokoll:</label>
                    <select id="protocol" required>
                        <option value="http">HTTP</option>
                        <option value="https">HTTPS</option>
                        <option value="socks4">SOCKS4</option>
                        <option value="socks5">SOCKS5</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="hostname">Proxy Hostname:</label>
                    <input type="text" id="hostname" placeholder="proxy.example.com" required>
                </div>
                <div class="form-group">
                    <label for="port">Port:</label>
                    <input type="text" id="port" placeholder="8080" required>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="authRequired"> Authentifizierung erforderlich
                    </label>
                    <div id="authFields" class="auth-fields">
                        <div class="form-group">
                            <label for="username">Benutzername:</label>
                            <input type="text" id="username">
                        </div>
                        <div class="form-group">
                            <label for="password">Passwort:</label>
                            <input type="password" id="password">
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <label for="targetUrl">Ziel URL:</label>
                    <input type="text" id="targetUrl" placeholder="https://example.com" required>
                </div>
                <div class="button-group">
                    <button type="button" class="test-btn" onclick="testConnection()">Verbindung testen</button>
                    <button type="submit" class="connect-btn">Verbinden</button>
                    <button type="button" class="clear-btn" onclick="clearLog()">Log löschen</button>
                </div>
            </form>
        </div>
        <div class="log-panel">
            <h2>Log Konsole</h2>
            <div id="logConsole"></div>
        </div>
    </div>

    <script>
        // Auth Fields Toggle
        document.getElementById('authRequired').addEventListener('change', function() {
            document.getElementById('authFields').style.display = this.checked ? 'block' : 'none';
        });

        // Logging functions
        function log(message, type = 'info') {
            const logConsole = document.getElementById('logConsole');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logConsole.appendChild(entry);
            logConsole.scrollTop = logConsole.scrollHeight;
        }

        function clearLog() {
            document.getElementById('logConsole').innerHTML = '';
            log('Log wurde gelöscht');
        }

        // Form submission
        document.getElementById('proxyForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = getFormData();
            log(`Verbindungsaufbau zu ${formData.targetUrl} über ${formData.protocol}://${formData.hostname}:${formData.port}`);
            // Hier würde die tatsächliche Verbindungslogik implementiert werden
        });

        // Test connection
        function testConnection() {
            const formData = getFormData();
            log('Teste Verbindung...', 'info');
            
            // Simuliere einen Verbindungstest
            setTimeout(() => {
                if (formData.hostname && formData.port) {
                    log(`Erfolgreicher Test: ${formData.protocol}://${formData.hostname}:${formData.port}`, 'success');
                } else {
                    log('Fehler: Hostname und Port sind erforderlich', 'error');
                }
            }, 1000);
        }

        // Helper function to get form data
        function getFormData() {
            return {
                protocol: document.getElementById('protocol').value,
                hostname: document.getElementById('hostname').value,
                port: document.getElementById('port').value,
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
                targetUrl: document.getElementById('targetUrl').value,
                authRequired: document.getElementById('authRequired').checked
            };
        }

        // Initial log message
        log('System bereit');
    </script>
</body>
</html>
