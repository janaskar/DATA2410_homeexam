import socket
import datetime
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
            print(f"{'' : <70}", end=f"seq_num: {seq_num}, ack_num: {ack_num}, flags: {flags}" + "\n")

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

def pack_header(seq_num, ack_num, flags):
    return DRTP_struct.pack(seq_num, ack_num, flags)

def unpack_header(header):
    seq_num, ack_num, flags = DRTP_struct.unpack(header)
    return (seq_num, ack_num, get_flags(flags))

def pack_file(filename):
    try:
        # Array to store the payload
        payload = []

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
                payload.append(file_raw_data)
                if not file_raw_data:
                    break
        
        # Print the number of packets
        if debug:
            print(f"Total packets to send {len(payload)}")

        # Print the first 2 packets
        if show_packets:
            print(f"First packet: {payload[0]}")
            print(f"Second packet: {payload[1]}")

        # Return the packets
        return payload
    
    # Handle file errors
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

def unpack_file(payload):
    try:
        # Create a new file
        filename = payload[:max_filename_length].decode().strip('\0')
        print(f"Filename: {filename}")
        filename = os.path.join("output", filename)
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(payload[max_filename_length:])
            print(f"File is written to {filename}")
    except Exception as e:
        print(f"Error: {e}")

# Send a packet with the given sequence number, acknowledgment number, flags, and optional payload
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
        print("Server is listening...\n")

        # Receive SYN packet
        packet, client_address = server_socket.recvfrom(DRTP_struct.size)
        ack_num , _, flags = unpack_header(packet)
        print("SYN packet is received")
        print_header(packet[:6], False)

        # Send SYN-ACK packet
        seq_num = 0
        if flags[0] == 1:
            packet = send_packet(seq_num, ack_num + 1, set_flags(1, 1, 0, 0))
            server_socket.sendto(packet, client_address)
            print("SYN-ACK packet is sent")
            print_header(packet[:6], True)
        else:
            socket.error("SYN packet is not received")

        # Receive ACK packet
        packet, _ = server_socket.recvfrom(DRTP_struct.size)
        ack_num, seq_num, flags = unpack_header(packet)
        if ack_num == seq_num + 1 and flags[1] == 1:
            print("ACK packet is received")
            print_header(packet[:6], False)
        else:
            socket.error("ACK packet is not received")

        # Connection established
        print("Connection established\n")   

        # Start receiving the file
        server_socket.settimeout(timeout * 10)
        start_time = datetime.datetime.now()

        # Receive file and send ACKs
        excpected_ack_num = 1
        payload = []
        seqs_received = []
        while True:
            packet, _ = server_socket.recvfrom(chunk_size)
            ack_num, seq_num, flags = unpack_header(packet[:DRTP_struct.size])

            # Discard the packet
            if ack_num == discard and flags[2] == 0:
                discard = None
                continue

            print_header(packet[:6], False)

            # Send ACK for the received packet
            if ack_num <= excpected_ack_num and not flags[2] == 1:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- packet {ack_num} is received")
                excpected_ack_num += 1
                payload.append(packet[DRTP_struct.size:])
                seqs_received.append(ack_num)
                packet = send_packet(seq_num, ack_num + 1, set_flags(0, 1, 0, 0))
                server_socket.sendto(packet, client_address)
                print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- sending ack for the received {ack_num}")
                print_header(packet[:6], True)
            elif flags[2] == 1:
                # FIN packet is received
                print("\nFIN packet is received")
                print_header(packet[:6], False)

                # Send FIN-ACK packet
                packet = send_packet(seq_num, ack_num + 1, set_flags(0, 1, 1, 0))
                server_socket.sendto(packet, client_address)
                print("FIN-ACK packet is sent\n")
                print_header(packet[:6], True)
                break
            else:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- out-of-order packet {ack_num} is received")
    
        # Elapsed time
        elapsed_time = datetime.datetime.now() - start_time

        # Cal
        throughput = ((len(payload) * (chunk_size - DRTP_struct.size)) / elapsed_time.total_seconds()) * 8
        if throughput > 1000000:
            throughput = float(throughput) / 1000000
            print(f"The throughput is {throughput:.2f} Mbps")
        elif throughput > 1000:
            throughput = float(throughput) / 1000
            print(f"The throughput is {throughput:.2f} Kbps")
        else:
            print(f"The throughput is {throughput:.2f} bps")
        
        print("Connection Closes\n")

        # Write the file
        unpack_file(b''.join(payload))

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
        seq_num = 0
        print("Connection Establisht Phase:\n")

        # Send SYN packet
        packet = send_packet(seq_num, 0, set_flags(1, 0, 0, 0))
        client_socket.send(packet)
        print("SYN packet is sent")
        print_header(packet[:6], True)

        # Receive SYN-ACK packet
        packet = client_socket.recv(DRTP_struct.size)
        ack_num, seq_num, flags = unpack_header(packet)
        if flags[0] == 1 and flags[1] == 1:
            print("SYN-ACK packet is received")
            print_header(packet[:6], False)
        else:
            print("SYN-ACK packet is not received")
            socket.error("SYN-ACK packet is not received")

        # Send ACK packet
        ack_num += 1
        packet = send_packet(seq_num, ack_num, set_flags(0, 1, 0, 0))
        client_socket.send(packet)
        print("ACK packet is sent")
        print_header(packet[:6], True)

        # Connection established
        print("Connection established\n")

        # Send file
        filesize = os.path.getsize(filename)
        print("Data Transfer:\n")

        if debug:
            filesize = os.path.getsize(filename)
            print(f"Filesize: {filesize}")

        # Pack the file without the header
        payload = pack_file(filename)

        # Send the packets with GBN
        start_time = datetime.datetime.now()
        client_socket.settimeout(timeout)

        # Set variables
        seq_num = 0
        slidding_window = []
        exspected_ack = 2

        while True:
            # Send the packets
            while(len(slidding_window) < window_size and seq_num < len(payload)):
                seq_num += 1
                slidding_window.append(seq_num)
                if seq_num > len(payload):
                    break
                packet = send_packet(seq_num, ack_num, set_flags(0, 0, 0, 0), payload[seq_num - 1])
                client_socket.send(packet)
                print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- packet with seq = {seq_num} is sent, sliding window = {slidding_window}")
                print_header(packet[:6], True)

            # Receive the ACKs
            try:
                packet = client_socket.recv(DRTP_struct.size)
                _, check_ack_num, flags = unpack_header(packet)
                if check_ack_num == exspected_ack:
                    slidding_window.pop(0)
                    exspected_ack += 1
                    print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- ACK for packet = {check_ack_num} is received")
                    print_header(packet[:6], False)
                else:
                    print(f"Expected ACK: {exspected_ack} received ACK: {check_ack_num}, Error: ACK is not expected")
                    exspected_ack = check_ack_num + 1
                    raise socket.timeout

            # Resend window on timeout
            except socket.timeout:
                print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- RTO occured")
                for seq_num in slidding_window:
                    if seq_num > len(payload):
                        break
                    packet = send_packet(seq_num, ack_num, set_flags(0, 0, 0, 0), payload[seq_num - 1])
                    client_socket.send(packet)
                    print(f"{datetime.datetime.now().strftime('%H:%M:%S.%f')} -- retransmitting packet with seq = {seq_num}")
            
            # Send FIN packet after sending all the packets
            if len(slidding_window) == 0:
                packet = send_packet(check_ack_num, ack_num, set_flags(0, 0, 1, 0))
                client_socket.send(packet)
                print("\nDATA Finished\n\nConnection Teardown:\n\nFIN packet is sent")
                print_header(packet[:6], True)

                # Receive FIN-ACK packet
                packet = client_socket.recv(DRTP_struct.size)
                _, check_ack_num, flags = unpack_header(packet)
                if flags[2] == 1 and flags[1] == 1:
                    print("FIN-ACK packet is received\nConnection Closes")
                    print_header(packet[:6], False)
                    break
                else:
                    print("FIN-ACK packet is not received")
                    print_header(packet[:6], False)
                    socket.error("FIN-ACK packet is not received")
                
    # Exit on keyboard interrupt
    except KeyboardInterrupt:
        print("Client is stopped")

    # Handle socket errors
    except socket.error as e:
        print(f"Error: {e}")