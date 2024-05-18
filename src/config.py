import struct

# Constants
max_filename_length = 32
default_ip = "127.0.0.1"
default_port = 8088
window_size = 3
DRTP_struct = struct.Struct("!HHH") # 2 bytes for sequence number, 2 bytes for ack number, 2 bytes for flags
packet_size = 1000
chunk_size = packet_size - DRTP_struct.size # 994 bytes for data
timeout = 0.5   # 500ms

# Debugging lines
debug = False
# File transfer packets only
show_packets = False