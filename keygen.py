from nacl.signing import SigningKey

signing_key = SigningKey.generate()
private_hex = signing_key.encode().hex()
public_hex = signing_key.verify_key.encode().hex()

print("PRIVATE_KEY:", private_hex)
print("PUBLIC_KEY:", public_hex)