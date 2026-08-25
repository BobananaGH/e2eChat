# code/certs/generate_certs.py
import datetime
import ipaddress
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_self_signed():
    # 1. Generate RSA Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # 2. Build Certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FLUX"),
        x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1"),
    ])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        now - datetime.timedelta(days=1)
    ).not_valid_after(
        now + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")), 
            x509.DNSName("localhost")
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # 3. Output Paths
    certs_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(certs_dir, exist_ok=True)
    
    key_path = os.path.join(certs_dir, "server.key")
    cert_path = os.path.join(certs_dir, "server.crt")
    
    # 4. Save Private Key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # 5. Save Certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

if __name__ == "__main__":
    generate_self_signed()
    print("Self-signed certificate (server.crt) and key (server.key) generated successfully.")