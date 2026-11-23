# Pesquisa de candidato: F.R.I.D.A.Y (saravanaspar)

**Data:** 2026-11-23  
**Origem do achado:** captura enviada pelo usuário de uma postagem sobre `saravanaspar/F.R.I.D.A.Y`.  
**Upstream:** https://github.com/saravanaspar/F.R.I.D.A.Y  
**Fonte principal consultada:** resultado indexado do README https://github.com/saravanaspar/F.R.I.D.A.Y e documento técnico https://github.com/saravanaspar/F.R.I.D.A.Y/blob/main/docs/PLUGIN_DEVELOPMENT.md

## Estado da verificação

**ATENÇÃO:** a consulta direta ao repositório via integração GitHub retornou HTTP 404 e a abertura da raiz pelo navegador também falhou na data da pesquisa. Resultados de busca ainda continham documentação indexada. Portanto, foram examinadas **páginas indexadas e documento de desenvolvimento de plugins**, sem árvore completa, sem acesso garantido ao HEAD e sem teste de execução. Tratar metadados como licença, suporte e funcionalidades como *informações declaradas na documentação recuperada*, que precisam ser reconfirmadas no upstream quando acessível. Não importar código indisponível nem fingir que foi auditado.

## O que o projeto descreve

- Assistente pessoal local-first/autohospedado com sessões duráveis, memória, agendamento, canais, ferramentas, plugins tipados, MCP, cofre de credenciais, permissões e recuperação.
- Recuperação de tarefas após falha/reinicialização, operações idempotentes e rastreamento dos efeitos externos.
- "Self-extension" controlada: procurar ações/plugins/MCP existentes -> confirmar capacidade exata -> verificar se o recurso ausente é realmente necessário -> autorização explícita -> branch/worktree isolada -> avaliações -> promoção com rollback e handoff autenticado.
- Arquitetura de **plugins com contratos de capacidades**, importação por interfaces públicas e verificações automáticas de arquitetura.
- Vault criptografado, credenciais fora de argumentos do modelo e logs; autenticação baseada em identidade confiável de canais; sandbox de execução com rede de saída não autorizada por padrão.
- Memória SQLite com busca híbrida, tarefas persistentes e limites de gastos por projeto/dia segundo documentação.
- **Atenção Windows:** documentação afirma que Windows deve executar no **WSL2** por limitações de garantias de permissões POSIX; Windows nativo ainda não é a opção endurecida. Requer Node.js 22.22.2 para o build descrito. Apps desktop e Android aparecem em direção/roadmap, não assumir que já funcionam.
- Licença **MIT** declarada no README indexado; antes de copiar confirmar arquivo LICENSE e notices/ACKNOWLEDGEMENTS do repositório atual.

## Comparação e potencial reaproveitamento para NEXUS MARK LVII

| Área | MARK LVII no snapshot anterior | Padrão F.R.I.D.A.Y a estudar | Decisão |
| --- | --- | --- | --- |
| Controle direto do PC | PyQt6, mouse, apps, tela, navegador | Agent runtime e canais, desktop ainda em evolução | **Preservar MARK** |
| Plugins | Python `exec_module` durante descoberta, sem manifesto estático pré-import | Define capabilities/contributions/hooks tipados, verificações em CI | **P1: adaptar ideia** |
| Aprovações | HUD confirma ações, mas cobertura geral requer testes | Permission broker e principal confiável separado do texto do modelo | **P1: adaptar política** |
| Segredos | `api_keys.json` em texto simples | Vault criptografado com referências opacas e redaction | **P1: alta relevância** |
| Tarefas | Background limitado com separação web/memória | Sessões e jobs duráveis com recovery e idempotência | **P2: avaliar** |
| Memória | JSON, busca e limite de tamanho | SQLite híbrido e memória delimitada | **P2: comparar após correção de atomic write** |
| Autodesenvolvimento | dev_agent instala e executa código | Reuse-first, MCP verificado, worktree, gates, rollback, handoff | **P2: padrão de segurança** |
| Dispositivos | Painel remoto e telefone envia áudio | Canais e client protocol descritos; apps futuros | **Não substituir Companion** |
| Custo de execução | Gemini e API compatível, controles a endurecer | Limites por projeto e medição de uso declarados | **P1: estudar budget** |

