# Auditoria comparativa de assistentes pessoais — 2026-11-02

**Status:** pesquisa e recomendação arquitetural; este documento não altera o runtime por si só.  
**Base examinada:** repositório N.E.X.U.S., branch main, commit de referência 852131e52f454175c501e6f36bcea2c04a73e9e7, documentação e módulos do runtime.  
**Objetivo:** aproveitar padrões úteis de assistentes pessoais sem substituir o núcleo do N.E.X.U.S., duplicar funcionalidades existentes ou aumentar riscos e custos desnecessariamente.

## 1. Decisão executiva

**Não adotar Hermes Agent, OpenClaw ou NanoClaw como dependência central do N.E.X.U.S.** Manter o runtime próprio em Python/SQLite e incorporar, em etapas, padrões úteis:

1. Ciclo nativo e limitado de chamadas de ferramentas: o modelo solicita uma ferramenta, o runtime valida e executa, o resultado volta ao modelo e a resposta é concluída.
2. Especialistas de IA com envelopes tipados, contexto mínimo, ferramentas explicitamente permitidas, orçamento e limite de etapas.
3. Skills procedurais carregadas sob demanda, separadas de memórias pessoais e conhecimento factual.
4. Gateway único para sessões, autenticação, roteamento e futuros canais.
5. Fronteira de execução isolada somente para tarefas que realmente executem código ou manipulem arquivos; sem shell irrestrito no host.
6. Melhorias propostas em ambiente isolado, testadas e revisadas antes de serem ativadas.

O objetivo não é reproduzir um “Jarvis” de demonstração. É criar um assistente confiável, útil, auditável, econômico e reversível.

## 2. Estado atual do N.E.X.U.S. observado

O repositório já contém uma base substancial:

- Aplicação local em Python/SQLite, API autenticada de usuário único, sessões e histórico persistentes e interface web.
- Recuperação contextual de memórias ativas e afirmações validadas com fontes; busca semântica é opcional e há fallback lexical.
- Adaptadores de modelos e roteamento manual/automático com verificação de disponibilidade, capacidade, contexto, política de privacidade e orçamento.
- Registro de ferramentas com schemas, allowlist e classes de permissão; pesquisa externa é tratada como ação sensível e pede confirmação.
- Ciclo de aprendizado persistente, fila/worker local, limites de chamadas e gastos, proveniência de fontes, checkpoints e auditoria.
- Sete papéis de produto registrados: orchestrator, researcher, analyst, architect, developer, reviewer e knowledge_manager.

**Limitações que continuam reais:**

- Os papéis de produto ainda são etapas determinísticas e sequenciais, não especialistas de IA independentes.
- A conversa ainda não possui um ciclo geral de provider-native tool calling → execução pelo registry → retorno do resultado ao modelo. A pesquisa atual é uma integração coordenada pelo backend, com confirmação, e não prova um protocolo geral de ferramentas do modelo.
- A revisão de citações verifica formato/índices, mas ainda precisa avaliar melhor se cada trecho realmente sustenta a afirmação e se há contradições.
- O worker descrito é local. O core ainda não foi implantado como serviço cloud público.
- Não há execução geral de shell/código; portanto, contêineres não devem ser adicionados apenas por aparência ou para simular autonomia.

Referências internas: PROJECT_STATUS.md, docs/LOCAL_API.md, docs/CONTINUOUS_LEARNING.md, nexus_learning/agents.py, nexus_learning/tools.py, nexus_learning/context.py, nexus_learning/routing.py e nexus_learning/runtime.py.

## 3. Comparação das referências

