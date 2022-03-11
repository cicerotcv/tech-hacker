# -*- coding: utf-8 -*-

import socket
import argparse

SINGLE_HOST_PORTS = list(range(21, 1001))
NETWORK_PORTS = [21, 22, 23, 25, 53, 514]


class Target:
    def __init__(self, target):
        self.target = target

    def is_network(self):
        return len(self.target.split('/')) == 2

    def is_single_host(self):
        return not self.is_network()

    def __iter__(self):
        target = self.target
        if self.is_network():
            (a, b, c, d) = target.split('/')[0].split('.')
            for i in range(255):
                yield f'{a}.{b}.{c}.{i}'
        else:
            yield target


class Connection():
    def __init__(self, ip, port, timeout=3):
        self.ip = ip
        self.port = port
        self.is_connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.service = self.get_service(port)

    def get_service(self, port):
        try:
            tcp_service = socket.getservbyport(port, 'tcp')
        except:
            tcp_service = None
        # try:
        #     udp_service = socket.getservbyport(port, 'udp')
        # except:
        #     udp_service = None

        return {
            "tcp": tcp_service,
            # "udp": udp_service
        }

    def attempt_connection(self, auto_close=True):
        ip = self.ip
        port = self.port

        result = self.sock.connect_ex((ip, port))

        self.is_connected = result == 0

        if auto_close:
            self.close()

    def close(self):
        self.sock.close()


def get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--target', type=str,
                        required=True, help='Target address. Accepted formats: xxx.xxx.xxx.0/xx for entire network or xxx.xxx.xxx.xxx for single host')

    parser.add_argument('-p', '--portrange', type=str,
                        help=f'target ports. [Defaults to 21:1000 if the target is a single host or 21,22,23,25,53,514 if the target is and entire network]')

    parser.add_argument('--timeout', type=float, default=3,
                        help=f'Timeout (seconds) for connection to wait before setting to "refused"')

    args = parser.parse_args()

    return args


def parse_ports(ports=None, target_is_single_host=None):
    if ports is None:
        return SINGLE_HOST_PORTS if target_is_single_host else NETWORK_PORTS
    if ':' in ports:
        start, end = ports.split(':')
        return list(range(int(start), int(end)))
    if ',' in ports:
        return [int(port) for port in ports.split(',')]
    raise Exception(f"Unaccepted port format: {ports}")


def log(connection: Connection):
    ip = connection.ip
    port = connection.port
    tcp_service = connection.service.get('tcp')
    # udp_service = connection.service.get('udp')
    status = 'established' if connection.is_connected else 'refused'
    line_start = f'[{ip}:{port}] '.ljust(22, ':')
    print(f'{line_start}:: {status} | tcp: {tcp_service}')


def main():
    args = get_args()

    target = Target(args.target)
    ports = args.portrange
    timeout = args.timeout

    for target_ip in target:
        for port in parse_ports(ports, target.is_single_host()):

            conn = Connection(target_ip, port, timeout=timeout)
            conn.attempt_connection(auto_close=True)
            if conn.is_connected:
                log(conn)


if __name__ == '__main__':
    main()
