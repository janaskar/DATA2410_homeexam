import argparse     # For parsing command line arguments
import sys          # For printing to stderr
import os           # For checking if a file exists
import socket       # For checking if an IP address is valid
import DRTP         # For running the DRTP application
from config import *    # Import the configuration variables

"""
Description:
    Function to print an error message in red text to stderr
Parameters:
    error_message: str - The error message to print
Return:
    None
"""
def print_error(error_message):
    print(f"\033[1;31;1mError: \n\t{error_message}\n\033[0m", file=sys.stderr)

"""
Description:
    Main function to parse command line arguments and run the DRTP application
Parameters:
    None
Return:
    None
"""
def main():
    """
    Description:
        Function to check if a file exists and is a valid file
    Parameters:
        filename: str - The name of the file to check
    Return:
        filename: str - The name of the file, else exit with error message
    """
    def check_file(filename):
        error_message = None
        try:
            test_filename = filename.encode('utf-8')
            if max_filename_length < len(test_filename):
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
    
    """
    Description:
        Function to check if an IP address is valid
    Parameters:
        ip: str - The IP address to check
    Return:
        ip: str - The IP address, else exit with error message
    """
    def check_ipaddress(ip):
        error_message = None
        try:
            socket.inet_pton(socket.AF_INET, ip)
        except socket.error as error_message:
            print_error(error_message)
            parser.print_help()
            exit(1)
        return ip
    
    """
    Description:
        Function to check if a port number is valid
    Parameters:
        port: str - The port number to check
    Return:
        port: int - The port number, else exit with error message # type: ignore
    """
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
    
    """
    Description:
        Function to check if a value is a positive integer
    Parameters:
        value: str - The value to check
    Return:
        value: int - The value, else exit with error message # type: ignore
    """
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
    
    # Create the argument parser and description of the application
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

    # Parse the command line arguments and run the application
    args = parser.parse_args()
    if args.server:
        DRTP.run_server(args.ip, args.port, args.discard)
    elif args.client:
        DRTP.run_client(args.ip, args.port, args.file, args.window)

# Run the main function if this script is executed
if __name__ == "__main__":
    main()