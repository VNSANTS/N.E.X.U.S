# Triagem ampliada de repositórios e ideias reutilizáveis

**Data:** 2026-11-23. Pesquisa documental/estática, sem instalações ou cópias de código. A licença listada é a principal reconhecida pelo GitHub no snapshot; verificar LICENSE e dependências antes de qualquer importação. Links de commits para reprodutibilidade.

## A. Arquitetura e segurança

| Projeto | Snapshot fixo | Licença principal | O que avaliar | Decisão |
| --- | --- | --- | --- | --- |
| [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) | c05ebe99e524 | Apache-2.0 | Políticas de capacidades, assinatura de skill, sandbox/container, dependências | **Alta utilidade arquitetural.** Não importar runtime inteiro |
| [OpenClaw](https://github.com/openclaw/openclaw) | e42e2404dc33 | MIT | Gateway, sessões, pairing, nós/Android, aprovações de execução, isolamento | **Alta utilidade como padrão.** Evitar trazer o grande ecossistema Node para dentro do MARK |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | 77001c96f950 | MIT | Contratos tipados de ferramentas/servidores, cliente local | **P1 somente após política fail-closed**, ferramenta READ primeiro |
| [OpenHands](https://github.com/OpenHands/OpenHands) | c5e47c4b4dab | MIT (metadados) | Agente de programação e fluxos de testes | Referência para futuro, não importar stack |

### Componentes OpenJarvis concretos
- [skills/security.py](https://github.com/open-jarvis/OpenJarvis/blob/c05ebe99e524a269a08d017ce3730a436ab4c46b/src/openjarvis/skills/security.py): TrustTier, validate_capabilities e classificação de capacidades perigosas. Ideia: registrar cada plugin com capacidades e bloquear privilégios não declarados.
- [skills/loader.py](https://github.com/open-jarvis/OpenJarvis/blob/c05ebe99e524a269a08d017ce3730a436ab4c46b/src/openjarvis/skills/loader.py): manifesto de skills, dependências, assinatura quando configurada.
- [sandbox/runner.py](https://github.com/open-jarvis/OpenJarvis/blob/c05ebe99e524a269a08d017ce3730a436ab4c46b/src/openjarvis/sandbox/runner.py): execução de agentes isolados em Docker/Podman, mas **não** assumir Docker disponível no PC.
- [sandbox/mount_security.py](https://github.com/open-jarvis/OpenJarvis/blob/c05ebe99e524a269a08d017ce3730a436ab4c46b/src/openjarvis/sandbox/mount_security.py): normalização de caminhos, padrões bloqueados e raízes permitidas. **Atenção:** sem roots configurados, o helper _is_under_allowed_root retorna True. Para NEXUS exigir explicitamente a raiz autorizada: sem autorização deve negar.
- O próprio MARK já separa web e memória no agente de background: conservar o que existe, não substituir só por ser externo.

## B. Voz e comunicador Android

| Projeto | Snapshot | Licença | Compatibilidade / ganho | Encaminhamento |
| --- | --- | --- | --- | --- |
| [VoiceAssistantPhone](https://github.com/VirtualyMichael/VoiceAssistantPhone) | 59ae7d092ebd | **Nenhuma licença pública identificada** | Kotlin/Compose, Android minSdk 26; mic+alto-falante+camera sobre Tailscale; approvals e wake word. Servidor depende de outro projeto, não é drop-in MARK | **Somente estudar arquitetura e comportamento; NÃO copiar código sem permissão** |
| [TailWispr](https://github.com/mitchfitzsimmons/tailwispr) | 7c39e516792e | MIT | Captura microfone do browser via WSS/Tailscale, reconexão, PWA; servidor para macOS/Linux, não Windows | Inspiração para HTTPS, WebSocket e reconexão; não usar como receiver Windows pronto |
| [AndroidMic](https://github.com/teamclouday/AndroidMic) | 611a0c94bfd1 | GPL-3.0 | App Android + receptor no PC Windows/Linux/macOS; Wi-Fi ou USB; virtual audio cable; só microfone | Plano B de teste de captura, não resolve retorno de voz/BT; GPL exige cuidado com redistribuição |
| [Mic2Bluetooth](https://github.com/thrillfall/mic2bluetooth) | 9545ee7f7d60 | GPL-3.0-or-later | A2DP vs HFP/SCO, PTT; **exige Android 12+** | **Não compatível com J6+ Android 10 atual**. Estudar conceitos, não instalar |
| [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 219ca7f9b9be | Apache-2.0 | VAD/STT/TTS e wake word on-device; diferentes modelos e tamanhos | P2, somente se ativação local leve for necessária |
| [LiveKit Agents](https://github.com/livekit/agents) | 8b202a2abc | Apache-2.0 | Conversação em tempo real, fluxo WebRTC | Adiar: infraestrutura adicional pode ser excesso |
| [Pipecat](https://github.com/pipecat-ai/pipecat) | 218a7f836356 | BSD-2-Clause | Pipeline de STT/LLM/TTS, interrupções | Adiar: comparar com fluxo MARK puro antes |
| [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) | 6cb639e70786 | MIT | STT local, já opcional no MARK | Testar recurso original antes de replicar |

**Observação de licença:** VoiceAssistantPhone não tem licença identificada na página/metadados examinados. O README também admite que o modelo de wake word da pasta de assets tem licença de redistribuição ainda não confirmada. Não importar esses arquivos nem se basear em cópia do APK.

## C. Câmeras, casa e Infinix

| Projeto | Snapshot | Licença | Ganho / custo | Decisão |
| --- | --- | --- | --- | --- |
| [go2rtc](https://github.com/AlexxIT/go2rtc) | 8eee2d4889f4 | MIT | Executável para Windows, RTSP/WebRTC/transcodificação apenas quando necessária, API HTTP; baixo acoplamento | **Principal candidato de câmera**, após confirmar stream/códigos da câmera |
| [Frigate](https://github.com/blakeblackshear/frigate) | 8c8875466476 | MIT | NVR com reconhecimento local, recursos e serviços adicionais | Não instalar na V0.1; PC modesto pode não justificar |
| [Home Assistant Core](https://github.com/home-assistant/core) | b6d170e227 | Apache-2.0 | Integrações de dispositivos, ONVIF, automações | Só se houver automação residencial ampla; evitar instalar stack apenas por 1 câmera |
| [Home Assistant Android](https://github.com/home-assistant/android) | ac538fab3282 | Apache-2.0 | Companion, notificações e integração Android | Estudar padrões de serviço e permissões, não importar aplicativo |
| [scrcpy](https://github.com/Genymobile/scrcpy) | c939183a7cdc | Apache-2.0 | Visualização/controle do Android pelo PC via ADB | Candidato futuro para testes Infinix com depuração autorizada, não solução remota permanente |
| [uiautomator2](https://github.com/openatx/uiautomator2) | 96f581d3b95e | MIT | Automação Android para testes e alguns controles | Laboratório, dependente de pareamento/ADB e permissões |
| [Tailscale](https://github.com/tailscale/tailscale) | (serviço já utilizado; não importar código) | BSD-3-Clause (metadados) | Rede privada criptografada e Serve HTTPS | Usar serviço, não recriar VPN |
| [Browser Use](https://github.com/browser-use/browser-use) | 753d629d76eb | MIT | Agente de navegador; pode usar modelos remotos e instalação extra | **Benchmark antes de substituir Playwright** |

### Câmera: mínimo que precisa existir
1. Confirmar que a câmera já fornece stream RTSP reproduzível no PC; guardar URL/senha fora do Git.
2. Testar 1 frame/snapshot, start/stop, reconexão; sem análise/vigilância contínua.
3. Somente se houver limitação de codecs/visualização, usar go2rtc como processo externo Windows. O HTTP API dele NÃO deve ser exposto à internet.
4. Se ONVIF existir, descobrir capacidades reais. Não pressupor PTZ, microfone ou motor.
5. Integrar via ferramenta READ para capturar frame; ação PTZ/mudança da câmera exige autorização específica.

## D. Memória e provedores

- [Mem0](https://github.com/mem0ai/mem0), fff8a6472512, Apache-2.0: interessante para relevância e resumo de memória, **mas defaults citam GPT e embeddings pagos**. Testar configuração local/gratuita e comparar com JSON aprimorado/SQLite.
- [Letta](https://github.com/letta-ai/letta), 8816d3a851, Apache-2.0: referência para estado/memória de agentes. Plataforma grande demais para a fase inicial.
- **Sign in with ChatGPT**: documentação oficial https://developers.openai.com/siwc/quickstart e https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt . Elegibilidade e escopos são específicos: integração opcional, sem confundir assinatura Plus com API geral e sem usar cookies da web.

## Não duplicar por padrão
- Browser Playwright: MARK já tem.
- Voz local Faster Whisper/Piper: MARK já permite.
- Memória: MARK já pesquisa JSON; só trocar após medir.
- Controle de mouse/janela: MARK já contém.
- Painel remoto/microfone de telefone: já existe parcialmente. Priorizar HTTPS e áudio de volta, não criar novo painel antes do teste.
- Docker/NVR/Home Assistant/OpenClaw completos: dependências excessivas para uma máquina modesta.

**Regra de engenharia:** problema específico -> alternativa comparada -> teste -> decisão -> adapter mínimo -> regressão. Nada foi integrado.
