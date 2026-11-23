# Experimentos e critérios de decisão (a serem executados no PC)

Este é um **plano de testes, não um histórico de testes aprovados**. A data de pesquisa é 2026-11-23 e o MARK LVII original ainda não foi executado neste trabalho.

## Etapa G0 — Base original (obrigatória)
| ID | Verificação | Prova mínima | Prioridade |
| --- | --- | --- | --- |
| G0-01 | Git/Python/venv/instalação original | versões e saída sem dados sensíveis; lista de deps | Alta |
| G0-02 | Iniciar MARK sem alterar código | screenshot da UI e log sanitizado; sem travamento | Alta |
| G0-03 | Modelo e ferramenta | conversação em PT-BR, abrir app inofensivo, usar diretório fictício | Alta |
| G0-04 | Entrada/saída de áudio | mic PC, som PC, troca dispositivo, microfone mutado, reconectar | Alta |
| G0-05 | Navegador e visão | leitura de página neutra e tela autorizada, sem ação externa | Média |
| G0-06 | Memória | adicionar fato fictício, reiniciar, buscar e apagar | Alta |
| G0-07 | Painel | status local, login, logout, revogação; NÃO usar rede pública | Alta |
| G0-08 | Desempenho | RAM/CPU em idle, voz, navegador; medir sem presumir limites | Alta |

## Etapa G1 — Pesquisas técnicas de alto retorno
| ID | Hipótese | Prova / decisão |
| --- | --- | --- |
| G1-01 | HTTP do dashboard bloqueia getUserMedia no J6 | testar somente após TLS válido; comparar browser HTTPS contra origem http sem mudar flags |
| G1-02 | Tailscale Serve resolve origem confiável e mantém rede privada | URL HTTPS *.ts.net, wss, sem exposição externa, autorização do app e revogação |
| G1-03 | O MARK recebe voz do telefone, mas não devolve áudio pelo mesmo fluxo | verificar PC log, headset J6; desenhar retorno de áudio como feature se falhar |
| G1-04 | Um app Android nativo será necessário para rodar com tela apagada | primeiro PWA + PTT em primeiro plano; só depois testar foreground service APK |
| G1-05 | J6 mantém microfone interno com saída Bluetooth | prova A2DP em Android 10, com fone sem microfone e teste de reconexão |
| G1-06 | Manifesto cloud tem arquivos obrigatórios não presentes | comparar MANIFEST com commit real e executar verificação isolada, sem credenciais |
| G1-07 | Memória tolera escrita interrompida | teste unitário de falha e restauração; preferir atomic write antes de trocar banco |
| G1-08 | Confirmações concorrentes podem se sobrepor | duas ações fictícias pendentes; nenhuma ação executa sem concordância específica |
| G1-09 | O gerenciador de plugins executa módulos durante descoberta | plugin inofensivo com side-effect de teste; decidir sobre manifesto estático |
| G1-10 | Receptor de câmera funciona com RTSP existente | pegar frame de teste em tempo limitado; comparar solução nativa x go2rtc |
| G1-11 | Browser Use agrega valor ao Playwright do MARK | repetir tarefas idênticas; contar acertos, chamadas LLM, recursos e falhas |
| G1-12 | Mem0 supera memória atual | 20 fatos fictícios, 20 consultas, precisão, latência, custos/privacidade |
| G1-13 | MCP reduz código sem ampliar permissões | registrar ferramenta READ simples, rejeitar chamadas WRITE por padrão |
| G1-14 | Sign in with ChatGPT é elegível para este aplicativo | validar autenticação oficial e quais modalidades são permitidas; sem usar chave API cobrada |
| G1-15 | Controle do Infinix pode respeitar ausência de root | app auxiliar/ADB só em dispositivo próprio e com confirmação; rejeitar ações restritas |

## Matriz de decisões: aceitar/rejeitar biblioteca
- **Necessidade:** funcionalidade não existe ou falha no baseline?
- **Compatibilidade:** Windows 10 modesto / J6+ Android 10, Python 3.12, ABI/SDK corretos?
- **Licença:** autorização documentada, autoria, modelos e mídias verificados?
- **Custo:** uso recorrente e infraestrutura gratuitos, salvo aprovação específica?
- **Segurança:** permissões mínimas, escopo restrito, autorização fora da IA, sem vazamento?
- **Performance:** tempo de resposta, memória, CPU e bateria comparados ao baseline?
- **Manutenção:** upstream ativo, releases, testes, deps estáveis, código duplicado?
- **Rollback:** alteração fácil de desligar, versionada e reversível?

Resultado possível para cada candidato: **ACEITAR**, **ADIAR**, **REJEITAR** ou **NECESSITA TESTE**. Nunca registrar ACEITAR sem execução e evidências.

## Template de evidência
- Data/hora e autor:
- Máquina / Android / versão de app:
- SHA MARK + SHA NEXUS + versão Python/Java:
- Cenário e dados fictícios:
- Comando/ação executada:
- Resultado: PASS/FAIL/BLOCKED/NOT RUN:
- Tempo, CPU/RAM/bateria (se aplicável):
- Erro/log com segredos removidos:
- Evidência (link):
- Mudança proposta:
- Decisão e possibilidade de rollback:

## Invariantes em regressões
- Sem root obrigatório no Infinix, sem alteração do firmware dos celulares.
- Sem shell irrestrito concedido ao modelo.
- Sem login/token no URL ou logs.
- Sem fallback pago automático.
- Sem chaves no Git.
- Sem expor câmera ou painel via Tailscale Funnel / portas públicas.
- Sem informar êxito de comandos quando dispositivos estiverem offline.
- Sem apagar dados pessoais para 'testar desempenho'.
