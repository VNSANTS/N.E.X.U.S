# Recuperação inteligente de falhas — NEXUS MARK LVII

**Aprovada em 2026-11-23, D-042.** Planejamento técnico, ainda não implementado.

## Comportamento aprovado
Quando um agente, ferramenta, provedor ou modelo falhar, o NEXUS deve:
1. Capturar o erro real, identificar etapa e causa provável, distinguir indisponibilidade, quota, autenticação, rede, falta de recursos e respostas inválidas.
2. Se houver risco crítico confirmado, **alertar imediatamente**, sem esperar o conselho terminar um debate.
3. Preservar um checkpoint seguro e registrar ações já realizadas, **sem segredos**.
4. Tentar corrigir dentro das permissões configuradas na Central, com limite de tentativas e backoff. Antes de repetir ações com efeitos externos, verificar se a tentativa anterior funcionou.
5. Consultar a skill de roteamento de especialistas e selecionar alternativas **já autorizadas, gratuitas, compatíveis e disponíveis**. Nunca habilitar API paga automaticamente.
6. Para tarefas com senha/token, preservar processamento local. Se não houver componente local seguro disponível, **parar a parte sensível**, nunca transferir o segredo para IA externa.
7. Validar os resultados. Se não resolver, informar o erro, alternativas tentadas e o que permanece pendente, mantendo o progresso para retomar sem duplicar ações.
8. Respeitar o orçamento diário, os limites de CPU/RAM e as permissões por categoria; o conselho não pode ampliar seus próprios privilégios.

## Cuidados
- **Idempotência:** não repetir cegamente pagamentos, mensagens, exclusões, alterações de contas ou outras operações que podem causar efeito duplicado.
- **Privacidade:** logs, checkpoints e relatórios nunca armazenam credenciais em claro.
- **Honestidade:** distinguir operação iniciada, não confirmada, concluída e verificada.
- **Sem loops infinitos:** encerrar tentativas diante de limite de tempo, quota, recursos, incerteza ou risco.
- **Retomada:** ao voltar conexão/provedor/PC, primeiro confirmar estado e efeitos prévios.

## Testes de aceite após homologação do MARK original
Simular quota de modelo gratuito, queda da rede, erro de ferramenta, indisponibilidade do modelo local, tarefa parcial, retorno falso de sucesso e ação não idempotente. Verificar ausência de cobrança, exposição de segredos, repetição de efeito e execução sem autorização.

**Status:** especificação aprovada. Nenhum código, serviço ou integração do MARK foi alterado.
