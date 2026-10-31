# N.E.X.U.S. — Especificação do MVP executável

**Status:** proposta técnica para revisão; não é implementação.  
**Base:** arquitetura v1 e auditoria estática preliminar do OpenJarvis.

## 1. Objetivo verificável

Entregar a primeira fatia funcional do N.E.X.U.S.: o usuário envia uma mensagem, o sistema consulta um provedor de IA configurado, pode executar uma ferramenta de consulta explicitamente permitida, verifica o resultado e devolve resposta com registro da tarefa.

O MVP deve provar o caminho completo com segurança e custo controlado, não simular autonomia completa.

## 2. Dentro do escopo

- API backend autenticada.
- Interface textual simples e responsiva para navegador/celular.
- Um provedor de modelo inicialmente.
- Gateway de IA com timeout, limite de tokens e orçamento por tarefa.
- Um orquestrador, uma tarefa ativa por requisição e máximo de passos/turnos.
- Uma ferramenta READ allowlisted, sem escrita ou efeitos externos.
- Política de autorização determinística.
- Estado da tarefa e logs estruturados sem segredos.
- Testes unitários e de integração offline usando modelo/ferramenta simulados.

## 3. Fora do escopo

Voz, wake word, microfone permanente, agentes paralelos, contas de terceiros, envio de mensagens, compras, transações, exclusão, shell, execução de código, browser automatizado, MCP remoto, agendamento, execução proativa, memória vetorial, fine-tuning, autoedição de código e deploy automático.

## 4. Fluxo de execução

1. API autentica a sessão e valida tamanho/formato da mensagem.
2. Cria `task_id` e estado `received`.
3. Recupera apenas o contexto recente da conversa.
4. O modelo propõe resposta ou plano limitado.
5. Se houver pedido de ferramenta, o backend valida nome, schema, allowlist, permissão e orçamento.
6. Ferramenta READ executa com timeout e limite de resposta.
7. O resultado é marcado como dado externo não confiável e devolvido ao modelo como observação, nunca como instrução.
8. O sistema verifica se houve erro, limite excedido ou resposta vazia.
9. API registra resultado e estado terminal.
10. Interface mostra resposta e ID da tarefa.

Se houver ferramenta não permitida, tentativa de escrita, parâmetro inválido, timeout ou orçamento excedido, bloquear/parar e registrar o motivo.

## 5. Estados e contrato da tarefa

Estados permitidos:
`received` → `understanding` → `planned` → `running` → `verifying` → `completed`.

Estados alternativos:
`failed`, `cancelled`, `blocked`.

Campos mínimos persistidos:
- `task_id`: UUID;
- `session_id`: identificador da sessão autenticada;
- `status`: enum de estado;
- `created_at`, `updated_at`;
- `input_summary`: resumo curto ou conteúdo conforme política de retenção;
- `provider_id`, `model_id`;
- `steps_used`, `tokens_in`, `tokens_out` quando disponíveis;
- `estimated_cost` quando o provedor fornecer dados suficientes;
- `tool_events`: ferramenta, parâmetros sanitizados, resultado resumido e duração;
- `error_code`: código seguro, sem segredos.

Não guardar cadeia de pensamento privada do modelo. Registrar apenas plano operacional resumido, chamadas de ferramentas, decisões de política e resultados.

## 6. Contratos iniciais da API

### `POST /api/v1/tasks`
Entrada:
```json
{"message":"texto do usuário","session_id":"uuid opcional"}
```
Saída:
```json
{"task_id":"uuid","status":"received"}
```

### `GET /api/v1/tasks/{task_id}`
Retorna status, timestamps, resumo do resultado e erro seguro quando houver.

### `GET /api/v1/sessions/{session_id}/messages`
Retorna apenas mensagens pertencentes à sessão autenticada, com paginação limitada.

### `POST /api/v1/tasks/{task_id}/cancel`
Solicita cancelamento; não afirma que cancelou se a operação já terminou ou se a ferramenta não permite interrupção.

O contrato pode ser síncrono no primeiro protótipo, mas manter `task_id` e estados facilita evoluir para execução em background.

