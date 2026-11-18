#!/usr/bin/env python3
"""Verify the native libraries and dependency notices shipped in the plugin AAR."""
import sys
from zipfile import ZipFile


def check(archive):
    # ELF class (32/64 bit) and e_machine for each supported Android ABI.
    targets = {"armeabi-v7a": (1, 40), "arm64-v8a": (2, 183), "x86_64": (2, 62)}
    with ZipFile(archive) as aar:
        for abi, (elf_class, machine) in targets.items():
            library = f"jni/{abi}/libflutter_tailscale.so"
            with aar.open(library) as stream:
                header = stream.read(20)
            if (len(header) != 20 or header[:4] != b"\x7fELF"
                    or header[4:6] != bytes([elf_class, 1])
                    or int.from_bytes(header[16:18], "little") != 3
                    or int.from_bytes(header[18:20], "little") != machine):
                raise SystemExit(f"{library} is not an Android shared library for {abi}")
            notices = aar.read(f"assets/flutter_tailscale/THIRD_PARTY_NOTICES-{abi}.txt")
            if b"=== Go runtime ===" not in notices or b"=== tailscale.com " not in notices:
                raise SystemExit(f"Missing runtime or Tailscale dependency notice for {abi}")
            print(f"Verified {abi} library and notices")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: check-android-aar.py <plugin.aar>")
    check(sys.argv[1])
