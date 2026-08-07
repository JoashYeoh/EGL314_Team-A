# Huats Club 2026
#!/usr/bin/env python3
"""
uart.py  —  UART Reader + OSC Sender
=====================================
Runs on the "sensor" Pi that is physically connected to the UWB module.

Reads raw UART frames from the BU03-Kit, parses them into 8 distances (m),
applies per-anchor calibration offsets, then broadcasts each frame over OSC
to the "game" Pi running game.py.

OSC message sent:  /distances  <tag_id:int> <d0:float> ... <d7:float>

Run:
    python3 uart.py --tags 2 --host 192.168.1.XX --port 5005
"""

import argparse
import struct
import sys
import time

import serial
from pythonosc import udp_client


import csv
from collections import Counter

# ---------------------------------------------------------------------------
# Hardware / protocol constants  (must match game.py)
# ---------------------------------------------------------------------------
SERIAL_PORT  = "/dev/serial0"
BAUD_RATE    = 115200
FRAME_HEADER = b"\xaa\x25\x01"
FRAME_SIZE   = 37
TRAILER      = 0x55

# Per-anchor calibration offsets (metres).
ANCHOR_OFFSETS = {
    0: -0.349,
    1: -0.055,
    2: +0.021,
    3: +0.025,
    4: -0.005,
    5: +0.255,
}

MAX_BUF = 8192   # runaway guard: never let the buffer grow unbounded

# ---------------------------------------------------------------------------
# OSC defaults  (override with CLI flags)
# ---------------------------------------------------------------------------
DEFAULT_HOST = "192.168.1.1"   # <-- change to game Pi's IP
DEFAULT_PORT = 5005



#------ DIAGNOSTICS -------
DIAGNOSTIC_MODE = True
DIAGNOSTIC_CSV = "uwb_uart_diagnostic.csv"
PRINT_EVERY_FRAME = True
#--------------------------


# ---------------------------------------------------------------------------
# Frame parsing helpers
# ---------------------------------------------------------------------------
def parse_frame(frame: bytes):
    """Checks if frame size is exactly 37 bytes and returns distance value (in m)"""
    """Return list of 8 distances (m) or None if the frame is invalid."""
    if len(frame) != FRAME_SIZE:
        return None
    if frame[:3] != FRAME_HEADER or frame[-1] != TRAILER:
        return None
    distances = []
    for i in range(8):
        off = 3 + i * 4
        (mm,) = struct.unpack_from("<I", frame, off)    # a function that unpacks the distance value in mm from the frame variable
                                                        # (is a Python function used to extract data from a binary buffer (like bytes or bytearray) starting at a specific position)
        distances.append(mm / 1000.0)   # converts mm distance to m by dividing by 1000

    # Byte 35 is currently unused by your existing parser.
    metadata_byte = frame[35]

    return distances, metadata_byte


def find_frames(buf: bytearray):
    frames = []
    # If the stream has desynced and the buffer is ballooning, drop everything
    # but the last couple of bytes. Without this, a bad sync byte-by-byte
    # search can exhaust RAM and trigger the Pi's OOM killer (full freeze).
    if len(buf) > MAX_BUF:
        del buf[:-2]
    while True:
        idx = buf.find(FRAME_HEADER)    # finds frame with the given header "\xaa\x25\x01", and limits the buffer (prevent RAM exhaustion)
        if idx < 0:
            if len(buf) > 2:    # if the length of the frame with header found is more than 2, it will remove 2 characters
                del buf[:-2]
            break
        if idx > 0:     # if the length of the frame with header found is more than 0 (but less than 2), it will delete the frame (the frame contains no useful characters)
            del buf[:idx]
        if len(buf) < FRAME_SIZE:   # if the length of the frame with header found is less than the stated frame size, it will end the while loop
            break
        candidate = bytes(buf[:FRAME_SIZE])
        if candidate[-1] == TRAILER:
            frames.append(candidate)
            del buf[:FRAME_SIZE]
        else:
            del buf[:1]
    return frames