| Projeto | Padrão útil observado | Aplicação recomendada no N.E.X.U.S. | O que não copiar automaticamente |
|---|---|---|---|
| Hermes Agent | Memória persistente curta e curada; skills sob demanda; toolsets configuráveis; tarefas agendadas; delegação e plugins. | Separar memória de procedimentos, carregar instruções só quando necessárias e oferecer ferramentas por capacidade/permissão. | Não importar o runtime inteiro, todos os canais, plugins ou automações sem necessidade. |
| OpenClaw | Um Gateway centraliza sessões, roteamento e conexões dos canais; suporta agentes/sessões separados; diferencia sandbox, política de ferramentas e acesso elevado. | Manter um ponto central de controle e separar autenticação, autorização de ferramenta e ambiente de execução. | Não habilitar execução elevada nem abrir acesso multiusuário/canais indiscriminadamente. |
| NanoClaw | Processo host coordena sessões isoladas; cada sessão pode executar em contêiner com mounts explícitos e usuário sem privilégios; comunicação host/contêiner tem fronteiras definidas. | Usar isolamento por tarefa/sessão quando o N.E.X.U.S. ganhar execução de código ou acesso ampliado a arquivos. | Não exigir Docker para conversa normal, não montar todo o host e não replicar a arquitetura de duas bases por sessão sem necessidade comprovada. |

### 3.1 Hermes Agent

Padrões que merecem ser aproveitados:

- **Memória curada e limitada:** perfil do usuário e notas operacionais ficam separados; o restante é recuperado do histórico quando necessário. Isso evita injetar todo o passado em cada chamada.
- **Limites entre sessões:** sessões longas precisam de encerramento/resumo em momentos naturais para que a memória atualizada seja relida e o contexto não cresça indefinidamente.
- **Skills com divulgação progressiva:** primeiro listar nome/descrição; carregar o conteúdo completo apenas quando a tarefa exigir; abrir referências específicas quando necessário.
- **Delegação controlada:** subagentes possuem contexto e ferramentas próprios; isso é útil somente quando as tarefas são independentes e há limites explícitos.
- **Ferramentas organizadas por grupos:** capacidades podem ser ativadas/desativadas por ambiente ou tipo de agente.

Fontes oficiais:
- Visão geral: https://hermes-agent.nousresearch.com/docs/user-guide/features/overview
- Memória persistente: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Skills: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Segurança: https://hermes-agent.nousresearch.com/docs/user-guide/security
- Arquitetura: https://hermes-agent.nousresearch.com/docs/developer-guide/architecture

### 3.2 OpenClaw

Padrões que merecem ser aproveitados:

- **Gateway como fonte de verdade:** sessões, roteamento e conexões dos canais precisam ser controlados por um serviço central, não duplicados em cada integração.
- **Sessões e agentes isolados:** cada agente deve ter identidade, contexto e ferramentas definidos; um canal externo não deve ganhar privilégios por simplesmente conseguir enviar uma mensagem.
- **Três controles diferentes:** sandbox define onde a ferramenta executa; política define quais ferramentas podem ser chamadas; acesso elevado é uma exceção separada e restrita.
- **Pairing/allowlist:** mensageiros externos precisam autenticar o remetente antes de permitir comandos.

Fontes oficiais:
- Documentação e visão geral: https://docs.openclaw.ai/
- Diferença entre sandbox, política de ferramentas e acesso elevado: https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated
- Skills: https://docs.openclaw.ai/skills

### 3.3 NanoClaw

Padrões que merecem ser aproveitados:

- **Privilégio mínimo por sessão:** um contêiner enxerga somente os diretórios explicitamente montados para aquela sessão e não deve executar como root.
- **Separação host/agente:** o host controla roteamento, identidade e entrega; o processo do agente trabalha dentro de uma área limitada.
- **Entrada e saída explícitas:** mensagens e ações do agente são entregues por interfaces controladas, em vez de conceder acesso geral ao processo host.

A documentação de arquitetura do NanoClaw identifica algumas decisões como rascunho e alerta que o código-fonte é a referência final; por isso, o N.E.X.U.S. deve adotar os princípios de isolamento, não copiar detalhes de implementação sem auditoria.

