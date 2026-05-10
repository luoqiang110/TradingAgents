from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path

from .models import AnalysisJob, AnalysisRequest, JobStatus, utc_now


class JobStore:
    def __init__(self, runtime_dir: str | Path) -> None:
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_dir / "jobs.json"
        self._lock = threading.RLock()
        self._jobs: dict[str, AnalysisJob] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._jobs = {
                item["id"]: AnalysisJob.model_validate(item) for item in payload
            }
        except Exception:
            self._jobs = {}

    def _persist(self) -> None:
        payload = [
            job.model_dump(mode="json")
            for job in sorted(
                self._jobs.values(), key=lambda item: item.created_at, reverse=True
            )
        ]
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def create(self, request: AnalysisRequest) -> AnalysisJob:
        with self._lock:
            job = AnalysisJob(
                id=uuid.uuid4().hex,
                status=JobStatus.queued,
                request=request,
            )
            self._jobs[job.id] = job
            self._persist()
            return job

    def get(self, job_id: str) -> AnalysisJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, limit: int = 50) -> list[AnalysisJob]:
        with self._lock:
            jobs = sorted(
                self._jobs.values(), key=lambda item: item.created_at, reverse=True
            )
            return jobs[:limit]

    def update(self, job_id: str, **updates) -> AnalysisJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            data = job.model_dump()
            data.update(updates)
            data["updated_at"] = utc_now()
            updated = AnalysisJob.model_validate(data)
            self._jobs[job_id] = updated
            self._persist()
            return updated

    def delete(self, job_id: str) -> bool:
        with self._lock:
            existed = self._jobs.pop(job_id, None) is not None
            if existed:
                self._persist()
            return existed

    def mark_interrupted(self) -> None:
        with self._lock:
            changed = False
            for job in list(self._jobs.values()):
                if job.status in {JobStatus.queued, JobStatus.running}:
                    self.update(
                        job.id,
                        status=JobStatus.failed,
                        completed_at=utc_now(),
                        error="Server restarted before this analysis finished.",
                    )
                    changed = True
            if changed:
                self._persist()

