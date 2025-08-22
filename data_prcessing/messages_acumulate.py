import json
import time
import uuid
import os
import threading
import fcntl
from typing import Dict, List, Any
from pathlib import Path

class MessageAccumulator:
    def __init__(self, batch_timeout: int = 50, storage_dir: str = "batch_storage"):
        """
        Inicializa o acumulador de mensagens usando arquivos locais
        
        Args:
            batch_timeout: Tempo em segundos para aguardar novas mensagens no batch
            storage_dir: Diretório para armazenar os arquivos de batch
        """
        self.batch_timeout = batch_timeout
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
    def _get_batch_files(self, session_id: str):
        """Retorna os caminhos dos arquivos para uma sessão"""
        return {
            'messages': self.storage_dir / f"batch_{session_id}_messages.json",
            'timer': self.storage_dir / f"batch_{session_id}_timer.json",
            'lock': self.storage_dir / f"batch_{session_id}.lock",
            'processor': self.storage_dir / f"batch_{session_id}_processor.json"
        }
    
    def _read_json_file(self, file_path: Path, default=None):
        """Lê arquivo JSON com tratamento de erro"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return default
    
    def _write_json_file(self, file_path: Path, data):
        """Escreve arquivo JSON com tratamento de erro"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def _acquire_lock(self, lock_file: Path, instance_id: str) -> bool:
        """Tenta adquirir lock exclusivo para o batch"""
        try:
            # Cria arquivo de lock se não existir
            lock_file.touch()
            
            with open(lock_file, 'r+') as f:
                try:
                    # Tenta fazer lock exclusivo
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # Verifica se o lock já tem dono
                    f.seek(0)
                    current_content = f.read().strip()
                    
                    if not current_content:
                        # Lock livre - toma posse
                        f.seek(0)
                        f.write(instance_id)
                        f.truncate()
                        return True
                    else:
                        # Verifica se é o mesmo processo
                        return current_content == instance_id
                        
                except (IOError, OSError):
                    return False
        except:
            return False
    
    def _release_lock(self, lock_file: Path):
        """Libera o lock do batch"""
        try:
            if lock_file.exists():
                lock_file.unlink()
        except:
            pass
    
    def _is_timer_expired(self, timer_file: Path) -> bool:
        """Verifica se o timer do batch expirou"""
        timer_data = self._read_json_file(timer_file)
        if not timer_data:
            return True
            
        start_time = timer_data.get('start_time', 0)
        return (time.time() - start_time) >= self.batch_timeout
    
    def accumulate_message(self, message_data: str) -> Dict[str, Any]:
        """
        Acumula mensagem por session_id e decide se deve processar o batch
        
        Args:
            message_data: JSON string com dados da mensagem (deve conter session_id)
            
        Returns:
            Dict com resultado:
            - should_process: bool - se deve processar o batch
            - messages: list - todas as mensagens do batch (se should_process=True)
            - status: str - status da operação
            - session_id: str - ID da sessão
        """
        
        try:
            # Parse da mensagem para extrair session_id
            message_dict = json.loads(message_data)
            session_id = message_dict.get('session_id')
            
            if not session_id:
                return {
                    "should_process": False,
                    "messages": [],
                    "status": "Erro: session_id não encontrado na mensagem",
                    "session_id": ""
                }
            
            # Obtém arquivos para esta sessão
            files = self._get_batch_files(session_id)
            instance_id = str(uuid.uuid4())
            
            # Verifica se existe timer ativo
            timer_data = self._read_json_file(files['timer'])
            
            if not timer_data or self._is_timer_expired(files['timer']):
                # Não existe batch ou timer expirou - tenta iniciar novo
                if self._acquire_lock(files['lock'], instance_id):
                    # Conseguiu o lock - inicia novo batch
                    current_time = time.time()
                    
                    # Inicializa arquivos do batch
                    self._write_json_file(files['messages'], [message_data])
                    self._write_json_file(files['timer'], {
                        'start_time': current_time,
                        'expires_at': current_time + self.batch_timeout
                    })
                    self._write_json_file(files['processor'], {
                        'instance_id': instance_id,
                        'created_at': current_time
                    })
                    
                    print(f"Iniciando batch para session_id: {session_id}, aguardando {self.batch_timeout}s...")
                    
                    # Aguarda o timeout
                    time.sleep(self.batch_timeout)
                    
                    # Verifica se ainda é o processador responsável
                    processor_data = self._read_json_file(files['processor'])
                    if processor_data and processor_data.get('instance_id') == instance_id:
                        # Coleta todas as mensagens do batch
                        all_messages_data = self._read_json_file(files['messages'], [])
                        
                        # Converte para objetos Python
                        messages_list = []
                        for msg_str in all_messages_data:
                            try:
                                messages_list.append(json.loads(msg_str))
                            except json.JSONDecodeError:
                                print(f"Erro ao decodificar mensagem: {msg_str}")
                        
                        # Limpa os arquivos do batch
                        for file_path in files.values():
                            try:
                                if file_path.exists():
                                    file_path.unlink()
                            except:
                                pass
                        
                        print(f"Processando batch para session_id: {session_id} com {len(messages_list)} mensagem(s)")
                        
                        return {
                            "should_process": True,
                            "messages": messages_list,
                            "status": f"Processando batch com {len(messages_list)} mensagem(s)",
                            "session_id": session_id
                        }
                    else:
                        # Outro processo assumiu
                        self._release_lock(files['lock'])
                        return {
                            "should_process": False,
                            "messages": [],
                            "status": "Outro processo assumiu o batch",
                            "session_id": session_id
                        }
                else:
                    # Não conseguiu o lock - adiciona ao batch existente
                    messages_data = self._read_json_file(files['messages'], [])
                    messages_data.append(message_data)
                    self._write_json_file(files['messages'], messages_data)
                    
                    return {
                        "should_process": False,
                        "messages": [],
                        "status": "Mensagem adicionada ao batch existente",
                        "session_id": session_id
                    }
            else:
                # Batch ativo existe - adiciona mensagem
                messages_data = self._read_json_file(files['messages'], [])
                messages_data.append(message_data)
                self._write_json_file(files['messages'], messages_data)
                
                # Calcula tempo restante
                start_time = timer_data.get('start_time', time.time())
                elapsed = time.time() - start_time
                remaining = max(0, self.batch_timeout - elapsed)
                
                return {
                    "should_process": False,
                    "messages": [],
                    "status": f"Mensagem adicionada ao batch. Tempo restante: {remaining:.1f}s",
                    "session_id": session_id
                }
                
        except json.JSONDecodeError as e:
            return {
                "should_process": False,
                "messages": [],
                "status": f"Erro ao decodificar JSON: {str(e)}",
                "session_id": ""
            }
        except Exception as e:
            return {
                "should_process": False,
                "messages": [],
                "status": f"Erro no acumulador: {str(e)}",
                "session_id": ""
            }
    
    def get_batch_status(self, session_id: str) -> Dict[str, Any]:
        """
        Obtém status atual do batch para uma sessão específica
        """
        files = self._get_batch_files(session_id)
        
        messages_data = self._read_json_file(files['messages'], [])
        timer_data = self._read_json_file(files['timer'])
        processor_data = self._read_json_file(files['processor'])
        
        active = bool(timer_data and not self._is_timer_expired(files['timer']))
        
        if timer_data:
            start_time = timer_data.get('start_time', time.time())
            elapsed = time.time() - start_time
            remaining = max(0, self.batch_timeout - elapsed)
        else:
            elapsed = 0
            remaining = 0
            
        return {
            "session_id": session_id,
            "active": active,
            "messages_count": len(messages_data),
            "elapsed_time": elapsed,
            "remaining_time": remaining,
            "processor": processor_data.get('instance_id') if processor_data else None
        }
    
    def clear_batch(self, session_id: str) -> bool:
        """
        Limpa um batch manualmente para uma sessão específica
        """
        files = self._get_batch_files(session_id)
        
        cleared = False
        for file_path in files.values():
            try:
                if file_path.exists():
                    file_path.unlink()
                    cleared = True
            except:
                pass
                
        return cleared

