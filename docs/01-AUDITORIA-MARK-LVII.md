# Auditoria estática inicial — MARK LVII

**Data:** 2026-11-23. **Upstream:** https://github.com/FatihMakes/Mark-LVII  
**Commit examinado:** `752ff618a4e6a4bf2e675866b993071d739cfce2`  
**Escopo:** leitura seletiva de código, README, estrutura, issues e dependências. **Não** é pentest, auditoria completa, nem prova de funcionamento em Windows. Não houve instalação nem execução do projeto.

## P0: Antes de instalar e confiar

### MLV-001: painel remoto aceita HTTP por padrão
- Evidência: `dashboard/server.py`, `DashboardServer._ssl_enabled()`; README seção `The phone dashboard`.
- O próprio projeto informa que, quando HTTPS não está ativo, o navegador pode enviar comandos sem proteção de transporte. Verificar também os caminhos `/api/command`, `/auto-login`, `/api/device-login` e tokens.
- Correção proposta: exigir canal autenticado e criptografado para Companion e uso remoto, com verificação de certificado ou túnel seguro; eliminar segredos de URLs; rever armazenamento de tokens, limitação de tentativas, logout e revogação por dispositivo. Não abrir a porta do dashboard à internet.
- Critério: teste comprova que cliente sem autenticação, sessão expirada, dispositivo revogado e conexão insegura são recusados; sessão válida só funciona no canal configurado.

### MLV-002: execução dinâmica de plugins Python
- Evidência: `core/plugin_loader.py` usa `spec.loader.exec_module(module)` durante descoberta; executar um import já pode executar código.
- Correção proposta: manifesto estático, procedência/versão, revisão de capacidades e habilitação explícita; nada de download/autoativação de `*.py` desconhecido. Sandboxing separado para plugins de maior risco.
- Referência: OpenJarvis `src/openjarvis/skills/security.py` (trust tiers e capacidades) e `skills/loader.py` (manifesto/assinaturas). Reaproveitar conceitos, não colar sem validar.
- Critério: plugin não confiável não é importado nem executado por mera descoberta.

### MLV-003: agente de desenvolvimento executa código e instala dependências
- Evidência: `actions/dev_agent.py`, funções `_install_dependencies`, `_run_project` e chamada `subprocess.Popen(..., shell=True)` no lançamento de VS Code.
- Correção proposta: execução opt-in em diretório de trabalho controlado, allowlist de comandos e pacotes, prévia de alterações, confirmação fora do modelo, limites de tempo, sem acesso a perfis de navegador, contas pessoais e rede por padrão. Se viável, processo isolado com Windows Sandbox/VM; Docker/Podman opcionais, não obrigatórios.
- Referência: OpenJarvis `src/openjarvis/sandbox/runner.py`, `sandbox/mount_security.py` para ideias de montagem segura.
- Critério: pedido malicioso via prompt ou conteúdo de página não instala programa, não executa shell de alto risco e não lê arquivos fora do workspace.

### MLV-004: segredos locais em texto simples
- Evidência: `config/api_keys.json`; documentação oficial admite plaintext.
- Correção proposta: utilizar mecanismo seguro do sistema (ex.: Windows Credential Manager) quando apropriado; bloquear logs de segredos; migrar com backup; nunca enviar ao Git.
- Critério: chave ausente gera erro seguro; segredos não aparecem em logs nem no repositório.

## P1: Estabilidade e comportamento

### MLV-005: autenticação e confirmação consistentes
- Evidência: `core/confirm.py` implementa confirmação pela interface, não pelo modelo, uma boa decisão. Contudo não é prova de cobertura integral dos comandos sensíveis.
- Correção proposta: classificar ferramentas em READ, WRITE_REVERSIBLE, SENSITIVE, CODE_EXEC, REMOTE_CONTROL; cobertura por camada central antes de executar. Testar reentrância, timeout, cancelamento e auditoria.
- Critério: exclusão, envio de mensagem, instalação, comandos de sistema ou acesso sensível não passam por confirmação simulada pelo próprio LLM.

