"""
Servico 2 - RECUPERACAO: dada uma pergunta, acha os trechos mais relevantes.

TAREFA 2: implementar a busca por similaridade.

Rodar: uvicorn servicos.recuperacao.app:app --port 8002
"""
import os

import requests
from fastapi import FastAPI
from pydantic import BaseModel

from servicos.comum.embeddings import Vetorizador, similaridade

app = FastAPI(title="Recuperacao - C2.A2")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://localhost:8001")


class Consulta(BaseModel):
    pergunta: str
    top_k: int = 3


@app.post("/buscar")
def buscar(consulta: Consulta):
    """Deve devolver os top_k trechos mais parecidos com a pergunta."""
    r = requests.get(f"{URL_INGESTAO}/indice", timeout=10)
    r.raise_for_status()
    dados_indice = r.json()
    itens = dados_indice.get("itens", [])

    if not itens:
        return {"resultados": []}

    # Extrai todos os textos para ajustar o vetorizador com o mesmo vocabulário
    textos = [item["texto"] for item in itens]
    
    vetorizador = Vetorizador()
    vetorizador.ajustar(textos)

    # Vetoriza a pergunta enviada pelo usuário
    vetor_pergunta = vetorizador.vetorizar(consulta.pergunta)

    # Calcula a similaridade de cada item com a pergunta
    resultados = []
    for item in itens:
        vetor_item = item.get("vetor")
        if not vetor_item:
            vetor_item = vetorizador.vetorizar(item["texto"])
            
        sim = similaridade(vetor_item, vetor_pergunta)
        resultados.append({
            "texto": item["texto"],
            "origem": item["origem"],
            "similaridade": sim
        })

    # Ordena por similaridade decrescente e pega os top_k
    resultados.sort(key=lambda x: x["similaridade"], reverse=True)
    top_resultados = resultados[:consulta.top_k]

    return {"resultados": top_resultados}


@app.get("/saude")
def saude():
    return {"status": "ok"}