## Detalhes úteis da documentação de plugins

O documento `docs/PLUGIN_DEVELOPMENT.md` declara:
- Contrato explícito `requires`, `optional`, `provides` e superfícies públicas.
- Plugins sem credenciais devem iniciar com status `unconfigured`/ `auth-required`, sem exigir segredos em bootstrap.
- Acesso à rede exige permissão explícita `network: true` e o ambiente isolado normalmente começa sem egress.
- Saídas de páginas web, arquivos, OCR e ferramentas são marcadas como **untrusted-data**, não como políticas do sistema.
- Operações com efeito externo: persistir admissão -> executar -> persistir resultado e idempotência -> confirmar ao usuário.
- Testes incluem instalação sem configuração, redaction, recuperação, permissões, limpeza de recursos, regressão arquitetural.

## Melhorias candidatas / histórias de implementação

### FRI-001 — Cofre de credenciais
Problema: chaves locais em JSON. Avaliar Credential Manager no Windows ou Vault com proteção de chave por usuário, migração sem apagar dados, APIs que entregam segredo apenas ao processo autorizado. **Aceite:** segredo não aparece em logs, prompt, Git ou relatório de erro.

### FRI-002 — Contrato e autorização de plugins
Problema: importar Python pode executar side effects. Manifesto estático por plugin com lista de ferramentas/capacidades, leitura antes de import, revisão de origem e allowlist. **Aceite:** plugin desconhecido não executa durante descoberta; permissões default deny.

### FRI-003 — Aprimoramento verificável sem autoedição irrestrita
Ciclo: buscar recurso existente / MCP -> provar compatibilidade -> aprovação -> workspace isolado -> build/test/security scan -> diff -> usuário aprova promoção -> rollback -> smoke test. **Aceite:** o assistente nunca modifica seus próprios controles de segurança ou código de produção silenciosamente.

### FRI-004 — Persistência de tarefas e confirmação
Guardar IDs, estados, leases, tentativas, limites e resultado; idempotência para evitar ações duplicadas após reiniciar. **Aceite:** tarefa retomada sem novo envio duplicado e com status coerente.

### FRI-005 — Orçamento por provider
Cotas e limites em unidades e moeda quando suportado; bloquear fallback pago. **Aceite:** sem chave/sem cota, resposta segura, sem gasto acidental.

## Restrições e decisão

- **NÃO** mudar a base para F.R.I.D.A.Y. agora. MARK LVII segue como base desktop candidata, e a fase 0 é testar seu funcionamento.
- **NÃO** adicionar Node.js/WSL2 como dependência obrigatória do assistente Windows; somente aproveitar ideias ou adaptadores se ganhos compensarem.
- **NÃO** copiar códigos ou alegar licença validada enquanto URL direta estiver indisponível. Quando acessível, verificar HEAD, LICENSE, changelog e os testes.
- Guardar como **CANDIDATO DE ARQUITETURA, prioridade alta para Vault + plugins, média para recovery + self-extension**.
- Confirmar implementação com código real e testes, não só README.

## Próxima validação
1. Reconsultar URL e identificar commit atual/LICENÇA.
2. Ler interfaces reais de `plugins/permissions`, `plugins/vault`, `plugins/self-improvement`, `plugins/sessions` e `plugins/scheduler`, se existirem.
3. Fazer tabela de incompatibilidades Python/Node e identificar quais conceitos podem ser implementados em Python.
4. Comparar segurança e custo antes de colocar algo na branch de desenvolvimento.

**Registro criado exclusivamente como planejamento. Nenhuma modificação no MARK LVII.**
