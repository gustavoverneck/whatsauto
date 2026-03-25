from interface import AppWhatsApp
from apscheduler.schedulers.background import BackgroundScheduler
import banco_dados
from whatsapp_bot import WhatsAppBot
from datetime import datetime

def verificar_agendamentos():
    # Esta função roda invisível a cada 1 minuto
    pendentes = banco_dados.buscar_pendentes()
    
    if pendentes:
        print(f"[{datetime.now().strftime('%H:%M')}] Encontrei {len(pendentes)} mensagem(ns) agendada(s) para agora!")
        
        # Inicia o bot uma única vez para enviar todas as pendentes deste minuto
        try:
            bot = WhatsAppBot()
            bot.iniciar_sessao()
            
            for msg in pendentes:
                id_msg = msg
                numero = msg
                texto = msg
                recorrencia = msg
                
                print(f"Enviando agendamento para {numero}...")
                bot.enviar_mensagem(numero, texto)
                
                # Marca como concluído ou joga para amanhã (se for diário)
                data_hora_agora = datetime.now().strftime("%Y-%m-%d %H:%M")
                banco_dados.atualizar_status_ou_reagendar(id_msg, recorrencia, data_hora_agora)
                
            bot.fechar()
            print("Todos os agendamentos do minuto foram enviados.")
            
        except Exception as e:
            print(f"Erro ao processar fila de agendamentos: {e}")

if __name__ == "__main__":
    # 1. Prepara o Banco de Dados
    banco_dados.criar_tabela()

    # 2. Prepara o Agendador (Relógio)
    scheduler = BackgroundScheduler()
    # Manda ele rodar a função verificar_agendamentos a cada 1 minuto
    scheduler.add_job(verificar_agendamentos, 'interval', minutes=1)
    scheduler.start()

    # 3. Inicia a Interface Gráfica
    app = AppWhatsApp()
    app.mainloop()