#!/usr/bin/env python3
"""
Заглушка симуляции AirSim ― позже замените вызовом настоящего API.
"""
import sys, time

def main(plan_path: str):
    print("=== AirSim stub ===")
    print(f"Would load {plan_path} into AirSim environment…")
    time.sleep(1)
    print("✔ done (stub)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: airsim_stub.py <mission.plan>")
        sys.exit(1)
    main(sys.argv[1])
