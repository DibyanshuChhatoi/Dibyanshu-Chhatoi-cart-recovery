"""Central configuration for deterministic synthetic data generation."""
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    seed: int = 20261022
    carts: int = 1000
    abandoned_carts: int = 400
    send_attempts: int = 200
    inactivity_minutes: int = 60
    attribution_days: int = 7
    email_cap: int = 2
    sms_cap: int = 2
    cap_window_days: int = 7
    simulation_start: str = "2026-10-01T00:00:00"
    db_path: str = "data/generated/yottaflex.db"
    output_dir: str = "data/generated"
    ground_truth_dir: str = "data/ground_truth"
    reports_dir: str = "data/reports"

    @classmethod
    def from_env(cls):
        return cls(
            seed=int(os.getenv("YOTTAFLEX_SEED", "20261022")),
            carts=int(os.getenv("YOTTAFLEX_CARTS", "1000")),
            abandoned_carts=int(os.getenv("YOTTAFLEX_ABANDONED", "400")),
            send_attempts=int(os.getenv("YOTTAFLEX_SENDS", "200")),
            db_path=os.getenv("YOTTAFLEX_DB", "data/generated/yottaflex.db"),
        )

    def validate(self):
        if self.carts < 1:
            raise ValueError("carts must be at least 1")
        if not 0 <= self.abandoned_carts <= self.carts:
            raise ValueError("abandoned_carts must be between 0 and carts")
        if self.send_attempts < 0:
            raise ValueError("send_attempts cannot be negative")
        if self.send_attempts > self.abandoned_carts:
            raise ValueError("send_attempts cannot exceed abandoned_carts in this starter implementation")
        if self.inactivity_minutes <= 0 or self.attribution_days <= 0:
            raise ValueError("time windows must be positive")
