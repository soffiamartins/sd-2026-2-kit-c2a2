"""
Servico 1 - INGESTAO: recebe documentos, gera embeddings e armazena.
Com mensageria via Redis (Fila) para atender à Tarefa 4.

Rodar: uvicorn servicos.ingestao.app:app --port 8001
"""
import os
import pickle
import threading
import time
import redis
from fastapi import FastAPI
from pydantic import BaseModel

from servicos.comum.embeddings import Vetorizador

app = FastAPI(title="Ingestao - C2.A2")

vetorizador = Vetorizador()
INDICE = []
INDICE_PATH = "documentos/indice_persistido.pkl"

# Configuração do Redis (pega do ambiente ou usa localhost)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
FILA_NOME = "fila_ingestao"


class Documento(BaseModel):
    texto: str
    origem: str = "desconhecida"


def carregar_indice():
    global INDICE, vetorizador
    if os.path.exists(INDICE_PATH):
        try:
            with open(INDICE_PATH, "rb") as f:
                dados = pickle.load(f)
                INDICE = dados.get("indice", [])
                if INDICE:
                    textos = [i["texto"] for i in INDICE]
                    vetorizador.ajustar(textos)
        except Exception:
            INDICE = []


def salvar_indice():
    os.makedirs(os.path.dirname(INDICE_PATH), exist_ok=True)
    with open(INDICE_PATH, "wb") as f:
        pickle.dump({"indice": INDICE}, f)


carregar_indice()


# Worker rodando em background para consumir da fila do Redis (Mensageria)
def worker_ingestao():
    global INDICE
    while True:
        try:
            # Pula se o redis não estiver disponível ainda
            item_fila = redis_client.brpop(FILA_NOME, timeout=2)
            if item_fila:
                _, doc_json = item_fila
                import json
                doc_dict = json.loads(doc_json)
                
                texto = doc_dict["texto"]
                origem = doc_dict["origem"]

                # Processa a indexação de forma assíncrona via fila
                textos_atuais = [i["texto"] for i in INDICE] + [texto]
                vetorizador.ajustar(textos_atuais)
                
                INDICE.append({"texto": texto, "origem": origem})
                for item in INDICE:
                    item["vetor"] = vetorizador.vetorizar(item["texto"])
                
                salvar_indice()
        except Exception:
            time.sleep(1)


# Inicia o worker em uma thread separada para processar a fila em segundo plano
threading.Thread(target=worker_ingestao, daemon=True).start()


@app.post("/indexar")
def indexar(docs: list[Documento]):
    """Publica os documentos na fila do Redis em vez de processar diretamente (Mensageria)."""
    import json
    for d in docs:
        doc_dict = {"texto": d.texto, "origem": d.origem}
        redis_client.lpush(FILA_NOME, json.dumps(doc_dict))
    
    return {"status": "enfileirado", "quantidade": len(docs)}


@app.get("/indice")
def indice():
    """Consumido pelo servico de recuperacao."""
    return {"total": len(INDICE),
            "itens": [{"texto": i["texto"], "origem": i["origem"],
                       "vetor": i["vetor"]} for i in INDICE]}


@app.get("/saude")
def saude():
    return {"status": "ok", "documentos": len(INDICE), "redis": redis_client.ping()}