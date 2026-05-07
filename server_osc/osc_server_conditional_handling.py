# Huats 2023 oscstarterkit 

from pythonosc import osc_server, dispatcher, udp_client

# SERVER (RECEIVE FROM CLIENTS)
receiver_ip = "192.168.254.149"   
receiver_port = 2000

# DESTINATIONS (AV SYSTEMS)
# grandMA
grandma_ip = "192.168.254.252"
grandma_port = 8080
grandma_client = udp_client.SimpleUDPClient(grandma_ip, grandma_port)

"""
# REAPER n L-ISA
reaper_ip = "192.168.254.12"
reaper_port = 8000
reaper_client = udp_client.SimpleUDPClient(reaper_ip, reaper_port)
"""


def route_message(address, *args):
    if address.startswith("/gma3"):
        grandma_client.send_message(address, args if args else None)
        print(f"[GRANDMA] {address} {args}")

    elif address.startswith("/action"):
        reaper_client.send_message(address, args if args else None)
        print(f"[REAPER] {address} {args}")

    # elif address.startswith("/ext"):
    #     lisa_client.send_message(address, args if args else None)
    #     print(f"[REAPER -MIDI- L-ISA] {address} {args}")

    else:
        print(f"[UNKNOWN] {address} {args}")


# ---- DISPATCHER ----
dispatcher = dispatcher.Dispatcher()
dispatcher.set_default_handler(route_message)



# ---- SERVER ----
server = osc_server.ThreadingOSCUDPServer(
    (receiver_ip, receiver_port), dispatcher
)

print(f"Serving on {server.server_address}")
server.serve_forever() 



