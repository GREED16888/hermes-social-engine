from .providers import get_provider
from .notify import build_notifier, Notification

class Scheduler:
    def __init__(self, store, data_dir, notifier=None):
        self.store = store
        self.data_dir = data_dir
        self.notifier = notifier or build_notifier(data_dir)

    def run_due(self):
        out = []
        for job in self.store.due_posts():
            if not self.store.claim(job.id):
                out.append((job.id, "skipped-not-claimed"))
                continue
            claimed = next(p for p in self.store.list_posts() if p.id == job.id)
            try:
                r = get_provider(claimed.platform, self.data_dir, claimed.account).publish(claimed)
                self.store.mark_posted(claimed.id, r.provider_post_id, r.release_url)
                self.notifier.send(Notification('success', 'HSE posted', f'{claimed.platform}: {r.release_url}', claimed.id))
                out.append((claimed.id, "posted"))
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                self.store.mark_failed(claimed.id, err)
                self.notifier.send(Notification('error', 'HSE failed', f'{claimed.platform}: {err}', claimed.id))
                out.append((claimed.id, "failed"))
        return out
