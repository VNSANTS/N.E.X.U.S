# Segunda inspeção estática do MARK LVII: problemas e oportunidades

**Pesquisa de 2026-11-23.** Upstream fixo: [FatihMakes/Mark-LVII](https://github.com/FatihMakes/Mark-LVII/tree/752ff618a4e6a4bf2e675866b993071d739cfce2), commit 752ff618a4e6a4bf2e675866b993071d739cfce2. **Sem executar, instalar ou alterar código.** As descobertas abaixo são hipóteses fundamentadas por código e não vulnerabilidades exploradas. O estudo anterior continua em [01-AUDITORIA-MARK-LVII.md](01-AUDITORIA-MARK-LVII.md).

## NOVOS BLOQUEADORES / riscos a investigar

### MLV-012 | ALTA | O microfone remoto no navegador depende de uma origem segura
- **Evidência:** [dashboard/static/app.html, linhas 445-585](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/static/app.html#L445-L585) usa getUserMedia e, se não existir, sugere ativar a flag Chrome "Insecure origins treated as secure". [dashboard/server.py, 755-800](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L755-L800) escolhe HTTP como padrão.
- **Causa:** getUserMedia requer contexto seguro (HTTPS ou exceções locais como localhost). Abrir http://IP-do-PC no Chrome do J6+ normalmente falha independentemente de o IP estar numa rede privada.
- **Solução preferida para protótipo:** testar um endpoint HTTPS privado usando **Tailscale Serve** com nome *.ts.net e TLS válido. Servidor MARK deve escutar apenas loopback se for encaminhado via proxy. Não usar flag para reclassificar origens inseguras, não aceitar certificados não confiáveis como solução final. Tailscale Serve não substitui autenticação do MARK.
- **Aceite:** Android concede acesso ao microfone sem flags; nenhum recurso remoto fica exposto à internet pública; transmissão em WSS; token revogável; teste com J6 em Wi-Fi e rede móvel.
- **Fontes:** [MDN: getUserMedia e contextos seguros](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve).

### MLV-013 | ALTA | Credenciais em parâmetros de URL
- **Evidência:** [dashboard/static/app.html, perto da linha 529](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/static/app.html#L525-L532) abre WebSocket com ?token=; [dashboard/server.py, perto de 925](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L921-L978) possui auto-login por chave via query, e [download /uploads/{filename}](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L1140-L1156) também recebe token em query.
- **Impacto potencial:** URLs podem aparecer em histórico, logs de proxy/servidor, diagnósticos e outras superfícies. A exposição concreta depende do ambiente.
- **Solução candidata:** código de pairing curto de uso único + troca de sessão autenticada; para WebSockets nativos, usar handshake de sessão, subprotocolo autorizado ou cookie HttpOnly/SameSite com CSRF/Origin adequados. Evitar tokens persistentes na URL; emitir tokens curtos, específicos por dispositivo e escopo.
- **Aceite:** logs e histórico não contêm segredo de autenticação; revogação invalida WebSockets e downloads abertos; ataques com token expirado são recusados.

### MLV-014 | ALTA | Fluxo de voz do telefone é apenas de entrada
- **Evidência:** [dashboard/server.py, 1044-1069](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L1044-L1069) recebe bytes PCM; [main.py, 2515-2535](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/main.py#L2515-L2535) encaminha PCM para sessão Gemini Live.
- **Lacuna:** esse caminho não demonstra envio do áudio da IA de volta ao smartphone. Durante fala da IA, o relay não encaminha áudio do telefone se _is_speaking estiver ativo, o que pode limitar interrupção por voz.
- **Solução:** protocolo bidirecional autenticação/controle/audio, teste de TTS na saída do PC, VAD/interrupção, full-/half-duplex, jitter buffer e backpressure. Não introduzir LiveKit/Pipecat antes de testar WebSocket simples.
- **Aceite:** J6 microfone -> PC -> voz sintetizada -> saída Bluetooth do J6; início e parada confiáveis; interrupção controlada, sem comandos duplicados.

### MLV-015 | MÉDIA | Memória JSON pode ser exposta a escrita interrompida
- **Evidência:** [memory/memory_manager.py, save_memory](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/memory/memory_manager.py#L105-L136) escreve diretamente no arquivo JSON. O próprio projeto já usa escrita temporária + os.replace em [memory/config_manager.py](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/memory/config_manager.py#L19-L64).
- **Risco:** interrupção durante escrita pode truncar o arquivo de memória; load_memory tende a retornar estrutura vazia em erro, confundindo corrupção com ausência de memória.
- **Correção mínima:** padrão de salvamento atômico já usado em config_manager; backup versionado, checksum e restauração assistida. Só comparar SQLite/Mem0 depois de testar essa correção simples.
- **Aceite:** simular encerramento durante gravação sem perda irreversível; recuperação verificável, notificações de corrupção.

### MLV-016 | MÉDIA | Manifesto cloud referencia arquivos de plugin ausentes
- **Evidência:** [core/cloud.py, MANIFEST/IMPORT_CHECK](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/core/cloud.py#L104-L152) inclui plugins/_telegram_ops.py e plugins/telegram_remote.py. Na listagem do commit inspecionado, plugins/ continha apenas __init__.py e _template.py.
- **Risco:** o empacotamento opcional de cloud pode falhar. **Não confundir com instalação desktop:** falta testar se o caminho de instalação cloud é realmente chamado e se existe mecanismo externo de obter plugins.
- **Correção:** teste de consistência MANIFEST vs árvore; marcar integrações ausentes como opcionais; excluir nomes não resolvidos de verificações obrigatórias ou providenciar módulo conforme licença.
- **Aceite:** cloud setup falha cedo com diagnóstico claro ou é funcional sem plugin opcional. Nenhum arquivo de plugin misterioso é baixado/executado automaticamente.

### MLV-017 | MÉDIA | Confirmação de ação com estado global único
- **Evidência:** [core/confirm.py](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/core/confirm.py#L45-L130) usa _pending único, sobrescrito a cada novo request.
- **Risco:** solicitações simultâneas podem substituir a confirmação visível; não foi demonstrada exploração.
- **Correção:** fila/ID de confirmação, vínculo entre usuário-sessão-ferramenta-parâmetros e decisão; estado fail-closed; log de pedidos expirados/substituídos.
- **Aceite:** duas confirmações concorrentes nunca executam operação diferente da que o usuário leu.

### MLV-018 | MÉDIA | Logs de ferramenta podem incluir dados de entrada
- **Evidência:** [core/cloud.py, execução de ferramentas](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/core/cloud.py#L1170-L1207) registra nome da ferramenta + primeiros 200 caracteres do JSON de argumentos. Dependendo da ferramenta, dados pessoais ou tokens podem aparecer.
- **Correção:** log estruturado por tipo/ID, redaction de campos sensíveis, política de retenção, sem transcrição completa padrão.
- **Aceite:** testes com senhas/token sintéticos não expõem valores nos logs.

### MLV-019 | MÉDIA | Upload de até 500 MB e arquivos remotos
- **Evidência:** [dashboard/server.py, upload e files](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L1074-L1157), MAX_UPLOAD_MB = 500; nome do arquivo sanitizado e limite checado durante streaming. O sanitizador é um controle existente e deve ser preservado.
- **Risco:** disco e processamento pesados em PC modesto. Uploads repetidos e falta de quota total ainda precisam de testes.
- **Correção:** cotas por sessão, limites menores por padrão, isolamento de pasta e limpeza com aprovação. Validar tipo real, não confiar apenas em extensão.
- **Aceite:** upload acima do limite não deixa lixo no disco; concorrência e nomes repetidos não sobrescrevem arquivos.

## Controles bons que NÃO devemos destruir
- Confirmação pelo HUD em core/confirm.py, sem aceitar parâmetro do LLM como autorização.
- Agentes em background em core/tasks/tools.py: sem ferramentas de controle desktop, diretório de tarefa restrito e separação entre acesso web e memória privada.
- memory/config_manager.py: gravar em temporário e substituir atomicamente.
- Dashboard: tokens aleatórios e expiração, rate limiting de login e revogação de dispositivos (revisar cobertura, não apagar).
- Os erros de áudio reportados são sinais de que testes de hardware precisam anteceder reescrita.

## Resumo de escopo
NENHUMA correção executada; nenhum bug validado em runtime; não publicar alegações de exploração. A prioridade imediata segue sendo testar a instalação desktop original no PC, usando dados fictícios.