def process_accumulated_messages(message_data: str) -> str:
    """
    Função principal para processar mensagens acumuladas
    
    Args:
        message_data: JSON string com dados da mensagem
        
    Returns:
        JSON string com resultado do processamento
    """
    
    # Inicializa o acumulador
    accumulator = MessageAccumulator()
    
    # Processa a mensagem
    result = accumulator.accumulate_message(message_data)
    
    if result["should_process"]:
        # Esta é a mensagem "ganhadora" que deve processar todo o batch
        messages = result["messages"]
        session_id = result["session_id"]
        
        print(f"=== PROCESSANDO BATCH PARA SESSION {session_id} ===")
        print(f"Total de mensagens: {len(messages)}")
        
        # Aqui você pode implementar a lógica específica para processar 
        # todas as mensagens acumuladas
        processed_result = {
            "session_id": session_id,
            "total_messages": len(messages),
            "messages": messages,
            "status": "batch_processed",
            "processed_at": time.time()
        }
        
        # Log das mensagens processadas
        for i, msg in enumerate(messages, 1):
            print(f"Mensagem {i}: {msg.get('mensagem', 'N/A')[:50]}...")
        
        return json.dumps(processed_result)
    
    else:
        # Esta mensagem foi apenas adicionada ao batch, não deve prosseguir
        print(f"Mensagem adicionada ao batch: {result['status']}")
        
        # Simula o comportamento do n8n onde outras mensagens "dão erro"
        error_result = {
            "session_id": result["session_id"],
            "status": "added_to_batch",
            "message": result["status"],
            "should_continue": False
        }
        
        return json.dumps(error_result)

# Função de conveniência para usar no workflow
def accumulate_messages_by_session(message_data: str) -> str:
    """
    Wrapper function para usar no main.py
    """
    return process_accumulated_messages(message_data)