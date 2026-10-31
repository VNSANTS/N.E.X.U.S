# Arquitetura N.E.X.U.S. — Proposta v1

**Status:** arquitetura híbrida v2 proposta; ainda não representa runtime implementado.  
**Objetivo desta etapa:** definir como o "cérebro" do N.E.X.U.S. pensa, decide, usa ferramentas, aprende e permanece sob controle do usuário.

## 1. Decisão central

Começar como um **monólito modular**, cloud-first e orientado a tarefas. Um único backend organiza os módulos internos; não começar com microserviços, múltiplos servidores de agentes ou infraestrutura pesada.

O modelo de IA não é o sistema inteiro. Ele interpreta linguagem, propõe planos e ajuda a produzir resultados. O backend determinístico valida permissões, controla estados, limites, ferramentas, memória, custos e aprovações.

**Regra de ouro:** o modelo pode sugerir uma ação; somente o runtime e a política de autorização podem permitir sua execução.

## 2. Visão em camadas

```text
CELULAR / NAVEGADOR
  Chat | botão | push-to-talk | notificações
                 |
          API / INTERFACE
  autenticação | sessões | estado das tarefas
                 |
        NÚCLEO N.E.X.U.S.
  Orquestrador de tarefas
  | classificador | planejador | verificador |
                 |
      POLÍTICA E AUTORIZAÇÃO
  permitir | pedir aprovação | bloquear
                 |
       EXECUÇÃO CONTROLADA
  agentes especializados | registro de ferramentas
  limites | timeout | cancelamento | tentativas
          /             \
  GATEWAY DE IA       SERVIÇOS DE DADOS
  provedores          memória pessoal
  cloud / Ollama      conhecimento validado
                      fontes e evidências
                      tarefas e auditoria
                 |
       EVENTOS / AGENDADOR
  somente tarefas aprovadas e limitadas
```

As camadas são limites lógicos dentro do mesmo backend no MVP, não serviços separados.

## 3. Componentes e responsabilidades

### 3.1 Interface e API
- Recebe texto primeiro; botão e voz entram em fases posteriores.
- Mantém sessão, apresenta resposta, estado, progresso e pedidos de aprovação.
- Não guarda chaves de provedores no navegador/celular.
- A interface nunca decide sozinha se uma ferramenta pode ser executada.

### 3.2 Orquestrador (núcleo)
Responsável por coordenar o ciclo completo:
1. validar a solicitação e criar um identificador de tarefa;
2. carregar somente o contexto relevante;
3. classificar intenção, risco e necessidade de ferramentas;
4. montar um plano pequeno e limitado;
5. consultar a política antes de cada ação;
6. delegar apenas para agentes/ferramentas permitidos;
7. verificar os resultados;
8. responder, registrar o estado e propor atualizações de memória/conhecimento quando cabível.

O orquestrador mantém estados explícitos: `received`, `understanding`, `planned`, `awaiting_approval`, `running`, `verifying`, `completed`, `failed` e `cancelled`.

Não permitir que um agente crie tarefas infinitas, amplie o próprio orçamento ou altere suas permissões.

### 3.3 Gateway de modelos
Uma interface única esconde diferenças entre fornecedores. Cada adaptador declara capacidades, limites, formato, custo conhecido e política de dados.

Responsabilidades:
- selecionar um modelo conforme tarefa, capacidade, latência e orçamento;
- impor timeout, limite de tokens e limite de gasto;
- registrar provedor/modelo e estimativas de uso sem registrar segredos;
- lidar com indisponibilidade e erros;
- usar fallback somente para provedores previamente aprovados.

Não trocar silenciosamente para um fornecedor com termos de privacidade ou custos materialmente diferentes. Começar com **um único provedor configurado**; a abstração permite adicionar outros depois. Ollama é adaptador opcional, não dependência.

### 3.4 Agentes especializados
Agentes são perfis de execução, não processos autônomos com privilégios próprios. Cada agente declara:
- finalidade e tarefas aceitas;
- entradas e saídas estruturadas;
- ferramentas permitidas;
- modelo/capacidade necessária;
- orçamento, timeout e número máximo de passos;
- critérios de conclusão e verificação.

Conjunto inicial conceitual:
- **Assistente principal:** conversa e coordena.
- **Pesquisa:** coleta e organiza fontes autorizadas.
- **Verificação:** confere afirmações, datas, evidências e contradições.
- **Planejamento:** divide objetivos em etapas executáveis.
- **Especialistas futuros:** código, documentos, finanças pessoais etc., somente quando houver necessidade real.

