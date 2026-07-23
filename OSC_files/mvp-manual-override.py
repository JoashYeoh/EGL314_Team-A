from threading import Timer

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client


OSC_REAPER_TARGET_IP = "192.168.254.12"    # IP of laptop running REAPER
OSC_REAPER_TARGET_PORT = 8000

OSC_GMA3_TARGET_IP = "192.168.254.252"    # IP of laptop running GMA3
OSC_GMA3_TARGET_PORT = 8080

# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
osc_tx_reaper = udp_client.SimpleUDPClient(OSC_REAPER_TARGET_IP, OSC_REAPER_TARGET_PORT)
osc_tx_gma3 = udp_client.SimpleUDPClient(OSC_GMA3_TARGET_IP, OSC_GMA3_TARGET_PORT)




#--- Outro Overide ---
osc_tx_gma3.send_message("/gma3/cmd", "Goto Cue 5 Sequence 80")
osc_tx_reaper.send_message("/action/41764", 1)  #jump to region 4
osc_tx_reaper.send_message("/action/43102", 1)  #set loop points to region
osc_tx_reaper.send_message("/action/1007", 1) #play
