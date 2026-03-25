import calendar
import sqlite3
from datetime import datetime, timedelta

# Conecta ao arquivo de banco de dados (ou cria um novo se não existir)
def conectar():
    return sqlite3.connect("agendamentos.db")

def criar_tabela():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT,
                mensagem TEXT,
                data_hora TEXT,
                recorrencia TEXT,
                status TEXT DEFAULT 'Pendente'
            )
        """)

def salvar_agendamento(numero, mensagem, data_hora, recorrencia):
    with conectar() as conn:
        conn.execute(
            "INSERT INTO mensagens (numero, mensagem, data_hora, recorrencia) VALUES (?, ?, ?, ?)",
            (numero, mensagem, data_hora, recorrencia)
        )

def buscar_pendentes():
    # Pega a data e hora de agora no formato YYYY-MM-DD HH:MM
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with conectar() as conn:
        cursor = conn.cursor()
        # Busca mensagens marcadas como Pendente cuja data/hora seja igual ou menor que o minuto atual
        cursor.execute("SELECT id, numero, mensagem, recorrencia FROM mensagens WHERE data_hora <= ? AND status = 'Pendente'", (agora,))
        return cursor.fetchall()

def buscar_todos_agendamentos():
    with conectar() as conn:
        cursor = conn.cursor()
        # Busca todos, ordenando pelos mais recentes/próximos primeiro
        cursor.execute("SELECT id, numero, mensagem, data_hora, recorrencia, status FROM mensagens ORDER BY data_hora ASC")
        return cursor.fetchall()

def atualizar_agendamento(id_msg, numero, mensagem, data_hora, recorrencia):
    with conectar() as conn:
        conn.execute(
            "UPDATE mensagens SET numero = ?, mensagem = ?, data_hora = ?, recorrencia = ? WHERE id = ?",
            (numero, mensagem, data_hora, recorrencia, id_msg)
        )

def deletar_agendamento(id_msg):
    with conectar() as conn:
        conn.execute("DELETE FROM mensagens WHERE id = ?", (id_msg,))

def adicionar_meses(data_original, meses):
    """Função inteligente para somar meses considerando anos bissextos e fins de mês"""
    mes = data_original.month - 1 + meses
    ano = data_original.year + mes // 12
    mes = mes % 12 + 1
    # Garante que não vamos agendar para 31 de fevereiro, limitando ao último dia válido do mês
    dia = min(data_original.day, calendar.monthrange(ano, mes))
    return data_original.replace(year=ano, month=mes, day=dia)

def atualizar_status_ou_reagendar(id_msg, recorrencia, data_hora_antiga):
    with conectar() as conn:
        if recorrencia == "Apenas uma vez":
            conn.execute("UPDATE mensagens SET status = 'Concluído' WHERE id = ?", (id_msg,))
        else:
            # Transforma a string do banco em um objeto de data real
            data_antiga_obj = datetime.strptime(data_hora_antiga, "%Y-%m-%d %H:%M")
            
            # Calcula a nova data com base na escolha
            if recorrencia == "Diariamente":
                nova_data = data_antiga_obj + timedelta(days=1)
            
            elif recorrencia.startswith("Semanalmente"):
                # Extrai os números dos dias (ex: "Semanalmente-0,2,4" vira a lista)
                _, dias_str = recorrencia.split("-")
                dias_permitidos = [int(d) for d in dias_str.split(",")]
                
                # Avança 1 dia de cada vez até encontrar um dia que esteja marcado na lista
                nova_data = data_antiga_obj + timedelta(days=1)
                while nova_data.weekday() not in dias_permitidos:
                    nova_data += timedelta(days=1)
                    
            elif recorrencia == "Mensalmente":
                nova_data = adicionar_meses(data_antiga_obj, 1)
            elif recorrencia == "Anualmente":
                nova_data = adicionar_meses(data_antiga_obj, 12)
            
            # Converte de volta para texto e salva no banco, mantendo como Pendente
            nova_data_str = nova_data.strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE mensagens SET data_hora = ? WHERE id = ?", (nova_data_str, id_msg))