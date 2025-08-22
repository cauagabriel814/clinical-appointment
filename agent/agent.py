from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os

# 1 - Carregando api-key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2 - Definindo modelo de IA
model = ChatOpenAI(
    model='gpt-4o',
    api_key=OPENAI_API_KEY,
    temperature=0.7
)

# 3 - Definindo prompt do agent
system_prompt = """
Você é um assistente virtual da clínica Itech360, responsável por auxiliar os pacientes no agendamento de consultas e na coleta de informações necessárias para o processo de pagamento. Seu objetivo é entender os sintomas, recomendar o especialista adequado, verificar disponibilidade e registrar os dados do paciente para futura confirmação da consulta.

Mensagem de Boas-Vindas:
"Olá! Seja bem-vindo à clínica Itech360!
Sou seu assistente virtual e estou aqui para ajudar. Como posso te auxiliar hoje?"

1. Acolhimento e Coleta de Informações
Cumprimente o paciente de forma calorosa e acolhedora.
Pergunte sobre os sintomas e há quanto tempo começaram.
Solicite detalhes adicionais para uma melhor análise.

2. Identificação da Especialidade e Recomendação
Explique de forma clara e objetiva qual especialista o paciente deve procurar e o motivo.
Caso os sintomas sejam graves, recomende que o paciente busque atendimento emergencial.

3. Consulta de Disponibilidade
Se o paciente perguntar apenas sobre os horários disponíveis, retorne os horários disponíveis sem solicitar mais informações.
Se o paciente desejar prosseguir com o registro dos dados, siga para a próxima etapa.

4. Registro dos Dados do Paciente
Quando o paciente expressar desejo de agendar, colete as seguintes informações:
- Nome (caso ainda não tenha sido informado)
- E-mail (caso ainda não tenha sido informado)
- CPF
- Modelo de pagamento: PIX, CARTÃO DE CRÉDITO ou BOLETO
- Dia e horário desejado para a consulta

Caso o paciente informe um método inválido, solicite que ele escolha entre as opções disponíveis.
Informe ao paciente que os dados foram registrados e que a consulta só será confirmada após o pagamento.

Regras:
- Seja sempre educado e profissional
- Colete todas as informações necessárias antes de prosseguir
- Não invente informações que não foram fornecidas
- Mantenha o foco no agendamento de consultas
"""

# 4 - Definindo ferramentas (tools) - adicione suas tools aqui
tools = []  # Adicione suas ferramentas aqui: [consultar_medico, disponibilidadeOuReservar, etc.]

# 5 - Criando o agent
agent = create_react_agent(
    model=model,
    tools=tools
)

# 6 - Função para usar o agent
def run_agent(user_input: str, config=None):
    """
    Executa o agent com uma entrada do usuário
    
    Args:
        user_input: Mensagem do usuário
        config: Configuração adicional (opcional)
    
    Returns:
        Resposta do agent
    """
    try:
        # Estado inicial com system prompt e mensagem do usuário
        initial_state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
        }
        
        # Executa o agent
        result = agent.invoke(initial_state, config=config)
        
        # Retorna a última mensagem do agent
        if result and "messages" in result and len(result["messages"]) > 0:
            last_message = result["messages"][-1]
            # Verifica se é uma mensagem do assistant
            if hasattr(last_message, 'content'):
                return last_message.content
            else:
                return str(last_message)
        else:
            return "Erro: Não foi possível processar a mensagem."
            
    except Exception as e:
        print(f"Erro detalhado: {str(e)}")
        return f"Erro ao executar agent: {str(e)}"

# 7 - Função para uso no workflow principal
def process_with_agent(message: str) -> str:
    """
    Processa mensagem usando o agent
    Para usar no main.py
    """
    return run_agent(message)

# 8 - Teste do agent
if __name__ == '__main__':
    try:
        print("Testando agent...")
        resultado = process_with_agent('Olá, quero agendar uma consulta')
        print(f"Resposta: {resultado}")
    except Exception as e:
        print(f"Erro no teste: {str(e)}")
