# Roadmap técnico e critérios de aceite

**Condição atual (D-043):** o MARK LVII original já foi instalado e executado no PC do proprietário; interface, conversa PT-BR e áudio foram relatados como funcionais, mas os demais itens de homologação estão pendentes. Este roadmap registra as etapas ainda necessárias, não uma implementação concluída.

## Fase 0 — Baseline e homologação (bloqueante)
- [ ] Clonar MARK LVII sem alterações, fixar SHA do commit de origem.
- [ ] Windows 10 + Python 3.12 (3.11–3.13 suportados pelo upstream); criar `venv`; verificar Git, armazenamento e áudio.
- [ ] Rodar `setup.py` com monitoramento de erros; documentar versões de dependências.
- [ ] Executar `main.py`; registrar comportamento sem armazenar credenciais no Git.
- [ ] Testar chat em português, microfone, alto-falante, Gemini Live, seleção de áudio, tela, apps, pesquisa, navegador, arquivos **fictícios**, memória e retomada.
- [ ] Testar o painel local sem expor interface publicamente; registrar limitações de HTTPS, áudio e QR.
- [ ] Coletar consumo de RAM/CPU, travamentos, erros, latência observada e logs sem dados sensíveis.
- [ ] Relatório PASS/FAIL/BLOCKED por recurso, com evidências.

**Portão:** não incorporar código externo nem mexer em automação sensível até homologação mínima concluída.

## Fase 1 — P0: endurecimento e reprodutibilidade
- [ ] MLV-001: canal remoto seguro por padrão e autenticação/revogação testadas.
- [ ] MLV-002: plugins por manifesto, procedência e permissão explícita antes de importar/executar.
- [ ] MLV-003: código e comandos do dev-agent isolados e sujeitos a confirmação.
- [ ] MLV-004: segredos protegidos e higienização de logs.
- [ ] CI com testes Python, import, contrato de ferramentas e checagem de dependências.
- [ ] Testes de prompt injection, path traversal, comandos indevidos, SSRF, perda de rede e segredo no log.

**Portão:** testes essenciais passam e nenhuma capacidade perigosa ganhou privilégio por acidente.

## Fase 2 — P1: arquitetura, estabilidade e IA
- [ ] MLV-005/006: centralização de autorização e preservar limites de agentes em segundo plano.
- [ ] MLV-007/008: catálogo de plugins real, diagnóstico de instalação e documentação atual.
- [ ] MLV-009: validar memória atual; comparar SQLite e Mem0 com conjunto de consultas representativas.
- [ ] MLV-010: provedores com configuração tipada, quota, timeout, custo zero por padrão e sem fallback pago.
- [ ] Avaliar provedor ChatGPT via mecanismo oficial, apenas se houver elegibilidade e compatibilidade demonstradas.
- [ ] Instrumentação de eventos, erros, duração e causas de falha; sem gravar conteúdo pessoal por padrão.

## Fase 3 — P1: NEXUS Companion J6+
- [ ] MLV-011: testar microfone de telefone já existente no dashboard.
- [ ] Provar fluxo bidirecional de voz com PC ativo: J6 microfone → PC → retorno Bluetooth.
- [ ] Prototipar PTT, status, cancelamento, reconnect/backoff e serviço Android em primeiro plano quando necessário.
- [ ] Roteamento real: microfone embutido J6, áudio A2DP Bluetooth sem microfone no fone.
- [ ] Autenticação segura e rede privada Tailscale; nunca expor `ws://` com tokens à internet.
- [ ] Testar tela apagada, mudança de aplicativo, reconexão BT, bateria e falha do PC.
- [ ] **Não** incluir IA própria no J6+ nem controle direto do Infinix nesta fase.

## Fase 4 — P2/P3: expansões medidas
- [ ] Comparar Browser Use vs Playwright nativo.
- [ ] Testar cliente MCP em ferramenta READ isolada.
- [ ] Considerar pipeline de voz LiveKit/Pipecat apenas se for necessário.
- [ ] Integrar Infinix via companion com permissões individuais.
- [ ] Câmera RTSP para visualização/autorização e ONVIF apenas se suportado; analisar frames sob solicitação, sem vigilância automática como padrão.
- [ ] Personalização da interface após estabilidade.

## Modelo de teste
| ID | Caso | Esperado |
| --- | --- | --- |
| T-01 | Instalação limpa | Inicializa sem traceback fatal; dependências verificadas |
| T-02 | Conversa PT-BR | Resposta coerente, áudio inteligível, sem chamada não autorizada |
| T-03 | Áudio e fones | Rota de microfone/alto-falante correta, controle de interrupção |
| T-04 | Abrir app | Abre programa fictício/seguro, valida sucesso real |
| T-05 | Ação sensível | Interface pede confirmação, LLM não se autoautoriza |
| T-06 | Arquivos | Apenas workspace de teste, sem alterar arquivos pessoais |
| T-07 | Memória | Persistência e recuperação após reiniciar |
| T-08 | Plugin desconhecido | Sem import/execução automática |
| T-09 | Dashboard remoto | Recusa cliente não autenticado, canal inseguro e token revogado |
| T-10 | Audio Companion | J6→PC→fone com conexão autenticada; reconexão testada |
| T-11 | PC desligado | J6 informa indisponível e não finge ter executado ação |
| T-12 | Modelo indisponível | Erro seguro, sem cobrança ou fallback implícito |
| T-13 | Câmera | Apenas stream autorizado, sem credenciais em logs |
| T-14 | Stress | Medir RAM/CPU e latência; registrar baseline antes de otimizar |

Cada mudança precisa de teste unitário e regressão correspondente. Valores numéricos de desempenho só serão estabelecidos após baseline real.


## Atualização de direção — D-043: desenvolver JARVIS sobre o MARK original funcional

**Decisão mais recente prevalece sobre o título/branding NEXUS nos documentos históricos:** produto final **JARVIS**, mantendo os requisitos aprovados no planejamento D-001 a D-042. A base de código será o **MARK LVII que o usuário instalou e está usando**, e não reconstrução do NEXUS do zero.

**Baseline revisado (relato do proprietário em 2026-11-23):** interface abriu, resposta textual PT-BR apareceu na captura, microfone funciona e o usuário relata resposta falada muito rápida. Isso modifica a premissa inicial "não instalado": MARK original **já está executando no PC do usuário**. Itens ainda não verificados permanecem pendentes; não considerar Fase 0 inteiramente concluída.

### Próximo ciclo no PC
1. Confirmar pasta original, `git status --short`, `git rev-parse --short HEAD`, `git branch --show-current` e versões do ambiente; não publicar .env ou credenciais.
2. Preservar instalação que já funciona e criar **ambiente/branch de desenvolvimento isolado**, com possibilidade de retornar ao original.
3. Registrar baseline de áudio, PT-BR, latência, CPU/RAM em repouso e carga, navegação, ferramentas e segurança em arquivos fictícios.
4. Priorizar **estabilidade e segurança P0** sem quebrar Gemini Live. Depois, adaptar personalidade e interface sob identidade JARVIS, memória, roteamento de agentes e demais funcionalidades aprovadas em etapas.
5. Testar regressões e comparar recursos a cada mudança; sem trocar de motor/provedor apenas por preferência estética.

**Escopo de marca:** novos textos, UX e futuro nome do assistente = JARVIS; títulos NEXUS já existentes são referências históricas de requisitos, não instrução para renomear o assistente de volta. Repositório GitHub atual permanece como está até decisão separada.

**Estado:** plano atualizado, nada modificado no PC pelo conector GitHub.
