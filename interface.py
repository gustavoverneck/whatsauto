import os

import customtkinter as ctk
import threading
from whatsapp_bot import WhatsAppBot

# Configuração do visual da janela (segue o tema do seu sistema)
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

class AppWhatsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela Principal
        self.title("WhatsAuto - Disparador")
        self.geometry("500x480")
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.fechar_aplicativo)

        # --- LAYOUT DOS ELEMENTOS ---
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(self, text="Nova Mensagem", font=("Segoe UI", 24, "bold"))
        self.lbl_titulo.pack(pady=(30, 20))

        # Campo do Número
        self.lbl_numero = ctk.CTkLabel(self, text="Número (com DDI e DDD):", font=("Segoe UI", 14))
        self.lbl_numero.pack(anchor="w", padx=50)
        
        self.input_numero = ctk.CTkEntry(self, placeholder_text="Ex: 5527999999999", width=400, height=40)
        self.input_numero.pack(pady=(0, 20))

        # Campo da Mensagem
        self.lbl_mensagem = ctk.CTkLabel(self, text="Mensagem:", font=("Segoe UI", 14))
        self.lbl_mensagem.pack(anchor="w", padx=50)

        self.input_mensagem = ctk.CTkTextbox(self, width=400, height=120)
        self.input_mensagem.pack(pady=(0, 20))

        # Botão de Enviar
        self.btn_enviar = ctk.CTkButton(self, text="Enviar Mensagem Agora", height=45, font=("Segoe UI", 16, "bold"), command=self.iniciar_envio)
        self.btn_enviar.pack(pady=(10, 10))
        
        # Label de Status (Fica avisando o que está acontecendo)
        self.lbl_status = ctk.CTkLabel(self, text="Pronto para enviar.", text_color="gray")
        self.lbl_status.pack()

    def iniciar_envio(self):
        # 1. Pega os textos que o usuário digitou
        numero = self.input_numero.get().strip()
        mensagem = self.input_mensagem.get("0.0", "end").strip()
        
        # Validação simples
        if not numero or not mensagem:
            self.lbl_status.configure(text="Erro: Preencha número e mensagem!", text_color="red")
            return

        # 2. Muda o status e bloqueia o botão para evitar cliques duplos
        self.lbl_status.configure(text="Iniciando envio nos bastidores...", text_color="orange")
        self.btn_enviar.configure(state="disabled", text="Enviando...")
        
        # 3. Dispara o bot em uma Thread separada
        # daemon=True garante que a thread morra se você fechar o aplicativo
        threading.Thread(target=self.processo_bot, args=(numero, mensagem), daemon=True).start()

    def processo_bot(self, numero, mensagem):
        try:
            # Instancia e roda o seu bot
            bot = WhatsAppBot()
            
            self.atualizar_status("Conectando ao WhatsApp...", "orange")
            bot.iniciar_sessao()
            
            self.atualizar_status("Enviando mensagem...", "orange")
            bot.enviar_mensagem(numero, mensagem)
            
            bot.fechar()
            self.atualizar_status("Mensagem enviada com sucesso!", "green")
            
            # Limpa os campos após o sucesso
            self.input_numero.delete(0, "end")
            self.input_mensagem.delete("0.0", "end")

        except Exception as e:
            self.atualizar_status("Erro ao enviar. Verifique o terminal.", "red")
            print(f"Erro detalhado na thread: {e}")

        finally:
            # Reativa o botão independentemente de sucesso ou erro
            self.btn_enviar.configure(state="normal", text="Enviar Mensagem Agora")

    def atualizar_status(self, texto, cor):
        # Função auxiliar para mudar o texto da interface
        self.lbl_status.configure(text=texto, text_color=cor)

    def fechar_aplicativo(self):
        print("Encerrando o WhatsAuto de forma segura...")
        self.destroy()  # Fecha a janela gráfica
        os._exit(0)     # Mata o processo do Python e do Playwright instantaneamente (Status 0 = Sucesso)