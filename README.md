# NEXUS MARK LVII

**Projeto pessoal, experimental e não comercial.** Repositório reaproveitado do antigo N.E.X.U.S., destinado a planejar, testar e depois desenvolver uma versão personalizada do [MARK LVII](https://github.com/FatihMakes/Mark-LVII).

> **Estado em 2026-11-23: PLANEJAMENTO DOCUMENTADO.** O MARK LVII ainda **não foi instalado, executado, copiado ou homologado** neste repositório. Nenhuma melhoria está implementada aqui. Primeiro será testado o projeto original em um PC Windows.

## Objetivo

Um assistente de IA pessoal, com MARK LVII no PC e, em fase posterior, um **NEXUS Companion** no Galaxy J6+ como comunicador: microfone interno do J6+, áudio de resposta por fone Bluetooth, conexão autenticada com o PC. O Infinix e a câmera de segurança poderão ser controlados apenas por interfaces específicas e autorizadas. Não haverá IA independente rodando no J6+ na primeira versão.

## Plano

1. **Homologar o MARK LVII original:** instalar em ambiente isolado, registrar versões, testar voz, tela, arquivos fictícios, navegador, memória e recursos remotos.
2. **Corrigir riscos e falhas:** controles de permissão, comunicação remota segura, plugins, segregação de tarefas, segredos e auditoria.
3. **Ampliar capacidades sem duplicações:** estudar OpenJarvis, MCP Python SDK, Browser Use, Mem0, LiveKit/Pipecat e ferramentas de câmeras, adotando somente o que passar nos testes.
4. **Construir Companion Android:** o J6+ como comunicador remoto dependente do PC; posteriormente integrar Infinix e vídeo RTSP/ONVIF.
5. **Otimizar e validar:** consumo de RAM/CPU, reconexão, latência, áudio em português, testes automatizados e regressões.

## Documentos

- [Auditoria técnica do MARK LVII](docs/01-AUDITORIA-MARK-LVII.md)
- [Repositórios de referência e política de reutilização](docs/02-REFERENCIAS-E-LICENCAS.md)
- [Roadmap priorizado e critérios de aceite](docs/03-ROADMAP-E-TESTES.md)
- [Arquitetura do NEXUS Companion e ecossistema](docs/04-COMPANION-E-ECOSSISTEMA.md)
- [Decisões e riscos](docs/05-DECISOES-E-RISCOS.md)
- [Estudo sobre ChatGPT Plus e provedores](docs/06-PROVEDORES-IA.md)
- [Roteiro de instalação e homologação](docs/07-PRIMEIRO-TESTE.md)
- [Origens e aviso de licenciamento](NOTICE.md)

### Pesquisa aprofundada de 23/11/2026
- [08 PESQUISA APROFUNDADA MARK](docs/08-PESQUISA-APROFUNDADA-MARK.md)
- [09 OUTROS REPOSITORIOS TRIAGEM](docs/09-OUTROS-REPOSITORIOS-TRIAGEM.md)
- [10 EXPERIMENTOS EVIDENCIAS](docs/10-EXPERIMENTOS-EVIDENCIAS.md)
- [11 COMPANION CONEXAO E ANDROID](docs/11-COMPANION-CONEXAO-E-ANDROID.md)
- [12 PESQUISA 2026 11 23 RESULTADO](docs/12-PESQUISA-2026-11-23-RESULTADO.md)

## Historial e fontes

- Branch de arquivo do projeto antigo: [archive/nexus-before-mark-lvii-2026-11-23](https://github.com/VNSANTS/N.E.X.U.S/tree/archive/nexus-before-mark-lvii-2026-11-23).
- A branch `main` deste repositório foi reiniciada em conteúdo, **não em histórico**: o código antigo permanece recuperável pelo Git e pela branch de arquivo. Outras branches e PRs anteriores não foram apagados.
- A URL do repositório continua `VNSANTS/N.E.X.U.S`; renomeação não foi realizada.
- O MARK LVII original é licenciado em **CC BY-NC 4.0** e o uso planejado aqui é pessoal e não comercial. A atribuição, a marcação de alterações e as condições de cada dependência permanecem exigíveis.

**Princípio:** testar antes de integrar, limitar privilégios, evitar custos adicionais e manter provas de que algo realmente funciona.
