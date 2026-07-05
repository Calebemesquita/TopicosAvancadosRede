#!/usr/bin/env python3
"""Verifica login SSH nos roteadores Mininet expostos em 127.0.0.1:220x."""

from __future__ import annotations

import argparse
import socket

import paramiko


def check_router(name, port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            "127.0.0.1",
            port=port,
            username="root",
            password="root",
            look_for_keys=False,
            allow_agent=False,
            timeout=5,
            banner_timeout=5,
            auth_timeout=5,
        )
        _, stdout, stderr = client.exec_command("hostname")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if error:
            return False, error
        return output == name, output or "sem saida"
    except (paramiko.SSHException, socket.error, TimeoutError) as exc:
        return False, str(exc)
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-r5", action="store_true", help="tambem testa r5 na porta 2205")
    args = parser.parse_args()

    routers = ["r1", "r2", "r3", "r4"]
    if args.with_r5:
        routers.append("r5")

    failed = False
    for name in routers:
        port = 2200 + int(name[1:])
        ok, message = check_router(name, port)
        status = "OK" if ok else "FAIL"
        print(f"{status} {name} ssh://root@127.0.0.1:{port} -> {message}")
        failed = failed or not ok

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
