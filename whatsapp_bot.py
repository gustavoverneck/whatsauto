from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time

class WhatsAppBot:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir="./sessao_whatsapp",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]  # evita detecção
        )
        # Obtém a página
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()

    def iniciar_sessao(self):
        self.page.goto("https://web.whatsapp.com")
        print("Aguardando o WhatsApp carregar...")
        
        try:
            # Espera pelo painel de conversas (#pane-side) OU pelo QR Code (canvas)
            self.page.wait_for_selector('#pane-side, canvas', timeout=60000)
        except Exception as e:
            print("Erro: O WhatsApp demorou demais para carregar.")
            raise e

        # Verifica se o que apareceu na tela foi o QR Code
        if self.page.locator('canvas').count() > 0:
            print("QR Code detectado. Por favor, escaneie com o seu celular...")
            
            # Como a sincronização de mensagens pode demorar, damos um tempo limite maior (2 minutos)
            print("Aguardando sincronização de mensagens...")
            self.page.wait_for_selector('#pane-side', timeout=120000) 
            print("QR Code lido e mensagens sincronizadas!")
        else:
            print("Sessão já estava ativa e pronta!")
        
        print("Interface principal carregada com sucesso.")

    def enviar_mensagem(self, numero, texto):
        # Monta o link
        link = f"https://web.whatsapp.com/send?phone={numero}&text={texto}"
        print(f"Acessando link: {link}")
        self.page.goto(link)
        
        # Aguarda o botão de enviar aparecer
        try:
            self.page.wait_for_selector('span[data-icon="send"]', timeout=30000)
            print("Botão de enviar encontrado. Clicando...")
            self.page.click('span[data-icon="send"]')
            time.sleep(2)
            print("Mensagem enviada.")
        except PlaywrightTimeoutError:
            print("Erro: Não foi possível encontrar o botão de enviar. Verifique se o número está correto.")
            raise

    def fechar(self):
        self.context.close()
        self.playwright.stop()