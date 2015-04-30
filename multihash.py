"""Multihash implementation in Python."""

import hashlib
import sys

import six

# Optional SHA-3 hashing via pysha3
try:
    import sha3
except ImportError:
    sha3 = None

# Optional BLAKE2 hashing via pyblake2
try:
    import pyblake2
except ImportError:
    pyblake2 = None


# Constants
SHA1 = 0x11
SHA2_256 = 0x12
SHA2_512 = 0x13
SHA3 = 0x14
BLAKE2B = 0x40
BLAKE2S = 0x41

NAMES = {
    'sha1':     SHA1,
    'sha2-256': SHA2_256,
    'sha2-512': SHA2_512,
    'sha3':     SHA3,
    'blake2b':  BLAKE2B,
    'blake2s':  BLAKE2S,
}

CODES = dict((v, k) for k, v in NAMES.items())

LENGTHS = {
    'sha1':    20,
    'sha256':  32,
    'sha512':  64,
    'sha3':    64,
    'blake2b': 64,
    'blake2s': 32,
}

FUNCS = {
    SHA1: hashlib.sha1,
    SHA2_256: hashlib.sha256,
    SHA2_512: hashlib.sha512,
}

if sha3:
    FUNCS[SHA3] = lambda: hashlib.new('sha3_512')

if pyblake2:
    FUNCS[BLAKE2B] = lambda: pyblake2.blake2b()
    FUNCS[BLAKE2S] = lambda: pyblake2.blake2s()


def _hashfn(hashfn):
    if six.callable(hashfn):
        return hashfn()

    elif isinstance(hashfn, six.integer_types):
        return FUNCS[hashfn]()

    elif isinstance(hashfn, six.string_types):
        if hashfn in NAMES:
            return FUNCS[NAMES[hashfn]]()

        elif hashfn.isdigit():
            return _hashfn(int(hashfn))

    raise ValueError('Unknown hash function "{0}"'.format(hashfn))


def is_app_code(code):
    """Check if the code is an application specific code."""
    if isinstance(code, six.integer_types):
        return code >= 0 and code < 0x10

    else:
        return False


def is_valid_code(code):
    """Check if the digest algorithm code is valid."""
    if is_app_code(code):
        return True

    elif isinstance(code, six.integer_types):
        return code in CODES

    else:
        return False


def decode(buf):
    """Decode a hash from the given Multihash."""
    if len(buf) < 3:
        raise ValueError('Buffer too short')

    if len(buf) > 129:
        raise ValueError('Buffer too long')

    buf = six.b(buf)
    code = buf[0]
    try:
        length = LENGTHS[code]
    except KeyError:
        raise ValueError('Invalid code "{0}"'.format(code))

    digest = buf[2:]
    if len(digest) != length:
        raise ValueError('Inconsistent length ({0} != {1})'.format(
            len(digest), length))

    return digest


def encode(digest, code):
    """Encode a hash digest along with the specified function code.

    >>> encoded = encode('testing', SHA1)
    >>> len(encoded)
    22
    >>> encoded[:2]
    bytearray(b'\\x11\\x07')

    >>> encoded = encode('works with sha3?', SHA3)
    >>> len(encoded)
    66
    >>> encoded[:2]
    bytearray(b'\\x14\\x10')
    """
    if not is_valid_code(code):
        raise TypeError('Unknown code')

    if len(digest) > 127:
        raise ValueError('Multihash does not support digest length > 127')

    hashfn = _hashfn(code)

    if isinstance(digest, six.binary_type):
        hashfn.update(digest)
    elif isinstance(digest, six.string_types):
        hashfn.update(digest.encode('utf-8'))

    output = bytearray([code, len(digest)])
    output.extend(hashfn.digest())
    return output
