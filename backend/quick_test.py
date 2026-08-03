#!/usr/bin/env python3
"""
🌐 SERVEUR DE TEST RAPIDE
========================

Serveur HTTP simple pour tester l'API sans problèmes CORS
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

def start_server():
    """Démarre un serveur HTTP local"""
    PORT = 8000
    
    # Changer vers le répertoire parent pour servir le fichier HTML
    os.chdir('..')
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Serveur démarré sur http://localhost:{PORT}")
        print(f"📱 Page de test: http://localhost:{PORT}/test_app_web.html")
        print("🔧 Appuyez sur Ctrl+C pour arrêter")
        
        # Ouvrir automatiquement le navigateur après 2 secondes
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{PORT}/test_app_web.html')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Serveur arrêté")

if __name__ == "__main__":
    print("🚀 Démarrage du serveur de test...")
    start_server()