#!/usr/bin/env python3
"""
Certificate Generation Script for mTLS
Tạo Root CA, Server Cert, và Client Certs cho ESP32

Usage:
    python generate_certs.py                    # Generate all (CA + Server + 2 clients)
    python generate_certs.py --client 3         # Generate client cert for machine_3
    python generate_certs.py --server mydomain  # Generate server cert with SAN

Requirements:
    - OpenSSL installed and in PATH
"""

import subprocess
import os
import sys
import argparse
import hashlib
from datetime import datetime

# Configuration
CA_VALID_DAYS = 3650  # 10 years
SERVER_VALID_DAYS = 365  # 1 year
CLIENT_VALID_DAYS = 365  # 1 year

# Key sizes
CA_KEY_SIZE = 4096
SERVER_KEY_SIZE = 2048
CLIENT_KEY_SIZE = 2048

# Base directory
CERTS_DIR = os.path.dirname(os.path.abspath(__file__))


def run_openssl(args: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run openssl command"""
    cmd = ['openssl'] + args
    print(f"  Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def ensure_dirs():
    """Create directory structure"""
    dirs = ['ca', 'server', 'clients', 'crl']
    for d in dirs:
        os.makedirs(os.path.join(CERTS_DIR, d), exist_ok=True)
    print("✅ Directory structure ready")


def generate_ca():
    """Generate Root CA"""
    ca_key = os.path.join(CERTS_DIR, 'ca', 'ca.key')
    ca_crt = os.path.join(CERTS_DIR, 'ca', 'ca.crt')
    
    if os.path.exists(ca_crt):
        print("⚠️  CA already exists, skipping...")
        return
    
    print("\n🔐 Generating Root CA...")
    
    # Generate CA private key
    run_openssl([
        'genrsa', '-out', ca_key, str(CA_KEY_SIZE)
    ])
    
    # Generate CA certificate
    run_openssl([
        'req', '-x509', '-new', '-nodes',
        '-key', ca_key,
        '-sha256',
        '-days', str(CA_VALID_DAYS),
        '-out', ca_crt,
        '-subj', '/CN=Vending Machine Root CA/O=VendingCorp/C=VN'
    ])
    
    # Print fingerprint
    result = run_openssl([
        'x509', '-in', ca_crt, '-noout', '-fingerprint', '-sha256'
    ])
    print(f"  CA Fingerprint: {result.stdout.strip()}")
    print("✅ Root CA generated")


def generate_server_cert(domain: str = 'localhost', ip: str = '127.0.0.1'):
    """Generate Server certificate with SAN"""
    server_key = os.path.join(CERTS_DIR, 'server', 'server.key')
    server_csr = os.path.join(CERTS_DIR, 'server', 'server.csr')
    server_crt = os.path.join(CERTS_DIR, 'server', 'server.crt')
    server_ext = os.path.join(CERTS_DIR, 'server', 'server.ext')
    
    ca_key = os.path.join(CERTS_DIR, 'ca', 'ca.key')
    ca_crt = os.path.join(CERTS_DIR, 'ca', 'ca.crt')
    
    if os.path.exists(server_crt):
        print("⚠️  Server cert already exists, skipping...")
        return
    
    print(f"\n🖥️  Generating Server certificate (domain={domain}, ip={ip})...")
    
    # Create extensions file for SAN
    with open(server_ext, 'w') as f:
        f.write(f"""authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = {domain}
DNS.2 = localhost
DNS.3 = vending-server.local
IP.1 = {ip}
IP.2 = 127.0.0.1
""")
    
    # Generate server key
    run_openssl([
        'genrsa', '-out', server_key, str(SERVER_KEY_SIZE)
    ])
    
    # Generate CSR
    run_openssl([
        'req', '-new',
        '-key', server_key,
        '-out', server_csr,
        '-subj', f'/CN={domain}/O=VendingCorp/C=VN'
    ])
    
    # Sign with CA
    run_openssl([
        'x509', '-req',
        '-in', server_csr,
        '-CA', ca_crt,
        '-CAkey', ca_key,
        '-CAcreateserial',
        '-out', server_crt,
        '-days', str(SERVER_VALID_DAYS),
        '-sha256',
        '-extfile', server_ext
    ])
    
    # Print info
    result = run_openssl([
        'x509', '-in', server_crt, '-noout', '-fingerprint', '-sha256'
    ])
    print(f"  Server Fingerprint: {result.stdout.strip()}")
    
    # Cleanup
    os.remove(server_ext)
    print("✅ Server certificate generated")


def generate_client_cert(device_id: int):
    """Generate Client certificate for ESP32 device"""
    client_dir = os.path.join(CERTS_DIR, 'clients', f'machine_{device_id}')
    os.makedirs(client_dir, exist_ok=True)
    
    client_key = os.path.join(client_dir, 'client.key')
    client_csr = os.path.join(client_dir, 'client.csr')
    client_crt = os.path.join(client_dir, 'client.crt')
    client_ext = os.path.join(client_dir, 'client.ext')
    
    ca_key = os.path.join(CERTS_DIR, 'ca', 'ca.key')
    ca_crt = os.path.join(CERTS_DIR, 'ca', 'ca.crt')
    
    if os.path.exists(client_crt):
        print(f"⚠️  Client cert for machine_{device_id} already exists, skipping...")
        return
    
    print(f"\n📱 Generating Client certificate for machine_{device_id}...")
    
    # Create extensions file
    with open(client_ext, 'w') as f:
        f.write(f"""authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
URI.1 = urn:device:vending:machine_{device_id}
""")
    
    # Generate client key
    run_openssl([
        'genrsa', '-out', client_key, str(CLIENT_KEY_SIZE)
    ])
    
    # Generate CSR with device_id in CN
    run_openssl([
        'req', '-new',
        '-key', client_key,
        '-out', client_csr,
        '-subj', f'/CN=machine_{device_id}/O=VendingDevices/C=VN/serialNumber=DEV{device_id:06d}'
    ])
    
    # Sign with CA
    result = run_openssl([
        'x509', '-req',
        '-in', client_csr,
        '-CA', ca_crt,
        '-CAkey', ca_key,
        '-CAcreateserial',
        '-out', client_crt,
        '-days', str(CLIENT_VALID_DAYS),
        '-sha256',
        '-extfile', client_ext
    ])
    
    # Get fingerprint and serial
    fp_result = run_openssl([
        'x509', '-in', client_crt, '-noout', '-fingerprint', '-sha256'
    ])
    serial_result = run_openssl([
        'x509', '-in', client_crt, '-noout', '-serial'
    ])
    
    print(f"  Fingerprint: {fp_result.stdout.strip()}")
    print(f"  Serial: {serial_result.stdout.strip()}")
    
    # Generate ESP32 header file
    generate_esp32_header(device_id, client_dir, ca_crt)
    
    # Cleanup
    os.remove(client_ext)
    print(f"✅ Client certificate for machine_{device_id} generated")


def generate_esp32_header(device_id: int, client_dir: str, ca_crt: str):
    """Generate C header file for ESP32 with embedded certs"""
    header_file = os.path.join(client_dir, f'certs_machine_{device_id}.h')
    
    # Read certificates
    with open(ca_crt, 'r') as f:
        ca_pem = f.read()
    
    with open(os.path.join(client_dir, 'client.crt'), 'r') as f:
        client_pem = f.read()
    
    with open(os.path.join(client_dir, 'client.key'), 'r') as f:
        client_key_pem = f.read()
    
    # Generate header
    with open(header_file, 'w') as f:
        f.write(f"""/*
 * Auto-generated certificates for machine_{device_id}
 * Generated: {datetime.now().isoformat()}
 * 
 * DO NOT COMMIT THIS FILE TO VERSION CONTROL!
 */

#ifndef CERTS_MACHINE_{device_id}_H
#define CERTS_MACHINE_{device_id}_H

// Root CA Certificate (to verify server)
const char* root_ca = R"EOF(
{ca_pem})EOF";

