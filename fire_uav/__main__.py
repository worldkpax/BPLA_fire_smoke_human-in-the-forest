"""
fire_uav launcher
Запуск:
    python -m fire_uav [gui|detect|plan]
Если без аргументов → выводит меню.
"""
from importlib import import_module
import inspect
import sys
from fire_uav.utils.logging import setup_logging

COMMANDS = {
    "detect": "fire_uav.ui.cli:cmd_detect",   # ждёт argv list
    "plan":   "fire_uav.ui.cli:cmd_plan",     # ждёт argv list
    "gui":    "fire_uav.ui.qt.app:main",      # argv не нужен
}

MENU = "Usage: python -m fire_uav [gui|detect|plan]"

def _run(target: str, argv):
    mod, fn = target.split(":")
    func = getattr(import_module(mod), fn)
    sig = inspect.signature(func)
    # если функция принимает хотя бы один позиционный параметр → передаём argv
    if sig.parameters:
        func(argv)
    else:
        func()

def main():
    if len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        print(MENU)
        sys.exit(0)
    cmd, *rest = sys.argv[1:]
    if cmd not in COMMANDS:
        sys.exit(f"Unknown command {cmd}\n{MENU}")
    setup_logging()
    _run(COMMANDS[cmd], rest)

if __name__ == "__main__":
    main()
