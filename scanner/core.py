import socket
from dataclasses import dataclass

@dataclass
class PortResult:
    port: int
    status: str
    detail: str = ""

def check_tcp_port(host: str, port: int, timeout: float = 0.3) -> PortResult:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)

    try:
        result = s.connect_ex((host, port))
        if result == 0:
            return PortResult(port, "OPEN")
        return PortResult(port, "CLOSED", f"code={result}")
    except socket.timeout:
        return PortResult(port, "TIMEOUT")
    except Exception as e:
        return PortResult(port, "ERROR", str(e))
    finally:
        s.close()
