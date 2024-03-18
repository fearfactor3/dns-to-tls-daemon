# DNS to DNS over TLS proxy

## Implementation

This is a proxy that listens to TCP on a socket, forwards the bytes received to a remote server, and returns the answer through the socket.  
It uses only Python 3 libraries.  It can handle one DNS query at a time.  By default, it listens on port `35353` and send DNS queries to Cloudflare.  The listening address, port, and the DNS server that should be used to forward the queries are configurable using environment variables.  Here are the options that are configurable and their default values:

```bash
DNS_SERVER_IP 1.1.1.1
DNS_SERVER_PORT 853
DNS_SERVER_NAME cloudflare-dns.com
CA_PATH /etc/ssl/certs/ca-certificates.crt
ENV LISTENING_PORT 35353
```

## How to run

Bring it up using the command below from where you cloned the source code:

```bash
docker build -t dns-proxy .
```

Run the image:

```bash
docker run -d -p 35353:35353/tcp -p 35353:35353/udp --name dns-proxy-instance --restart=always dns-proxy
```

## Testing

You can test it running the `dig` command for UDP connection below:

```bash
dig @localhost -p 35353 google.com AAAA
```

This should be the response from testing it via UDP

```bash
; <<>> DiG 9.18.24 <<>> @localhost -p 35353 example.com AAAA
; (2 servers found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 40171
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; PAD: (396 bytes)
;; QUESTION SECTION:
;example.com.                   IN      AAAA

;; ANSWER SECTION:
example.com.            80589   IN      AAAA    2606:2800:220:1:248:1893:25c8:1946

;; Query time: 83 msec
;; SERVER: ::1#35353(localhost) (UDP)
;; WHEN: Mon Mar 18 14:34:53 EDT 2024
;; MSG SIZE  rcvd: 468
```

You can test it running the `dig` command for TCP connection below:

```bash
dig @localhost -p 35353 google.com +tcp
```

```bash
; <<>> DiG 9.18.24 <<>> @localhost -p 35353 example.com +tcp
; (2 servers found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 7910
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; PAD: (408 bytes)
;; QUESTION SECTION:
;example.com.                   IN      A

;; ANSWER SECTION:
example.com.            81487   IN      A       93.184.216.34

;; Query time: 79 msec
;; SERVER: ::1#35353(localhost) (TCP)
;; WHEN: Mon Mar 18 14:34:56 EDT 2024
;; MSG SIZE  rcvd: 468
```

Here are the logs created to test the connection on the Docker container.

```bash
2024-03-18 18:34:51,134 - INFO - Listening for DNS queries on TCP and UDP port 35353
2024-03-18 18:34:53,338 - INFO - UDP query from ('192.168.127.1', 20703)
2024-03-18 18:34:56,340 - INFO - TCP connection from ('192.168.127.1', 45511)
```

## Improvements

- Implement using the `asyncio` method instead of the `threading` method.
- Better Metrics and Logging.
- Graceful Shutdown

## Imagine this proxy being deployed in an infrastructure.  What would be the security concerns you would raise?
  
### These are some of the following concerns I would raise

- Man in the middle attacks
- Currently, it is accessible by `localhost` and we will want to place it on a private subnet that can only be accessed with the proper
security groups configured and outbound traffic going through a NAT gateway.
- Denial of Service (DoS) Attacks
- Logging and Privacy Concerns

## How would you integrate that solution in a distributed, microservices-oriented and containerized architecture?

Integrating a DNS to DNS-over-TLS proxy solution into a distributed, microservices-oriented, and containerized architecture involves considering several factors to ensure scalability, resilience, and security.

- **Containerization**: Package the DNS to DNS-over-TLS proxy solution into a Docker container or any container runtime-compatible image. This ensures consistency across different environments and simplifies deployment.

- **Service Discovery**: In a microservices architecture, services need to discover and communicate with each other dynamically. Use a service discovery mechanism such as Kubernetes DNS or Consul to register and discover instances of the DNS proxy service.

- **Load Balancing**: Implement load balancing to distribute incoming DNS queries across multiple instances of the DNS proxy. This improves scalability and resilience by preventing overload on individual proxy instances.

- **Health Checking and Auto-Scaling**: Configure health checks to monitor the status of DNS proxy instances. Automatically scale the number of proxy instances up or down based on demand to handle fluctuating query loads efficiently.

- **Secret Management**: Manage sensitive information such as TLS certificates securely using a secret management solution like Kubernetes Secrets or HashiCorp Vault. Avoid hardcoding credentials or sensitive data in the container images.

- **Network Security Policies**: Implement network security policies to control inbound and outbound traffic to the DNS proxy instances. Use firewall rules, network policies, or Kubernetes Network Policies to restrict access to authorized clients and upstream DNS servers.

- **Logging and Monitoring**: Collect logs and metrics from the DNS proxy instances to monitor performance, detect anomalies, and troubleshoot issues. Use logging solutions like ELK Stack or centralized logging platforms and monitoring tools like Prometheus and Grafana.

- **Container Orchestration**: Deploy the DNS proxy solution using a container orchestration platform such as Kubernetes or Docker Swarm. These platforms provide features for deployment automation, rolling updates, self-healing, and resource management.

- **High Availability**: Ensure high availability of the DNS proxy solution by deploying it across multiple availability zones or regions. Use features like Kubernetes ReplicaSets or Kubernetes Deployments with multiple replicas to ensure redundancy and fault tolerance.

- **Continuous Integration/Continuous Deployment (CI/CD)**: Implement CI/CD pipelines to automate the build, test, and deployment processes of the DNS proxy solution. Use tools like Jenkins, GitLab CI/CD, or GitHub Actions to streamline the development and deployment workflows.