# N.E.X.U.S. — Backlog técnico de implementação

**Data da revisão:** 2026-10-31  
**Escopo:** revisão somente do repositório N.E.X.U.S.; não inclui Nexus Finance nem outros projetos.

Este documento é o plano operacional derivado do código e da documentação existentes. Ele separa o que está no repositório do que ainda depende de escolhas, credenciais ou execução no computador.

## 1. Estado verificado no código

| Área | Evidência no repositório | Estado real |
|---|---|---|
| Persistência | `nexus_learning/engine.py` | SQLite para memórias, fontes, afirmações, tarefas e auditoria |
| Ingestão | `nexus_learning/ingestion.py` | TXT/Markdown, hash, chunks e busca lexical; sem PDF, OCR ou embeddings |
| Pesquisa | `nexus_learning/crossref.py` | Metadados bibliográficos da Crossref; não baixa artigos nem valida afirmações |
| Política | `nexus_learning/policy.py` | Allowlist fail-closed para READ, WRITE_REVERSIBLE e SENSITIVE |
| Runtime | `nexus_learning/runtime.py` | Uma tarefa textual por vez usando um provider; sem ferramentas executáveis |
| Providers | `nexus_learning/providers/` | Contrato e MockProvider offline; nenhum provider remoto implementado |
| CLI | `nexus_learning/__main__.py` | Comandos locais de memória, fontes, afirmações, tarefas, ingestão, pesquisa e demonstração offline |
| Testes | `tests/` | unittest; execução CI anterior confirmada em Python 3.11 e 3.12 |
| API/web | Não existe implementação correspondente no tree atual | Pendente |
| Cloud/worker | Não existe implementação correspondente no tree atual | Pendente |

## 2. Endurecimento aplicado nesta revisão

- Corrigido o modo SQLite `:memory:`: como o engine abre conexões curtas por operação, agora usa uma URI SQLite compartilhada com uma conexão âncora para manter o banco em memória vivo.
- Adicionado `LearningEngine.close()` para liberar a conexão âncora desse modo.
- O runtime agora reivindica uma tarefa com transação de escrita e atualização condicional. Uma tarefa que já está `running` não deve ser iniciada novamente por outra chamada.
- Mensagens de exceção do provider deixaram de ser persistidas literalmente. Elas podem conter URLs, cabeçalhos ou credenciais; o banco guarda um resumo seguro e o tipo da exceção.
- O runtime valida limites de entrada/saída e os campos essenciais do retorno do provider.
- Adicionados testes de regressão para banco em memória, reentrada da mesma tarefa, vazamento de mensagem sensível e limites inválidos.
- Corrigido o filtro de paths do workflow; agora ele observa o arquivo de workflow real. Adicionadas permissões mínimas, timeout e compilação antes da suíte de testes.

**Estado de validação desta revisão:** as alterações foram gravadas no GitHub. A execução de CI disparada por estas mudanças precisa ser conferida antes de declarar os novos testes aprovados. Não foi possível executar o checkout local neste ambiente.

## 3. Próximo marco recomendado — primeira conversa com IA real

Não implementar um provider por adivinhação. Antes, escolher o provedor e verificar seu protocolo, termos, limites, preço e política de dados.

### Tarefas

1. Definir a interface de configuração por ambiente, sem segredos no repositório.
2. Implementar um adaptador remoto atrás de `ModelProvider`.
3. Normalizar erros de autenticação, rate limit, timeout, indisponibilidade e resposta malformada.
4. Registrar provedor/modelo e uso de tokens somente quando reportado pela API.
5. Manter MockProvider como padrão de testes e modo sem internet.
6. Testar respostas vazias, falhas, limites e ausência de credencial.
7. Não adicionar fallback automático para outro fornecedor sem consentimento e regras de custo/privacidade.

### Critérios de aceite

- A aplicação continua funcionando sem chave e sem internet usando MockProvider.
- Segredos vêm do ambiente/secret store e nunca aparecem em logs, exceções persistidas ou Git.
- Timeout e rate limit resultam em falha controlada.
- O adaptador não executa ferramentas; devolve somente dados do modelo.
- Testes offline passam e um teste real é executado localmente pelo usuário com sua própria chave, sem compartilhá-la.

