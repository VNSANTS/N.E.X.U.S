# Aprendizagem contínua e operação local

## Ciclo persistente

`LearningCycleService` persiste ciclo, fase, checkpoint, orçamento, eventos, achados, perguntas e execuções dos sete papéis internos. Um job executa uma fase por vez. Chaves de idempotência, limite de dez fases, até duas recuperações automáticas e limites diários impedem loops ilimitados. O ciclo é retomado quando `worker` inicia/pesquisa a fila; a recorrência só roda com autonomia global habilitada, tópico ativo e computador/serviço em execução.

Fases: observar → oportunidade → planejar → pesquisar → analisar → verificar → organizar → consolidar → avaliar → lacunas. A pesquisa Crossref/Tavily só roda com `NEXUS_RESEARCH_ENABLED=true`, consentimento do tópico e orçamento diário disponível; Tavily exige ainda `NEXUS_TAVILY_ENABLED=true`, `TAVILY_API_KEY` e a aprovação de custos recorrentes `NEXUS_TAVILY_AUTONOMOUS_APPROVED=true`; esta última fica falsa por padrão. Crossref pode ser desligado em `NEXUS_CROSSREF_ENABLED=false`. O default não faz pesquisa externa.

## Autonomia, orçamento e pausa

A aba **Inteligência** da interface autenticada mostra ciclo, fase, fontes, achados, perguntas, papéis, worker e uso diário. Ativar autonomia é separado de criar ciclo manual. Cada tópico define frequência (1 hora–30 dias), ativação e consentimento para pesquisa. Ações de controle e respostas exigem confirmação na API. O worker é de thread única, local e só trabalha enquanto o processo estiver ativo.

Chamadas de providers remotos falham fechadas até o proprietário configurar um orçamento em **Inteligência**: limite diário e por tarefa de chamadas/tokens/valor, além do preço por milhão de tokens. O orçamento padrão é zero/desativado. Chamadas que terminam em timeout mantêm reserva de custo, pois o provider pode ter processado a solicitação. Uso real informado pela API substitui a estimativa. Estimativas de entrada usam comprimento de texto como limite conservador; o preço escolhido pelo proprietário precisa corresponder ao modelo/contrato atual.

Tavily usa um limite local de até 50 chamadas/dia, configurável em `NEXUS_TAVILY_DAILY_CALL_LIMIT` (default 5). Ciclos também contam uma chamada por provider, reservada atomicamente. GitHub permite até 15 sincronizações/dia (3 chamadas REST por sincronização), Crossref até 50/dia e cooldown entre buscas. Não há retry externo automático.

## Providers internos

Os sete papéis internos são `orchestrator`, `researcher`, `analyst`, `architect`, `developer`, `reviewer` e `knowledge_manager`. São trilhas de execução estruturadas e registradas. Gemini pode produzir análise candidata na fase `analyze` se estiver explicitamente configurado e o orçamento estiver habilitado. Nenhum agente pode validar automaticamente afirmações; a saída do modelo vira achado não confiável para revisão, nunca memória/fato.

Gemini Embedding `gemini-embedding-001` é opcional. Para indexar uma memória existente, use `POST /api/v1/memories/{id}/embed` com `confirm: true` e orçamento ativo. Recuperação semântica consulta vetores indexados e cai para busca lexical se embedder, chave, orçamento ou provider falhar. Memórias existentes não são reindexadas automaticamente.

## Perguntas humanas

Temas que indicam objetivos ou preferências pessoais criam pergunta pendente e pausam aquele ciclo. Ao responder, o ciclo é retomado. A resposta só vira memória semântica quando `remember: true` é escolhido explicitamente. O detector atual usa marcadores em português e precisa de evolução para outros idiomas e para intenção implícita.

## Início e retomada (PowerShell)

Na raiz do repositório:

```powershell
python -m unittest discover -s tests -v
python -m nexus_learning --db nexus_learning.db serve --host 127.0.0.1 --port 8765
# em um segundo terminal
python -m nexus_learning --db nexus_learning.db worker --poll 1
```

O worker recupera jobs e ciclos persistidos; fechar o terminal ou desligar o PC interrompe o trabalho até iniciar novamente. `scripts/run-worker.ps1` pode ser executado manualmente. Não há tarefa agendada do Windows instalada.

Para pausa imediata, use o controle de autonomia ou encerre o worker com Ctrl+C. Em erro repetido o ciclo entra em `paused_error`. Evite editar a base SQLite enquanto os processos estão abertos.

## Limites

Crossref entrega metadados depositados e trechos curtos; abstracts podem ter copyright. Tavily fornece snippets e extração com limite; textos coletados ficam classificados `external_untrusted`, nunca como instruções. Contradições são candidatos lexicais de baixa confiança. Não há validação epistemológica automatizada, treinamento de pesos, crawler ilimitado, execução de código ou funcionamento quando o computador está desligado.