// Client Certificate (device identity)
const char* client_cert = R"EOF(
{client_pem})EOF";

// Client Private Key (KEEP SECRET!)
const char* client_key = R"EOF(
{client_key_pem})EOF";

#endif // CERTS_MACHINE_{device_id}_H
""")
    print(f"  Generated ESP32 header: certs_machine_{device_id}.h")


def get_cert_info(cert_path: str) -> dict:
    """Extract certificate information"""
    info = {}
    
    # Get fingerprint
    result = run_openssl(['x509', '-in', cert_path, '-noout', '-fingerprint', '-sha256'], check=False)
    if result.returncode == 0:
        info['fingerprint'] = result.stdout.strip().split('=')[1]
    
    # Get serial
    result = run_openssl(['x509', '-in', cert_path, '-noout', '-serial'], check=False)
    if result.returncode == 0:
        info['serial'] = result.stdout.strip().split('=')[1]
    
    # Get subject
    result = run_openssl(['x509', '-in', cert_path, '-noout', '-subject'], check=False)
    if result.returncode == 0:
        info['subject'] = result.stdout.strip()
    
    # Get expiry
    result = run_openssl(['x509', '-in', cert_path, '-noout', '-enddate'], check=False)
    if result.returncode == 0:
        info['expires'] = result.stdout.strip()
    
    return info


def list_certs():
    """List all generated certificates"""
    print("\n📋 Certificate Inventory:")
    print("=" * 60)
    
    # CA
    ca_crt = os.path.join(CERTS_DIR, 'ca', 'ca.crt')
    if os.path.exists(ca_crt):
        info = get_cert_info(ca_crt)
        print(f"\n🔐 Root CA:")
        print(f"   {info.get('subject', 'N/A')}")
        print(f"   Fingerprint: {info.get('fingerprint', 'N/A')}")
        print(f"   {info.get('expires', 'N/A')}")
    
    # Server
    server_crt = os.path.join(CERTS_DIR, 'server', 'server.crt')
    if os.path.exists(server_crt):
        info = get_cert_info(server_crt)
        print(f"\n🖥️  Server:")
        print(f"   {info.get('subject', 'N/A')}")
        print(f"   Serial: {info.get('serial', 'N/A')}")
        print(f"   {info.get('expires', 'N/A')}")
    
    # Clients
    clients_dir = os.path.join(CERTS_DIR, 'clients')
    if os.path.exists(clients_dir):
        for device_dir in os.listdir(clients_dir):
            client_crt = os.path.join(clients_dir, device_dir, 'client.crt')
            if os.path.exists(client_crt):
                info = get_cert_info(client_crt)
                print(f"\n📱 {device_dir}:")
                print(f"   Serial: {info.get('serial', 'N/A')}")
                print(f"   Fingerprint: {info.get('fingerprint', 'N/A')}")
                print(f"   {info.get('expires', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description='Generate mTLS certificates')
    parser.add_argument('--client', type=int, help='Generate client cert for specific machine_id')
    parser.add_argument('--server', type=str, help='Server domain name (default: localhost)')
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='Server IP address')
    parser.add_argument('--list', action='store_true', help='List all certificates')
    parser.add_argument('--all', action='store_true', help='Generate all (CA + Server + 2 clients)')
    
    args = parser.parse_args()
    
    ensure_dirs()
    
    if args.list:
        list_certs()
        return
    
    if args.client:
        # Check CA exists
        if not os.path.exists(os.path.join(CERTS_DIR, 'ca', 'ca.crt')):
            print("❌ CA not found. Run without --client first to generate CA.")
            sys.exit(1)
        generate_client_cert(args.client)
        return
    
    if args.server:
        # Check CA exists
        if not os.path.exists(os.path.join(CERTS_DIR, 'ca', 'ca.crt')):
            print("❌ CA not found. Run without --server first to generate CA.")
            sys.exit(1)
        generate_server_cert(args.server, args.ip)
        return
    
    # Default: generate all
    print("🚀 Generating complete PKI infrastructure...")
    generate_ca()
    generate_server_cert()
    generate_client_cert(1)
    generate_client_cert(2)
    
    print("\n" + "=" * 60)
    print("🎉 PKI Infrastructure Ready!")
    print("=" * 60)
    list_certs()
    
    print("\n📝 Next steps:")
    print("   1. Keep ca/ca.key SECURE (offline if possible)")
    print("   2. Copy clients/machine_X/certs_machine_X.h to ESP32 project")
    print("   3. Configure server with server/server.crt and server/server.key")


if __name__ == '__main__':
    main()
