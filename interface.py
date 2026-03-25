import customtkinter as ctk
import threading
import os
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from whatsapp_bot import WhatsAppBot
import banco_dados

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

# --- JANELA FLUTUANTE DE EDIÇÃO ---
class JanelaEdicao(ctk.CTkToplevel):
    def __init__(self, master, agendamento, callback_atualizar):
        super().__init__(master)
        self.title("Editar Agendamento")
        self.geometry("450x520")
        self.resizable(False, False)
        
        # Pausa para o Linux desenhar a tela antes de focar
        self.wait_visibility() 
        self.grab_set() 
        
        self.callback_atualizar = callback_atualizar
        
        self.id_msg = agendamento[0]            # id
        numero_atual = agendamento[1]           # numero
        mensagem_atual = agendamento[2]         # mensagem
        data_hora_atual = agendamento[3]        # data_hora (ex: "2026-03-25 12:30")
        recorrencia_atual = agendamento[4]      # recorrencia (ex: "Apenas uma vez" ou "Semanalmente-0,2,4")
        # status = agendamento[5] (não usado)
        
        # Separa data e hora da string data_hora
        partes_data = data_hora_atual.split()
        data_atual = partes_data[0] if len(partes_data) > 0 else datetime.now().strftime("%Y-%m-%d")
        hora_completa = partes_data[1] if len(partes_data) > 1 else "12:00"
        
        if ":" in hora_completa:
            hora_salva, minuto_salvo = hora_completa.split(":")
        else:
            hora_salva, minuto_salvo = "12", "00"
        
        # Extrai a recorrência base (sem os dias) para exibição no combo
        if recorrencia_atual.startswith("Semanalmente"):
            recorrencia_base = "Semanalmente"
            # Extrai os dias da semana armazenados
            dias_salvos = recorrencia_atual.split("-")[1].split(",") if "-" in recorrencia_atual else []
        else:
            recorrencia_base = recorrencia_atual
            dias_salvos = []
        recorrencia_base = "Semanalmente" if recorrencia_atual.startswith("Semanalmente") else recorrencia_atual

        # --- BOTÃO SALVAR (PREGADO NO FUNDO) ---
        self.btn_salvar = ctk.CTkButton(self, text="Salvar Alterações", fg_color="green", hover_color="darkgreen", command=self.salvar_edicao)
        self.btn_salvar.pack(side="bottom", pady=20)

        # --- CAMPOS DA EDIÇÃO (TOPO) ---
        ctk.CTkLabel(self, text="Número:").pack(anchor="w", padx=20, pady=(10,0))
        self.input_numero = ctk.CTkEntry(self, width=410)
        self.input_numero.pack(padx=20)
        self.input_numero.insert(0, numero_atual)

        ctk.CTkLabel(self, text="Mensagem:").pack(anchor="w", padx=20, pady=(10,0))
        self.input_mensagem = ctk.CTkTextbox(self, width=410, height=80)
        self.input_mensagem.pack(padx=20)
        self.input_mensagem.insert("0.0", mensagem_atual)

        frame_dh = ctk.CTkFrame(self, fg_color="transparent")
        frame_dh.pack(pady=15, fill="x", padx=20)

        self.lbl_data = ctk.CTkLabel(frame_dh, text="Data:")
        self.lbl_data.grid(row=0, column=0, sticky="w", padx=(0,20))
        
        self.input_data = DateEntry(frame_dh, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.input_data.grid(row=1, column=0, sticky="w", padx=(0,20))
        
        # O Failsafe: Se vier algum lixo pro calendário, ele não quebra o app
        try:
            self.input_data.set_date(data_atual)
        except Exception as e:
            print(f"Data recebida do banco estava inválida, carregando data de hoje. Erro ignorado: {e}")

        ctk.CTkLabel(frame_dh, text="Hora:").grid(row=0, column=1, sticky="w")
        self.combo_hora = ctk.CTkComboBox(frame_dh, values=[f"{i:02d}" for i in range(24)], width=70)
        self.combo_hora.grid(row=1, column=1)
        self.combo_hora.set(hora_salva)

        ctk.CTkLabel(frame_dh, text=":").grid(row=1, column=2, padx=5)

        self.combo_minuto = ctk.CTkComboBox(frame_dh, values=[f"{i:02d}" for i in range(60)], width=70)
        self.combo_minuto.grid(row=1, column=3)
        self.combo_minuto.set(minuto_salvo)

        ctk.CTkLabel(self, text="Recorrência:").pack(anchor="w", padx=20, pady=(5,0))
        self.combo_recorrencia = ctk.CTkComboBox(self, values=["Apenas uma vez", "Diariamente", "Semanalmente", "Mensalmente", "Anualmente"], width=410, command=self.mostrar_ocultar_elementos)
        self.combo_recorrencia.pack(padx=20)
        self.combo_recorrencia.set(recorrencia_base)

        # Frame de Dias da Semana (Edição)
        self.frame_dias = ctk.CTkFrame(self, fg_color="transparent")
        self.variaveis_dias = []
        for i, nome in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
            # Marca o checkbox se o dia estiver na lista de salvos
            val = str(i) if str(i) in dias_salvos else ""
            var = ctk.StringVar(value=val)
            chk = ctk.CTkCheckBox(self.frame_dias, text=nome, variable=var, onvalue=str(i), offvalue="", width=40)
            chk.grid(row=0, column=i, padx=2)
            self.variaveis_dias.append(var)

        self.mostrar_ocultar_elementos(recorrencia_base)

    def mostrar_ocultar_elementos(self, escolha):
        if escolha in ["Semanalmente", "Diariamente"]:
            self.lbl_data.grid_remove()
            self.input_data.grid_remove()
        else:
            self.lbl_data.grid()
            self.input_data.grid()
            
        if escolha == "Semanalmente":
            self.frame_dias.pack(pady=10)
        else:
            self.frame_dias.pack_forget()

    def salvar_edicao(self):
        numero = self.input_numero.get().strip()
        mensagem = self.input_mensagem.get("0.0", "end").strip()
        hora_formatada = f"{self.combo_hora.get()}:{self.combo_minuto.get()}"
        recorrencia = self.combo_recorrencia.get()

        if recorrencia == "Semanalmente":
            dias_selecionados = [var.get() for var in self.variaveis_dias if var.get() != ""]
            if not dias_selecionados: return
            recorrencia = f"Semanalmente-{','.join(dias_selecionados)}"

        if recorrencia.startswith("Semanalmente") or recorrencia == "Diariamente":
            hoje = datetime.now()
            hora_obj = datetime.strptime(hora_formatada, "%H:%M").time()
            prox_data = datetime.combine(hoje.date(), hora_obj)

            if recorrencia == "Diariamente" and hoje >= prox_data:
                prox_data += timedelta(days=1)
            elif recorrencia.startswith("Semanalmente"):
                dias_int = [int(d) for d in recorrencia.split("-").split(",")]
                if hoje >= prox_data: prox_data += timedelta(days=1)
                while prox_data.weekday() not in dias_int:
                    prox_data += timedelta(days=1)
            data_final = prox_data.strftime("%Y-%m-%d")
        else:
            data_final = self.input_data.get().strip()

        if numero and mensagem and data_final:
            data_hora_final = f"{data_final} {hora_formatada}"
            banco_dados.atualizar_agendamento(self.id_msg, numero, mensagem, data_hora_final, recorrencia)
            self.callback_atualizar() 
            self.destroy()


# --- JANELA PRINCIPAL ---
class AppWhatsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WhatsAuto - Disparador Automático")
        self.geometry("550x580")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.fechar_aplicativo)
        
        self.abas = ctk.CTkTabview(self, width=510, height=540)
        self.abas.pack(pady=10, padx=10)
        
        self.aba_agora = self.abas.add("Enviar Agora")
        self.aba_agendar = self.abas.add("Agendar")
        self.aba_gerenciar = self.abas.add("Gerenciar")

        self.montar_aba_agora()
        self.montar_aba_agendar()
        self.montar_aba_gerenciar()

    def montar_aba_agora(self):
        self.btn_enviar = ctk.CTkButton(self.aba_agora, text="Enviar Imediatamente", font=("Segoe UI", 14, "bold"), command=self.iniciar_envio_imediato)
        self.btn_enviar.pack(side="bottom", pady=(5, 20))
        self.lbl_status_agora = ctk.CTkLabel(self.aba_agora, text="Pronto.", text_color="gray")
        self.lbl_status_agora.pack(side="bottom")

        self.var_revisar = ctk.BooleanVar(value=False)
        self.chk_revisar = ctk.CTkCheckBox(self.aba_agora, text="Revisar mensagem antes de enviar", variable=self.var_revisar)
        self.chk_revisar.pack(side="bottom", pady=(10, 5))

        ctk.CTkLabel(self.aba_agora, text="Número (Ex: 552799999999):").pack(anchor="w", padx=30, pady=(10,0))
        self.input_numero_agora = ctk.CTkEntry(self.aba_agora, width=400)
        self.input_numero_agora.pack(pady=(0, 15))

        ctk.CTkLabel(self.aba_agora, text="Mensagem:").pack(anchor="w", padx=30)
        self.input_mensagem_agora = ctk.CTkTextbox(self.aba_agora, width=400, height=120)
        self.input_mensagem_agora.pack(pady=(0, 15))

    def montar_aba_agendar(self):
        self.btn_salvar_agenda = ctk.CTkButton(self.aba_agendar, text="Salvar Agendamento", font=("Segoe UI", 14, "bold"), fg_color="green", hover_color="darkgreen", command=self.salvar_no_banco)
        self.btn_salvar_agenda.pack(side="bottom", pady=(5, 20))
        self.lbl_status_agenda = ctk.CTkLabel(self.aba_agendar, text="", text_color="gray")
        self.lbl_status_agenda.pack(side="bottom")

        ctk.CTkLabel(self.aba_agendar, text="Número:").pack(anchor="w", padx=30, pady=(5,0))
        self.input_numero_agenda = ctk.CTkEntry(self.aba_agendar, width=400)
        self.input_numero_agenda.pack()

        ctk.CTkLabel(self.aba_agendar, text="Mensagem:").pack(anchor="w", padx=30, pady=(10,0))
        self.input_mensagem_agenda = ctk.CTkTextbox(self.aba_agendar, width=400, height=80)
        self.input_mensagem_agenda.pack()

        frame_dh = ctk.CTkFrame(self.aba_agendar, fg_color="transparent")
        frame_dh.pack(pady=15, fill="x", padx=30)

        self.lbl_data_agenda = ctk.CTkLabel(frame_dh, text="Data:")
        self.lbl_data_agenda.grid(row=0, column=0, sticky="w", padx=(0,20))
        self.input_data_agenda = DateEntry(frame_dh, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.input_data_agenda.grid(row=1, column=0, sticky="w", padx=(0,20))

        ctk.CTkLabel(frame_dh, text="Hora:").grid(row=0, column=1, sticky="w")
        self.combo_hora = ctk.CTkComboBox(frame_dh, values=[f"{i:02d}" for i in range(24)], width=70)
        self.combo_hora.grid(row=1, column=1)
        self.combo_hora.set("12")

        ctk.CTkLabel(frame_dh, text=":").grid(row=1, column=2, padx=5)

        self.combo_minuto = ctk.CTkComboBox(frame_dh, values=[f"{i:02d}" for i in range(60)], width=70)
        self.combo_minuto.grid(row=1, column=3)
        self.combo_minuto.set("30")

        ctk.CTkLabel(self.aba_agendar, text="Recorrência:").pack(anchor="w", padx=30, pady=(5,0))
        self.combo_recorrencia_agenda = ctk.CTkComboBox(self.aba_agendar, values=["Apenas uma vez", "Diariamente", "Semanalmente", "Mensalmente", "Anualmente"], width=400, command=self.mostrar_ocultar_dias_agenda)
        self.combo_recorrencia_agenda.pack()

        self.frame_dias_agenda = ctk.CTkFrame(self.aba_agendar, fg_color="transparent")
        self.variaveis_dias_agenda = []
        for i, nome in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
            var = ctk.StringVar(value="")
            chk = ctk.CTkCheckBox(self.frame_dias_agenda, text=nome, variable=var, onvalue=str(i), offvalue="", width=45)
            chk.grid(row=0, column=i, padx=3)
            self.variaveis_dias_agenda.append(var)

    def mostrar_ocultar_dias_agenda(self, escolha):
        if escolha in ["Semanalmente", "Diariamente"]:
            self.lbl_data_agenda.grid_remove()
            self.input_data_agenda.grid_remove()
        else:
            self.lbl_data_agenda.grid()
            self.input_data_agenda.grid()

        if escolha == "Semanalmente":
            self.frame_dias_agenda.pack(pady=10)
        else:
            self.frame_dias_agenda.pack_forget()

    def salvar_no_banco(self):
        numero = self.input_numero_agenda.get().strip()
        mensagem = self.input_mensagem_agenda.get("0.0", "end").strip()
        hora_formatada = f"{self.combo_hora.get()}:{self.combo_minuto.get()}"
        recorrencia = self.combo_recorrencia_agenda.get()

        if recorrencia == "Semanalmente":
            dias_selecionados = [var.get() for var in self.variaveis_dias_agenda if var.get() != ""]
            if not dias_selecionados:
                self.lbl_status_agenda.configure(text="Selecione pelo menos um dia!", text_color="red")
                return
            recorrencia = f"Semanalmente-{','.join(dias_selecionados)}"

        if recorrencia.startswith("Semanalmente") or recorrencia == "Diariamente":
            hoje = datetime.now()
            hora_obj = datetime.strptime(hora_formatada, "%H:%M").time()
            prox_data = datetime.combine(hoje.date(), hora_obj)

            if recorrencia == "Diariamente" and hoje >= prox_data:
                prox_data += timedelta(days=1)
            elif recorrencia.startswith("Semanalmente"):
                dias_int = [int(d) for d in dias_selecionados]
                if hoje >= prox_data: prox_data += timedelta(days=1)
                while prox_data.weekday() not in dias_int:
                    prox_data += timedelta(days=1)
            data_final = prox_data.strftime("%Y-%m-%d")
        else:
            data_final = self.input_data_agenda.get().strip()

        if not numero or not mensagem or not data_final:
            self.lbl_status_agenda.configure(text="Preencha todos os campos!", text_color="red")
            return
        
        data_hora_final = f"{data_final} {hora_formatada}"
        banco_dados.salvar_agendamento(numero, mensagem, data_hora_final, recorrencia)
        self.lbl_status_agenda.configure(text=f"Agendado para {data_hora_final}!", text_color="green")
        
        self.input_mensagem_agenda.delete("0.0", "end")
        self.input_numero_agenda.delete(0, "end")
        for var in self.variaveis_dias_agenda: var.set("")
        self.carregar_lista_agendamentos()

    def montar_aba_gerenciar(self):
        btn_atualizar = ctk.CTkButton(self.aba_gerenciar, text="↻ Atualizar Lista", width=120, command=self.carregar_lista_agendamentos)
        btn_atualizar.pack(pady=(5, 10), anchor="e", padx=20)

        self.frame_lista = ctk.CTkScrollableFrame(self.aba_gerenciar, width=420, height=350)
        self.frame_lista.pack(padx=10, pady=5)
        self.carregar_lista_agendamentos()

    def carregar_lista_agendamentos(self):
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        agendamentos = banco_dados.buscar_todos_agendamentos()
        
        if not agendamentos:
            ctk.CTkLabel(self.frame_lista, text="Nenhum agendamento encontrado.", text_color="gray").pack(pady=20)
            return

        for ag in agendamentos:
            id_msg, numero, mensagem, data_hora, recorrencia, status = ag
            msg_curta = mensagem[:15] + "..." if len(mensagem) > 15 else mensagem
            cor_status = "green" if status == "Concluído" else ("orange" if status == "Pendente" else "gray")

            linha = ctk.CTkFrame(self.frame_lista, fg_color=("gray85", "gray20"))
            linha.pack(fill="x", pady=5, padx=5)
            
            btn_excluir = ctk.CTkButton(linha, text="X", width=30, fg_color="red", hover_color="darkred", command=lambda i=id_msg: self.excluir_agendamento(i))
            btn_excluir.pack(side="right", padx=(0, 10), pady=5)
            
            btn_editar = ctk.CTkButton(linha, text="✎", width=30, command=lambda a=ag: self.abrir_edicao(a))
            btn_editar.pack(side="right", padx=5, pady=5)
            
            lbl_status = ctk.CTkLabel(linha, text=status, text_color=cor_status, width=65)
            lbl_status.pack(side="right", padx=10)

            texto_resumo = f"{data_hora} | {numero} | {msg_curta}"
            lbl = ctk.CTkLabel(linha, text=texto_resumo, anchor="w", font=("Segoe UI", 12))
            lbl.pack(side="left", padx=10, fill="x", expand=True)

    def abrir_edicao(self, agendamento):
        JanelaEdicao(self, agendamento, self.carregar_lista_agendamentos)

    def excluir_agendamento(self, id_msg):
        banco_dados.deletar_agendamento(id_msg)
        self.carregar_lista_agendamentos()

    def iniciar_envio_imediato(self):
        numero = self.input_numero_agora.get().strip()
        mensagem = self.input_mensagem_agora.get("0.0", "end").strip()
        revisar = self.var_revisar.get()
        if not numero or not mensagem:
            self.lbl_status_agora.configure(text="Erro: Preencha número e mensagem!", text_color="red")
            return
            
        if revisar:
            self.lbl_status_agora.configure(text="Abrindo navegador para revisão...", text_color="orange")
        else:
            self.lbl_status_agora.configure(text="Iniciando envio nos bastidores...", text_color="orange")
            
        self.btn_enviar.configure(state="disabled", text="Enviando...")
        threading.Thread(target=self.processo_bot, args=(numero, mensagem, revisar), daemon=True).start()

    def processo_bot(self, numero, mensagem, revisar):
        try:
            bot = WhatsAppBot() 
            self.atualizar_status("Conectando ao WhatsApp...", "orange")
            bot.iniciar_sessao()
            if revisar:
                self.atualizar_status("Aguardando você clicar em Enviar...", "#0078D7")
            else:
                self.atualizar_status("Enviando mensagem invisível...", "orange")
            bot.enviar_mensagem(numero, mensagem, aguardar_confirmacao=revisar)
            bot.fechar()
            self.atualizar_status("Mensagem enviada com sucesso!", "green")
            self.input_numero_agora.delete(0, "end")
            self.input_mensagem_agora.delete("0.0", "end")
        except Exception as e:
            self.atualizar_status("Erro ao enviar.", "red")
            print(f"Erro detalhado: {e}")
        finally:
            self.btn_enviar.configure(state="normal", text="Enviar Imediatamente")

    def atualizar_status(self, texto, cor):
        self.lbl_status_agora.configure(text=texto, text_color=cor)

    def fechar_aplicativo(self):
        print("Encerrando...")
        self.destroy()
        os._exit(0)