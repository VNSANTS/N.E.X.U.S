"""Local development server entry point."""
import argparse
import getpass
import logging
from wsgiref.simple_server import make_server

from .api import create_app
from .auth import AuthStore
from .engine import LearningEngine


def serve(argv=None):
    from .envfile import load_local_env
    load_local_env()
    parser = argparse.ArgumentParser(description="Run the local N.E.X.U.S. API")
    parser.add_argument("--db", default="nexus_learning.db")
    parser.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    engine = LearningEngine(args.db)
    auth = AuthStore(engine)
    if not auth.has_users():
        print("Primeira inicialização: crie uma senha local (mínimo 14 caracteres).")
        username = input("Usuário [owner]: ").strip() or "owner"
        password = getpass.getpass("Senha: ")
        confirmation = getpass.getpass("Confirme a senha: ")
        if password != confirmation:
            raise SystemExit("As senhas não conferem; nenhum usuário foi criado.")
        auth.create_user(username, password)
    app = create_app(engine=engine)
    provider_state = app.provider_manager.status()
    state = provider_state["default"]
    detail = next((item for item in provider_state["providers"] if item["id"] == state["provider"]), {})
    availability = detail.get("availability", "not_checked")
    model = state.get("model") or detail.get("suggested_model") or "not selected"
    with make_server(args.host, args.port, app) as server:
        print(f"N.E.X.U.S. local em http://{args.host}:{args.port}/")
        print(f"Provider: {state['provider']} | model: {model} | {availability}")
        print("Parada: Ctrl+C.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")
        finally:
            engine.close()
