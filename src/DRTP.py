import struct
import socket
import random
import os

debug = False
show_packets = False
max_filename_length = 32
chunk_size = 1000
timeout = 5

print("\n")

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
    if debug:
        seq_num, ack_num, flags = unpack_header(header)
        print(f"seq_num: {seq_num}, ack_num: {ack_num}, flags: {flags}")

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

def run_server(ip, port):
    try:
        # Start connection
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((ip, port))
        print("Server is listening...\n")

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
            socket.error("SYN packet is not received")

        # Receive ACK packet
        ack_packet, _ = server_socket.recvfrom(DRTP_struct.size)
        _, _, flags = unpack_header(ack_packet)
        if flags[1] == 1:
            print("ACK packet is received")
            print_header(ack_packet)
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

def run_client(ip, port, filename):
    try:
        # Start connection
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.connect((ip, port))
        print("Connection Establisht Phase:\n")

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
            socket.error("SYN-ACK packet is not received")

        # Send ACK packet
        ack_packet = pack_header(ack_num, seq_num + 1, set_flags(0, 1, 0, 0))
        client_socket.send(ack_packet)
        print("ACK packet is sent")
        print_header(ack_packet)

        # Connection established
        print("Connection established\n")

        # Send file
        filesize = os.path.getsize(filename)
        print("Data Transfer Phase:\n")

        if debug:
            filesize = os.path.getsize(filename)
            print(f"Filesize: {filesize}")

        # Pack the file without the header
        packets = pack_file(filename)

    # Exit on keyboard interrupt
    except KeyboardInterrupt:
        print("Client is stopped")

    # Handle socket errors
    except socket.error as e:
        print(f"Error in handshake: {e}")