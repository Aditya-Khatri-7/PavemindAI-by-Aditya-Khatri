from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
print(f"Testing URI: {MONGODB_URI}")

try:
    print("Testing with default options...")
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    print("Successfully connected with default options!")
except Exception as e:
    print(f"Default options failed: {e}")
    
try:
    print("\nTesting with tlsAllowInvalidCertificates=True...")
    client = MongoClient(MONGODB_URI, tls=True, tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("Successfully connected with tlsAllowInvalidCertificates=True!")
except Exception as e:
    print(f"tlsAllowInvalidCertificates=True failed: {e}")

try:
    print("\nTesting with direct connection and tlsAllowInvalidCertificates...")
    # Try a simple connection without replica set options if needed, but the SRV record parses it
    # We can also parse the connection string manually or add tlsAllowInvalidCertificates=true to the URL
    if "?" in MONGODB_URI:
        uri_tls = MONGODB_URI + "&tlsAllowInvalidCertificates=true"
    else:
        uri_tls = MONGODB_URI + "?tlsAllowInvalidCertificates=true"
    client = MongoClient(uri_tls)
    client.admin.command('ping')
    print("Successfully connected with modified URI string!")
except Exception as e:
    print(f"Modified URI string failed: {e}")
