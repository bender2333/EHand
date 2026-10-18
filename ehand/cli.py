import argparse
import json
import sys
from typing import Any, Dict

from ehand import __version__
from ehand.periphery import (
    add_injection,
    get_active_injections,
    get_active_periphery,
    load_periphery_file,
    save_active_periphery,
)
from ehand.timeline import (
    add_mark,
    get_timeline_summary,
    get_transactions_detail,
)
from ehand.service import EHandService


def output_json(data: Any, exit_code: int = 0) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


def cmd_apply(args: argparse.Namespace) -> None:
    try:
        data = load_periphery_file(args.file)
        save_active_periphery(data)
        # Record an apply mark on timeline
        mark_res = add_mark(f"apply_{data.get('name', 'periphery')}")
        output_json({
            "status": "applied",
            "file": args.file,
            "channels": list(data.get("channel", {}).keys()),
            "mark": mark_res,
        })
    except Exception as e:
        output_json({"status": "error", "message": str(e)}, exit_code=1)


def cmd_inject(args: argparse.Namespace) -> None:
    params: Dict[str, Any] = {}
    if args.ms is not None:
        params["ms"] = args.ms
    if args.param:
        for p in args.param:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k] = v
    inj = add_injection(
        channel=args.channel,
        kind=args.kind,
        params=params,
        persistent=args.persistent,
    )
    output_json({"status": "injected", "injection": inj})


def cmd_set(args: argparse.Namespace) -> None:
    periph = get_active_periphery() or {}
    channels = periph.get("channel", {})
    if args.channel not in channels:
        channels[args.channel] = {}
    channels[args.channel]["state"] = args.value
    periph["channel"] = channels
    save_active_periphery(periph)
    add_mark(f"set_{args.channel}_{args.value}")
    output_json({"status": "set", "channel": args.channel, "value": args.value})


def cmd_status(args: argparse.Namespace) -> None:
    periph = get_active_periphery()
    injections = get_active_injections()
    output_json({
        "status": "active" if periph else "idle",
        "periphery": periph,
        "active_injections": injections,
    })


def cmd_mark(args: argparse.Namespace) -> None:
    res = add_mark(args.name)
    output_json(res)


def cmd_log(args: argparse.Namespace) -> None:
    level = args.level
    if level == "summary":
        res = get_timeline_summary(since_mark=args.since_mark)
        output_json(res)
    elif level == "transaction":
        res = get_transactions_detail(since_mark=args.since_mark, channel=args.channel)
        output_json(res)
    elif level == "byte":
        # Byte-level drill down
        res = get_transactions_detail(since_mark=args.since_mark, channel=args.channel)
        output_json(res)
    else:
        output_json({"error": f"Unknown level: {level}"}, exit_code=1)


def cmd_serve(args: argparse.Namespace) -> None:
    svc = EHandService(port_override=args.port)
    try:
        svc.serve_forever(poll_interval=args.poll)
    except KeyboardInterrupt:
        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ehand",
        description="Real hardware feedback for embedded-coding Agents",
    )
    parser.add_argument("--version", action="version", version=f"ehand {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply a Virtual Periphery declaration file")
    p_apply.add_argument("file", help="Path to periphery.toml file")
    p_apply.set_defaults(func=cmd_apply)

    # inject
    p_inj = subparsers.add_parser("inject", help="Inject a fault into a channel")
    p_inj.add_argument("channel", help="Channel name (e.g. uart1, rs485)")
    p_inj.add_argument("kind", help="Injection kind (e.g. delay, drop, corrupt, truncate)")
    p_inj.add_argument("--ms", type=float, default=None, help="Delay duration in ms")
    p_inj.add_argument("--persistent", action="store_true", help="Keep injection active across transactions")
    p_inj.add_argument("-p", "--param", action="append", help="Extra param key=value")
    p_inj.set_defaults(func=cmd_inject)

    # set
    p_set = subparsers.add_parser("set", help="Set channel state value")
    p_set.add_argument("channel", help="Channel name")
    p_set.add_argument("value", help="New value")
    p_set.set_defaults(func=cmd_set)

    # status
    p_stat = subparsers.add_parser("status", help="Get current peripheral status and active injections")
    p_stat.set_defaults(func=cmd_status)

    # mark
    p_mark = subparsers.add_parser("mark", help="Place a named Mark on the Timeline")
    p_mark.add_argument("name", help="Mark name (e.g. build_1_test)")
    p_mark.set_defaults(func=cmd_mark)

    # log
    p_log = subparsers.add_parser("log", help="Read Timeline records (Summary by default)")
    p_log.add_argument("--since-mark", default=None, help="Only return records since this Mark")
    p_log.add_argument(
        "--level",
        choices=["summary", "transaction", "byte"],
        default="summary",
        help="Detail level (default: summary)",
    )
    p_log.add_argument("--channel", default=None, help="Filter by channel name")
    p_log.set_defaults(func=cmd_log)

    # serve
    p_serve = subparsers.add_parser("serve", help="Run EHand peripheral service on configured channels")
    p_serve.add_argument("--port", default=None, help="Override serial port")
    p_serve.add_argument("--poll", type=float, default=0.05, help="Poll interval in seconds")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