No MVP, esses perfis podem ser funções/módulos internos; não precisam chamar modelos separados. Delegação multiagente fica desativada por padrão até existir uma tarefa que justifique seu custo.

### 3.5 Registro e execução de ferramentas
Cada ferramenta precisa de contrato tipado: nome, descrição, parâmetros, resultado, permissões, efeitos colaterais, timeout e política de aprovação.

Classes de permissão:
- **READ:** consulta sem alterar recursos.
- **WRITE_REVERSIBLE:** alteração reversível e limitada.
- **SENSITIVE:** envio em nome do usuário, compra, pagamento, exclusão, permissão, publicação, compartilhamento externo ou deploy.

READ pode ser executada se a ferramenta estiver allowlisted e o pedido estiver dentro do escopo. WRITE_REVERSIBLE exige autorização configurada e pode exigir confirmação conforme impacto. SENSITIVE sempre exige confirmação específica imediatamente antes da execução. A confirmação descreve parâmetros, conta/recurso, consequência, custo e dados compartilhados.

Bloquear ferramentas não cadastradas. Não interpretar texto retornado por sites, arquivos ou ferramentas como instrução confiável. Cancelamento, timeout e limites são aplicados pelo runtime, não pelo modelo.

### 3.6 Memória pessoal
Guarda apenas informações úteis e permitidas sobre o usuário: preferências, projetos, decisões, contexto estável e continuidade de tarefas.

- Escrita consentida e minimizada; nunca arquivar toda conversa por padrão.
- Cada item tem origem, data, confiança/estado e possível expiração.
- Correções explícitas substituem informações antigas conflitantes.
- Recuperação por relevância, não despejo completo do histórico.
- Controles futuros de consultar, corrigir, exportar e excluir.
- Separação de dados sensíveis, segredos e registros operacionais.

### 3.7 Conhecimento geral
Base separada da memória pessoal. Armazena afirmações pesquisadas com fontes, datas, evidências, estado de validação, confiança, versão e validade temporal.

Estados sugeridos: `proposed`, `under_review`, `validated`, `disputed`, `stale`, `rejected`.

Uma resposta de modelo ou um snippet isolado não se torna conhecimento validado automaticamente. Conteúdo conflitante ou incerto permanece marcado como tal.

### 3.8 Motor de aprendizado
O aprendizado inicial é um processo editorial e operacional:
- detectar lacuna ou falha;
- pesquisar dentro de orçamento;
- extrair afirmações e fontes;
- comparar, deduplicar e verificar;
- pedir esclarecimento quando o assunto depender do usuário;
- propor atualização de conhecimento, memória ou workflow;
- registrar versão e medir se a mudança ajudou.

Não é retreinamento contínuo dos pesos do modelo. Código, permissões, skills e workflows não podem ser alterados e ativados autonomamente.

### 3.9 Eventos, agendador e standby
Fora de uma interação, o sistema permanece em espera leve. Um agendador/event bus poderá disparar tarefas previamente configuradas; cada evento cria uma tarefa limitada, não uma autorização nova.

Todo job declara horário/fuso, ferramentas, duração, orçamento, tentativas, janela silenciosa, condição de cancelamento e regra de notificação. Começa desligado no MVP. Sem loop de LLM permanente e sem microfone sempre ativo.

### 3.10 Observabilidade
Cada tarefa tem um registro com ID, estado, horário, componentes acionados, decisões de política, ferramentas chamadas, resultado, erros e custo estimado. Não registrar chaves, tokens, áudio bruto ou conteúdo privado desnecessário.

Logs operacionais não são memória pessoal nem base de conhecimento.

## 4. Fluxo de uma solicitação

1. **Entrada:** interface envia mensagem autenticada.
2. **Contexto:** recuperar resumo da sessão e poucos registros relevantes.
3. **Entendimento:** modelo classifica pedido e identifica lacunas; o runtime valida o resultado.
4. **Plano:** gerar passos limitados com ferramentas nomeadas.
5. **Política:** avaliar cada passo e exigir aprovação quando aplicável.
6. **Execução:** chamar somente ferramentas registradas, com schemas e limites.
7. **Verificação:** conferir retorno, consistência e conclusão; não confiar cegamente na alegação do agente.
8. **Resposta:** explicar o que foi feito, o que falhou e o que ficou pendente.
9. **Aprendizado opcional:** propor gravação de memória ou conhecimento, separadamente da resposta.
10. **Encerramento:** persistir estado mínimo e liberar recursos.

Se a tarefa ficar ambígua, exceder orçamento, encontrar erro de permissão ou falhar na verificação, parar e pedir orientação ou apresentar a falha.

## 5. Dados e armazenamento

