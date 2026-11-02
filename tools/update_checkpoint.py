"""Append a factual, timestamped development checkpoint without rewriting history."""
import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "CHECKPOINT.md"
STATUSES = {"CONCLUÍDA E TESTADA", "EM ANDAMENTO", "PENDENTE", "BLOQUEADA"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--task",required=True)
    parser.add_argument("--status",required=True,choices=sorted(STATUSES))
    parser.add_argument("--summary",required=True)
    parser.add_argument("--tests",default="Não executados nesta atualização.")
    parser.add_argument("--files",default="Não especificados.")
    parser.add_argument("--next",default="Consultar NEXUS_EXECUTION_PLAN.md.")
    args=parser.parse_args()
    for label,value in (("task",args.task),("summary",args.summary),("tests",args.tests),
                        ("files",args.files),("next",args.next)):
        if len(value)>3000 or "\x00" in value: parser.error(f"invalid {label}")
    stamp=datetime.now(timezone.utc).isoformat(timespec="seconds")
    block=(f"\n\n## Registro de execução — {stamp}\n\n"
           f"- Tarefa: `{args.task}` — **{args.status}**\n"
           f"- Resumo: {args.summary}\n- Testes (resultado observado): {args.tests}\n"
           f"- Arquivos: {args.files}\n- Próxima tarefa: {args.next}\n")
    with CHECKPOINT.open("a",encoding="utf-8",newline="\n") as file: file.write(block)
    print(f"Checkpoint appended: {args.task} ({args.status})")

if __name__=="__main__": main()