Fontes:
- Repositório: https://github.com/nanocoai/nanoclaw
- Arquitetura: https://github.com/nanocoai/nanoclaw/blob/main/docs/architecture.md
- Modelo de segurança: https://github.com/nanocoai/nanoclaw/blob/main/docs/SECURITY.md

## 4. Arquitetura alvo recomendada

**NAVEGADOR / PWA / FUTUROS CANAIS**  
↓  
**GATEWAY N.E.X.U.S.** — autenticação, sessões, roteamento  
↓  
**ORQUESTRADOR PRINCIPAL** — plano tipado, estado, orçamento  
↓  
**ESPECIALISTAS** — pesquisa, análise e planejamento  
↓  
**REVISOR / VERIFICADOR** — fontes, evidências e incertezas  
↓  
**POLÍTICA CENTRAL** — allowlist, schemas e aprovação  
↓  
**TOOL REGISTRY** — execução somente de ferramentas cadastradas  
↓  
**EXECUTOR CONTROLADO** — serviço seguro ou sandbox isolado  
↓  
**DADOS** — memória, conhecimento, tarefas, fontes, skills e auditoria  
↓  
**WORKER OPCIONAL DO PC** — conexão de saída e jobs permitidos

### 4.1 Memória em quatro domínios

1. **Perfil:** preferências estáveis e instruções explícitas de interação, em formato curto e corrigível.
2. **Memória episódica:** eventos, conversas e decisões de projeto; recuperação por sessão/consulta, não despejo completo.
3. **Conhecimento semântico:** afirmações com fonte, trecho, data, estado e nível de confiança; só registros revisados/validados podem ser apresentados como conhecimento confirmado.
4. **Memória procedural (skills):** passos reutilizáveis para executar uma classe de tarefa. Skill não é fato, não é memória pessoal e não pode alterar permissões.

Toda escrita continua consentida e auditável. Conteúdo recuperado de arquivos, sites, mensagens e skills externas permanece dado não confiável; não pode sobrescrever instruções de sistema nem autorizar ferramentas.

### 4.2 Skills procedurais

Criar futuramente um registry próprio com:

- Manifesto: nome, descrição, versão, origem, requisitos, ferramentas permitidas e estado de revisão.
- Índice compacto disponível ao orquestrador.
- Carregamento do conteúdo completo somente quando a skill for selecionada.
- Referências adicionais lidas individualmente, evitando carregar uma biblioteca inteira.
- Estados draft, reviewed, approved, disabled e rejected.
- Alterações propostas pelo agente ficam em rascunho e exigem revisão antes de uso.
- Instalação de skills externas passa por auditoria de origem, licença, scripts, dependências, rede e permissões.

**Importante:** o catálogo docs/skills/ do repositório é inventário de skills de engenharia e pesquisa. Não o tratar automaticamente como catálogo de habilidades do produto N.E.X.U.S.; os dois usos precisam permanecer separados.

### 4.3 Chamada de ferramentas pelo modelo

Esta é a prioridade técnica mais importante.

Fluxo obrigatório:

1. O modelo devolve texto final ou uma solicitação estruturada de ferramenta.
2. O runtime valida o formato, o nome, o schema, o tamanho e a quantidade de chamadas.
3. O registry identifica a ferramenta e sua classe de risco.
4. A política permite, pede confirmação específica ou bloqueia.
5. A ferramenta executa com timeout, orçamento, contexto mínimo e idempotência quando aplicável.
6. O resultado é sanitizado e marcado como dado não confiável.
7. O runtime devolve o resultado ao modelo para continuação.
8. O ciclo termina ao obter resposta final ou atingir o limite; nunca há loop ilimitado.

Limites iniciais sugeridos: até 3 rodadas de ferramentas por turno, no máximo 4 chamadas por rodada, limite total de tempo/tokens/custo e cancelamento efetivo. Esses valores são parâmetros de segurança para benchmark, não garantias de qualidade.

