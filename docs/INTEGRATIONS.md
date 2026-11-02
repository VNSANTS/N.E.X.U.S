# Integrações externas locais

## Configuração de segredo

O app carrega um `.env` somente na raiz do projeto, sem substituir variáveis já definidas no processo, sem interpolação e sem imprimir conteúdo. O arquivo é ignorado pelo Git. Copie `.env.example` para `.env` e edite localmente; restrinja ACL do Windows à sua conta. O `.env` é texto simples: para produção, use Windows Credential Manager/secret store. Não envie chaves no chat ou em relatórios.

```powershell
Copy-Item .env.example .env
notepad .env
$account = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls .env /inheritance:r /grant:r "$($account):(R,W)"
```

Nenhuma credencial estava disponível no ambiente quando esta integração foi construída. Chamadas remotas não foram testadas com credencial real. A interface mantém MockProvider por padrão até seleção explícita.

## Gemini

Defina `NEXUS_PROVIDER=gemini`, `NEXUS_ENABLE_REMOTE_PROVIDER=true`, `GEMINI_API_KEY` e `GEMINI_MODEL`. `GEMINI_EMBEDDING_MODEL` default é `gemini-embedding-001`. Gemini usa `x-goog-api-key`, REST `generateContent` e `embedContent`; a chave nunca entra na URL nem no prompt. A resposta tem timeout e erros normalizados. Antes de gerar, a política local de orçamento deve estar configurada e habilitada na aba **Inteligência**. O adaptador não usa ferramentas nativas/function calling.

Para checar custo de forma deliberada, use primeiro limites pequenos por tarefa e confira o preço vigente do modelo no Google AI Studio. Não há estimativa de preço embutida, para não aplicar preço desatualizado. Chamadas reais podem ser cobradas conforme plano/uso.

## Tavily

Use `TAVILY_API_KEY` e habilite `NEXUS_TAVILY_ENABLED=true`. Pesquisa automatica em ciclos tambem requer `NEXUS_RESEARCH_ENABLED=true`, permissao por topico e aprovacao de custo recorrente `NEXUS_TAVILY_AUTONOMOUS_APPROVED=true` (falso por padrao). A pesquisa manual exige `confirm: true` e consome creditos Tavily. O ciclo faz busca basica e extrai no maximo duas paginas, reservando duas chamadas Tavily; falhas de extracao preservam snippets e registram tipo de falha. `NEXUS_TAVILY_DAILY_CALL_LIMIT` aceita 1 a 50 (default 5). Busca advanced pode consumir mais creditos.

Extração aceita URLs públicas previamente descobertas por Tavily, bloqueia esquema diferente de HTTP(S), URLs com credenciais e endereços locais/privados literais. Conteúdo fica limitado a 12.000 caracteres e etiquetado como não confiável. A API nunca repassa o token ao modelo.

## Crossref

A API pública Crossref não exige chave; `CROSSREF_MAILTO` identifica o cliente e pode habilitar o polite pool. `NEXUS_CROSSREF_ENABLED=true` é o default. A aplicação consulta apenas API REST fixa, limita resultados e segue cooldown. Crossref retorna metadados depositados; resumos (abstracts) podem ser protegidos por copyright. Não baixa artigos completos.

## GitHub

A leitura de repositórios públicos funciona sem chave. Opcionalmente `GITHUB_TOKEN` aumenta limite; use token fine-grained somente com permissões read mínimas (`Metadata`, `Contents`, `Issues`) e não configure escopo de escrita. N.E.X.U.S. executa apenas GET. `POST /api/v1/integrations/github/repos` registra um repositório para acompanhamento; `/.../{id}/sync` exige confirmação e grava snapshots, commits recentes, issues abertas e diferenças. Uma sincronização faz três leituras API e o limite local é 15/dia. Não faz clone, comentário, criação de issue nem push.

## Endpoints autenticados

