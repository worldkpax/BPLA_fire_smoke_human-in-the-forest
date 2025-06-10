"""
CLI-вход: fire-detect, fire-plan.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from shapely import wkt

from ..core.camera import CameraParams
from ..core.detection import DetectionEngine
from ..io.recorder import Recorder
from ..utils.logging import setup_logging
from ..flight.planner import FlightPlanner, GridParams, CameraSpec
from ..flight.energy import EnergyModel


# ---------------------------------------------------------------------- #
# detect command
# ---------------------------------------------------------------------- #
def cmd_detect(argv: list[str]) -> None:
    ap = argparse.ArgumentParser("fire-detect")
    ap.add_argument("--model", default="best_yolo11.pt")
    ap.add_argument("--video", default="0", help="'0' for webcam or path")
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--out", default="./artifacts")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(argv)

    setup_logging(debug=args.debug)
    engine = DetectionEngine(args.model, conf_threshold=args.conf)
    cap = cv2.VideoCapture(0 if args.video == "0" else args.video)
    if not cap.isOpened():
        sys.exit("Cannot open video source")

    recorder = Recorder(args.out)
    cam = CameraParams()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        batch = engine.infer(frame, camera_id="cam0", cam_params=cam, return_batch=True)
        recorder.save_detections(batch)
        recorder.save_frame(frame)
        cv2.imshow("fire-detect", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break


# ---------------------------------------------------------------------- #
# plan command
# ---------------------------------------------------------------------- #
def cmd_plan(argv: list[str]) -> None:
    ap = argparse.ArgumentParser("fire-plan")
    ap.add_argument("--aoi-wkt", required=True, help="Polygon WKT string or file path")
    ap.add_argument("--out", default="./mission.waypoints")
    ap.add_argument("--gsd", type=float, default=2.5)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(argv)

    setup_logging(debug=args.debug)

    # read AOI
    if Path(args.aoi_wkt).is_file():
        aoi_wkt_str = Path(args.aoi_wkt).read_text(encoding="utf-8")
    else:
        aoi_wkt_str = args.aoi_wkt
    aoi = wkt.loads(aoi_wkt_str)

    grid = GridParams(gsd_target_cm=args.gsd)
    planner = FlightPlanner(aoi, grid=grid)
    missions = planner.generate()

    out = Path(args.out)
    out.write_text("\n".join(f"{wp.lat},{wp.lon},{wp.alt}" for wp in missions[0]), encoding="utf-8")
    print(f"Waypoints saved to {out}")


# ---------------------------------------------------------------------- #
def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage:\n  fire-detect ...  |  fire-plan ...")
        sys.exit(0)
    command, *rest = sys.argv[1:]
    if command == "fire-detect":
        cmd_detect(rest)
    elif command == "fire-plan":
        cmd_plan(rest)
    else:
        sys.exit(f"Unknown command {command}")


if __name__ == "__main__":
    main()
