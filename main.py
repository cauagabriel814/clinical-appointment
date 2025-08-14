from monitore_queues import monitor_rabbitmq_queue
from processing_data import ProcessingFile
from check_lead_exits import check_lead_exits
from pydantic import BaseModel
from dotenv import load_dotenv
from langgraph.graph import START, END,StateGraph
import os

# 1 - Carrega variáveis de ambiente
load_dotenv()

# 2 - Define o estado do graph
from typing import TypedDict

class GraphState(TypedDict):
    input: str
    output: str

# 3 - Recebendo mensagem
def receiver_message(state: GraphState):
    """Recebe mensagem do RabbitMQ"""
    print("Aguardando mensagem do webhook...")
    
    webhook_data = monitor_rabbitmq_queue(
        'santa-casa', 
        host='rabbitmq.itech360.com.br', 
        port=5672, 
        username='admin', 
        password='admin'
    )
    
    # Atualiza o estado com os dados recebidos
    new_input = webhook_data if webhook_data else ""
    print(f"Dados recebidos: {new_input}")
    
    return {"input": new_input, "output": state["output"]}


# 4 - Processando os dados
def processing_data(state: GraphState):

    if state["input"]:
        print("Processando dados...")
        
        processing_file = ProcessingFile(state["input"])
        processed_data = processing_file.get_variable()

        new_output = str(processed_data)
        print(f"Dados processados: {new_output}")
        return {"input": state["input"], "output": new_output}
    else:
        new_output = "Nenhum dado recebido"
        print("Nenhum dado para processar")
        return {"input": state["input"], "output": new_output}

#checando a existencia de um lead
def check_lead(state: GraphState):

    if state['output']:
        print('Verificando existencia do lead... ')

        useful_dict = check_lead_exits(state["output"])
        new_output = str(useful_dict)

        return {"input": state["input"], "output": new_output}

    else:
        new_output = 'Nenhum dado recebido'
        print('Nenhum dado recebido')
        return {"input": state["input"], "output": new_output}

# 5 - Criando o workflow
def create_workflow():
    workflow = StateGraph(GraphState)
    
    # Adicionar nós
    workflow.add_node("receive", receiver_message)
    workflow.add_node("process", processing_data)
    workflow.add_node('check_lead', check_lead)
    
    # Adicionar conexão
    workflow.set_entry_point("receive")
    workflow.add_edge("receive", "process")
    workflow.add_edge("process", 'check_lead' )
    
    # Definir pontos de entrada e saída
    
    workflow.add_edge('check_lead', END)
    workflow_start = workflow.compile()
    
    return workflow_start

# 6 - Execução principal
if __name__ == "__main__":
    print("Iniciando workflow...")
    
    # Criar workflow
    app = create_workflow()
    
    # Estado inicial
    initial_state = {"input": "", "output": ""}
    
    try:
        # Executar workflow
        final_state = app.invoke(initial_state)
        
        print(f"\n=== RESULTADO FINAL ===")
        print(f"Input: {final_state['input']}")
        print(f"Output: {final_state['output']}")
        
    except Exception as e:
        print(f"Erro no workflow: {e}")