- `GET /api/v1/integrations`: disponibilidade/configuração sem revelar segredo.
- `POST /api/v1/integrations/tavily/search`: consulta confirmada, registra fontes e consumo local.
- `POST /api/v1/integrations/tavily/extract`: extrai URLs descobertas e arquiva conteúdo não confiável.
- `GET/POST /api/v1/integrations/github/repos`: consulta/adiciona repositórios rastreados.
- `POST /api/v1/integrations/github/repos/{id}/sync`: captura somente metadados públicos.
- `GET /api/v1/usage` e `GET/POST /api/v1/usage/budget`: registros e orçamento do provider LLM.

Logs e falhas mantêm códigos/tipos fixos; conteúdo da exceção HTTP, cabeçalhos de autenticação e bodies de erro do fornecedor não são registrados. Chamadas externas são reservadas no ledger antes do acesso. Os adaptadores não fazem retry automático e não executam ações externas.

## Estado de implementação

- **Gemini geração:** adaptador implementado e conectado ao runtime; teste HTTP simulado. Chamada real pendente de chave, modelo, orçamento e opt-in.
- **Gemini análise de ciclo:** candidato de análise em `analyze`, somente se provider e orçamento ativos; teste real pendente.
- **Gemini embeddings:** endpoint e indexação/recuperação semântica opcionais; vetores antigos exigem indexação manual.
- **Tavily:** search/extract implementados e ligados a fontes/ciclo; teste simulado. Sem chave e sem chamada real.
- **Crossref:** API pública implementada, teste simulado existente; não necessita chave. Não executamos chamada real nessa sessão.
- **GitHub:** leitura pública, snapshots e diff implementados; teste simulado. Sem token pessoal e sem chamada real.

## Gemini e OpenAI — configuração e estado (2026-11-01)

Os adaptadores compartilham HTTPModelProvider e o contrato ModelProvider; ProviderManager continua responsável por catálogo, seleção manual e credenciais. O ModelRoutingService/Model Router permanece intacto: no modo automático, candidatos remotos precisam estar na allowlist, disponíveis no catálogo e autorizados pelo orçamento local. O modo manual continua selecionando um modelo descoberto. O padrão não foi alterado e chamadas remotas não foram habilitadas.

Configuração local no arquivo .env (nunca versionar o arquivo):

~~~dotenv
NEXUS_ENABLE_REMOTE_PROVIDER=true
NEXUS_REMOTE_PROVIDERS=gemini,openai
GEMINI_API_KEY=
GEMINI_MODEL=
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
OPENAI_API_KEY=
OPENAI_MODEL=
~~~

