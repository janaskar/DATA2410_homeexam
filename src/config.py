import struct

max_filename_length = 32
default_ip = "127.0.0.1"
default_port = 8088
window_size = 3
DRTP_struct = struct.Struct("!HHH")
chunk_size = 1000 - DRTP_struct.size
timeout = 0.5

debug = False
# File transfer packets only
show_packets = False