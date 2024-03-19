"""DNS to DNS over TLS proxy."""

import os
import socket
import ssl
import logging
import select
import threading
import dns.message
import dns.query

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

    # Parse the DNS query using dnspython
    try:
        dns_query = dns.message.from_wire(query)
    except Exception as e:
        logging.error(f"Failed to parse DNS query: {e}")
        return None

    # Use dnspython's dns.query.tls() function to send the query over TLS
    try:
        response = dns.query.tls(dns_query, server_ip, port=server_port, server_hostname=server_name, ssl_context=context, timeout=timeout)
        return response.to_wire()
    except Exception as e:
        logging.error(f"Failed to send DNS query over TLS: {e}")
        return None
    
def handle_tcp_client(client_socket, address, dns_info):
    logging.info(f"TCP connection from {address}")
    length_bytes = client_socket.recv(2)
    if not length_bytes:
        return
    
    data_length = int.from_bytes(length_bytes, byteorder='big')
    data = client_socket.recv(data_length)  # Now read the DNS query
    
    if data:
        response = query_dns_over_tls(*dns_info, data)
        if response:
            # Prepend the response length as per TCP DNS protocol
            response_length_bytes = len(response).to_bytes(2, byteorder='big')
            client_socket.sendall(response_length_bytes + response)
        client_socket.close()

def handle_udp_client(udp_socket, data, address, dns_info):
    logging.info(f"UDP query from {address}")
    response = query_dns_over_tls(*dns_info, data)
    if response:
        udp_socket.sendto(response, address)
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