Preencha os identificadores de modelo com IDs retornados pelo catálogo autenticado do próprio provedor. O catálogo Gemini é publicado em [Gemini models](https://ai.google.dev/gemini-api/docs/models); gemini-embedding-001 é o valor configurado por padrão para embeddings. A OpenAI mantém catálogo consultável via [Models API](https://platform.openai.com/docs/api-reference/models/list), portanto o projeto não presume um ID universal. Verifique a disponibilidade e capacidades do modelo escolhido na sua conta antes de selecioná-lo.

Gemini envia a chave no cabeçalho x-goog-api-key e usa generateContent/SSE streamGenerateContent; OpenAI usa Bearer e Chat Completions/SSE. A chave não é colocada em URL, prompt, resposta de status ou logs. Os adaptadores não executam tool calls; Tavily/pesquisa continua sendo integração separada. Erros HTTP são convertidos em erros seguros, sem repassar corpos de erro do fornecedor. Os testes usam transporte substituto e não fazem tráfego de rede.

NEXUS_ENABLE_REMOTE_PROVIDER=true é apenas um opt-in técnico. O ledger de orçamento do N.E.X.U.S. continua independente e desativado até ativação autorizada na aplicação. API key não significa cota grátis ou ilimitada: confira [preços Gemini](https://ai.google.dev/gemini-api/docs/pricing) e [preços OpenAI](https://openai.com/api/pricing/) antes de qualquer uso real. Nenhuma chamada ou consumo foi realizado nesta validação.

### Resultado de validação desta etapa

- Adaptadores Gemini e OpenAI: configuração, modelos/chat e streaming cobertos por mocks.
- Seleção manual e catálogo/status: teste sem rede para os dois adapters; status não expõe segredo.
- OpenAI no roteamento automático: teste unitário aprova a seleção somente com candidato permitido e orçamento de teste habilitado. O orçamento de produção permanece inalterado.
- provider_from_env agora respeita NEXUS_REMOTE_PROVIDERS quando a variável está presente; allowlist vazia bloqueia todos. Sem a variável, mantém compatibilidade com configurações antigas que usam apenas o opt-in global.
- Não houve verificação de conexão real nem validação de chave/modelo junto aos serviços.


## Ollama e provedores de geracao

O adaptador Ollama usa exclusivamente enderecos loopback HTTP, consulta `/api/version`, `/api/ps` e `/api/tags`, envia historico para `/api/chat` e suporta NDJSON em streaming. Nenhum modelo e baixado automaticamente. Modelo ausente gera erro explicito; nao troca para MockProvider.

Este computador foi verificado com Ollama 0.40.13 e o modelo instalado `qwen2.5:0.5b` (397 MB). A configuracao local usa `OLLAMA_NUM_CTX=2048`, `OLLAMA_NUM_PREDICT=384` e temperatura 0.2 para limitar o trabalho num PC com 8 GB de RAM. A selecao persistida em `nexus_learning.db` e Ollama/Qwen. O teste real ponta a ponta confirmou streaming e persistencia do historico; a qualidade do modelo e limitada e respostas aritmeticas simples foram inconsistentes. Conexao funcional nao significa qualidade factual validada.

Provedores adicionais atras de `ProviderManager`: OpenAI, Anthropic, Gemini, Groq e OpenRouter, alem de Ollama e MockProvider. Adaptadores remotos exigem `NEXUS_ENABLE_REMOTE_PROVIDER=true`, credencial e modelo no `.env`, alem do orcamento remoto habilitado explicitamente no app. `NEXUS_REMOTE_PROVIDERS=gemini` limita o opt-in a Gemini e evita ativar credenciais de outros provedores presentes no ambiente. Validacao real somente de autenticacao/metadados: Gemini listou 46 modelos e `gemini-2.5-flash` esta disponivel; Tavily retornou uso da conta/chave sem consumir credito. Nenhuma geracao Gemini nem busca Tavily foi executada; chamadas de inferencia e pesquisa podem ter custo. MockProvider fica restrito ao ambiente development/testes e nao substitui silenciosamente falhas de providers reais.

O estado e catalogo de modelos sao acessiveis em `GET /api/v1/providers`; selecao exige confirmacao em `POST /api/v1/providers/default`, e conexao em `POST /api/v1/providers/{provider}/check` com `{"confirm":true}`. O check de Gemini lista modelos com autenticacao (sem gerar tokens) e o check de Tavily usa `GET /usage` (sem pesquisa/creditos); uma busca real continua exigindo confirmacao e pode consumir creditos. O check de Ollama e local. A interface usa `POST /api/v1/sessions/{id}/messages/stream`; a resposta so entra no historico apos conclusao e revisao estrutural.

## Continuity - ALL FOR ONE / initial routing (2026-11-01)

- Audit confirmed that chat provider selection remains manually persisted; automatic model routing is not yet connected to chat runtime.
- Added `nexus_learning/model_router.py`: pure deterministic policy for SIMPLE, STANDARD, ADVANCED and RESEARCH; filters availability, capability, context, cost and latency metadata; fallback stays within local/remote trust boundary.
- Fail-closed behavior: remote candidates require explicit remote permission and budget authorization; unavailable, disallowed, malformed or insufficient-context candidates are rejected.
- This policy is not yet wired into runtime provider choice. Model latency, price and capability metadata need a trusted catalog or reviewed configuration before automatic routing. Manual Ollama/Qwen selection remains unchanged.
- Product-agent roles remain sequential and deterministic, not independent LLM agents. Research, knowledge and memory infrastructure exist, but chat does not delegate model tool calls. No Gemini generation or Tavily search was run during this work.
- Initial integrity audit found numerous existing local changes; all preserved. `.env` and local database remain Git-ignored. No commit/push. Codex profiles passed static validation, but subagent startup failed because the local OAuth token had been invalidated after the user's logout; no global settings were changed.
- Verification: `python -m compileall -q nexus_learning tests` passed; `python -m unittest discover -s tests -v` passed with 97 tests, including 9 router tests; `git diff --check` passed.
