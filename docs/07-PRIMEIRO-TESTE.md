# Homologação do MARK original no PC

Não executar agora no repositório `VNSANTS/N.E.X.U.S`. Este é um roteiro **para quando o PC estiver disponível**, após inspecionar o repositório de terceiros.

## Ambiente
- Windows 10/11.
- Git e Python 3.12 (upstream documenta 3.11–3.13).
- Microfone, alto-falantes, conexão estável para Gemini Live.
- Área de teste sem dados pessoais; não executar como administrador.

## Instalação base (PowerShell)
```powershell
git --version
py -3.12 --version
cd $HOME\Downloads
git clone https://github.com/FatihMakes/Mark-LVII.git
cd Mark-LVII
git rev-parse HEAD
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe setup.py
.\.venv\Scripts\python.exe main.py
```
Registrar commit do clone, versões Python/bibliotecas e erros. O setup original instala dependências e Playwright; só rodar após avaliar o código. Em caso de falha de política do Windows, não desabilitar proteções sem entender a causa.

## Checklist de homologação
- [ ] Inicia sem erro.
- [ ] Chat de texto e Gemini em português.
- [ ] Captura microfone e responde por voz.
- [ ] Seleção correta de entrada/saída de áudio.
- [ ] Abre programas e comprova que abriram.
- [ ] Navega em site neutro.
- [ ] Analisa a tela após autorização.
- [ ] Trabalha apenas em pasta de arquivos fictícios.
- [ ] Memória resiste a reinício.
- [ ] Controle remoto local sem exposição externa.
- [ ] Teste de microfone do celular no dashboard.
- [ ] Resposta de áudio no celular: verificar; não assumir.
- [ ] Uso de CPU/RAM/bateria e desconexões registrados.

## Evidências
Para cada teste: ambiente, versão/commit, passos, resultado PASS/FAIL/BLOCKED e evidência (log redigido/captura). Nunca incluir credenciais, IP/URL privada de câmera, texto de conversas íntimas ou imagens privadas.

**Só depois da Fase 0:** importar o código do MARK e abrir branches de correção no repositório reaproveitado.
