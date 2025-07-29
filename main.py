from datetime import datetime
from collections import deque
from urllib.parse import urlparse
from interface import Ui_MainWindow
from download_widget import Ui_Form
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QTreeWidgetItem, QLabel, QProgressBar, QPushButton

import os
import re
import sys
import time
import socket
import easygui
import requests
import configparser

def convert_bytes(size):
    if size < 1024:
        return f"{size} bytes"
    
    for unit in ['KB', 'MB', 'GB', 'TB']:
        size /= 1024.0
        if size < 1024.0:
            return f"{size:.1f} {unit}"
    
    return f"{size:.1f} PB"

class PortListenerThread(QThread):
    url_received = Signal(str)
    
    def __init__(self, port=8080, parent=None):
        super().__init__(parent)
        self.port = port
        self.running = True
        
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', self.port))
            s.listen(1)
            s.settimeout(1.0)  # Adicionado timeout para evitar bloqueio
            while self.running:
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                with conn:
                    # Receba todos os dados
                    data = b""
                    while True:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                        if b'\r\n\r\n' in data:  # Fim dos headers HTTP
                            break
                    
                    if data:
                        request_str = data.decode('utf-8', errors='ignore')

                        # Analisar solicitação HTTP
                        if request_str.startswith('POST'):
                            # Extrair corpo da solicitação POST
                            if '\r\n\r\n' in request_str:
                                headers, body = request_str.split('\r\n\r\n', 1)
                                url = body.strip()
                                if url:
                                    self.url_received.emit(url)

                                    # Enviar resposta HTTP
                                    response = (
                                        "HTTP/1.1 200 OK\r\n"
                                        "Content-Type: text/plain\r\n"
                                        "Access-Control-Allow-Origin: *\r\n"
                                        "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                                        "Access-Control-Allow-Headers: Content-Type\r\n"
                                        "Content-Length: 2\r\n"
                                        "\r\n"
                                        "OK"
                                    )
                                    conn.sendall(response.encode())
                        elif request_str.startswith('OPTIONS'):
                            # Lidar com solicitação CORS preflight
                            response = (
                                "HTTP/1.1 200 OK\r\n"
                                "Access-Control-Allow-Origin: *\r\n"
                                "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
                                "Access-Control-Allow-Headers: Content-Type\r\n"
                                "Content-Length: 0\r\n"
                                "\r\n"
                            )
                            conn.sendall(response.encode())
                        else:
                            # Lidar com outras solicitações
                            response = (
                                "HTTP/1.1 405 Method Not Allowed\r\n"
                                "Content-Length: 0\r\n"
                                "\r\n"
                            )
                            conn.sendall(response.encode())
    
    def stop(self):
        self.running = False
        # Gera uma conexão dummy para desbloquear o accept()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', self.port))
                s.sendall(b'')
        except Exception:
            pass

