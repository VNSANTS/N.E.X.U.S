# Catálogo de referências para melhorias

Leitura inicial em **2026-11-23**; commits indicam snapshots, não versões recomendadas automaticamente. Os nomes de licença abaixo refletem a identificação observada no GitHub; verificar os arquivos `LICENSE`, subcomponentes, modelos e dependências antes de copiar ou distribuir código.

| Prioridade | Projeto (URL) | Licença do repositório | Snapshot | Candidato a aproveitar | Decisão atual |
| --- | --- | --- | --- | --- | --- |
| Base | [FatihMakes/Mark-LVII](https://github.com/FatihMakes/Mark-LVII) | CC BY-NC 4.0 | `752ff618a4e6` | Desktop, voz, controle, dashboard | Testar original, sem copiar ainda |
| P1 | [open-jarvis/OpenJarvis](https://github.com/open-jarvis/OpenJarvis) | Apache-2.0 | `c05ebe99e524` | Política de skills, verificação de capacidades, sandbox e orquestração | Estudar interfaces, **não trocar runtime** |
| P1 | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | MIT | `77001c96f950` | Cliente/servidor MCP e ferramentas tipadas | Adotar apenas com autorização e allowlist |
| P2 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | MIT | `753d629d76eb` | Browser agents e recuperação de estado | Benchmark contra Playwright já presente |
| P2 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | `fff8a6472512` | Busca e organização de memória | Benchmark contra JSON e SQLite antes de adotar; defaults podem usar APIs pagas |
| P2 | [livekit/agents](https://github.com/livekit/agents) | Apache-2.0 | `8b202a2abc49` | Fluxo e interrupção de voz em tempo real | Referência, sem introduzir servidor obrigatório |
| P2 | [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | BSD-2-Clause | `218a7f836356` | Pipeline de voz e transporte de áudio | Comparar peso e latência |
| P2 | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT | `6cb639e70786` | STT local em português | Já opcional no MARK; testar antes |
| P3 | [home-assistant/core](https://github.com/home-assistant/core) | Apache-2.0 | `b6d170e22714` | Padrões para dispositivos e automação local | Preferir usar API do Home Assistant se houver instância; não clonar sistema inteiro |
| P3 | [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) | MIT | `8c8875466476` | NVR e eventos de câmera | Não exigir servidor NVR; só se hardware justificar |
| P3 | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | MIT (metadados) | `c5e47c4b4dab` | Fluxo de agente de código e testes | Referência; verificar licenças de componentes |

## O que o OpenJarvis realmente inspira

- `src/openjarvis/skills/security.py`: níveis de confiança e validação de capacidades declaradas pelas skills.
- `src/openjarvis/skills/loader.py`: manifesto, procedência e validação de assinatura.
- `src/openjarvis/sandbox/runner.py`: execução isolada baseada em Docker/Podman.
- `src/openjarvis/sandbox/mount_security.py`: allowlist de diretórios e bloqueio de montagens perigosas.
- `src/openjarvis/skills/manager.py`: descoberta e resolução de dependências de skills.

**Cuidado:** o OpenJarvis é local-first e inclui uma pilha considerável de serviços e modelos. A nossa meta inicial é um Windows modesto com assistente remoto e APIs gratuitas. Importar o runtime inteiro para o MARK geraria forte risco de conflito de dependências.

## Método para adicionar componentes

1. Registrar problema concreto, teste reproduzível e componente candidato.
2. Registrar repositório, commit/tag, licença, origem dos arquivos e termos do serviço.
3. Verificar se o MARK já implementa a capacidade.
4. Criar adaptador pequeno em branch isolada; evitar importar o monorepo inteiro.
5. Validar licenças, segredos, permissões, uso de CPU/RAM, latência e fallback.
6. Comparar contra a versão sem o componente; aceitar apenas se o ganho compensar.
7. Atualizar NOTICE e testes de regressão.

**Regra:** uso pessoal não anula condições de licença. Não copiar código sem licença ou recursos proprietários apenas porque estão públicos.
