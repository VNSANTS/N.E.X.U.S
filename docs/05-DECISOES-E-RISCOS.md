# Decisões, limites e pendências

Atualizado em 2026-11-23.

## Decisões já tomadas
- **D-001:** substituição de foco: aproveitar o MARK LVII para uso pessoal em vez de construir o antigo N.E.X.U.S. do zero.
- **D-002:** reusar o repositório GitHub `VNSANTS/N.E.X.U.S`. Novo conteúdo na `main`; preservar histórico anterior em `archive/nexus-before-mark-lvii-2026-11-23`; não apagar branches nem PRs legados sem necessidade.
- **D-003:** não copiar/instalar/modificar MARK LVII neste repositório antes de testar a versão original no PC.
- **D-004:** Galaxy J6+ será comunicador do PC, usando microfone interno e saída Bluetooth; sem IA independente na primeira versão.
- **D-005:** Infinix e câmera RTSP/ONVIF são integrações futuras, não promessas de funcionalidades existentes.
- **D-006:** prioridade em custo adicional zero, segurança e desempenho; sem fallback para APIs pagas por padrão.
- **D-007:** pesquisar/avaliar OpenJarvis e componentes reutilizáveis, importar somente mediante benchmark e compatibilidade.

## Restrições de segurança e licença
- MARK LVII upstream: CC BY-NC 4.0, uso planejado estritamente não comercial. Preservar avisos e indicar alterações quando aplicável.
- Licenças de outras ferramentas variam. Uso pessoal não remove exigência de condições, e código publicamente acessível pode não ser reutilizável sem licença.
- Nunca publicar chaves/tokens, endereços privados de câmeras, transcrições, vídeos privados ou senhas.
- Plugins não confiáveis, execução de código e integrações que enviam mensagens não terão permissão automática.
- Testes iniciais usarão dados fictícios e diretórios isolados; não abrir painel diretamente na internet.

## Riscos e mitigação
| Risco | Mitigação |
| --- | --- |
| MARK não inicia no Windows | Diagnóstico do `venv`, versões pinadas, logs, sem desativar antivírus |
| Conflitos de dependências com outros projetos | Adaptadores pequenos, ambientes separados, instalação por fases |
| API consome cota/gera custos | Monitorar cota, allowlist e opt-in por provedor; nunca fallback pago automático |
| Controle remoto interceptado | Transporte autenticado/criptografado, sessão revogável e rede privada |
| Autorização indevida por LLM | Executor determinístico verifica cada permissão fora do prompt |
| Agente revela memória em sites | Preservar isolamento entre acesso à web e dados privados |
| J6 sem retorno de áudio BT | Teste de roteamento e protocolo bidirecional antes de desenvolver produto |
| PC fraco/lentidão | Sem GPU ou modelos grandes obrigatórios; medir antes de adicionar frameworks |
| Câmera incompatível | Verificar RTSP/ONVIF e permissões na própria câmera |
| Mudanças upstream quebram fork | Fixar SHA, branches separadas, testes de regressão e revisão de diffs |

## Pendências
- Instalação real do MARK original.
- Verificação de desempenho e recursos prometidos.
- Validação de requisitos do Sign in with ChatGPT para uso com o projeto (não pressupor que Plus = API OpenAI gratuita).
- Decidir plataforma final do Companion: web/PWA para protótipo ou APK nativo para integração de áudio/foreground.
- Decidir, após teste, quais módulos externos realmente superam o que MARK já entrega.

## D-008 — Pesquisa sem implementação (2026-11-23)
- Este repositório permanece **somente como registro de decisões, fontes, testes e hipóteses** até o MARK original passar pela homologação no Windows. Não importar código nem fazer deploy nesta etapa.
- A segunda inspeção acrescentou MLV-012 a MLV-019 e novos candidatos de voz/Android/câmera; consultar docs/08 a docs/12.
- Para o J6+, priorizar teste PWA com HTTPS privado e botão de falar; considerar APK somente se necessário. Não habilitar a flag do Chrome que aceita origens inseguras como solução.
- Estudos de outros projetos **não equivalem a decisão de adotar dependências**. Código sem licença pública identificada não será copiado.
