import logging
from ipaddress import IPv4Address, IPv4Network
from typing import List, Sequence, Tuple

logger = logging.getLogger(__name__)


class NetworkACL:
    """Simple IPv4-only ACL supporting CIDR blocks, single hosts, and ranges."""

    def __init__(self, entries: Sequence[str]) -> None:
        self._allow_all = False
        self._single_hosts: set[IPv4Address] = set()
        self._cidrs: List[IPv4Network] = []
        self._ranges: List[Tuple[IPv4Address, IPv4Address]] = []
        self._load(entries)

    def _load(self, entries: Sequence[str]) -> None:
        for entry in entries:
            normalized = (entry or "").strip()
            if not normalized:
                continue
            if normalized in {"*", "0.0.0.0", "0.0.0.0/0"}:
                self._allow_all = True
                self._single_hosts.clear()
                self._cidrs.clear()
                self._ranges.clear()
                return
            if "|" in normalized:
                start_raw, end_raw = [part.strip() for part in normalized.split("|", 1)]
                try:
                    start_ip = IPv4Address(start_raw)
                    end_ip = IPv4Address(end_raw)
                except ValueError:
                    logger.warning("Invalid IPv4 range entry ignored: %s", normalized)
                    continue
                if int(end_ip) < int(start_ip):
                    start_ip, end_ip = end_ip, start_ip
                self._ranges.append((start_ip, end_ip))
                continue
            if "/" in normalized:
                try:
                    cidr = IPv4Network(normalized, strict=False)
                except ValueError:
                    logger.warning("Invalid CIDR entry ignored: %s", normalized)
                    continue
                self._cidrs.append(cidr)
                continue
            # Treat as single host
            try:
                address = IPv4Address(normalized)
            except ValueError:
                logger.warning("Invalid IPv4 entry ignored: %s", normalized)
                continue
            self._single_hosts.add(address)

    def is_allowed(self, host: str | None) -> bool:
        if self._allow_all:
            return True
        if not host:
            return False
        try:
            ip = IPv4Address(host)
        except ValueError:
            logger.warning("Rejecting non-IPv4 host: %s", host)
            return False
        if ip in self._single_hosts:
            return True
        for cidr in self._cidrs:
            if ip in cidr:
                return True
        for start_ip, end_ip in self._ranges:
            if int(start_ip) <= int(ip) <= int(end_ip):
                return True
        return False

