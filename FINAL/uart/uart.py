#!/usr/bin/env python3
"""
uart_reliable.py — Reliable UART Reader + OSC Sender
====================================================

Reads 37-byte UWB frames from the BU03-Kit, validates and calibrates the
eight anchor distances, then sends them to the game Pi over OSC.

OSC message:
    /distances  <tag_id:int> <d0:float> ... <d7:float>

Important:
    The original code assigns tags using frame_count % n_tags. This can cause
    tags to swap after one missing or corrupted UART frame.

    This version supports two tag assignment modes:

    1. round-robin
       Compatible with the original code, but still vulnerable to swapping.

    2. byte35
       Uses byte 35 of the UART frame as the tag identifier. Use this only
       after confirming that byte 35 identifies the physical tag.

Examples:
    python3 uart_reliable.py --tags 5 --host 192.168.1.1 --port 5005

    python3 uart_reliable.py --tags 5 --tag-source byte35 \
        --host 192.168.1.1 --port 5005

    python3 uart_reliable.py --tags 5 --diagnostic
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import serial
from pythonosc import udp_client


# ---------------------------------------------------------------------------
# Hardware / protocol constants
# ---------------------------------------------------------------------------
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200

FRAME_HEADER = b"\xaa\x25\x01"
FRAME_SIZE = 37
TRAILER = 0x55

DISTANCE_COUNT = 8
DISTANCE_START_BYTE = 3
TAG_ID_BYTE = 35

MAX_BUFFER_SIZE = 8192

# Plausible operating range for a UWB anchor measurement.
# Invalid values are sent as -1.0 and should be ignored by trilateration.
MIN_DISTANCE_M = 0.10
MAX_DISTANCE_M = 30.0
INVALID_DISTANCE = -1.0

# Minimum measurements required for 2D trilateration.
MIN_VALID_ANCHORS = 3

# OSC defaults
DEFAULT_HOST = "192.168.1.1"
DEFAULT_PORT = 5005

# Per-anchor calibration offsets in metres.
ANCHOR_OFFSETS = {
    0: -0.349,
    1: -0.055,
    2: +0.021,
    3: +0.025,
    4: -0.005,
    5: +0.255,
}



@dataclass
class ReaderStats:
    bytes_read: int = 0
    frames_found: int = 0
    frames_sent: int = 0
    invalid_frames: int = 0
    invalid_distance_frames: int = 0
    buffer_resets: int = 0
    tag_counts: dict[int, int] = field(default_factory=dict)


def parse_frame(frame: bytes) -> Optional[list[float]]:
    """Return eight distances in metres, or None if the frame is invalid."""
    if len(frame) != FRAME_SIZE:
        return None

    if frame[: len(FRAME_HEADER)] != FRAME_HEADER:
        return None

    if frame[-1] != TRAILER:
        return None

    distances: list[float] = []

    try:
        for index in range(DISTANCE_COUNT):
            offset = DISTANCE_START_BYTE + index * 4
            millimetres = struct.unpack_from("<I", frame, offset)[0]
            distances.append(millimetres / 1000.0)
    except struct.error:
        return None

    return distances


def extract_frames(buffer: bytearray, stats: ReaderStats) -> list[bytes]:
    """
    Remove and return all complete valid-looking frames currently in buffer.

    The parser retains up to the final two bytes when no header is found so
    that a header split across two serial reads can still be recovered.
    """
    frames: list[bytes] = []

    if len(buffer) > MAX_BUFFER_SIZE:
        del buffer[:-2]
        stats.buffer_resets += 1

    while True:
        header_index = buffer.find(FRAME_HEADER)

        if header_index < 0:
            if len(buffer) > len(FRAME_HEADER) - 1:
                del buffer[: -(len(FRAME_HEADER) - 1)]
            break

        if header_index > 0:
            del buffer[:header_index]

        if len(buffer) < FRAME_SIZE:
            break

        candidate = bytes(buffer[:FRAME_SIZE])

        if candidate[-1] == TRAILER:
            frames.append(candidate)
            stats.frames_found += 1
            del buffer[:FRAME_SIZE]
        else:
            # False header or corrupted packet. Shift by one byte and rescan.
            del buffer[0]
            stats.invalid_frames += 1

    return frames


def calibrate_and_validate(
    distances: list[float],
) -> tuple[list[float], int]:
    """
    Apply anchor calibration and replace invalid measurements with -1.0.

    Returns:
        corrected_distances, valid_anchor_count
    """
    corrected: list[float] = []
    valid_count = 0

    for anchor_id, raw_distance in enumerate(distances):
        offset = ANCHOR_OFFSETS.get(anchor_id, 0.0)
        value = raw_distance + offset

        if (
            math.isfinite(value)
            and MIN_DISTANCE_M <= value <= MAX_DISTANCE_M
        ):
            corrected.append(value)
            valid_count += 1
        else:
            corrected.append(INVALID_DISTANCE)

    return corrected, valid_count


def resolve_tag_id(
    raw_frame: bytes,
    tag_source: str,
    round_robin_index: int,
    n_tags: int,
    byte35_base: int,
) -> Optional[int]:
    """
    Resolve the tag ID using the selected assignment mode.

    byte35_base:
        0 means byte 35 values are expected to be 0..n-1.
        1 means byte 35 values are expected to be 1..n.
    """
    if tag_source == "round-robin":
        return round_robin_index % n_tags

    raw_tag_id = raw_frame[TAG_ID_BYTE]
    tag_id = raw_tag_id - byte35_base

    if 0 <= tag_id < n_tags:
        return tag_id

    return None


def print_diagnostic(
    raw_frame: bytes,
    assigned_tag: Optional[int],
    distances: list[float],
    valid_count: int,
) -> None:
    """Print one compact diagnostic line for a parsed UART frame."""
    preview = " ".join(
        f"d{i}={distance:.3f}"
        for i, distance in enumerate(distances[:3])
    )

    assigned_text = "invalid" if assigned_tag is None else str(assigned_tag)

    print(
        f"[frame] byte35={raw_frame[TAG_ID_BYTE]:3d} "
        f"assigned=T{assigned_text} "
        f"valid={valid_count}/{DISTANCE_COUNT} "
        f"{preview}"
    )


def print_status(stats: ReaderStats, buffer_size: int) -> None:
    tag_summary = ", ".join(
        f"T{tag_id}={count}"
        for tag_id, count in sorted(stats.tag_counts.items())
    )

    if not tag_summary:
        tag_summary = "none"

    print(
        "[uart] "
        f"bytes={stats.bytes_read} "
        f"found={stats.frames_found} "
        f"sent={stats.frames_sent} "
        f"invalid={stats.invalid_frames} "
        f"bad-distance={stats.invalid_distance_frames} "
        f"buffer={buffer_size} "
        f"resets={stats.buffer_resets} "
        f"tags=[{tag_summary}]"
    )


def run(
    n_tags: int,
    host: str,
    port: int,
    serial_port: str,
    baud_rate: int,
    tag_source: str,
    byte35_base: int,
    diagnostic: bool,
    report_interval: float,
) -> None:
    """Read UART frames continuously and send valid measurements over OSC."""
    osc = udp_client.SimpleUDPClient(host, port)

    print(f"[uart] OSC target -> {host}:{port}")
    print(f"[uart] Tag assignment -> {tag_source}")

    if tag_source == "round-robin":
        print(
            "[WARNING] Round-robin assignment can swap tags after a missing "
            "or corrupted frame."
        )
    else:
        print(
            f"[uart] Byte 35 ID base -> {byte35_base} "
            f"({'0..n-1' if byte35_base == 0 else '1..n'})"
        )

    try:
        serial_connection = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            timeout=0.02,
        )
    except serial.SerialException as exc:
        print(f"[ERROR] Could not open {serial_port}: {exc}")
        sys.exit(1)

    try:
        serial_connection.reset_input_buffer()
    except serial.SerialException as exc:
        serial_connection.close()
        print(f"[ERROR] Could not reset UART input buffer: {exc}")
        sys.exit(1)

    print(f"[uart] Serial open on {serial_port} @ {baud_rate} baud")
    print(f"[uart] Tracking {n_tags} tag(s). Press Ctrl-C to stop.\n")

    buffer = bytearray()
    stats = ReaderStats()
    round_robin_index = 0
    next_report_time = time.monotonic() + report_interval

    try:
        while True:
            try:
                waiting = serial_connection.in_waiting
                read_size = waiting if waiting > 0 else 1
                data = serial_connection.read(read_size)
            except serial.SerialException as exc:
                print(f"[reader error] {exc}")
                break

            if data:
                stats.bytes_read += len(data)
                buffer.extend(data)

            for raw_frame in extract_frames(buffer, stats):
                distances = parse_frame(raw_frame)

                if distances is None:
                    stats.invalid_frames += 1
                    continue

                corrected, valid_count = calibrate_and_validate(distances)

                tag_id = resolve_tag_id(
                    raw_frame=raw_frame,
                    tag_source=tag_source,
                    round_robin_index=round_robin_index,
                    n_tags=n_tags,
                    byte35_base=byte35_base,
                )

                if diagnostic:
                    print_diagnostic(
                        raw_frame=raw_frame,
                        assigned_tag=tag_id,
                        distances=corrected,
                        valid_count=valid_count,
                    )

                if valid_count < MIN_VALID_ANCHORS:
                    stats.invalid_distance_frames += 1
                    continue

                if tag_id is None:
                    stats.invalid_frames += 1
                    continue

                try:
                    osc.send_message(
                        "/distances",
                        [tag_id, *corrected],
                    )
                except OSError as exc:
                    print(f"[OSC error] {exc}")
                    continue

                stats.frames_sent += 1
                stats.tag_counts[tag_id] = stats.tag_counts.get(tag_id, 0) + 1

                # Only advance round robin after a frame is successfully sent.
                if tag_source == "round-robin":
                    round_robin_index += 1

            current_time = time.monotonic()

            if current_time >= next_report_time:
                print_status(stats, len(buffer))
                next_report_time = current_time + report_interval

    except KeyboardInterrupt:
        print("\n[uart] Stopped by user.")

    finally:
        serial_connection.close()
        print_status(stats, len(buffer))
        print("[uart] Serial closed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read UWB UART frames and send distances over OSC."
    )

    parser.add_argument(
        "--tags",
        type=int,
        default=2,
        help="Number of active tags, from 1 to 8. Default: 2.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOST,
        help=f"Game Pi IP address. Default: {DEFAULT_HOST}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Game Pi OSC port. Default: {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--serial-port",
        type=str,
        default=SERIAL_PORT,
        help=f"UART serial port. Default: {SERIAL_PORT}",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=BAUD_RATE,
        help=f"UART baud rate. Default: {BAUD_RATE}",
    )
    parser.add_argument(
        "--tag-source",
        choices=("round-robin", "byte35"),
        default="round-robin",
        help=(
            "How tag IDs are assigned. Default: round-robin. "
            "Use byte35 only after confirming byte 35 is the hardware tag ID."
        ),
    )
    parser.add_argument(
        "--byte35-base",
        type=int,
        choices=(0, 1),
        default=0,
        help=(
            "For --tag-source byte35: use 0 for IDs 0..n-1 or "
            "1 for IDs 1..n. Default: 0."
        ),
    )
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Print byte 35, assigned tag, and sample distances for every frame.",
    )
    parser.add_argument(
        "--report-interval",
        type=float,
        default=5.0,
        help="Seconds between status reports. Default: 5.0.",
    )

    args = parser.parse_args()

    if not 1 <= args.tags <= 8:
        parser.error("--tags must be between 1 and 8")

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    if args.baud <= 0:
        parser.error("--baud must be greater than zero")

    if args.report_interval <= 0:
        parser.error("--report-interval must be greater than zero")

    run(
        n_tags=args.tags,
        host=args.host,
        port=args.port,
        serial_port=args.serial_port,
        baud_rate=args.baud,
        tag_source=args.tag_source,
        byte35_base=args.byte35_base,
        diagnostic=args.diagnostic,
        report_interval=args.report_interval,
    )


if __name__ == "__main__":
    main()
