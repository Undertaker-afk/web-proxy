// Socket.io Verbindung aufbauen
const socket = io();

// DOM Elemente
const authCheckbox = document.getElementById('authRequired');
const authFields = document.querySelector('.auth-fields');
const consoleOutput = document.getElementById('console');
const navigationBar = document.querySelector('.navigation-bar');
const webContent = document.getElementById('webContent');

// Event Listener für Auth Checkbox
authCheckbox.addEventListener('change', () => {
    authFields.style.display = authCheckbox.checked ? 'block' : 'none';
});

// Funktion zum Hinzufügen von Konsoleneinträgen
function addConsoleLog(message, type = 'info') {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    consoleOutput.appendChild(logEntry);
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// Proxy-Verbindung testen
document.getElementById('testConnection').addEventListener('click', async () => {
    const proxyData = getProxyData();
    addConsoleLog('Teste Proxy-Verbindung...', 'info');
    
    try {
        const response = await fetch('/test-proxy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(proxyData)
        });
        
        const result = await response.json();
        if (result.success) {
            addConsoleLog('Proxy-Verbindung erfolgreich!', 'success');
        } else {
            addConsoleLog(`Proxy-Verbindung fehlgeschlagen: ${result.error}`, 'error');
        }
    } catch (error) {
        addConsoleLog(`Fehler beim Testen der Verbindung: ${error}`, 'error');
    }
});

// Mit URL über Proxy verbinden
document.getElementById('connectButton').addEventListener('click', async () => {
    const proxyData = getProxyData();
    const targetUrl = document.getElementById('targetUrl').value;
    
    if (!targetUrl) {
        addConsoleLog('Bitte geben Sie eine Ziel-URL ein.', 'error');
        return;
    }

    addConsoleLog(`Verbinde mit ${targetUrl}...`, 'info');
    
    try {
        const response = await fetch('/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ...proxyData, targetUrl })
        });
        
        const result = await response.json();
        if (result.success) {
            showWebContent(result.content);
            navigationBar.style.display = 'flex';
            document.getElementById('currentUrl').textContent = targetUrl;
            addConsoleLog('Verbindung erfolgreich hergestellt!', 'success');
        } else {
            addConsoleLog(`Verbindung fehlgeschlagen: ${result.error}`, 'error');
        }
    } catch (error) {
        addConsoleLog(`Fehler beim Verbinden: ${error}`, 'error');
    }
});

// Hilfsfunktion zum Sammeln der Proxy-Daten
function getProxyData() {
    return {
        host: document.getElementById('proxyHost').value,
        port: document.getElementById('proxyPort').value,
        protocol: document.getElementById('protocol').value,
        auth: authCheckbox.checked ? {
            username: document.getElementById('proxyUsername').value,
            password: document.getElementById('proxyPassword').value
        } : null
    };
}

// Webinhalt anzeigen
function showWebContent(content) {
    const iframe = document.createElement('iframe');
    iframe.srcdoc = content;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    
    webContent.innerHTML = '';
    webContent.appendChild(iframe);
}

// Navigation Buttons
document.getElementById('backButton').addEventListener('click', () => {
    // Implementierung der Zurück-Funktion
    addConsoleLog('Navigiere zurück...', 'info');
});

document.getElementById('forwardButton').addEventListener('click', () => {
    // Implementierung der Vorwärts-Funktion
    addConsoleLog('Navigiere vorwärts...', 'info');
});

document.getElementById('disconnectButton').addEventListener('click', () => {
    webContent.innerHTML = '';
    navigationBar.style.display = 'none';
    addConsoleLog('Verbindung getrennt.', 'info');
});

// Socket.io Event Listener für Live-Updates
socket.on('proxyLog', (data) => {
    addConsoleLog(data.message, data.type);
});