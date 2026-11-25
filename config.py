import os

from cryptography.hazmat.primitives.asymmetric import rsa

from cryptography.hazmat.primitives import serialization


def generate_keys():

    os.makedirs("keys", exist_ok=True)

    private_path = "keys/doctor_private_key.pem"

    public_path = "keys/doctor_public_key.pem"

    if os.path.exists(private_path) or os.path.exists(public_path):

        print("Keys already exist.")

        return

    private_key = rsa.generate_private_key(

        public_exponent=65537,

        key_size=2048

    )

    with open(private_path, "wb") as file:

        file.write(

            private_key.private_bytes(

                encoding=serialization.Encoding.PEM,

                format=serialization.PrivateFormat.PKCS8,

                encryption_algorithm=serialization.NoEncryption()

            )

        )

    public_key = private_key.public_key()

    with open(public_path, "wb") as file:

        file.write(

            public_key.public_bytes(

                encoding=serialization.Encoding.PEM,

                format=serialization.PublicFormat.SubjectPublicKeyInfo

            )

        )

    try:

        os.chmod(private_path, 0o600)

    except OSError:

        pass

    print("RSA keys generated successfully!")


if __name__ == "__main__":

    generate_keys()