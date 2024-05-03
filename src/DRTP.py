import struct
import socket
import random

def set_flags(syn, ack, fin, rst):
    flags = 0
    if syn:
        flags |= (1 << 3)  # 1 << 3 = 1000
    if ack:
        flags |= (1 << 2)  # 1 << 2 = 0100
    if fin:
        flags |= (1 << 1)  # 1 << 1 = 0010
    if rst:
        flags |= (1 << 0)  # 1 << 0 = 0001
    return flags

def get_flags(flags):
    syn = int(bool(flags & (1 << 3)))
    ack = int(bool(flags & (1 << 2)))
    fin = int(bool(flags & (1 << 1)))
    rst = int(bool(flags & (1 << 0)))
    return (syn, ack, fin, rst)

DRTP_struct = struct.Struct("!HHH")

def pack_header(seq_num, ack_num, flags):
    return DRTP_struct.pack(seq_num, ack_num, flags)

def unpack_header(header):
    seq_num, ack_num, flags = DRTP_struct.unpack(header)
    return (seq_num, ack_num, get_flags(flags))

def print_header(header):
    if 1 == 1:
        seq_num, ack_num, flags = unpack_header(header)
        print(f"seq_num: {seq_num}, ack_num: {ack_num}, flags: {flags}")

def random_seq_num():
    return random.randint(0, 2 ** 16 - 1)

def run_server(ip, port):
    timeout = 5

    # Start connection
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.settimeout(timeout)
    server_socket.bind((ip, port))
    print("Server is listening...")

    # Receive SYN packet
    syn_packet, client_address = server_socket.recvfrom(DRTP_struct.size)
    seg_num, _, flags = unpack_header(syn_packet)
    print("SYN packet is received")
    print_header(syn_packet)

    # Send SYN-ACK packet
    if flags[0] == 1:
        packet = pack_header(random_seq_num(), seg_num + 1, set_flags(1, 1, 0, 0))
        server_socket.sendto(packet, client_address)
        print("SYN-ACK packet is sent")
        print_header(packet)
    else:
        print("SYN packet is not received")

    # Receive ACK packet
    ack_packet, _ = server_socket.recvfrom(DRTP_struct.size)
    _, _, flags = unpack_header(ack_packet)
    if flags[1] == 1:
        print("ACK packet is received")
        print_header(ack_packet)
    else:
        print("ACK packet is not received")        

    # Connection established
    print("Connection established")

def run_client(ip, port):
    timeout = 0.5

    # Start connection
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    client_socket.connect((ip, port))
    print("Connection Establisht Phase:")

    # Send SYN packet
    packet = pack_header(random_seq_num(), 0, set_flags(1, 0, 0, 0))
    client_socket.send(packet)
    print("SYN packet is sent")
    print_header(packet)

    # Receive SYN-ACK packet
    syn_ack_packet = client_socket.recv(DRTP_struct.size)
    seq_num, ack_num, flags = unpack_header(syn_ack_packet)
    if flags[0] == 1 and flags[1] == 1:
        print("SYN-ACK packet is received")
        print_header(syn_ack_packet)
    else:
        print("SYN-ACK packet is not received")

    # Send ACK packet
    ack_packet = pack_header(ack_num, seq_num + 1, set_flags(0, 1, 0, 0))
    client_socket.send(ack_packet)
    print("ACK packet is sent")
    print_header(ack_packet)

    # Connection established
    print("Connection established")