## 4. Próximo marco — API autenticada mínima

A especificação de endpoints está em `docs/MVP_SPEC.md`. Antes de codificar:
- confirmar framework e versão suportada pelo PC;
- escolher autenticação de usuário único;
- definir armazenamento de sessão e expiração;
- definir limites de requisição e tamanho do corpo;
- decidir onde ficará o backend e como guardar segredos.

Implementação inicial limitada:
- `POST /api/v1/tasks`;
- `GET /api/v1/tasks/{task_id}`;
- `GET /api/v1/sessions/{session_id}/messages`;
- `POST /api/v1/tasks/{task_id}/cancel`.

A API não pode confiar em `session_id` enviado pelo cliente sem verificar a titularidade. Toda consulta deve ser vinculada à identidade autenticada. Não expor SQLite, painel administrativo ou worker sem autenticação.

## 5. Próximo marco — memória na conversa

A memória já é persistida, mas ainda não é recuperada automaticamente pelo runtime de conversa.

Implementar somente depois de definir:
- quais memórias podem entrar no contexto;
- limite de caracteres/tokens por memória;
- regra de relevância;
- expiração e correção;
- consentimento para salvar fatos pessoais;
- como separar memória pessoal de conhecimento com fontes.

Critérios:
- contexto mínimo e limitado;
- memória arquivada nunca é recuperada;
- nenhuma memória é gravada automaticamente sem uma regra explícita;
- fontes e estado de validação acompanham conhecimento pesquisado;
- texto recuperado é dado, não instrução de sistema.

## 6. Próximo marco — worker do PC e nuvem

A arquitetura cloud + PC está documentada em `ARCHITECTURE.md` e D-014. O worker só deve começar depois que houver API autenticada e contrato de tarefas.

Requisitos mínimos:
- conexão de saída autenticada iniciada pelo worker;
- nunca abrir shell remoto ou porta pública de entrada;
- tipos de tarefa em allowlist;
- lease/expiração para evitar dois workers executarem a mesma tarefa;
- idempotência e retry limitado;
- heartbeat, cancelamento e estado `waiting_for_pc`;
- tamanho máximo de entrada/saída e limites de CPU/RAM;
- sincronização versionada, sem sobrescrever silenciosamente;
- fila local quando o PC estiver offline.

## 7. Decisões que continuam pendentes

| Decisão | Por que não foi escolhida automaticamente |
|---|---|
| Provedor de IA inicial | Afeta preço, quotas, privacidade, protocolo e disponibilidade em português |
| Hospedagem cloud | Plano gratuito pode ter suspensão, limites e armazenamento efêmero |
| Autenticação | Precisa proteger sessões e acesso remoto de um único usuário |
| Frontend | Reaproveitar UI existente (se houver em outro checkout) ou iniciar uma página web leve |
| Política de retenção | Define quanto tempo conversas, logs e memórias permanecem armazenados |
| Execução de testes no PC | Precisa confirmar ambiente, Python e consumo real no equipamento |

Nenhuma chave, cartão, domínio ou serviço pago deve ser presumido. A meta de custo obrigatório zero continua como objetivo, não como garantia de disponibilidade gratuita ilimitada.

## 8. Ordem recomendada para o Codex

1. Conferir a branch e o estado de trabalho local antes de editar.
2. Ler `AGENTS.md`, `CODEX_HANDOFF.md`, `PROJECT_STATUS.md` e este backlog.
3. Executar compileall e unittest; registrar resultados literais.
4. Corrigir regressões sem substituir o núcleo existente.
5. Implementar somente um adaptador de provider após o provedor ser escolhido.
6. Criar API/auth antes de qualquer worker remoto.
7. Integrar memória com testes de privacidade e isolamento.
8. Só então iniciar UI, worker e sincronização.

**Regra de conclusão:** nenhuma etapa é considerada concluída por existir documentação. Exigir código, teste executado e evidência de funcionamento.
