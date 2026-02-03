import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from scanner.core import check_tcp_port
from scanner.logger import setup_logger

def parse_ports(text: str) -> list[int]:
    if "-" in text:
        a, b = text.split("-", 1)
        start, end = int(a), int(b)
        if start > end:
            start, end = end, start
        return list(range(start, end + 1))
    return [int(text)]

def main():
    parser = argparse.ArgumentParser(
        description="TCP Port Scanner (Safe Lab – localhost only)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--ports", default="1-100")
    parser.add_argument("--timeout", type=float, default=0.3)
    parser.add_argument("--threads", type=int, default=50)
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost"):
        raise SystemExit("Only localhost allowed for this lab.")

    host = "127.0.0.1"
    ports = parse_ports(args.ports)

    logger = setup_logger()
    logger.info(f"Scanning {host} ports {args.ports}")

    with ThreadPoolExecutor(max_workers=args.threads) as ex:
        futures = [ex.submit(check_tcp_port, host, p, args.timeout) for p in ports]
        results = [f.result() for f in as_completed(futures)]

    results.sort(key=lambda r: r.port)

    for r in results:
        logger.info(f"{host}:{r.port} -> {r.status}")

if __name__ == "__main__":
    main()
