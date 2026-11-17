"""Génère (ou conserve) un certificat HTTPS auto-signé. Usage : python selfsigned.py cert.pem key.pem"""
import os, sys, ipaddress, datetime as dt
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

cert, key = sys.argv[1], sys.argv[2]
names = [n.strip() for n in os.environ.get('TLS_DOMAIN', 'localhost').split(',') if n.strip()]
for n in ('localhost', '127.0.0.1'):
    if n not in names: names.append(n)
mark, sig = cert + '.san', ','.join(sorted(names))

def valid():
    try:
        c = x509.load_pem_x509_certificate(open(cert, 'rb').read())
        return os.path.exists(key) and open(mark).read() == sig and c.not_valid_after_utc > dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)
    except Exception:
        return False

if valid():
    print('Certificat auto-signé existant conservé'); sys.exit()

def san(n):
    try: return x509.IPAddress(ipaddress.ip_address(n))
    except ValueError: return x509.DNSName(n)

k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
sub = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, names[0]), x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Nounoutil')])
now = dt.datetime.now(dt.timezone.utc)
c = (x509.CertificateBuilder().subject_name(sub).issuer_name(sub).public_key(k.public_key()).serial_number(x509.random_serial_number())
     .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=825))
     .add_extension(x509.SubjectAlternativeName([san(n) for n in names]), False)
     .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
     .add_extension(x509.KeyUsage(digital_signature=True, key_encipherment=True, key_cert_sign=True, content_commitment=False, data_encipherment=False, key_agreement=False, crl_sign=False, encipher_only=False, decipher_only=False), True)
     .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
     .sign(k, hashes.SHA256()))
os.makedirs(os.path.dirname(cert) or '.', exist_ok=True)
open(key, 'wb').write(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())); os.chmod(key, 0o600)
open(cert, 'wb').write(c.public_bytes(serialization.Encoding.PEM)); open(mark, 'w').write(sig)
print('Certificat auto-signé créé pour :', sig)
