from services.monitore_queues import monitor_rabbitmq_queue
from services.processing_data import ProcessingFile
from services.operation import get_lead, create_lead_db
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph
import os
from dotenv import load_dotenv
from data_prcessing.ready_message import classifying_mensagem

load_dotenv()

RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')

class GraphState(TypedDict):
    input: str
    output: str


# 3 - Recebendo mensagem
def receiver_message(state: GraphState):
    """Recebe mensagem do RabbitMQ"""
    print("Aguardando mensagem do webhook...")
    
    webhook_data = monitor_rabbitmq_queue(
        RABBITMQ_QUEUE, #type: ignore
        host=RABBITMQ_HOST,#type: ignore
        port=RABBITMQ_PORT,#type: ignore
        username=RABBITMQ_USERNAME,#type: ignore
        password=RABBITMQ_PASSWORD#type: ignore
    )
    
    # Atualiza o estado com os dados recebidos
    new_input = webhook_data if webhook_data else ""
    print(f"Dados recebidos: {new_input}")
    
    return {"input": new_input, "output": state.get("output", "")}


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
def search_lead(state: GraphState):

    if state['output']:
        print('Verificando existencia do lead... ')

        useful_dict = get_lead(state["output"])
        new_output = str(useful_dict)
        print(f'informações do lead {new_output}')

        return {"input": state["input"], "output": new_output}

    else:
        new_output = 'Nenhum dado recebido'
        print('Nenhum dado recebido')
        return {"input": state["input"], "output": new_output}    
    
 # Função para decidir o próximo nó baseado no lead_found
def decide_next_step_client(state: GraphState):
    import json
    try:
        # Converte o output (string) para dict para acessar lead_found
        result = json.loads(state["output"])
        lead_found = result.get("lead_found", False)

        if lead_found:
              return 'classificate_type_message'  # Lead existe
        else:
              return "create_lead"             # Lead não existe - vai cadastrar
    except (json.JSONDecodeError, KeyError):
          # Em caso de erro, assume que deve cadastrar
          return "create_lead"
    

#Criando cadastro do lead
def create_lead(state:GraphState):
    print('Estou criando lead')
    try:    
        useful_dict = create_lead_db(state["output"])
        new_output = str(useful_dict)
    except Exception as e:
        print(e.args)
        
    return {"input": state["input"], "output": new_output}



def classificate_message(state:GraphState):
    print('Estou classificando mensagem')
    try:    
        useful_dict = classifying_mensagem(state["output"])
        new_output = str(useful_dict)
    except Exception as e:
        print(e.args)
        
    input(new_output)
    return {"input": state["input"], "output": new_output}


# 5 - Criando o workflow
def create_workflow():
    workflow = StateGraph(GraphState)
    
    # Adicionar nós
    workflow.add_node("receive", receiver_message)
    workflow.add_node("process", processing_data)
    workflow.add_node('check_lead', search_lead)
    workflow.add_node('create_lead', create_lead)
    workflow.add_node('classificate_type_message', classificate_message)
    
    # Adicionar conexão
    workflow.set_entry_point("receive")
    workflow.add_edge("receive", "process")
    workflow.add_edge("process", 'check_lead' )
    workflow.add_conditional_edges(
        "check_lead",
        decide_next_step_client, {
        'create_lead': 'create_lead',
        'classificate_type_message': 'classificate_type_message'
        }
)
    # Definir pontos de entrada e saída
    workflow.add_edge('create_lead', 'classificate_type_message')
    workflow.add_edge('classificate_type_message', END)
    workflow_start = workflow.compile()
    
    return workflow_start

app = create_workflow()
# 6 - Execução principal
if __name__ == "__main__":
    print("Iniciando workflow...")
    
    # Criar workflow
    
    
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