A aprovação humana nunca pode vir do texto do modelo. Para ações SENSITIVE, a UI precisa mostrar ferramenta, parâmetros, conta/recurso afetado, consequência e dados que serão compartilhados; a confirmação deve ser específica e vinculada à execução.

### 4.4 Agentes especialistas reais

Evoluir os papéis existentes sem fingir que já são agentes independentes. Começar com três especialistas:

- **Researcher:** pesquisa e registra fontes; não valida fatos.
- **Analyst:** compara trechos, datas, divergências e incerteza.
- **Planner:** divide tarefas em passos tipados e verifica pré-condições.

O orquestrador principal mantém controle do fluxo. Cada tarefa delegada precisa declarar:

- parent_task_id, agent_id e operação;
- conjunto de dados/contexto que o agente pode acessar;
- ferramentas autorizadas;
- limite de passos, tokens, custo, tempo e concorrência;
- política de cancelamento e estado;
- resultado estruturado, fontes e erros.

O agente não pode ampliar sua própria lista de ferramentas, herdar segredos indiscriminadamente ou autorizar outro agente. Todas as ferramentas passam pela mesma política e auditoria. Um agente revisor independente deve avaliar sustentação de afirmações por trechos, não apenas a presença de referências.

### 4.5 Execução isolada

Não adicionar terminal irrestrito ao agente. Enquanto o N.E.X.U.S. não executar código, o registry de ferramentas seguras é suficiente.

Quando uma capacidade realmente exigir execução:

- serviço executor separado do processo web/API;
- contêiner não-root por tarefa ou sessão;
- diretório de trabalho temporário e mounts explícitos;
- sistema de arquivos base somente leitura quando possível;
- rede desabilitada por padrão e liberada por destino/caso de uso;
- limites de CPU, RAM, tempo, tamanho de saída e processos;
- nenhum acesso direto a .env, banco principal, diretório pessoal ou tokens;
- resultados validados e transferidos por um contrato tipado;
- exclusão do ambiente temporário após a tarefa, preservando somente artefatos aprovados.

Contêiner é uma fronteira adicional, não substituto de autenticação, autorização, validação de argumentos ou aprovação.

### 4.6 Gateway, canais e worker

- Manter API/gateway como única autoridade de identidade, sessão, roteamento e auditoria.
- Frontend web/PWA continua sendo o canal principal inicial.
- Adicionar mensageiros por adaptadores independentes, um de cada vez, depois de autenticação, pairing/allowlist, rate limit e isolamento de sessão.
- Não implementar todos os canais de uma vez; a escolha do primeiro mensageiro depende do uso real e das condições de privacidade/custo.
- Preservar a direção cloud-first já registrada em D-014: o core deve permanecer acessível com o PC desligado; o PC é worker opcional que inicia conexão autenticada de saída e recebe somente jobs allowlisted.
- Voz deve começar com push-to-talk; wake word e microfone sempre ativo ficam fora da prioridade.

### 4.7 Melhoria contínua controlada

O sistema pode aprender procedimentos e propor melhorias, mas não ativá-las sozinho:

- skill nova/alterada: rascunho → revisão → aprovação;
- melhoria de código: branch/workspace isolado → diff explícito → testes allowlisted → revisão → aprovação humana;
- alteração de permissões, credenciais, orçamento, modelo padrão, publicação e deploy: sempre sob controle do proprietário;
- guardar resultado dos testes e possibilidade de rollback;
- saída de um modelo nunca altera políticas, instala dependências ou concede permissões.

## 5. Ordem de implementação

