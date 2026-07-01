import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.services.config_handler import get_config, get_form_profile
from app.services.scheduler_runner import DATA_DIR, LOGS_DIR, RUNS_DIR, build_payload

LOCK_FILE = DATA_DIR / "scheduler.lock"


def main() -> int:
    parser = argparse.ArgumentParser(description="Tara Caraka scheduler for Ubuntu/Linux.")
    parser.add_argument("--mode", choices=["dryrun", "submit"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--record-mode", choices=["dryrun", "submit", "submit-test"], default=None)
    parser.add_argument("--attempt-times-override", default="")
    args = parser.parse_args()

    runner = Scheduler(args.run_id)
    try:
        if args.mode == "dryrun":
            runner.run_dryrun(args.record_mode or "dryrun")
        else:
            runner.run_submit(args.record_mode or "submit", args.attempt_times_override)
        return 0
    except Exception as exc:
        runner.fail(str(exc))
        return 1
    finally:
        runner.close()


class Scheduler:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = LOGS_DIR / f"{run_id}.log"
        self.run_file = RUNS_DIR / f"{run_id}.json"
        self.record: dict = self._load_existing_record()

    def run_dryrun(self, record_mode: str) -> None:
        config = get_config()
        profile = get_form_profile()
        payload = build_payload(config, profile)
        started_at = datetime.now().isoformat()

        self.log("============================================")
        self.log(f"Tara Caraka Ceria -- DryRun ({record_mode})")
        self.log(f"Run ID : {self.run_id}")
        self.log("============================================")
        self.log(f"Endpoint : {profile.get('responseUrl', '(unknown)')}")
        self.log(f"fbzx     : {profile.get('fbzx', '(none)')}")
        self.log("")
        self.log("Payload preview:")
        for key, value in payload.items():
            if isinstance(value, list):
                for item in value:
                    self.log(f"  {key} = {item}")
            else:
                self.log(f"  {key} = {value}")
        self.log("")
        self.log("Mode DryRun -- form TIDAK dikirim.")
        self.log("Status: SUCCESS")

        self.record.update({
            "runId": self.run_id,
            "sessionId": profile.get("sessionId", ""),
            "sessionLabel": profile.get("sessionLabel", ""),
            "mode": record_mode,
            "startedAt": started_at,
            "status": "success",
            "responseUrl": profile.get("responseUrl", ""),
            "payload": payload,
            "logFile": str(self.log_file),
            "configSnapshot": config,
        })
        self._save_record()

    def run_submit(self, record_mode: str, attempt_times_override: str) -> None:
        if LOCK_FILE.exists():
            existing = LOCK_FILE.read_text(encoding="utf-8").strip()
            raise RuntimeError(f"Scheduler sudah aktif (lock: {existing}). Batalkan dulu.")

        config = get_config()
        profile = get_form_profile()
        response_url = profile.get("responseUrl", "")
        if not response_url:
            raise RuntimeError("responseUrl kosong. Parse Google Form terlebih dahulu.")

        payload = build_payload(config, profile)
        body = urlencode(_flatten_payload(payload))
        target_times = _resolve_attempt_times(config, attempt_times_override)
        attempt_datetimes = _today_datetimes(target_times)

        LOCK_FILE.write_text(self.run_id, encoding="utf-8")
        try:
            self.log("============================================")
            self.log(f"Tara Caraka Ceria -- Submit ({record_mode})")
            self.log(f"Run ID : {self.run_id}")
            self.log("============================================")
            self.log(f"Response URL : {response_url}")
            self.log("Jadwal pengiriman:")
            for attempt_time in attempt_datetimes:
                self.log(f"  {attempt_time.isoformat()}")

            self.record.update({
                "runId": self.run_id,
                "sessionId": profile.get("sessionId", ""),
                "sessionLabel": profile.get("sessionLabel", ""),
                "mode": record_mode,
                "startedAt": datetime.now().isoformat(),
                "status": "scheduled",
                "responseUrl": response_url,
                "logFile": str(self.log_file),
                "attemptTimes": target_times,
                "results": [],
            })
            self._save_record()

            results = []
            overall_status = "success"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": response_url,
            }

            for attempt_time in attempt_datetimes:
                if not self._lock_still_active():
                    self.log("Lock sudah dihapus. Scheduler dibatalkan.")
                    overall_status = "cancelled"
                    break

                wait_seconds = (attempt_time - datetime.now()).total_seconds()
                if wait_seconds > 0:
                    self.log(f"Menunggu {round(wait_seconds, 1)} detik hingga {attempt_time.isoformat()} ...")
                    self._sleep_with_cancel_check(wait_seconds)

                if not self._lock_still_active():
                    self.log("Lock sudah dihapus. Scheduler dibatalkan.")
                    overall_status = "cancelled"
                    break

                self.log(f"Mengirim attempt ke {attempt_time.isoformat()} ...")
                try:
                    response = httpx.post(
                        response_url,
                        content=body,
                        headers=headers,
                        timeout=10.0,
                        follow_redirects=True,
                    )
                    self.log(f"  HTTP {response.status_code}")
                    results.append({
                        "time": attempt_time.isoformat(),
                        "status": response.status_code,
                        "error": None,
                    })
                    if response.status_code >= 400:
                        overall_status = "partial"
                except httpx.HTTPError as exc:
                    self.log(f"  ERROR: {exc}")
                    results.append({
                        "time": attempt_time.isoformat(),
                        "status": None,
                        "error": str(exc),
                    })
                    overall_status = "partial"

            self.record["status"] = overall_status
            self.record["results"] = results
            self.record["endedAt"] = datetime.now().isoformat()
            self._save_record()
            self.log(f"Status akhir: {overall_status}")
        finally:
            if LOCK_FILE.exists() and LOCK_FILE.read_text(encoding="utf-8").strip() == self.run_id:
                LOCK_FILE.unlink()
                self.log("Lock dihapus.")

    def fail(self, message: str) -> None:
        self.log(f"FATAL ERROR: {message}")
        self.record.update({
            "runId": self.run_id,
            "status": "error",
            "error": message,
            "endedAt": datetime.now().isoformat(),
            "logFile": str(self.log_file),
        })
        self._save_record()
        if LOCK_FILE.exists() and LOCK_FILE.read_text(encoding="utf-8").strip() == self.run_id:
            LOCK_FILE.unlink()
            self.log("Lock dihapus setelah error.")

    def close(self) -> None:
        pass

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {message}\n")

    def _load_existing_record(self) -> dict:
        if not self.run_file.exists():
            return {}
        try:
            return json.loads(self.run_file.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}

    def _save_record(self) -> None:
        self.run_file.write_text(
            json.dumps(self.record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _lock_still_active(self) -> bool:
        return LOCK_FILE.exists() and LOCK_FILE.read_text(encoding="utf-8").strip() == self.run_id

    def _sleep_with_cancel_check(self, wait_seconds: float) -> None:
        deadline = datetime.now() + timedelta(seconds=wait_seconds)
        while datetime.now() < deadline:
            if not self._lock_still_active():
                return
            remaining = (deadline - datetime.now()).total_seconds()
            time.sleep(min(1.0, max(0.0, remaining)))


def _flatten_payload(payload: dict) -> list[tuple[str, str]]:
    parts = []
    for key, value in payload.items():
        if isinstance(value, list):
            for item in value:
                parts.append((key, str(item)))
        else:
            parts.append((key, str(value)))
    return parts


def _resolve_attempt_times(config: dict, override: str) -> list[str]:
    if override:
        return [item.strip() for item in override.split(",") if item.strip()]
    configured = config.get("attemptTimes") or []
    return configured or ["12:59:58", "12:59:59", "13:00:00"]


def _today_datetimes(times: list[str]) -> list[datetime]:
    today = datetime.now().date()
    result = []
    for raw in times:
        parsed = datetime.strptime(raw, "%H:%M:%S").time()
        result.append(datetime.combine(today, parsed))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