## 7. Componentes mínimos

- `api/`: rotas, autenticação e schemas HTTP.
- `core/`: configuração, estados, erros e limites.
- `orchestrator/`: fluxo de tarefa e validação dos planos.
- `providers/`: interface de modelo e um adaptador concreto.
- `tools/`: registry e uma ferramenta READ.
- `policy/`: allowlist, permissões e decisão de bloqueio.
- `storage/`: repositórios e migrações.
- `observability/`: logs e métricas mínimas.
- `tests/`: testes unitários, integração e adversariais.

A estrutura exata será ajustada depois de confirmar a compatibilidade do OpenJarvis local e escolher o provedor.

## 8. Dados e persistência

Proposta inicial: SQLite para desenvolvimento e primeiro protótipo, com interface de repositório para permitir PostgreSQL na hospedagem. Não adicionar vetor/embeddings no MVP.

Separar tabelas/coleções de:
- sessões;
- mensagens;
- tarefas;
- eventos de ferramenta;
- decisões de política.

Memória pessoal duradoura fica para fase posterior e não deve ser confundida com histórico de chat.

## 9. Segurança obrigatória

- Chaves somente no ambiente do backend/secret manager.
- HTTPS em hospedagem.
- Autenticação e autorização por sessão.
- Allowlist fechada de ferramentas.
- Validar schema e limites dos argumentos.
- Timeout, limite de tokens, passos e gasto.
- Limite de tamanho de entrada/saída e rate limiting.
- Conteúdo web/arquivo/ferramenta é não confiável.
- Não habilitar shell, escrita, MCP ou ferramentas sensíveis.
- Não persistir segredos, cookies ou dados pessoais desnecessários.
- Logs sem prompt privado completo por padrão.
- Cancelamento e falha fecham a tarefa em estado terminal.

## 10. Stack candidata, ainda não decisão final

- Backend: Python + FastAPI, por compatibilidade com o ecossistema OpenJarvis e facilidade de integração.
- Validação de dados: Pydantic.
- Testes: pytest.
- Persistência inicial: SQLite.
- Interface: página web responsiva pequena; reaproveitar React/Vite somente se a auditoria local justificar.
- Modelo: um provedor cloud selecionado após comparar preço, qualidade em português, limites e política de dados.
- Ollama: opcional e fora do caminho obrigatório do MVP.
- Execução local: mocks e serviços mínimos; não exigir modelo local.

## 11. Testes de aceitação

1. Mensagem válida produz tarefa e resposta com modelo simulado.
2. Erro do provedor produz `failed` sem expor segredo.
3. Timeout encerra a tarefa.
4. Ferramenta READ permitida recebe apenas argumentos válidos.
5. Ferramenta fora da allowlist é bloqueada.
6. Tentativa de chamada com parâmetros extras/inválidos é bloqueada.
7. Resposta de ferramenta com prompt injection não altera política nem concede permissões.
8. Orquestrador não ultrapassa máximo de turnos/passos.
9. Cancelamento impede próximos passos quando possível.
10. Sessão A não acessa tarefas/mensagens da sessão B.
11. Orçamento esgotado bloqueia nova chamada de modelo.
12. Logs não contêm API keys, cookies ou cabeçalhos de autorização.

## 12. Critério de pronto

O MVP só é considerado pronto quando os testes 1–12 passam, uma execução manual de ponta a ponta é demonstrada, os custos estimados são apresentados e nenhum segredo/dado privado aparece nos logs ou no repositório.

## 13. Bloqueios antes da implementação

- Auditoria local do checkout OpenJarvis pretendido, sem modificar upstream.
- Decidir se algum componente será importado como dependência, copiado/adaptado com atribuição ou apenas usado como referência.
- Escolher provedor cloud e avaliar custo/privacidade.
- Definir autenticação e hospedagem.
- Confirmar stack disponível no PC e requisitos mínimos.

---

**Próxima ação:** validar a auditoria local do OpenJarvis no PC e fechar as decisões pendentes do MVP. Não instalar o conjunto completo nem iniciar serviços com credenciais nesta fase.
