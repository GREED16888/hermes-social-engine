from datetime import datetime
from pathlib import Path
import sqlite3
from .models import PostJob, STATUS_SCHEDULED, STATUS_PUBLISHING, utcnow
from .media import inspect_media
SCHEMA="""
CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT, platform TEXT NOT NULL, content TEXT NOT NULL, media_path TEXT, scheduled_at TEXT NOT NULL, status TEXT NOT NULL, provider_post_id TEXT, release_url TEXT, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, event_type TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS media(id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL);
"""
class Store:
    def __init__(self,path:Path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.conn=sqlite3.connect(self.path); self.conn.row_factory=sqlite3.Row
    def init(self): self.conn.executescript(SCHEMA); self.conn.commit()
    def register_media(self,media_path):
        info=inspect_media(media_path)
        if not info: return None
        now=utcnow().isoformat()
        self.conn.execute("INSERT OR IGNORE INTO media(path,sha256,mime,size,created_at) VALUES(?,?,?,?,?)",(info['path'],info['sha256'],info['mime'],info['size'],now))
        self.conn.commit(); return info
    def add_post(self,platform,content,scheduled_at,media_path=None,status=STATUS_SCHEDULED):
        media_info=self.register_media(media_path) if media_path else None
        if media_info:
            duplicate = self.conn.execute(
                """
                SELECT p.id, p.media_path, p.status
                FROM posts p
                JOIN media m ON m.path = p.media_path
                WHERE p.platform=? AND m.sha256=? AND p.status IN ('scheduled','publishing','posted')
                ORDER BY p.id DESC LIMIT 1
                """,
                (platform, media_info['sha256']),
            ).fetchone()
            if duplicate:
                raise ValueError(
                    f"duplicate media blocked for platform={platform}: "
                    f"sha256={media_info['sha256']} already used by post_id={duplicate['id']} "
                    f"status={duplicate['status']} path={duplicate['media_path']}"
                )
        now=utcnow().isoformat(); cur=self.conn.execute("INSERT INTO posts(platform,content,media_path,scheduled_at,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(platform,content,media_path,scheduled_at.isoformat(),status,now,now)); pid=int(cur.lastrowid); self.event(pid,"created",platform); 
        if media_info: self.event(pid,"media_registered",media_info['sha256'])
        self.conn.commit(); return pid
    def list_posts(self): return [self._row(r) for r in self.conn.execute("SELECT * FROM posts ORDER BY scheduled_at,id").fetchall()]
    def list_events(self,post_id=None):
        if post_id is None: rows=self.conn.execute("SELECT * FROM events ORDER BY id").fetchall()
        else: rows=self.conn.execute("SELECT * FROM events WHERE post_id=? ORDER BY id",(post_id,)).fetchall()
        return [dict(r) for r in rows]
    def due_posts(self,now=None): now=now or utcnow(); return [self._row(r) for r in self.conn.execute("SELECT * FROM posts WHERE status=? AND scheduled_at<=? ORDER BY scheduled_at,id",(STATUS_SCHEDULED,now.isoformat())).fetchall()]
    def claim(self,pid):
        cur=self.conn.execute("UPDATE posts SET status=?, attempts=attempts+1, updated_at=? WHERE id=? AND status=?",(STATUS_PUBLISHING,utcnow().isoformat(),pid,STATUS_SCHEDULED)); self.conn.commit(); return cur.rowcount==1
    def mark_posted(self,pid,provider_post_id,release_url): self.conn.execute("UPDATE posts SET status='posted', provider_post_id=?, release_url=?, last_error=NULL, updated_at=? WHERE id=?",(provider_post_id,release_url,utcnow().isoformat(),pid)); self.event(pid,"posted",release_url); self.conn.commit()
    def mark_failed(self,pid,error): self.conn.execute("UPDATE posts SET status='failed', last_error=?, updated_at=? WHERE id=?",(error,utcnow().isoformat(),pid)); self.event(pid,"failed",error); self.conn.commit()
    def retry_failed(self,pid=None):
        now=utcnow().isoformat()
        if pid is None: cur=self.conn.execute("UPDATE posts SET status='scheduled', last_error=NULL, updated_at=? WHERE status='failed'",(now,))
        else: cur=self.conn.execute("UPDATE posts SET status='scheduled', last_error=NULL, updated_at=? WHERE id=? AND status='failed'",(now,pid))
        self.conn.commit(); return cur.rowcount
    def event(self,pid,t,msg): self.conn.execute("INSERT INTO events(post_id,event_type,message,created_at) VALUES(?,?,?,?)",(pid,t,msg,utcnow().isoformat()))
    def _row(self,r): return PostJob(r["id"],r["platform"],r["content"],datetime.fromisoformat(r["scheduled_at"]),r["status"],r["media_path"],r["provider_post_id"],r["release_url"],r["attempts"],r["last_error"])
