import argparse
import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def setup_logger(log_file: str) -> None:
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def resolve_host(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror as e:
        raise ValueError(f"Could not resolve host '{host}': {e}") from e


def scan_port(ip: str, port: int, timeout: float) -> tuple[int, str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        result = s.connect_ex((ip, port))
        if result == 0:
            return port, "open"
        return port, "closed"
    except socket.timeout:
        return port, "timeout"
    except Exception:
        return port, "error"
    finally:
        try:
            s.close()
        except Exception:
            pass


def parse_ports(ports_str: str | None, start: int, end: int) -> list[int]:
    if ports_str:
        ports = []
        for p in ports_str.split(","):
            p = p.strip()
            if not p:
                continue
            if "-" in p:
                a, b = p.split("-", 1)
                a, b = int(a), int(b)
                ports.extend(range(min(a, b), max(a, b) + 1))
            else:
                ports.append(int(p))
        return sorted(set([p for p in ports if 1 <= p <= 65535]))

    if start < 1 or end > 65535 or start > end:
        raise ValueError("Port range must be between 1 and 65535 and start <= end.")
    return list(range(start, end + 1))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simple TCP Port Scanner (educational use only)"
    )
    parser.add_argument("host", help="Target host (IP or domain)")
    parser.add_argument("--start", type=int, default=1, help="Start port (default: 1)")
    parser.add_argument("--end", type=int, default=1024, help="End port (default: 1024)")
    parser.add_argument(
        "--ports",
        type=str,
        default=None,
        help="Comma-separated ports or ranges, e.g. '22,80,443' or '1-100,8080'",
    )
    parser.add_argument(
        "--threads", type=int, default=100, help="Number of threads (default: 100)"
    )
    parser.add_argument(
        "--timeout", type=float, default=0.6, help="Socket timeout seconds (default: 0.6)"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="Log file name (default: auto-generated)",
    )

    args = parser.parse_args()

    ip = resolve_host(args.host)

    log_file = args.log or f"scan_{args.host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logger(log_file)

    ports = parse_ports(args.ports, args.start, args.end)
    threads = max(1, min(args.threads, 1000))

    print(f"Target: {args.host} ({ip})")
    print(f"Ports count: {len(ports)}")
    print(f"Threads: {threads} | Timeout: {args.timeout}s")
    print(f"Logging to: {log_file}\n")

    results = {"open": [], "closed": 0, "timeout": 0, "error": 0}

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(scan_port, ip, port, args.timeout) for port in ports]
            for fut in as_completed(futures):
                port, status = fut.result()
                if status == "open":
                    results["open"].append(port)
                    print(f"{port}/tcp OPEN")
                    logging.info("%s/tcp OPEN", port)
                elif status == "closed":
                    results["closed"] += 1
                elif status == "timeout":
                    results["timeout"] += 1
                else:
                    results["error"] += 1
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
    finally:
        results["open"].sort()
        print("\n=== Summary ===")
        print(f"Open ports: {results['open']}")
        print(f"Closed: {results['closed']}")
        print(f"Timeouts: {results['timeout']}")
        print(f"Errors: {results['error']}")


if __name__ == "__main__":
    main()
