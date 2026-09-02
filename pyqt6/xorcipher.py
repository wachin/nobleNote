# nobleNote, a note taking application - PyQt6 port
# Licensed under the MIT license.
"""Simple Xor encryption/decryption class (equivalent of xorcipher.h/cpp)."""


class XorCipher:
    # only static methods; no instances are created
    def __new__(cls):
        raise TypeError("XorCipher cannot be instantiated")

    @staticmethod
    def encrypt(source_string: str, key: int) -> str:
        chars = [chr((ord(c) ^ (key % 255)) & 0xFF) for c in source_string]
        return "".join(chars)

    @staticmethod
    def decrypt(encrypted_string: str, key: int) -> str:
        chars = [chr((ord(c) ^ (key % 255)) & 0xFF) for c in encrypted_string]
        return "".join(chars)