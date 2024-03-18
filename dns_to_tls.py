#!/usr/bin/env python3
"""DNS to DNS over TLS proxy."""

import os
import socket
import ssl
import logging
import select
import threading

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def query_dns_over_tls(server_ip, server_port, server_name, ca_path, query, timeout=20):
    """Queries the given DNS server over TLS & returns response."""
    context = ssl.create_default_context()
    
    # Load the CA certificates from ca_path to validate the server's certificate
    if ca_path:
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(ca_path)
    else:
        logging.error("CA path not provided. Unable to verify server TLS certificate.")
        return None
    
    with socket.create_connection((server_ip, server_port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=server_name) as tls_sock:
            tls_sock.sendall(query)
            response = tls_sock.recv(4096)  # Adjust buffer size if necessary
            return response

def handle_tcp_client(client_socket, address, dns_info):
    logging.info(f"TCP connection from {address}")
    data = client_socket.recv(1024)  # Adjust buffer size if necessary
    if data:
        response = query_dns_over_tls(*dns_info, data)
        if response:
            client_socket.sendall(response)
        client_socket.close()

def handle_udp_client(udp_socket, data, address, dns_info):
    logging.info(f"UDP query from {address}")
    # Convert UDP DNS query to TCP format by adding a two-byte length prefix
    tcp_formatted_query = len(data).to_bytes(2, byteorder='big') + data
    
    # Query the DNS server over RLS using the TCP-formatted query
    tcp_formatted_response = query_dns_over_tls(*dns_info, tcp_formatted_query)
    
    if tcp_formatted_response:
        # Strip the two-byte length prefix from the response to convert it back to the UDP format
        udp_formatted_response = tcp_formatted_response[2:]
        
        # Send the UDP-formatted response back to the client
        udp_socket.sendto(udp_formatted_response, address)
    else:
        logging.error(f"Failed to get response for UDP query from {address}.")

def main():
    dns_server_ip = os.getenv('DNS_SERVER_IP', '1.1.1.1')
    dns_server_port = int(os.getenv('DNS_SERVER_PORT', '853'))
    dns_server_name = os.getenv('DNS_SERVER_NAME', 'cloudflare-dns.com')
    ca_path = os.getenv('CA_PATH', '/etc/ssl/certs/ca-certificates.crt')
    port = int(os.getenv('LISTENING_PORT', '35353'))  # Common port for both TCP and UDP DNS queries

    dns_info = (dns_server_ip, dns_server_port, dns_server_name, ca_path)

    # Setup TCP and UDP sockets
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind(('', port))
    udp_socket.bind(('', port))
    tcp_socket.listen(5)

    logging.info(f"Listening for DNS queries on TCP and UDP port {port}")

    try:
        while True:
            readable, _, _ = select.select([tcp_socket, udp_socket], [], [])
            for sock in readable:
                if sock is tcp_socket:
                    client_socket, addr = tcp_socket.accept()
                    threading.Thread(target=handle_tcp_client, args=(client_socket, addr, dns_info)).start()
                elif sock is udp_socket:
                    data, addr = udp_socket.recvfrom(512)  # Typical DNS query size
                    threading.Thread(target=handle_udp_client, args=(udp_socket, data, addr, dns_info)).start()
    except KeyboardInterrupt:
        logging.info("Shutting down the server.")
    finally:
        tcp_socket.close()
        udp_socket.close()

if __name__ == '__main__':
    main()