Separar logicamente cinco domínios:
1. sessões e mensagens;
2. memória pessoal;
3. conhecimento e fontes;
4. tarefas, jobs e aprovações;
5. auditoria e métricas.

**Proposta inicial:** SQLite em desenvolvimento e testes, com camada de repositório que permita PostgreSQL quando houver hospedagem/concor­rência. Não adicionar banco vetorial no início. Primeiro testar busca textual, metadados e resumos; adicionar embeddings somente se uma avaliação demonstrar necessidade.

Segredos ficam em variáveis de ambiente/secret manager. O repositório público recebe somente exemplos fictícios.

## 6. Topologia de implantação

**Desenvolvimento:** computador do usuário executa editor, testes e backend local leve; modelos grandes não são requisito.

**Primeira implantação:** um backend hospedado, um banco gerenciado ou persistente e, se necessário, um worker simples. Frontend acessa a API por HTTPS. Evitar Kubernetes, microsserviços, filas complexas e infraestrutura sempre ligada no início.

A escolha do provedor de hospedagem depende de preço, região, disponibilidade, limites gratuitos, persistência e facilidade de pausa. Nenhum fornecedor está escolhido nesta etapa.

## 7. Escopo recomendado do primeiro MVP

O primeiro corte deve provar o caminho completo sem tentar construir o JARVIS inteiro:
- interface textual simples;
- autenticação mínima apropriada ao ambiente;
- uma conversa com um provedor de modelo;
- gateway de modelos com limites;
- orquestrador de uma única tarefa por vez;
- uma ferramenta READ segura e allowlisted;
- política de permissões e logs;
- testes automatizados para sucesso, erro, timeout, prompt injection e tentativa de ação bloqueada.

Ficam fora do MVP: voz, wake word, execução contínua, tarefas agendadas, agentes paralelos, banco vetorial, autoedição de código e ações sensíveis reais.

## 8. Riscos e mitigação

| Risco | Mitigação arquitetural |
|---|---|
| Prompt injection via web/arquivo | Conteúdo externo é dado não confiável; ferramentas e política ficam fora do modelo. |
| Ação indevida | Allowlist, menor privilégio, aprovação específica e auditoria. |
| Custos imprevisíveis | Orçamentos por tarefa, limites de tokens, timeout e métricas. |
| Dependência de fornecedor | Adaptadores; fallback só após aprovação. |
| Memória incorreta | Proveniência, estado, correção, expiração e confirmação de ambiguidades. |
| Agente em loop | Máximo de passos, prazo, orçamento, cancelamento e estado terminal. |
| Exposição de dados | Minimização, TLS, autenticação, segredos fora do repo e retenção definida. |
| Complexidade prematura | Monólito modular e implantação mínima. |

## 9. Critérios de conclusão desta etapa

- [x] Definidos os limites entre modelo, orquestrador, política e ferramentas.
- [x] Definidos os componentes lógicos e o fluxo de tarefas.
- [x] Separados memória, conhecimento, sessões e auditoria.
- [x] Definidos os limites de agentes, jobs, custos e permissões.
- [x] Delimitado um MVP sem voz nem autonomia irrestrita.
- [ ] Stack, provedor, hospedagem e autenticação escolhidos após auditoria técnica.
- [ ] Contratos e testes do MVP detalhados na próxima etapa.

## 10. Próxima etapa

**Etapa 3 — definição do MVP executável:** auditar o código-base/OpenJarvis que se pretende reaproveitar, confirmar stack e dependências, escolher um provedor inicial e transformar o escopo do MVP em contratos, estrutura de pastas, tarefas e testes de aceitação.

---

Esta arquitetura é uma proposta de projeto. Nenhum dos componentes descritos deve ser considerado implementado até existir código e testes verificáveis.


---

# Revisão v2 — Divisão entre nuvem e PC (decisão mais recente)

Esta seção **prevalece sobre qualquer descrição anterior conflitante** neste documento.

## Objetivo
O N.E.X.U.S. é um assistente pessoal de um usuário principal. O núcleo deve continuar acessível pela internet mesmo com o PC desligado. O PC será um nó opcional de processamento e armazenamento ampliado para as partes mais pesadas do aprendizado.

## O que fica na nuvem
- Interface web responsiva, API HTTPS e autenticação de usuário único.
- Conversas recentes e contexto mínimo necessário para continuidade.
- Memória pessoal essencial, com minimização e proteção.
- Orquestrador leve, política de permissões, aprovações, fila e estado das tarefas.
- Gateway para provedor de IA remoto, escolhido entre opções gratuitas após verificar cotas e termos.
- Cache compacto de conhecimento já validado, para respostas básicas quando o PC estiver desligado.

