"""Generates the synthetic sample CSV fixture used by tests and the demo seed.

Mimics session_20260813_111730.csv characteristics per the spec (section 4):
~50 Hz but not perfectly regular (median dt=20ms, max gap ~86ms), ~4 min,
single sensor, no filename metadata, accel ~+-2g, gyro up to ~360 deg/s.
This is synthetic data generated for development/testing -- it is NOT the
real uploaded sample file, which was not available in this environment.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def generate_sample(duration_s: float = 240.0, fs_hz: float = 50.0) -> pd.DataFrame:
    n = int(duration_s * fs_hz)
    dt_ms = 1000.0 / fs_hz

    # Mostly-regular timestamps with jitter and a few larger gaps.
    jitter = RNG.normal(0, 1.5, n)
    timestamps = np.cumsum(np.full(n, dt_ms) + jitter)
    # Inject a handful of larger gaps (up to ~86ms) matching the spec's fixture.
    gap_indices = RNG.choice(n, size=6, replace=False)
    for idx in gap_indices:
        if idx > 0:
            timestamps[idx:] += RNG.uniform(40, 86)
    timestamps = np.round(timestamps).astype(int)

    t = timestamps / 1000.0

    # Simulate ~10s rest, then walking bouts with ~1.8 Hz step frequency,
    # separated by short pauses, with realistic gravity + gait dynamics.
    walking_freq_hz = 1.8
    gait_signal = 0.35 * np.sin(2 * np.pi * walking_freq_hz * t)
    envelope = np.ones(n)
    still_samples = int(10 * fs_hz)
    envelope[:still_samples] = 0.0
    pause_start = int(n * 0.55)
    pause_end = pause_start + int(5 * fs_hz)
    envelope[pause_start:pause_end] = 0.0

    accel_x = 0.05 * RNG.normal(size=n) + gait_signal * envelope
    accel_y = 0.05 * RNG.normal(size=n) + 0.15 * np.sin(2 * np.pi * walking_freq_hz * t + 0.5) * envelope
    accel_z = 1.0 + 0.1 * RNG.normal(size=n) + 0.2 * np.sin(2 * np.pi * walking_freq_hz * t + 1.0) * envelope

    gyro_x = 60 * np.sin(2 * np.pi * walking_freq_hz * t) * envelope + 5 * RNG.normal(size=n)
    gyro_y = 40 * np.sin(2 * np.pi * walking_freq_hz * t + 0.3) * envelope + 5 * RNG.normal(size=n)
    gyro_z = 20 * np.sin(2 * np.pi * walking_freq_hz * t + 0.8) * envelope + 5 * RNG.normal(size=n)

    return pd.DataFrame({
        "timestamp_ms": timestamps,
        "accel_x": np.round(accel_x, 4),
        "accel_y": np.round(accel_y, 4),
        "accel_z": np.round(accel_z, 4),
        "gyro_x": np.round(gyro_x, 3),
        "gyro_y": np.round(gyro_y, 3),
        "gyro_z": np.round(gyro_z, 3),
    })


if __name__ == "__main__":
    df = generate_sample()
    df.to_csv("session_20260813_111730.csv", index=False)
    print(f"Wrote {len(df)} rows")
