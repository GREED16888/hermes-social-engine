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
    a.add_argument("--account", help="Named account/channel key, e.g. youtube_en or youtube_th")
    acct = sub.add_parser("accounts")
    acct.add_argument("--platform")
    sub.add_parser("run-due")
    sub.add_parser("list")
    ev = sub.add_parser("events")
    ev.add_argument("--post-id", type=int)
    rt = sub.add_parser("retry-failed")
    rt.add_argument("--post-id", type=int)
    nt = sub.add_parser("notify-test")
    nt.add_argument("--message", default="Hermes Social Engine notification test")
    sub.add_parser("platform-status")
    ds = sub.add_parser("dashboard")
    ds.add_argument("--host", default="127.0.0.1")
    ds.add_argument("--port", type=int, default=8000)
    ds.add_argument("--reload", action="store_true")
    ya = sub.add_parser("youtube-auth")
    ya.add_argument("--client-secrets", default=str(HOME / "secrets" / "google_oauth_client.json"))
    ya.add_argument("--token-file", help="Override token output path. Prefer --account for multi-channel.")
    ya.add_argument("--account", help="Named YouTube channel/account key, e.g. youtube_en or youtube_th")
    ya.add_argument("--label", help="Human label to store after OAuth verification")
    ya.add_argument("--language", choices=["th", "en", "other"], help="Channel language label")
    ya.add_argument("--max-posts-per-day", type=int, default=1)
    ya.add_argument("--port", type=int, default=8088)
    ys = sub.add_parser("youtube-status")
    ys.add_argument("--account")
    ys.add_argument("--token-file")
    mt = sub.add_parser("meta-template")
    mt.add_argument("--app-id", default="1464342022114588")
    mt.add_argument("--app-file", default=str(HOME / "secrets" / "meta_app.json"))
    ma = sub.add_parser("meta-auth")
    ma.add_argument("--app-file", default=str(HOME / "secrets" / "meta_app.json"))
    ma.add_argument("--token-file", default=str(DATA / "meta_token.json"))
    ma.add_argument("--port", type=int, default=8089)
    au = sub.add_parser("media-audit")
    au.add_argument("media_paths", nargs="+", help="Media files to preflight before batch upload")
    au.add_argument("--similar-threshold", type=float, default=10.0)
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
        print(f"ADDED id={s.add_post(args.platform, args.content, parse_when(args.when), args.media_path, account=args.account)}")
        return 0
    if args.cmd == "accounts":
        print("platform\taccount\tstatus\tlanguage\tmax_posts_per_day\tlabel\ttoken_path")
        for row in s.list_accounts(args.platform):
            print(f"{row['platform']}\t{row['account']}\t{row['status']}\t{row.get('language') or ''}\t{row['max_posts_per_day']}\t{row.get('label') or ''}\t{row.get('token_path') or ''}")
        return 0
    if args.cmd == "run-due":
        notifier = build_notifier(data_dir, args.notify)
        for pid, st in Scheduler(s, data_dir, notifier).run_due():
            print(f"{pid}\t{st}")
        return 0
    if args.cmd == "list":
        print("id\tstatus\tplatform\taccount\tattempts\tscheduled_at\trelease_url\tcontent")
        for j in s.list_posts():
            acct = j.account or ''
            print(f"{j.id}\t{j.status}\t{j.platform}\t{acct}\t{j.attempts}\t{j.scheduled_at.isoformat()}\t{j.release_url or ''}\t{j.content[:80]}")
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
    if args.cmd == "dashboard":
        import uvicorn
        uvicorn.run("hse.dashboard.main:app", host=args.host, port=args.port, reload=args.reload)
        return 0
    if args.cmd == "youtube-auth":
        from .providers.youtube import run_oauth_local_server, client_id_preview, channel_identity
        from .accounting import youtube_token_path
        print(f"Using OAuth client {client_id_preview(Path(args.client_secrets))}; secret=[REDACTED]", flush=True)
        token_path = Path(args.token_file) if args.token_file else youtube_token_path(data_dir, args.account)
        token = run_oauth_local_server(Path(args.client_secrets), token_path, args.port)
        print(f"YOUTUBE_TOKEN_SAVED={token}")
        try:
            ident = channel_identity(token)
            print(f"YOUTUBE_CHANNEL_ID={ident.get('channel_id') or ''}")
            print(f"YOUTUBE_CHANNEL_TITLE={ident.get('title') or ''}")
            if args.account:
                s.upsert_account('youtube', args.account, label=args.label or ident.get('title'), language=args.language, token_path=str(token), max_posts_per_day=args.max_posts_per_day)
                print(f"YOUTUBE_ACCOUNT_REGISTERED={args.account}")
        except Exception as e:
            print(f"YOUTUBE_CHANNEL_VERIFY_FAILED={type(e).__name__}: {e}")
            if args.account:
                s.upsert_account('youtube', args.account, label=args.label, language=args.language, token_path=str(token), max_posts_per_day=args.max_posts_per_day, status='needs_verify')
        return 0
    if args.cmd == "youtube-status":
        from .providers.youtube import channel_identity
        from .accounting import youtube_token_path
        token_path = Path(args.token_file) if args.token_file else youtube_token_path(data_dir, args.account)
        print(f"YOUTUBE_TOKEN_FILE={token_path}")
        ident = channel_identity(token_path)
        print(f"YOUTUBE_CHANNEL_ID={ident.get('channel_id') or ''}")
        print(f"YOUTUBE_CHANNEL_TITLE={ident.get('title') or ''}")
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
    if args.cmd == "media-audit":
        from .media import audit_media_batch
        result = audit_media_batch(args.media_paths, args.similar_threshold)
        for left, right, sha in result.exact_duplicates:
            print(f"EXACT_DUPLICATE\t{sha}\t{left}\t{right}")
        for left, right, distance in result.similar_videos:
            print(f"SIMILAR_VIDEO\tdistance={distance:.2f}\t{left}\t{right}")
        for warning in result.warnings:
            print(f"WARNING\t{warning}")
        print("MEDIA_AUDIT_OK" if result.ok else "MEDIA_AUDIT_FAILED")
        return 0 if result.ok else 2
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
