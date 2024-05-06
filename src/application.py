import argparse
import sys
import os
import socket
import DRTP
from config import *

def print_error(error_message):
    print(f"\033[1;31;1mError: \n\t{error_message}\n\033[0m", file=sys.stderr)

def main():
    def check_file(filename):
        error_message = None
        try:
            if max_filename_length < len(filename):
                error_message = f"{filename} is too long, the file name must be less than {max_filename_length} characters"
                raise ValueError
            if not os.path.isfile(filename):
                error_message = f"{filename} does not exist"
                raise ValueError
        except ValueError:
            print_error(error_message)
            parser.print_help()
            exit(1)
        return filename
    
    def check_ipaddress(ip):
        error_message = None
        try:
            socket.inet_pton(socket.AF_INET, ip)
        except socket.error as error_message:
            print_error(error_message)
            parser.print_help()
            exit(1)
        return ip
    
    def check_port(port):
        error_message = None
        try:
            port = int(port)
            if not 1024 <= port <= 65535:
                error_message = f"{port} is not a valid port number in the range 1024-65535"
                raise ValueError
        except ValueError:
            print_error(error_message)
            parser.print_help()
            exit(1)
        return port
    
    def check_positive_integer(value):
        error_message = None
        try:
            value = int(value)
            if value <= 0:
                error_message = f"{value} is not a positive integer"
                raise ValueError
        except ValueError:
            print_error(error_message)
            parser.print_help()
            exit(1)
        return value

    parser = argparse.ArgumentParser(description="DRTP file transfer application", epilog="end of help")

    # Define mutually exclusive group for client and server modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-s', '--server', action="store_true", help="Run in server mode")
    mode_group.add_argument('-c', '--client', action="store_true", help="Run in client mode")

    # Server arguments
    server_group = parser.add_argument_group('Server')
    server_group.add_argument('-d', '--discard', type=check_positive_integer, help="Discard a packet with the given sequence number")

    # Client arguments
    client_group = parser.add_argument_group('Client')
    client_group.add_argument('-f', '--file', type=check_file, required='-c' in sys.argv or '--client' in sys.argv, help="Name of the file to send")
    client_group.add_argument('-w', '--window', type=check_positive_integer, default=window_size, help="Set the window size, default %(default)s packets per window")

    # Common arguments
    parser.add_argument('-i', '--ip', type=check_ipaddress, default=default_ip, help="IP address to connect/bind to, in dotted decimal notation. Default %(default)s")
    parser.add_argument('-p', '--port', type=check_port, default=default_port, help="Port to use, default %(default)s")

    args = parser.parse_args()

    if args.server:
        DRTP.run_server(args.ip, args.port, args.discard)
    elif args.client:
        DRTP.run_client(args.ip, args.port, args.file, args.window)
    
if __name__ == "__main__":
    main()