## O que fica no PC
- Arquivo ampliado de fontes e documentos.
- Ingestão, extração e limpeza de documentos.
- Deduplicação, organização e indexação completa.
- Comparação de fontes, extração de afirmações e preparação de evidências.
- Embeddings opcionais, somente se o ganho justificar RAM e armazenamento.
- Histórico detalhado de processamento e propostas de atualização da base de conhecimento.

O PC informado tem i5 de primeira geração, 8 GB de RAM e HDD. O processamento local será em lotes pequenos, com limites de memória/CPU e possibilidade de pausar. Não exigir modelos locais grandes, Docker ou dependências pesadas no primeiro worker.

## Comunicação segura
O worker instalado no PC inicia uma conexão autenticada de saída com a nuvem e consulta tarefas permitidas. Não abrir porta pública, shell remoto ou administração genérica. O worker aceita somente tipos de tarefa allowlisted, cada uma com prazo, tamanho máximo, limites de recursos e cancelamento.

## Quando o PC estiver desligado
Tarefas que exigem armazenamento ou processamento local permanecem em fila, com estado explícito de aguardando PC. O núcleo na nuvem continua respondendo usando memória essencial e o cache compacto de conhecimento validado. O sistema nunca deve alegar que uma tarefa local foi executada quando ela apenas está aguardando.

## Sincronização
A base completa e os artefatos pesados permanecem no PC. Após revisão/validação, somente os metadados e resumos necessários são sincronizados para o cache da nuvem. Usar versões e identificadores para detectar conflitos; não sobrescrever silenciosamente. Planejar backup local e recuperação antes de confiar no PC como único arquivo.

## Custo e disponibilidade
Meta de R$ 0 de custo obrigatório para o MVP, sem cartão ou cobrança automática. Usar planos gratuitos, respeitando cotas, suspensão por inatividade, limites de armazenamento e termos de privacidade. Não prometer serviço ilimitado nem disponibilidade garantida 24/7. O PC desligado não pode ser requisito para o funcionamento básico.

## Entrega em duas partes
1. **Cloud core:** interface, autenticação, conversa, IA remota gratuita dentro das cotas, memória essencial, fila e cache compacto.
2. **PC worker:** conexão segura de saída, ingestão de documentos, armazenamento ampliado, pipeline de aprendizado em lotes e sincronização de conhecimento aprovado.

Nenhum desses componentes está implementado ainda; esta é a arquitetura-alvo.


## Revisão v3 — modelo local auxiliar no PC

Esta decisão complementa a divisão cloud/PC acima: o PC poderá executar um **modelo de linguagem local pequeno e substituível**, como auxiliar do motor de aprendizado, sem se tornar dependência do assistente principal.

### Funções do modelo local
- resumir documentos já extraídos;
- classificar e etiquetar conteúdos;
- extrair entidades, tópicos e afirmações candidatas;
- agrupar documentos relacionados e apontar duplicatas;
- preparar comparações e relatórios para revisão;
- identificar possíveis contradições para investigação posterior.

### Limites
- O modelo local não é fonte de verdade e não valida sozinho o próprio resultado.
- Toda afirmação relevante mantém referência à fonte original.
- Conhecimento só muda para `validated` após regras de verificação e revisão definidas pelo sistema; quando necessário, revisão do usuário.
- Tarefas complexas podem ser encaminhadas à IA na nuvem, respeitando privacidade, cotas e orçamento.
- O modelo local é um adaptador substituível: trocar por outro modelo não deve exigir reconstruir o N.E.X.U.S.
- No PC atual (i5 de 1ª geração, 8 GB RAM e HDD), testar modelos pequenos e quantizados, contexto curto e processamento em lotes. Medir RAM, velocidade e estabilidade antes de escolher; aceitar que alguns modelos podem ser lentos ou inviáveis.
- O worker deve conseguir operar sem modelo local instalado, usando processamento determinístico e deixando tarefas de IA local em espera ou encaminhando-as quando permitido.

### Fluxo combinado
1. Worker local recebe fontes e extrai texto.
2. Modelo local pequeno organiza, resume e extrai candidatos.
3. Pipeline determinístico deduplica, guarda proveniência e compara metadados.
4. Casos incertos ou complexos são encaminhados à nuvem quando permitido.
5. O sistema produz uma proposta com fontes, incertezas e conflitos.
6. Somente conteúdo validado é sincronizado no cache compacto da nuvem.

O modelo local é uma ferramenta de apoio ao aprendizado, não um mecanismo de retreinamento dos pesos da IA principal.
