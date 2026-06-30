from pathlib import Path
from hse.store import Store
from hse.models import parse_when
from hse.scheduler import Scheduler
def test_dryrun(tmp_path:Path):
    s=Store(tmp_path/"x.db"); s.init(); pid=s.add_post("dryrun","hello",parse_when("now")); assert Scheduler(s,tmp_path).run_due()==[(pid,"posted")]; assert s.list_posts()[0].status=="posted"
def test_local_json(tmp_path:Path):
    s=Store(tmp_path/"x.db"); s.init(); pid=s.add_post("local_json","hello",parse_when("now")); assert Scheduler(s,tmp_path).run_due()==[(pid,"posted")]; assert (tmp_path/"published"/f"post_{pid}.json").exists()
def test_empty_fails(tmp_path:Path):
    s=Store(tmp_path/"x.db"); s.init(); pid=s.add_post("dryrun","   ",parse_when("now")); assert Scheduler(s,tmp_path).run_due()==[(pid,"failed")]; assert s.list_posts()[0].status=="failed"