class UrlResolverThread(QThread):
    """Thread para resolver URLs que precisam de redirecionamentos"""
    url_resolved = Signal(str, str)  # url_original, url_final
    resolution_failed = Signal(str, str)  # url_original, erro
    
    def __init__(self, original_url, parent=None):
        super().__init__(parent)
        self.original_url = original_url
        self.max_redirects = 10
        self.timeout = 30
        
    def run(self):
        try:
            resolved_url = self.resolve_download_url(self.original_url)
            if resolved_url and resolved_url != self.original_url:
                print(f"URL resolvida: {self.original_url} -> {resolved_url}")
                self.url_resolved.emit(self.original_url, resolved_url)
            else:
                # Se não houve mudança, usa a URL original
                self.url_resolved.emit(self.original_url, self.original_url)
                
        except Exception as e:
            print(f"Erro ao resolver URL {self.original_url}: {e}")
            self.resolution_failed.emit(self.original_url, str(e))
    
    def resolve_download_url(self, url):
        """
        Resolve URLs com redirecionamentos e retorna o link final do arquivo
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        current_url = url
        redirect_count = 0
        
        while redirect_count < self.max_redirects:
            try:
                print(f"Verificando URL: {current_url}")
                
                # Primeiro tenta HEAD para ser mais rápido
                response = session.head(current_url, allow_redirects=False, timeout=self.timeout)
                
                # Se é um redirecionamento
                if response.status_code in [301, 302, 303, 307, 308]:
                    location = response.headers.get('Location')
                    if location:
                        # Resolve URL relativas
                        if location.startswith('/'):
                            from urllib.parse import urljoin
                            current_url = urljoin(current_url, location)
                        elif location.startswith('http'):
                            current_url = location
                        else:
                            from urllib.parse import urljoin
                            current_url = urljoin(current_url, location)
                        
                        redirect_count += 1
                        print(f"Redirecionamento {redirect_count}: {current_url}")
                        continue
                
                # Se chegou aqui, não há mais redirecionamentos
                if response.status_code == 200:
                    # Verifica se é realmente um arquivo para download
                    content_type = response.headers.get('content-type', '').lower()
                    content_disposition = response.headers.get('content-disposition', '').lower()
                    
                    # Se tem content-disposition, provavelmente é um download
                    if 'attachment' in content_disposition or 'filename=' in content_disposition:
                        return current_url
                    
                    # Verifica tipos de conteúdo que indicam arquivo
                    download_content_types = [
                        'application/octet-stream',
                        'application/zip',
                        'application/pdf',
                        'application/x-msdownload',
                        'application/vnd.ms-excel',
                        'application/vnd.openxmlformats',
                        'image/',
                        'video/',
                        'audio/'
                    ]
                    
                    if any(ct in content_type for ct in download_content_types):
                        return current_url
                    
                    # Se é HTML, pode precisar de mais análise
                    if 'text/html' in content_type:
                        # Tenta GET para analisar o conteúdo
                        get_response = session.get(current_url, timeout=self.timeout)
                        if get_response.status_code == 200:
                            # Busca por links de download no HTML
                            download_url = self.extract_download_link_from_html(get_response.text, current_url)
                            if download_url:
                                # Recursivamente resolve o novo link encontrado
                                return self.resolve_download_url(download_url)
                    
                    return current_url
                
                elif response.status_code == 405:  # Metodo não permitido
                    # Tenta GET se HEAD não for permitido
                    get_response = session.get(current_url, stream=True, timeout=self.timeout)
                    if get_response.status_code == 200:
                        return current_url
                
                # Se chegou aqui e não é sucesso, retorna a URL atual
                return current_url
                
            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição para {current_url}: {e}")
                # Em caso de erro, retorna a URL que estava tentando
                return current_url
        
        # Se excedeu o limite de redirecionamentos
        print(f"Limite de redirecionamentos excedido para {url}")
        return current_url
    
    def extract_download_link_from_html(self, html_content, base_url):
        """
        Extrai links de download do conteúdo HTML
        """
        import re
        from urllib.parse import urljoin
        
        # Padrões comuns para links de download
        patterns = [
            r'href=["\']([^"\']*(?:download|file|attachment)[^"\']*)["\']',
            r'href=["\']([^"\']*\.(?:zip|rar|exe|pdf|mp4|mp3|doc|xlsx)[^"\']*)["\']',
            r'data-download-url=["\']([^"\']+)["\']',
            r'data-file-url=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    return match
                elif match.startswith('/'):
                    return urljoin(base_url, match)
                else:
                    return urljoin(base_url, match)
        
        return None

class DownloadThread(QThread):
    progress_changed = Signal(int)
    size_changed = Signal(int, int)
    time_remaining_changed = Signal(str)
    speed_changed = Signal(str)
    download_finished = Signal(bool)
    cancelled = Signal(bool)

    def __init__(self, url, filename):
        """
        url: link do arquivo para ser baixado
        filename: nome do arquivo
        """
        
        super().__init__()
        self.url = url
        self.filename = filename
        self.speed_history = deque(maxlen = 10)
        self._cancelled = False
        self._response = None

    def cancel(self):
        """
        Cancela o download atual
        """
        self._cancelled = True
        if self._response:
            try:
                self._response.close()
            except Exception:
                pass

    def run(self):
        self.setPriority(QThread.TimeCriticalPriority)
        
        try:
            # Verifica cancelamento antes de iniciar
            if self._cancelled:
                self.cancelled.emit(True)
                return
                
            # Configurações mais robustas para a requisição
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            print(f"Iniciando download da URL: {self.url}")
            
            self._response = requests.get(self.url, stream=True, headers=headers, allow_redirects=True, timeout=30)
            print(f"Resposta HTTP: {self._response.status_code}")
            print(f"Headers da resposta: {dict(self._response.headers)}")
            
            # Verifica cancelamento após obter a resposta
            if self._cancelled:
                self._response.close()
                self.cancelled.emit(True)
                return
            
            self._response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
            
            total_size = int(self._response.headers.get('content-length', 0))
            print(f"Tamanho total do arquivo: {total_size} bytes")
            
            block_size = 8192  # Aumenta o tamanho do bloco para melhor performance
            start_time = time.time()
            downloaded = 0
            
            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            print(f"Salvando arquivo em: {self.filename}")
            
            with open(self.filename, 'wb') as file:
                for data in self._response.iter_content(block_size):
                    # Verifica cancelamento a cada iteração
                    if self._cancelled:
                        self._response.close()
                        # Remove arquivo parcial
                        try:
                            file.close()
                            if os.path.exists(self.filename):
                                os.remove(self.filename)
                        except Exception:
                            pass
                        self.cancelled.emit(True)
                        return
                        
                    if data:  # Filtra blocos vazios
                        file.write(data)
                        downloaded += len(data)
                        
                        # Calcula progresso
                        if total_size > 0:
                            progress = min(int(downloaded * 100 / total_size), 100)
                        else:
                            progress = 0
                        
                        self.progress_changed.emit(progress)
                        self.size_changed.emit(downloaded, total_size)
                        
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed = downloaded / elapsed_time
                            self.speed_history.append(speed)
                            average_speed = sum(self.speed_history) / len(self.speed_history)
                            speed_mbps = average_speed / (1024 * 1024)
                            self.speed_changed.emit(f'Velocidade: {speed_mbps:.2f} MB/s')
                            
                            if average_speed > 0 and total_size > 0:
                                remaining_time = (total_size - downloaded) / average_speed
                                if remaining_time < 60:
                                    self.time_remaining_changed.emit(f'Tempo restante: {remaining_time:.1f} segundos')
                                else:
                                    minutes = int(remaining_time // 60)
                                    seconds = int(remaining_time % 60)
                                    self.time_remaining_changed.emit(f'Tempo restante: {minutes}m {seconds}s')
                            else:
                                self.time_remaining_changed.emit('Tempo restante: calculando...')
                                
            # Download concluído com sucesso (só chega aqui se não foi cancelado)
            if not self._cancelled:
                final_size = os.path.getsize(self.filename)
                print(f"Download concluído! Arquivo salvo: {self.filename} ({final_size} bytes)")
                self.download_finished.emit(True)
                self.time_remaining_changed.emit('Download concluído!')
                                
        except requests.exceptions.RequestException as e:
            if not self._cancelled:
                print(f"Erro durante o download: {e}")
                self.time_remaining_changed.emit(f'Erro: {str(e)}')
                self.download_finished.emit(False)
        except Exception as e:
            if not self._cancelled:
                print(f"Erro inesperado durante o download: {e}")
                self.time_remaining_changed.emit(f'Erro inesperado: {str(e)}')
                self.download_finished.emit(False)
                        
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Smart Downloader")
        self.download_dialog = QDialog(self)
        self.download_ui = Ui_Form()
        self.download_ui.setupUi(self.download_dialog)
        
        self.download_thread = None
        self.connections_setup = False  # Flag para controlar conexões
        
        self.novo_download.clicked.connect(self.show_download_widget)
        self.btn_clean_debug.clicked.connect(self.clear_downloads_history)
        self.download_ui.baixar.clicked.connect(self.init_download)
        self.download_ui.cancelar.clicked.connect(self.close_dialog)
        
        self.setStyleSheet("QFrame { border: None; }")
        
        self.saved_urls = set()
        self.load_settings()
        
        # Inicia o escutador de porta para receber a URL do navegador
        self.port_listener = PortListenerThread(port=8080)
        self.port_listener.url_received.connect(self.handle_url_received)
        self.port_listener.start()
    
    def setup_download_dialog_connections(self):
        """Configura as conexões do diálogo de download apenas uma vez"""
        if not self.connections_setup:
            self.download_ui.caminho_explorar.clicked.connect(self.set_local_save)
            self.download_ui.URL.textChanged.connect(self.check_fields)
            self.download_ui.caminho.textChanged.connect(self.check_fields)
            self.connections_setup = True
    
    def closeEvent(self, event):
        self.save_settings()
        self.port_listener.stop()
        self.port_listener.terminate()
        
        # Para a thread de resolução se estiver rodando
        if hasattr(self, 'url_resolver') and self.url_resolver.isRunning():
            self.url_resolver.terminate()
            
        event.accept()
        
    def handle_url_received(self, url):
        # Define o campo URL com a url recebida e tenta resolver redirecionamentos
        
        # Limpa e valida a URL recebida
        url = url.strip()
        
        # Se a URL não tem protocolo, assume http://
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('www.'):
                url = 'https://' + url
            else:
                url = 'https://' + url
        
        # Extrai apenas a URL da string recebida (remove possíveis caracteres extras)
        match = re.search(r'(https?://[^\s<>"]+)', url)
        extracted_url = match.group(1) if match else url
        
        # Remove caracteres problemáticos do final da URL
        extracted_url = extracted_url.rstrip('.,;!?)')
        
        print(f"URL recebida: {extracted_url}")
        
        # Inicia o processo de resolução da URL
        self.resolve_and_show_download(extracted_url)
    
    def resolve_and_show_download(self, url):
        """
        Resolve a URL e exibe o widget de download com a URL final
        """
        print(f"Iniciando resolução da URL: {url}")
        
        # Define a URL original no campo (será atualizada quando resolver)
        self.download_ui.URL.setText(url)
        
        # Cria e inicia a thread de resolução
        self.url_resolver = UrlResolverThread(url)
        self.url_resolver.url_resolved.connect(self.on_url_resolved)
        self.url_resolver.resolution_failed.connect(self.on_url_resolution_failed)
        self.url_resolver.start()
        
        # Mostra o widget imediatamente com a URL original
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.show_download_widget_from_url)
    
    def on_url_resolved(self, original_url, resolved_url):
        """
        Callback chamado quando a URL é resolvida com sucesso
        """
        print(f"URL resolvida com sucesso: {original_url} -> {resolved_url}")
        
        # Atualiza o campo URL com a URL resolvida
        self.download_ui.URL.setText(resolved_url)
        
        # Se a janela já estiver aberta, força uma atualização
        if self.download_dialog.isVisible():
            self.download_dialog.setWindowTitle("Novo Download - URL Resolvida")
    
    def on_url_resolution_failed(self, original_url, error):
        """
        Callback chamado quando a resolução da URL falha
        """
        print(f"Falha ao resolver URL {original_url}: {error}")
        
        # Mantém a URL original
        self.download_ui.URL.setText(original_url)
        
        # Se a janela já estiver aberta, mostra uma notificação
        if self.download_dialog.isVisible():
            self.download_dialog.setWindowTitle("Novo Download - URL Original (Resolução Falhou)")
    
    def show_download_widget_from_url(self):
        """Exibe o widget de download quando uma URL é recebida da extensão"""
        
        # Configura a janela para aparecer em primeiro plano
        self.download_dialog.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.download_dialog.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.download_dialog.setWindowTitle("Novo Download - Resolvendo URL...")
        self.download_dialog.setModal(False)
        
        # Configura as conexões apenas uma vez
        self.setup_download_dialog_connections()
        
        # Define um caminho padrão se não existir
        if not self.download_ui.caminho.text():
            default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_ui.caminho.setText(default_path)
        
        self.check_fields()
        
        # Centraliza a janela na tela
        screen = QApplication.primaryScreen().geometry()
        dialog_size = self.download_dialog.sizeHint()
        x = (screen.width() - dialog_size.width()) // 2
        y = (screen.height() - dialog_size.height()) // 2
        self.download_dialog.move(x, y)
        
        # Exibe e força foco na janela
        self.download_dialog.show()
        self.download_dialog.raise_()
        self.download_dialog.activateWindow()
        
        # Força a janela para frente no Windows
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.download_dialog.winId())
                
                # Diferentes tentativas para garantir que a janela apareça
                ctypes.windll.user32.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_TOPMOST
                
            except Exception:
                pass
        
        # Força o processamento de eventos
        QApplication.processEvents()
        
        # Tentar novamente após um pequeno delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, lambda: self._ensure_dialog_visible())
    
    def _ensure_dialog_visible(self):
        """Garante que o diálogo esteja visível"""
        if not self.download_dialog.isVisible():
            self.download_dialog.show()
            self.download_dialog.raise_()
            self.download_dialog.activateWindow()
    
    def save_settings(self):
        """
        Salva as configurações e histórico de downloads no arquivo settings.ini
        """
        config = configparser.ConfigParser()
        
        try:
            # Salva configurações gerais
            config['Settings'] = {
                'caminho': self.download_ui.caminho.text(),
                'versao': '1.0',
                'ultima_atualizacao': datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            }
            
            downloads_saved = 0
            
            # Salva histórico de downloads
            for i in range(self.downloads_window.topLevelItemCount()):
                item = self.downloads_window.topLevelItem(i)
                section_name = f'Download_{i:03d}'  # Usa padding para manter ordem
                config[section_name] = {}
                
                # Salva nome do arquivo
                arquivo_nome = item.text(0)
                config[section_name]['arquivo_nome'] = arquivo_nome
                
                # Inicializa campos com valores padrão
                download_data = {
                    'url': '',
                    'tamanho': '',
                    'tempo_restante': '',
                    'velocidade': '',
                    'data_hora': '',
                    'salvo_em': ''
                }
                
                # Extrai informações dos widgets filhos
                for j in range(item.childCount()):
                    child = item.child(j)
                    child_widget = self.downloads_window.itemWidget(child, 0)
                    
                    if isinstance(child_widget, QLabel):
                        text = child_widget.text()
                        
                        # Remove emojis e formata o texto para salvamento
                        clean_text = self._clean_text_for_saving(text)
                        
                        # Identifica o tipo de informação baseado no conteúdo
                        if any(keyword in clean_text.lower() for keyword in ["url:", "🔗"]):
                            download_data['url'] = clean_text
                        elif any(keyword in clean_text.lower() for keyword in ["tamanho:", "📊"]):
                            download_data['tamanho'] = clean_text
                        elif any(keyword in clean_text.lower() for keyword in ["tempo restante:", "status:", "⏱️"]):
                            download_data['tempo_restante'] = clean_text
                        elif any(keyword in clean_text.lower() for keyword in ["velocidade:", "🚀"]):
                            download_data['velocidade'] = clean_text
                        elif any(keyword in clean_text.lower() for keyword in ["baixado em:", "data e hora:", "📅"]):
                            download_data['data_hora'] = clean_text
                        elif any(keyword in clean_text.lower() for keyword in ["local:", "salvo em:", "pasta:", "💾"]):
                            download_data['salvo_em'] = clean_text
                
                # Salva os dados no arquivo de configuração
                for key, value in download_data.items():
                    config[section_name][key] = value if value else f"{key.replace('_', ' ').title()}: não disponível"
                
                downloads_saved += 1
            
            # Salva o arquivo
            with open('settings.ini', 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            
            print(f"Configurações salvas: {downloads_saved} downloads no histórico")
            
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    
    def _clean_text_for_saving(self, text):
        """
        Limpa o texto removendo emojis e formatação para salvamento
        """
        if not text:
            return ""
        
        # Remove emojis comuns
        emojis_to_remove = ["📊", "⏱️", "🚀", "📅", "💾", "🔗"]
        cleaned_text = text
        
        for emoji in emojis_to_remove:
            cleaned_text = cleaned_text.replace(emoji, "").strip()
        
        # Remove espaços extras
        cleaned_text = " ".join(cleaned_text.split())
        
        return cleaned_text
    
    def load_settings(self):
        """
        Carrega as configurações e histórico de downloads do arquivo settings.ini
        """
        config = configparser.ConfigParser()
        downloads_loaded = 0
        
        self.downloads_window.setUniformRowHeights(True)
        
        try:
            config.read('settings.ini', encoding='utf-8')
            print("Carregando configurações do arquivo settings.ini...")
            
            # Carrega configurações gerais
            if 'Settings' in config:
                saved_path = config['Settings'].get('caminho', '')
                if saved_path:
                    self.download_ui.caminho.setText(saved_path)
                    print(f"Caminho padrão carregado: {saved_path}")
                else:
                    # Define caminho padrão se não existir
                    default_path = os.path.join(os.path.expanduser("~"), "Downloads")
                    self.download_ui.caminho.setText(default_path)
                    print(f"Usando caminho padrão: {default_path}")
            
            # Carrega histórico de downloads
            download_sections = [section for section in config.sections() if section.startswith('Download_')]
            
            if download_sections:
                print(f"Encontradas {len(download_sections)} entradas de download no histórico:")
                
                # Ordena as seções por número para manter ordem cronológica
                download_sections.sort(key=lambda x: int(x.split('_')[1]) if x.split('_')[1].isdigit() else 0)
                
                for section in download_sections:
                    try:
                        # Verifica se a seção tem os campos obrigatórios
                        if 'arquivo_nome' not in config[section]:
                            print(f"Seção {section} incompleta - faltando arquivo_nome, pulando...")
                            continue
                        
                        # Extrai informações do download
                        download_info = {
                            'arquivo_nome': config[section]['arquivo_nome'],
                            'url': self._clean_field_value(config[section].get('url', '')),
                            'tamanho': self._clean_field_value(config[section].get('tamanho', 'Tamanho: não disponível')),
                            'tempo_restante': self._clean_field_value(config[section].get('tempo_restante', 'Tempo restante: não disponível')),
                            'velocidade': self._clean_field_value(config[section].get('velocidade', 'Velocidade: não disponível')),
                            'data_hora': self._clean_field_value(config[section].get('data_hora', 'Data e Hora: não disponível')),
                            'salvo_em': self._clean_field_value(config[section].get('salvo_em', 'Salvo em: não disponível'))
                        }
                        
                        # Adiciona o item ao histórico
                        self.add_download_item(download_info)
                        downloads_loaded += 1
                        
                        # Adiciona URL ao conjunto de URLs salvas (se existir)
                        if download_info['url'] and download_info['url'] != 'URL: não disponível':
                            url_clean = download_info['url'].replace('URL: ', '').strip()
                            if url_clean:
                                self.saved_urls.add(url_clean)
                        
                        # Log detalhado do download carregado
                        filename = download_info['arquivo_nome']
                        date_info = download_info['data_hora'].replace('Data e Hora: ', '') if 'Data e Hora:' in download_info['data_hora'] else 'data não disponível'
                        print(f"{filename} - {date_info}")
                        
                    except Exception as e:
                        print(f"Erro ao carregar seção {section}: {e}")
                        continue
                
                print(f"{downloads_loaded} downloads carregados com sucesso do histórico")
                
            else:
                print("Nenhum histórico de download encontrado")
                
        except FileNotFoundError:
            print("Arquivo settings.ini não encontrado - será criado na primeira execução")
            # Define caminho padrão quando não há arquivo de configuração
            default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_ui.caminho.setText(default_path)
            
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            # Define caminho padrão em caso de erro
            default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_ui.caminho.setText(default_path)
            
        # Log final
        if downloads_loaded > 0:
            print(f"Configurações carregadas: {downloads_loaded} downloads no histórico")
        else:
            print("Configurações carregadas: histórico vazio")
    
    def _clean_field_value(self, field_value):
        """
        Limpa e normaliza valores de campo do arquivo de configuração
        """
        if not field_value:
            return ""
        
        # Remove quebras de linha e espaços extras
        cleaned = field_value.strip().replace('\n', ' ').replace('\r', '')
        
        # Se o campo estiver vazio após limpeza, retorna valor padrão baseado no prefixo esperado
        if not cleaned:
            return field_value
            
        return cleaned
    
    def add_download_item(self, download):
        """
        Adiciona um item de download ao histórico com informações organizadas
        """
        # Cria o item principal com o nome do arquivo
        download_item = QTreeWidgetItem(self.downloads_window)
        download_item.setText(0, download["arquivo_nome"])
        download_item.setExpanded(False)
        
        # Define ícones ou estilos baseados no status (se disponível)
        if "concluído" in download.get("tempo_restante", "").lower():
            download_item.setIcon(0, self.style().standardIcon(self.style().SP_DialogApplyButton))
        elif "erro" in download.get("tempo_restante", "").lower():
            download_item.setIcon(0, self.style().standardIcon(self.style().SP_DialogCancelButton))
        
        # Adiciona informações de forma organizada
        info_items = [
            ("📊", download["tamanho"], "Informações sobre o tamanho do arquivo"),
            ("⏱️", download["tempo_restante"], "Status do download ou tempo restante"),
            ("🚀", download["velocidade"], "Velocidade de download registrada"),
            ("📅", download["data_hora"], "Data e hora do download"),
            ("💾", download["salvo_em"], "Local onde o arquivo foi salvo"),
            ("🔗", download["url"], "URL original do download")
        ]
        
        for emoji, info_text, tooltip in info_items:
            if info_text:  # Só adiciona se houver informação
                info_item = QTreeWidgetItem(download_item)
                
                # Formata o texto de forma mais clara
                display_text = self._format_download_info(info_text)
                
                info_label = QLabel(f"{emoji} {display_text}")
                info_label.setToolTip(tooltip)
                info_label.setWordWrap(True)
                
                # Aplica estilo baseado no tipo de informação
                if "erro" in info_text.lower():
                    info_label.setStyleSheet("QLabel { color: #d32f2f; font-weight: bold; }")
                elif "concluído" in info_text.lower():
                    info_label.setStyleSheet("QLabel { color: #388e3c; font-weight: bold; }")
                elif info_text.startswith("URL:"):
                    info_label.setStyleSheet("QLabel { color: #1976d2; }")
                elif info_text.startswith("Salvo em:"):
                    info_label.setStyleSheet("QLabel { color: #7b1fa2; }")
                
                self.downloads_window.setItemWidget(info_item, 0, info_label)
    
    def _format_download_info(self, info_text):
        """
        Formata as informações de download para exibição mais clara
        """
        if not info_text:
            return ""
        
        # Remove prefixos redundantes e formata
        formatted_text = info_text.strip()
        
        # Formatação específica para diferentes tipos de informação
        if formatted_text.startswith("Tamanho:"):
            # Melhora a formatação de tamanho
            size_part = formatted_text.replace("Tamanho:", "").strip()
            if "/" in size_part:
                current, total = size_part.split("/", 1)
                formatted_text = f"Tamanho: {current.strip()} de {total.strip()}"
            else:
                formatted_text = f"Tamanho: {size_part}"
                
        elif formatted_text.startswith("Tempo restante:"):
            # Melhora a formatação de tempo
            time_part = formatted_text.replace("Tempo restante:", "").strip()
            if time_part.lower() in ["calculando...", "não disponível"]:
                formatted_text = f"Status: {time_part}"
            else:
                formatted_text = f"Tempo restante: {time_part}"
                
        elif formatted_text.startswith("Velocidade:"):
            # Melhora a formatação de velocidade
            speed_part = formatted_text.replace("Velocidade:", "").strip()
            if "mb/s" in speed_part.lower() or "kb/s" in speed_part.lower():
                formatted_text = f"Velocidade: {speed_part}"
            else:
                formatted_text = f"Velocidade: {speed_part}"
                
        elif formatted_text.startswith("Data e Hora:"):
            # Melhora a formatação de data
            date_part = formatted_text.replace("Data e Hora:", "").strip()
            formatted_text = f"Baixado em: {date_part}"
            
        elif formatted_text.startswith("Salvo em:"):
            # Melhora a formatação do caminho
            path_part = formatted_text.replace("Salvo em:", "").strip()
            # Mostra apenas o nome da pasta se o caminho for muito longo
            if len(path_part) > 50:
                try:
                    folder_name = os.path.basename(os.path.dirname(path_part))
                    file_name = os.path.basename(path_part)
                    formatted_text = f"Pasta: .../{folder_name}/{file_name}"
                except:
                    formatted_text = f"Local: {path_part[:47]}..."
            else:
                formatted_text = f"Local: {path_part}"
                
        elif formatted_text.startswith("URL:"):
            # Melhora a formatação da URL
            url_part = formatted_text.replace("URL:", "").strip()
            if len(url_part) > 60:
                formatted_text = f"URL: {url_part[:57]}..."
            else:
                formatted_text = f"URL: {url_part}"
        
        return formatted_text
    
    def close_dialog(self):
        self.download_dialog.close()
        
    def clear_downloads_history(self):
        """
        Limpa o histórico de downloads com confirmação
        """
        downloads_count = self.downloads_window.topLevelItemCount()
        
        if downloads_count == 0:
            print("Histórico já está vazio")
            return
        
        # Aqui você pode adicionar um diálogo de confirmação se desejar
        # Por enquanto, limpa diretamente
        self.downloads_window.clear()
        self.saved_urls.clear()
        
        print(f"Histórico limpo: {downloads_count} downloads removidos")
        
        # Salva as configurações para persistir a limpeza
        self.save_settings()
        
    def validate_url(self, url):
        """
        Valida se a URL é acessível antes de iniciar o download
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            # Primeiro tenta HEAD
            try:
                response = requests.head(url, headers=headers, allow_redirects=True, timeout=15)
                print(f"HEAD response: {response.status_code}")
                
                if response.status_code == 200:
                    # Verifica se é realmente um arquivo
                    content_type = response.headers.get('content-type', '').lower()
                    content_length = response.headers.get('content-length', '0')
                    
                    # Se tem content-disposition, provavelmente é um download
                    if 'content-disposition' in response.headers:
                        print("URL válida: Content-Disposition encontrado")
                        return True
                    
                    # Se não é HTML, provavelmente é um arquivo
                    if 'text/html' not in content_type:
                        print("URL válida: Não é HTML")
                        return True
                    
                    # Se tem tamanho significativo, pode ser um arquivo
                    if int(content_length) > 1024:  # Maior que 1KB
                        print("URL válida: Arquivo com tamanho significativo")
                        return True
                        
                elif response.status_code == 405:  # Method Not Allowed
                    # Tenta GET com range limitado
                    headers['Range'] = 'bytes=0-1023'  # Apenas os primeiros 1KB
                    get_response = requests.get(url, headers=headers, timeout=15)
                    print(f"GET range response: {get_response.status_code}")
                    return get_response.status_code in [200, 206]  # 206 = Partial Content
                    
            except requests.exceptions.RequestException as e:
                print(f"HEAD falhou: {e}")
                
            # Se HEAD falhar completamente, tenta GET com range limitado
            try:
                headers['Range'] = 'bytes=0-1023'  # Apenas os primeiros 1KB
                response = requests.get(url, headers=headers, timeout=15)
                print(f"GET range fallback response: {response.status_code}")
                
                if response.status_code in [200, 206]:  # 206 = Partial Content
                    print("URL válida via GET range")
                    return True
                    
            except requests.exceptions.RequestException as e:
                print(f"GET range também falhou: {e}")
            
            # Último recurso: GET simples mas com timeout curto
            try:
                simple_response = requests.get(url, headers=headers, stream=True, timeout=10)
                print(f"GET simples response: {simple_response.status_code}")
                
                if simple_response.status_code == 200:
                    # Para o download imediatamente
                    simple_response.close()
                    print("URL válida via GET simples")
                    return True
                    
            except requests.exceptions.RequestException as e:
                print(f"GET simples falhou: {e}")
            
            print("URL não pôde ser validada - assumindo inválida")
            return False
            
        except Exception as e:
            return False

    def get_filename_from_url(self, url):
        """
        Extrai o nome do arquivo da URL de forma mais robusta
        """
        try:
            # Primeiro, verifica se há filename na própria URL (parâmetros GET)
            from urllib.parse import urlparse, parse_qs, unquote
            parsed_url = urlparse(url)
            
            # Verifica parâmetro response-content-disposition na URL
            if 'response-content-disposition' in url:
                import re
                # Extrai filename do parâmetro response-content-disposition
                match = re.search(r'response-content-disposition=attachment[^&]*filename%3D%22([^%"&]+)', url)
                if not match:
                    match = re.search(r'response-content-disposition=attachment[^&]*filename%3D([^%"&]+)', url)
                if not match:
                    match = re.search(r'filename%3D%22([^%"&]+)', url)
                if not match:
                    match = re.search(r'filename%3D([^%"&]+)', url)
                
                if match:
                    filename = unquote(match.group(1))
                    return filename
            
            # Verifica outros parâmetros comuns na URL
            query_params = parse_qs(parsed_url.query)
            for param_name in ['filename', 'file', 'name', 'download']:
                if param_name in query_params:
                    filename = query_params[param_name][0]
                    if filename and '.' in filename:
                        return unquote(filename)
            
            # Tenta fazer uma requisição HEAD para obter o nome do arquivo do header
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.head(url, headers=headers, allow_redirects=True, timeout=15)
            
            # Verifica se há Content-Disposition header com filename
            if 'content-disposition' in response.headers:
                content_disposition = response.headers['content-disposition']
                
                # Diferentes padrões para extrair filename
                import re
                patterns = [
                    r'filename\*=UTF-8\'\'([^;]+)',
                    r'filename\*=([^;]+)',
                    r'filename="([^"]+)"',
                    r'filename=([^;]+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content_disposition, re.IGNORECASE)
                    if match:
                        filename = unquote(match.group(1).strip())
                        if filename:
                            return filename
            
            # Se não houver Content-Disposition, usa a URL final (após redirecionamentos)
            final_url = response.url if hasattr(response, 'url') else url
            parsed_final_url = urlparse(final_url)
            
            # Extrai o nome do arquivo do path
            filename = os.path.basename(parsed_final_url.path)
            if filename and '.' in filename:
                return unquote(filename)
            
            # Se não há extensão, tenta deduzir do Content-Type
            if not filename or '.' not in filename:
                content_type = response.headers.get('content-type', '').lower()
                
                # Mapeia tipos de conteúdo para extensões
                content_type_map = {
                    'application/zip': '.zip',
                    'application/x-zip-compressed': '.zip',
                    'application/pdf': '.pdf',
                    'application/octet-stream': '.bin',
                    'application/x-msdownload': '.exe',
                    'image/jpeg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'text/plain': '.txt',
                    'video/mp4': '.mp4',
                    'audio/mpeg': '.mp3',
                    'application/vnd.ms-excel': '.xls',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                    'application/msword': '.doc',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
                }
                
                base_name = filename if filename else 'download'
                extension = content_type_map.get(content_type.split(';')[0], '.bin')
                filename = base_name + extension
                return filename
            
            # Se ainda não tem nome válido, usa um padrão com timestamp
            if not filename:
                timestamp = int(time.time())
                filename = f"download_{timestamp}.bin"
                
            return filename
            
        except Exception as e:
            # Fallback mais robusto
            try:
                from urllib.parse import urlparse, unquote
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if filename and '.' in filename:
                    return unquote(filename)
            except:
                pass
            
            # Último recurso
            timestamp = int(time.time())
            filename = f"download_{timestamp}.bin"
            return filename

    def init_download(self):
        url = self.download_ui.URL.text().strip()
        
        # Valida a URL antes de prosseguir
        if not url:
            print("URL vazia!")
            return
            
        if not url.startswith(('http://', 'https://')):
            print("URL inválida - deve começar com http:// ou https://")
            return
        
        # Desabilita o botão baixar durante o processo
        self.download_ui.baixar.setEnabled(False)
        
        try:
            # Se a URL ainda não foi totalmente resolvida, tenta resolver novamente
            if hasattr(self, 'url_resolver') and self.url_resolver.isRunning():
                # Espera a resolução terminar (máximo 5 segundos)
                if self.url_resolver.wait(5000):
                    url = self.download_ui.URL.text().strip()
            
            # Usa a nova função para obter nome do arquivo
            arquivo_nome = self.get_filename_from_url(url)
            
            caminho_final = os.path.join(self.download_ui.caminho.text(), arquivo_nome)
            
            # Verifica se a URL é acessível
            if not self.validate_url(url):
                print("URL não acessível ou inválida")
                tempo_item_label = QLabel("Erro: URL não acessível")
                self.download_ui.baixar.setEnabled(True)
                return
            
            download_item = QTreeWidgetItem(self.downloads_window)
            download_item.setText(0, str(arquivo_nome))
            download_item.setExpanded(True)
            
            progress_bar = QTreeWidgetItem(download_item)
            progress_bar_widget = QProgressBar()
            progress_bar_widget.setValue(0)
            progress_bar_widget.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #2b2b2b;
                    border-radius: 0px;
                    text-align: center;
                    font-weight: bold;
                    background-color: #f0f0f0;
                    height: 10px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 0px;
                }
            """)
            
            self.downloads_window.setItemWidget(progress_bar, 0, progress_bar_widget)
            
            tamanho_item = QTreeWidgetItem(download_item)
            tamanho_item_label = QLabel(f"📊Tamanho: 0 bytes")
            self.downloads_window.setItemWidget(tamanho_item, 0, tamanho_item_label)
            
            tempo_item = QTreeWidgetItem(download_item)
            tempo_item_label = QLabel(f"⏱️Tempo restante: calculando...")
            self.downloads_window.setItemWidget(tempo_item, 0, tempo_item_label)

            velocidade_item = QTreeWidgetItem(download_item)
            velocidade_item_label = QLabel(f"🚀Velocidade: 0.00 MB/s")
            self.downloads_window.setItemWidget(velocidade_item, 0, velocidade_item_label)
            
            data_item = QTreeWidgetItem(download_item)
            data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            data_item_label = QLabel(f"📅Data e Hora: {data_hora}")
            self.downloads_window.setItemWidget(data_item, 0, data_item_label)

            salvo_item = QTreeWidgetItem(download_item)
            salvo_item_label = QLabel(f"💾Salvo em: {caminho_final}")
            self.downloads_window.setItemWidget(salvo_item, 0, salvo_item_label)
            
            url_item = QTreeWidgetItem(download_item)
            url_item_label = QLabel(f"🔗URL: {url}")
            self.downloads_window.setItemWidget(url_item, 0, url_item_label)
            
            botao_cancelar_item = QTreeWidgetItem(download_item)
            botao_cancelar = QPushButton("Cancelar")
            botao_cancelar.clicked.connect(self.cancelar_download)
            self.downloads_window.setItemWidget(botao_cancelar_item, 0, botao_cancelar)
            
            self.download_thread = DownloadThread(url, caminho_final)
            self.download_thread.progress_changed.connect(progress_bar_widget.setValue)
            self.download_thread.size_changed.connect(lambda current, total: tamanho_item_label.setText(f"📊Tamanho: {convert_bytes(current)} / {convert_bytes(total)}"))
            self.download_thread.time_remaining_changed.connect(lambda text: tempo_item_label.setText(f"⏱️Tempo restante: {text}"))
            self.download_thread.speed_changed.connect(lambda text: velocidade_item_label.setText(f"🚀Velocidade: {text}"))
            self.download_thread.download_finished.connect(lambda success: self.download_ui.baixar.setEnabled(True))
            self.download_thread.cancelled.connect(lambda: self.on_download_cancelled())
            
            self.download_thread.start()
            self.download_dialog.close()
            
        except Exception as e:
            print(f"Erro ao iniciar download: {e}")
            self.download_ui.baixar.setEnabled(True)
    
    def on_download_cancelled(self):
        """
        Callback chamado quando o download é cancelado
        """
        print("Download cancelado - atualizando interface")
        self.download_ui.baixar.setEnabled(True)
    
    def cancelar_download(self):
        """
        Cancela o download atual, se houver
        """
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            
            # Chama o método cancel da thread para cancelar adequadamente
            self.download_thread.cancel()
            
            # Aguarda a thread terminar naturalmente
            if self.download_thread.wait(3000):  # Aguarda até 3 segundos
                print("Download cancelado")
            else:
                # Se não terminar em 3 segundos, força o término
                self.download_thread.terminate()
                self.download_thread.wait()
            
            # Atualiza o status para indicar que foi cancelado
            if hasattr(self, 'downloads_window') and self.downloads_window.topLevelItemCount() > 0:
                # Pega o último item de download (o atual)
                current_item = self.downloads_window.topLevelItem(self.downloads_window.topLevelItemCount() - 1)
                
                # Procura e atualiza o label de tempo restante
                for i in range(current_item.childCount()):
                    child = current_item.child(i)
                    widget = self.downloads_window.itemWidget(child, 0)
                    if isinstance(widget, QLabel) and "Tempo restante:" in widget.text():
                        widget.setText("⏱️Tempo restante: Download cancelado")
                        widget.setStyleSheet("QLabel { color: #d32f2f; font-weight: bold; }")
                    
                    if isinstance(widget, QProgressBar):
                        current_item.removeChild(child)
                    
                    if isinstance(widget, QPushButton) and widget.text() == "Cancelar":
                        current_item.removeChild(child)
                            
            print("Download cancelado pelo usuário")
            self.download_ui.baixar.setEnabled(True)
        else:
            print("Nenhum download em andamento para cancelar")
    
    def show_download_widget(self):
        """Exibe o widget de download quando chamado manualmente (botão Novo Download)"""
        
        self.download_dialog.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Configura as conexões apenas uma vez
        self.setup_download_dialog_connections()
        
        # Define um caminho padrão se não existir
        if not self.download_ui.caminho.text():
            default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_ui.caminho.setText(default_path)
        
        self.check_fields()
        self.download_dialog.show()
        self.download_dialog.raise_()
        self.download_dialog.activateWindow()
    
    def check_fields(self):
        url = self.download_ui.URL.text()
        caminho = self.download_ui.caminho.text()
        if url and caminho:
            self.download_ui.baixar.setEnabled(True)
        else:
            self.download_ui.baixar.setEnabled(False)
    
    def set_local_save(self):
        # Evita múltiplas execuções simultâneas
        if hasattr(self, '_selecting_folder') and self._selecting_folder:
            return
        
        self._selecting_folder = True
        try:
            caminho = easygui.diropenbox()
            if caminho:
                self.download_ui.caminho.setText(caminho)
        finally:
            self._selecting_folder = False
    
    def test_url_resolution(self, url):
        """
        Função de teste para resolver URLs manualmente
        """
        resolver = UrlResolverThread(url)
        resolver.url_resolved.connect(lambda orig, final: print(f"Teste - URL resolvida: {orig} -> {final}"))
        resolver.resolution_failed.connect(lambda orig, error: print(f"Teste - Falha: {orig} - {error}"))
        resolver.start()
        return resolver
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()