import struct
import socket
import random
import os
from config import *

print("\n")

def print_header(header, sent):
    if debug:
        if sent:
            seq_num, ack_num, flags = unpack_header(header)
            print(f"seq_num: {seq_num}, ack_num: {ack_num}, flags: {flags}")
        else:
            seq_num, ack_num, flags = unpack_header(header)
            print(f"{'seq_num: {seq_num}, ack_num: {ack_num}, flags: {flags}': <20}")

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

def random_seq_num():
    return random.randint(0, 2 ** 8 - 1) # max 256

def pack_file(filename):
    try:
        # Array to store the packets
        packets = []

        # Encode the filename
        encoded_filename = filename.encode()
        # Pad the filename with null bytes to make it max_filename_length bytes long
        encoded_filename = encoded_filename.ljust(max_filename_length, b'\0')

        # Open the file and send it in chunks of 1024 bytes
        with open(filename, 'rb') as f:

            # Name of the file
            if debug:
                print(f"Reading from {filename}")

            # Loop until the end of the file
            first_packet = True
            while True:

                # Add the filename to the first packet and read the first chunk of the file
                if first_packet:
                    file_raw_data = encoded_filename + f.read(chunk_size - DRTP_struct.size - max_filename_length)
                    first_packet = False

                # Read the next chunks of the file
                else:
                    file_raw_data = f.read(chunk_size - DRTP_struct.size)
                
                # Append the packet to the list
                packets.append(file_raw_data)
                if not file_raw_data:
                    break
        
        # Print the number of packets
        if debug:
            print(f"Total packets to send {len(packets)}")

        # Print the first 2 packets
        if show_packets:
            print(f"First packet: {packets[0]}")
            print(f"Second packet: {packets[1]}")

        # Return the packets
        return packets
    
    # Handle file errors
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

def send_packet(seq_num, ack_num, flags, payload=None):
    if not payload:
        packet = pack_header(seq_num, ack_num, flags)
    else:
        packet = pack_header(seq_num, ack_num, flags) + payload
    return packet

def run_server(ip, port, discard):
    try:
        # Start connection
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((ip, port))
        server_seq_num = random_seq_num()
        base_server_seq_num = server_seq_num
        print("Server is listening...\n")

        # Receive SYN packet
        packet, client_address = server_socket.recvfrom(DRTP_struct.size)
        client_seq_num , _, flags = unpack_header(packet)
        base_client_seq_num = client_seq_num
        print("SYN packet is received")
        print_header(packet[:6], False)

        # Send SYN-ACK packet
        if flags[0] == 1:
            packet = send_packet(server_seq_num, client_seq_num + 1, set_flags(1, 1, 0, 0))
            server_socket.sendto(packet, client_address)
            print("SYN-ACK packet is sent")
            print_header(packet[:6], True)
        else:
            print("SYN packet is not received")
            socket.error("SYN packet is not received")

        # Receive ACK packet
        packet, _ = server_socket.recvfrom(DRTP_struct.size)
        _, ack_num, flags = unpack_header(packet)
        if ack_num == server_seq_num + 1 and flags[1] == 1:
            print("ACK packet is received")
            print_header(packet[:6], False)
        else:
            print("ACK packet is not received")
            socket.error("ACK packet is not received")

        # Connection established
        print("Connection established\n")
    
    # Exit on keyboard interrupt
    except KeyboardInterrupt:
        print("Server is stopped")
    
    # Handle socket errors
    except socket.error as e:
        print(f"Error: {e}")

def run_client(ip, port, filename, window_size):
    try:
        # Start connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.connect((ip, port))
        client_seq_num = random_seq_num()
        base_client_seq_num = client_seq_num
        print("Connection Establisht Phase:\n")

        # Send SYN packet
        packet = send_packet(client_seq_num, 0, set_flags(1, 0, 0, 0))
        client_socket.send(packet)
        print("SYN packet is sent")
        print_header(packet[:6], True)

        # Receive SYN-ACK packet
        packet = client_socket.recv(DRTP_struct.size)
        server_seq_num, ack_num, flags = unpack_header(packet)
        if ack_num == client_seq_num + 1 and flags[0] == 1 and flags[1] == 1:
            client_seq_num = ack_num
            print("SYN-ACK packet is received")
            print_header(packet[:6], False)
        else:
            print("SYN-ACK packet is not received")
            socket.error("SYN-ACK packet is not received")

        # Send ACK packet
        packet = send_packet(client_seq_num, server_seq_num + 1, set_flags(0, 1, 0, 0))
        client_socket.send(packet)
        print("ACK packet is sent")
        print_header(packet[:6], True)

        # Connection established
        print("Connection established\n")

        # Send file
        filesize = os.path.getsize(filename)
        print("Data Transfer Phase:\n")

        if debug:
            filesize = os.path.getsize(filename)
            print(f"Filesize: {filesize}")

        # Pack the file without the header
        payload = pack_file(filename)

        # Send the packets with GBN
        client_socket.settimeout(timeout)

    # Exit on keyboard interrupt
    except KeyboardInterrupt:
        print("Client is stopped")

    # Handle socket errors
    except socket.error as e:
        print(f"Error in handshake: {e}")