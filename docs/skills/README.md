# Skills — N.E.X.U.S.

Este diretório contém o catálogo de pesquisa, o inventário instalado e as decisões de auditoria de Agent Skills para o desenvolvimento do N.E.X.U.S.

## Documentos

- [Catálogo de candidatos](SKILLS_CATALOG.md)
- [Relatório de instalação anterior](INSTALLATION_AUDIT.md)
- [Auditoria consolidada e decisões](FINAL_AUDIT.md)

## Para o Codex

1. Consulte o catálogo e a auditoria consolidada antes de adicionar novas skills.
2. As 46 skills atualmente instaladas estão em `.agents/skills/`; a auditoria registra a origem e as ressalvas conhecidas.
3. Não execute scripts de skills desconhecidas durante a inspeção.
4. Antes de incorporar novos pacotes, confira caminho, licença, conteúdo integral, scripts, dependências, permissões e comportamento de rede.
5. Skills que exigem scripts, referências, CLIs ou servidores devem ser instaladas com todos os arquivos necessários; não copie somente o `SKILL.md` se isso deixar o pacote incompleto.
6. Não envie dados privados, áudio, credenciais ou arquivos do usuário a serviços externos sem autorização específica.
7. Não execute servidores MCP desconhecidos durante scanners.
8. Preserve aprovação humana específica para ações sensíveis.

## Distinção importante

- **Skill de desenvolvimento:** instruções que ajudam o Codex a construir, testar e manter o N.E.X.U.S.
- **Skill do runtime:** capacidade que poderá ser oferecida pelo próprio N.E.X.U.S. quando estiver implementado.
- **Componente de runtime:** código real do produto, como memória, orquestrador, roteador de modelos e sistema de permissões.

Uma skill de desenvolvimento não implementa automaticamente uma capacidade no produto.

## Aprovação

O usuário autorizou a implementação das candidatas restantes do catálogo original. Essa autorização cobre a triagem e incorporação dos itens adequados, não elimina as verificações de segurança, licença, compatibilidade, privacidade ou os gates específicos de ações sensíveis. Novas candidatas fora do escopo catalogado devem ser avaliadas antes de serem adicionadas.