### MLV-006: agente em segundo plano tem barreiras úteis a preservar
- Evidência: `core/tasks/tools.py` limita acesso a arquivos no diretório da tarefa e separa agentes com internet de agentes com memória privada.
- Ação: **preservar** esses controles ao ampliar ferramentas; adicionar testes de prompt injection, caminhos relativos/`..`, links simbólicos, SSRF e acesso indevido a dados.
- Critério: regressões automatizadas não permitem expandir permissões por conteúdo externo.

### MLV-007: plugin catalog e documentação incompletos
- Evidência: no snapshot, pasta `plugins/` contém `__init__.py` e `_template.py`, embora README descreva mais integrações e o código referencie nomes de plugins adicionais; relato #183.
- Ação: detectar plugins opcionais faltantes; distinguir embutido, externo e experimental; desativar recursos não presentes sem quebrar inicialização.
- Critério: interface não anuncia plugin operacional se dependência/código não estiver disponível.

### MLV-008: instalação e automação de testes
- Evidência: `setup.py` instala via `requirements.txt` e Playwright. Relatos de `sounddevice` ausente (#180, #163), falhas de conexão (#181) e voz sem resposta (#175). Não foi identificado workflow GitHub Actions na raiz examinada.
- Ação: criar `venv`, checagem de versão Python, diagnóstico pré-execução, suíte `pytest`/unittest com mocks, testes manuais de áudio e CI. Não desativar proteções do Windows para contornar bloqueios.
- Critério: instalação reproduzível e smoke test documentado; falhas identificáveis sem comando invasivo.

### MLV-009: memória e contexto
- Evidência: `memory/memory_manager.py` utiliza `long_term.json`, mecanismo de busca e controle de tamanho. Não concluir que é incapaz apenas por usar JSON.
- Ação: testar recuperação, colisões, concorrência, corrupção, backup, exclusão seletiva e qualidade de relevância; avaliar SQLite/Mem0 **somente depois dos testes**.
- Critério: recuperar preferências corretas após reiniciar sem vazamento entre usuários e sem apagar memórias sem aviso.

### MLV-010: motores de IA e custo
- Evidência: `providers/llm_openai.py` usa endpoints OpenAI-compatíveis de `/chat/completions`; Gemini Live tem fluxo próprio; configuração da API não é uma assinatura Plus.
- Ação: gateway tipado com capabilities, quotas, timeouts e opt-in por provedor; averiguar separadamente elegibilidade oficial de Sign in with ChatGPT antes de prometer uso da assinatura.
- Critério: nenhuma cobrança acidental; falha de provedor não causa loop ou fallback pago não autorizado.

## P1: NEXUS Companion, lacuna de áudio

### MLV-011: microfone remoto já existe; áudio de retorno precisa ser confirmado
- Evidência: `dashboard/static/app.html` usa `getUserMedia`, PCM16 a 16 kHz e `/ws/phone-audio`; `dashboard/server.py` recebe áudio; `main.py` tem `_relay_phone_audio`.
- Limitação encontrada: esse caminho é explicitamente **telefone -> Gemini Live no PC**. Não encontramos nele implementação comprovada de transmissão de PCM/TTS do PC para o fone Bluetooth no telefone.
- Ação: primeiro verificar o painel atual; só depois criar transporte bidirecional autenticado de áudio com protocolo de sessão, backpressure, reconexão e interrupção da resposta; usar microfone interno do J6+ e saída Bluetooth A2DP, verificando roteamento real.
- Critério: áudio capturado no J6 chega ao motor; voz sintetizada retorna e toca no fone; sem eco excessivo, vazamento de tokens ou desconexões silenciosas.

## P2: Qualidade
- UI em português brasileiro, diagnósticos acessíveis, modos de baixo consumo, tratamento de rede intermitente e queda do PC.
- Integração com Infinix por ações explicitamente aprovadas; câmera RTSP/ONVIF apenas com credenciais locais e fonte autorizada.
- Testes de carga: RAM, CPU, latência, bateria, retomada de áudio e memória.

## Links de issues pertinentes
- https://github.com/FatihMakes/Mark-LVII/issues/180
- https://github.com/FatihMakes/Mark-LVII/issues/181
- https://github.com/FatihMakes/Mark-LVII/issues/175
- https://github.com/FatihMakes/Mark-LVII/issues/183

**Status de todas as correções:** propostas; **nenhuma foi aplicada**.