| Ordem | Entrega | Critério de conclusão |
|---|---|---|
| 1 | Tool calling nativo com retorno de resultado | Um modelo chama uma ferramenta READ permitida, recebe o resultado e responde; chamadas inválidas, injeção, loops e orçamento excedido são bloqueados em testes. |
| 2 | Agentes especialistas tipados | Researcher, analyst e planner executam tarefas limitadas com logs, isolamento de contexto, orçamento e revisão. |
| 3 | Verificação de evidências | Revisor confronta afirmações com trechos, datas e fontes; divergências permanecem explícitas. |
| 4 | Skills procedurais com divulgação progressiva | O agente lista habilidades sem carregar todas; abre somente a skill necessária; alterações exigem aprovação. |
| 5 | Gateway cloud e adaptadores de canal | Sessões e identidade centralizadas; acesso remoto protegido; cada canal isolado e validado. |
| 6 | Executor isolado para tarefas específicas | Código/arquivos executados fora do processo web, com mounts, rede e recursos restritos. |
| 7 | Voz e melhoria controlada | Push-to-talk funcional; propostas de skills/código testadas e aprovadas antes de ativação. |

Não adiantar a etapa 5 ou 6 antes de fechar os controles da etapa 1. A autonomia é ampliada somente depois de demonstrar segurança e confiabilidade em testes.

## 6. Testes de aceitação obrigatórios

### Tool calling
- Ferramenta desconhecida, schema inválido e argumento excessivo são negados.
- Chamada SENSITIVE sem aprovação específica é bloqueada.
- Conteúdo externo com instruções maliciosas não altera o plano nem a política.
- Limite de rodadas, chamadas, tempo e orçamento encerra o ciclo corretamente.
- Resultado da ferramenta retorna ao modelo sem ser tratado como instrução confiável.
- Falha, timeout, cancelamento e repetição não duplicam efeitos colaterais.

### Agentes
- Especialista não acessa ferramentas/dados fora do envelope.
- Agente filho não consegue alterar o orçamento nem delegar privilégios.
- Cancelamento e timeout chegam a todos os trabalhos filhos.
- Concorrência respeita limite global e por agente.
- Reviewer detecta afirmação sem evidência, fonte única e contradição não resolvida.

### Skills
- Skill não utilizada não é carregada integralmente.
- Skill externa não revisada não é executada/ativada.
- Instruções de skill não podem mudar políticas, segredos ou permissões.
- Atualização/reversão preserva versão e trilha de auditoria.

### Gateway e sandbox
- Remetente não autorizado não cria ou controla sessões.
- Sessão de um usuário/agente não acessa estado de outra.
- Executor não enxerga arquivos do host fora dos mounts.
- Rede, processos, tempo, CPU/RAM e tamanho de saída são limitados.
- Falha do worker local não derruba o core cloud.

## 7. O que evitar

- Substituir o N.E.X.U.S. por Hermes/OpenClaw/NanoClaw ou adicionar o projeto inteiro como dependência.
- Rodar um LLM permanentemente em loop para parecer “sempre acordado”.
- Vincular a disponibilidade do assistente ao PC atual ligado 24 horas.
- Dar shell irrestrito ou acesso amplo ao sistema de arquivos ao modelo.
- Ativar dezenas de agentes paralelos sem independência real ou orçamento.
- Carregar todas as skills e memórias em todo prompt.
- Transformar resposta de IA, snippet ou uma única fonte em fato validado automaticamente.
- Instalar skill/plugin externo sem auditoria e sem revisão.
- Fazer fallback silencioso entre serviços com privacidade/custo diferentes.
- Confundir aprovação do usuário para uma etapa com autorização permanente para ações futuras.

## 8. Conclusão

A arquitetura atual do N.E.X.U.S. já aponta na direção correta: monólito modular, memória e conhecimento separados, roteamento com orçamento, ferramentas allowlisted, worker limitado e autonomia supervisionada.

A melhor melhoria agora não é mais um framework nem um canal: é completar o ciclo geral de ferramentas do modelo. Depois disso, agentes especialistas, skills procedurais e execução isolada podem ser adicionados em uma sequência verificável.

**Esta auditoria é uma proposta.** Não instala Hermes Agent, OpenClaw, NanoClaw, skills ou dependências; não ativa execução remota, não altera permissões e não afirma que as etapas propostas já estejam implementadas.
