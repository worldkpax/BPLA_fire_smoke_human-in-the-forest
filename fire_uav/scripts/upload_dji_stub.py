#!/usr/bin/env python3
"""
Заглушка: показывает, как будет загружаться маршрут в DJI SDK.
"""
import sys, time, json

def main(plan_path: str):
    print("=== DJI upload stub ===")
    print(f"Would parse {plan_path} and send waypoints via DJI Mobile SDK…")
    time.sleep(1)
    print("✔ mission uploaded (stub)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: upload_dji_stub.py <mission.plan>")
        sys.exit(1)
    main(sys.argv[1])
