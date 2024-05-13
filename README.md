# DRTP File Transfer Application

This Python application facilitates file transfer using the DATA2410 Reliable Transport Protocol (DRTP). It offers both server and client modes for transferring files over a network.

## Requirements

- python
- mininet
- xterm
- openvswitch-switch

```bash
sudo apt-get install python3 mininet xterm openvswitch-switch
```

## Installation

1. Clone this repository.
2. Ensure the `config.py` file is correctly configured.
3. Start the Mininet network using the following command:

```bash
sudo python3 simple_topo.py
```
4. Start the server in one terminal and the client in another terminal.

## Usage

To run DRTP, you MUST run it in either server mode or client mode. The server mode must be started first.

- `-h`, `--help`: Show the help message and exit.

### Server Mode

To run the application in server mode:

```bash
python3 application.py -s [-d DISCARD] [-i IP] [-p PORT]
```

- `-d`, `--discard`: Discard a packet with the given sequence number.
- `-i`, `--ip`: IP address to bind to (default is specified in `config.py`).
- `-p`, `--port`: Port to bind to (default is specified in `config.py`).

### Client Mode

To run the application in client mode:

```bash
python application.py -c -f FILE [-w WINDOW_SIZE] [-i IP] [-p PORT]
```

- `-f`, `--file`: Name of the file to send. (required).
- `-w`, `--window`: Set the window size (default is specified in `config.py`).
- `-i`, `--ip`: IP address to connect to (default is specified in `config.py`).
- `-p`, `--port`: Port to connect to (default is specified in `config.py`).

## Example

### Server Mode

```bash
python application.py -s -d 8 -i 10.0.1.2 -p 8080
```

This command runs the server in discard mode on IP address `10.0.1.2` and port `8080`. It discards the packet with sequence number 8.

### Client Mode

```bash
python application.py -c -f iceland_safiqul.jpg -w 5 -i 10.0.1.2 -p 8080
```

This command sends the file `iceland_safiqul.jpg` using a window size of 5 packets to the server at IP address `10.0.1.2` and port `8080`.

## Discussion:

Test your code in mininet using `simple-topo.py`

1. Execute the file transfer application with window sizes of 3, 5, and 10. Calculate the throughput values for each of these configurations and provide an explanation for your results. For instance, discuss why you observe an increase in throughput as you increase the window size.
2. Modify the RTT to 50ms and 200ms. Run the file transfer application with window sizes of 3, 5, and 10. Calculate throughput values for all these scenarios and provide an explanation for your results.
To change the RTT, replace the value of 100ms with 50ms or 200ms in line 43 of your simple-topo.py file: `net["r"].cmd("tc qdisc add dev r-eth1 root netem delay 100ms")` in your `simple-topo.py` 
3. Use the `--discard` or `-d` flag on the server side to drop a packet, which will make the client resend it. Show how the reliable transport protocol works and how it deals with resent packets.
4. To demonstrate how effective your code is, use tc-netem (refer to the [lab manual](https://github.com/safiqul/2410/blob/main/docs/netem/mininet-tc-delay.md)) to simulate packet loss. To do this, modify your simple-topo.py file by commenting out line#43 `net["r"].cmd("tc qdisc add dev r-eth1 root netem delay 100ms")` and uncommenting line#44: `net["r"].cmd("tc qdisc add dev r-eth1 root netem delay 100ms loss 2%")`. Test with a loss rate of 5% as well. Include the results in your discussion section and explain what you observe.