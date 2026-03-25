from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time

class WhatsAppBot:
    def __init__(self):
        self.playwright = sync_playwright().start()
        
        # Modo "Robô Humano": Sempre visível (headless=False)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir="./sessao_whatsapp",
            headless=False, # <--- Deixamos visível para enganar o sistema de segurança
            viewport={"width": 800, "height": 600} # Janela um pouco menor para não atrapalhar sua tela
        )
        
        self.page = self.context.pages[0]

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

    # Adicionamos a variável "aguardar_confirmacao"
    def enviar_mensagem(self, numero, texto, aguardar_confirmacao=False):
        link = f"https://web.whatsapp.com/send?phone={numero}"
        print(f"Acessando conversa do número: {numero}")
        self.page.goto(link)
        
        try:
            print("Aguardando o chat carregar...")
            caixa_de_texto = self.page.locator('footer div[contenteditable="true"]')
            caixa_de_texto.wait_for(state="visible", timeout=45000)
            
            caixa_de_texto.click()
            caixa_de_texto.fill("") # Limpa a caixa por precaução
            
            print("Digitando como um humano...")
            # O TRUQUE: Separa o texto pelas quebras de linha
            linhas = texto.split('\n')
            
            for i, linha in enumerate(linhas):
                self.page.keyboard.type(linha, delay=50) # Digita a linha
                
                # Se não for a última linha, aperta Shift+Enter para pular a linha sem enviar!
                if i < len(linhas) - 1:
                    self.page.keyboard.press("Shift+Enter")
            
            if aguardar_confirmacao:
                print("Modo Revisão: Aguardando você enviar a mensagem...")
                # O robô cruza os braços e espera você apertar o Enter de verdade
                while caixa_de_texto.inner_text().strip() != "":
                    self.page.wait_for_timeout(1000) 
                print("Mensagem enviada manualmente pelo usuário!")
                
            else:
                print("Disparando mensagem com a tecla 'Enter'...")
                caixa_de_texto.press("Enter")
                time.sleep(3) 
                print("Mensagem enviada automaticamente.")
                
        except Exception as e:
            print(f"Erro: Falha na interação com o chat. Detalhes: {e}")
            raise

    def fechar(self):
        self.context.close()
        self.playwright.stop()