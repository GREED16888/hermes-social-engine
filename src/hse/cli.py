import argparse
from pathlib import Path
from .models import parse_when
from .store import Store
from .scheduler import Scheduler
from .notify import build_notifier, Notification

HOME = Path("/mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine")
DATA = HOME / "data"
DB = DATA / "hse.sqlite3"

def main(argv=None):
    p = argparse.ArgumentParser(prog="hse")
    p.add_argument("--db", default=str(DB))
    p.add_argument("--data-dir", default=str(DATA))
    p.add_argument("--notify", choices=["file", "none"], default="file")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    a = sub.add_parser("add")
    a.add_argument("--platform", required=True, choices=["dryrun", "local_json", "telegram", "youtube", "facebook", "tiktok"])
    a.add_argument("--content", required=True)
    a.add_argument("--when", required=True)
    a.add_argument("--media-path")
    sub.add_parser("run-due")
    sub.add_parser("list")
    ev = sub.add_parser("events")
    ev.add_argument("--post-id", type=int)
    rt = sub.add_parser("retry-failed")
    rt.add_argument("--post-id", type=int)
    nt = sub.add_parser("notify-test")
    nt.add_argument("--message", default="Hermes Social Engine notification test")
    sub.add_parser("platform-status")
    ya = sub.add_parser("youtube-auth")
    ya.add_argument("--client-secrets", default=str(HOME / "secrets" / "google_oauth_client.json"))
    ya.add_argument("--token-file", default=str(DATA / "youtube_token.json"))
    ya.add_argument("--port", type=int, default=8088)
    mt = sub.add_parser("meta-template")
    mt.add_argument("--app-id", default="1464342022114588")
    mt.add_argument("--app-file", default=str(HOME / "secrets" / "meta_app.json"))
    ma = sub.add_parser("meta-auth")
    ma.add_argument("--app-file", default=str(HOME / "secrets" / "meta_app.json"))
    ma.add_argument("--token-file", default=str(DATA / "meta_token.json"))
    ma.add_argument("--port", type=int, default=8089)
    sub.add_parser("meta-status")
    tt = sub.add_parser("tiktok-template")
    tt.add_argument("--app-file", default=str(HOME / "secrets" / "tiktok_app.json"))
    ta = sub.add_parser("tiktok-auth")
    ta.add_argument("--app-file", default=str(HOME / "secrets" / "tiktok_app.json"))
    ta.add_argument("--token-file", default=str(DATA / "tiktok_token.json"))
    ta.add_argument("--port", type=int, default=8090)
    tac = sub.add_parser("tiktok-auth-code")
    tac.add_argument("--code", required=True)
    tac.add_argument("--app-file", default=str(HOME / "secrets" / "tiktok_app.json"))
    tac.add_argument("--token-file", default=str(DATA / "tiktok_token.json"))
    sub.add_parser("tiktok-status")
    sub.add_parser("tiktok-creator-info")

    args = p.parse_args(argv)
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    s = Store(Path(args.db))
    s.init()

    if args.cmd == "init":
        print(f"OK db={args.db}")
        return 0
    if args.cmd == "add":
        print(f"ADDED id={s.add_post(args.platform, args.content, parse_when(args.when), args.media_path)}")
        return 0
    if args.cmd == "run-due":
        notifier = build_notifier(data_dir, args.notify)
        for pid, st in Scheduler(s, data_dir, notifier).run_due():
            print(f"{pid}\t{st}")
        return 0
    if args.cmd == "list":
        print("id\tstatus\tplatform\tattempts\tscheduled_at\trelease_url\tcontent")
        for j in s.list_posts():
            print(f"{j.id}\t{j.status}\t{j.platform}\t{j.attempts}\t{j.scheduled_at.isoformat()}\t{j.release_url or ''}\t{j.content[:80]}")
        return 0
    if args.cmd == "events":
        print("id\tpost_id\ttype\tcreated_at\tmessage")
        for e in s.list_events(args.post_id):
            print(f"{e['id']}\t{e['post_id'] or ''}\t{e['event_type']}\t{e['created_at']}\t{e['message']}")
        return 0
    if args.cmd == "retry-failed":
        print(f"RETRIED {s.retry_failed(args.post_id)}")
        return 0
    if args.cmd == "notify-test":
        build_notifier(data_dir, args.notify).send(Notification('info', 'HSE notify-test', args.message, None))
        print("NOTIFIED")
        return 0
    if args.cmd == "platform-status":
        from .providers import credential_status
        for k,v in credential_status().items():
            print(f"{k}={'ready' if v else 'missing_credentials'}")
        return 0
    if args.cmd == "youtube-auth":
        from .providers.youtube import run_oauth_local_server, client_id_preview
        print(f"Using OAuth client {client_id_preview(Path(args.client_secrets))}; secret=[REDACTED]", flush=True)
        token = run_oauth_local_server(Path(args.client_secrets), Path(args.token_file), args.port)
        print(f"YOUTUBE_TOKEN_SAVED={token}")
        return 0
    if args.cmd == "meta-template":
        from .providers.meta import build_app_template
        path = build_app_template(Path(args.app_file), args.app_id)
        print(f"META_APP_TEMPLATE={path}")
        print("Edit app_secret locally; never send it in chat.")
        return 0
    if args.cmd == "meta-auth":
        from .providers.meta import run_oauth_local_server, app_id_preview, token_summary
        print(f"Using Meta app {app_id_preview(Path(args.app_file))}; secret=[REDACTED]", flush=True)
        token = run_oauth_local_server(Path(args.app_file), Path(args.token_file), args.port)
        print(f"META_TOKEN_SAVED={token}")
        print(token_summary(token))
        return 0
    if args.cmd == "meta-status":
        from .providers.meta import token_summary, DEFAULT_META_TOKEN
        print(token_summary(DEFAULT_META_TOKEN))
        return 0
    if args.cmd == "tiktok-template":
        from .providers.tiktok import build_app_template
        path = build_app_template(Path(args.app_file))
        print(f"TIKTOK_APP_TEMPLATE={path}")
        print("Edit client_key/client_secret locally; never send secrets in chat.")
        return 0
    if args.cmd == "tiktok-auth":
        from .providers.tiktok import run_oauth_local_server, client_key_preview, token_summary
        print(f"Using TikTok app {client_key_preview(Path(args.app_file))}; secret=[REDACTED]", flush=True)
        token = run_oauth_local_server(Path(args.app_file), Path(args.token_file), args.port)
        print(f"TIKTOK_TOKEN_SAVED={token}")
        print(token_summary(token))
        return 0
    if args.cmd == "tiktok-auth-code":
        from .providers.tiktok import exchange_auth_code, token_summary
        token = exchange_auth_code(args.code, Path(args.app_file), Path(args.token_file))
        print(f"TIKTOK_TOKEN_SAVED={token}")
        print(token_summary(token))
        return 0
    if args.cmd == "tiktok-status":
        from .providers.tiktok import token_summary, DEFAULT_TIKTOK_TOKEN
        print(token_summary(DEFAULT_TIKTOK_TOKEN))
        return 0
    if args.cmd == "tiktok-creator-info":
        from .providers.tiktok import creator_info
        import json
        print(json.dumps(creator_info(), ensure_ascii=False, indent=2))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