# ---------------------------------------------------------------------------
# Main reader / sender loop via OSC
# ---------------------------------------------------------------------------
def run(n_tags: int, host: str, port: int):
    # Open OSC client (fire-and-forget UDP — no connection needed)
    osc = udp_client.SimpleUDPClient(host, port)
    print(f"[uart] OSC target → {host}:{port}")

    # Open serial port -> to pull UART Data
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    except serial.SerialException as e:
        print(f"[ERROR] Could not open {SERIAL_PORT}: {e}")
        sys.exit(1)
    ser.reset_input_buffer()
    print(f"[uart] Serial open on {SERIAL_PORT} @ {BAUD_RATE} baud")
    print(f"[uart] Tracking {n_tags} tag(s).  Press Ctrl-C to stop.\n")

    buf        = bytearray() # In Python, bytearray() is a built-in function that creates a mutable sequence of integers ranging from 0 to 255.
                             # Think of it as a version of the bytes type that you can actually change after creating it.
    frame_count = 0
    last_frame_time = None
    last_tag_time = [None] * n_tags
    tag_frame_counts = [0] * n_tags

    test_start_time = time.monotonic()

    last_metadata = None
    metadata_counts = Counter()

    diagnostic_file = None
    diagnostic_writer = None

    if DIAGNOSTIC_MODE:
        diagnostic_file = open(
            DIAGNOSTIC_CSV,
            "w",
            newline="",
            buffering=1,
        )

        diagnostic_writer = csv.writer(diagnostic_file)

        diagnostic_writer.writerow([
            "timestamp",
            "frame_count",
            "assigned_tag",
            "metadata_decimal",
            "metadata_hex",
            "frame_gap_ms",
            "d0",
            "d1",
            "d2",
            "d3",
            "d4",
            "d5",
            "d6",
            "d7",
            "raw_hex",
        ])

    try:
        while True:
            try:
                data = ser.read(256)    # Read UART data (up to 256 bytes)
            except Exception as e:
                print(f"[reader error] {e}")
                break

            if data:
                buf.extend(data)    # Append to buffer

            for raw in find_frames(buf):
                parsed = parse_frame(raw)

                if parsed is None:
                    continue

                distances, metadata_byte = parsed

                now = time.monotonic()

                if last_frame_time is None:
                    frame_gap_ms = 0.0
                else:
                    frame_gap_ms = (now - last_frame_time) * 1000.0

                last_frame_time = now

                # This remains the CURRENT assumed assignment.
                # Do not use metadata_byte as the tag ID yet.
                assigned_tag_id = frame_count % n_tags

                tag_frame_counts[assigned_tag_id] += 1

                if last_tag_time[assigned_tag_id] is None:
                    tag_gap_ms = 0.0
                else:
                    tag_gap_ms = (
                        now - last_tag_time[assigned_tag_id]
                    ) * 1000.0

                last_tag_time[assigned_tag_id] = now

                metadata_counts[metadata_byte] += 1

                if PRINT_EVERY_FRAME:
                    metadata_change = (
                        last_metadata is not None
                        and metadata_byte != last_metadata
                    )

                    print(
                        f"[frame {frame_count:06d}] "
                        f"assigned=T{assigned_tag_id} "
                        f"frame_gap={frame_gap_ms:7.2f}ms "
                        f"tag_gap={tag_gap_ms:7.2f}ms "
                        f"d0={distances[0]:6.3f} "
                        f"d1={distances[1]:6.3f} "
                        f"d2={distances[2]:6.3f}"
                    )

                last_metadata = metadata_byte

                if diagnostic_writer is not None:
                    diagnostic_writer.writerow([
                        time.time(),
                        frame_count,
                        assigned_tag_id,
                        metadata_byte,
                        f"0x{metadata_byte:02X}",
                        f"{frame_gap_ms:.3f}",
                        *[f"{distance:.3f}" for distance in distances],
                        raw.hex(" "),
                    ])

                # Apply anchor calibration.
                for anchor_id, offset in ANCHOR_OFFSETS.items():
                    if anchor_id < len(distances):
                        distances[anchor_id] = max(
                            0.0,
                            distances[anchor_id] + offset,
                        )

                osc_args = [assigned_tag_id] + distances
                osc.send_message("/distances", osc_args)

                frame_count += 1

                if frame_count > 0 and frame_count % 100 == 0:
                    elapsed = time.monotonic() - test_start_time

                    total_rate = frame_count / elapsed

                    print(
                        f"\n[RATE] total={total_rate:.2f} frames/s"
                    )

                    for current_tag_id, count in enumerate(tag_frame_counts):
                        print(
                            f"[RATE] tag={current_tag_id} "
                            f"rate={count / elapsed:.2f} updates/s "
                            f"count={count}"
                        )

                    print()

    except KeyboardInterrupt:
        print("\n[uart] Stopped by user.")
    finally:
        ser.close()

        if diagnostic_file is not None:
            diagnostic_file.close()

        print(f"[uart] Serial closed. Total frames sent: {frame_count}")
        print(f"[uart] byte35 counts: {dict(metadata_counts)}")


# ---------------------------------------------------------------------------
# Entry point -- what is typed in the CLI when running the code. 
# e.g. python3 uart.py --tags 2 --192.168.254.100 --5005
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Read UWB UART frames and stream distances via OSC.")
    ap.add_argument("--tags", type=int, default=2,
                    help="Number of active tags (1..8). Default: 2.")
    ap.add_argument("--host", type=str, default=DEFAULT_HOST,
                    help=f"IP of the game Pi. Default: {DEFAULT_HOST}")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT,
                    help=f"UDP port to send OSC to. Default: {DEFAULT_PORT}")
    args = ap.parse_args()

    if not 1 <= args.tags <= 8:
        print("--tags must be between 1 and 8")
        sys.exit(1)

    run(args.tags, args.host, args.port)


if __name__ == "__main__":
    main()
