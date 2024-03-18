# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY dns_to_tls.py .

# Install any needed packages specified in requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt

# Make port 53 available to the world outside this container
EXPOSE 35353/udp 35353/tcp

# Define environment variable
ENV DNS_SERVER_IP=1.1.1.1
ENV DNS_SERVER_PORT=853
ENV DNS_SERVER_NAME=cloudflare-dns.com
ENV CA_PATH=/etc/ssl/certs/ca-certificates.crt
ENV LISTENING_PORT=35353

# Run dns_proxy.py when the container launches
CMD ["python", "./dns_to_tls.py"]
