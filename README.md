# Trabalho — C2.A2: RAG Distribuído em Microsserviços

**Sistemas Distribuídos e Computação em Nuvem · FAESA · 2026/2**
## Sobre o Projeto
Este repositório contém a implementação do sistema RAG (Retrieval-Augmented Generation) distribuído. O projeto foi arquitetado em três microsserviços independentes (Ingestão, Recuperação e Geração) que se comunicam via REST e mensageria, garantindo resiliência, persistência e processamento assíncrono.

##Arquitetura e Diagrama (Tarefa 6)

A arquitetura final do sistema foi projetada para garantir o desacoplamento das responsabilidades e a tolerância a falhas na comunicação com a API do LLM:

```text
       [ Cliente / Usuário ]
                 │
                 ▼ (POST /perguntar)
       ┌───────────────────┐
       │ Serviço Geração   │ ──(Circuit Breaker)──> [ API do LLM ]
       └─────────┬─────────┘
                 │ (REST)
                 ▼
       ┌───────────────────┐
       │Serv. Recuperação  │
       └─────────┬─────────┘
                 │ (REST)
                 ▼
       ┌───────────────────┐     (Fila / Assíncrono)     ┌───────────────────┐
       │  Serv. Ingestão   │ ◄──────────────────────── │    Redis (Broker) │
       └───────────────────┘                           └───────────────────┘
```

### Estrutura do projeto
```bash
sd-2026-2-kit-c2a2/
├── servicos/
│   ├── comum/
│   │   ├── embeddings.py       # Vetorização offline
│   │   ├── llm.py              # Cliente LLM com modo simulado
│   │   └── circuit_breaker.py  # Padrão de resiliência e tolerância a falhas
│   ├── ingestao/app.py         # Microsserviço de Ingestão (com Fila Redis)
│   ├── recuperacao/app.py      # Microsserviço de Recuperação por Similaridade
│   └── geracao/app.py          # Microsserviço de Geração (com Circuit Breaker)
├── documentos/                 # Base de dados e arquivos persistidos (.pkl)
├── Dockerfile                  # Imagem base unificada para os microsserviços
├── docker-compose.yml          # Orquestração dos serviços e do Redis
└── README.md                   # Documentação da arquitetura e execução
```
## Como Executar (Execução Reproduzível)

O projeto está configurado para rodar de forma isolada via containers, garantindo que os serviços funcionem offline e sem necessidade de configurações complexas na máquina hospedeira.

**1. Clone o repositório:**
```bash
git clone <url-do-seu-repositorio>
cd sd-2026-2-kit-c2a2
```

**2. Suba a infraestrutura completa:**
```bash
docker-compose up --build
```

**3. Acesse a documentação interativa (Swagger) dos serviços:**
* **Ingestão:** `http://localhost:8001/docs`
* **Recuperação:** `http://localhost:8002/docs`
* **Geração:** `http://localhost:8003/docs`

### Como Testar o Fluxo

1. **Ingestão via Fila (Assíncrona):**
   Envie um POST para `http://localhost:8001/indexar` com o payload:
   ```json
   [
     {"texto": "O teorema CAP trata de consistencia e disponibilidade.", "origem": "aula11.txt"}
   ]
   ```
   *Retornará status de enfileirado e será processado pelo worker.*

2. **Geração (Fluxo Completo):**
   Envie um POST para `http://localhost:8003/perguntar` com o payload:
   ```json
   {
     "pergunta": "O que diz o teorema CAP?"
   }
   ```
   *O serviço retornará a resposta do LLM embasada no contexto recuperado.*



