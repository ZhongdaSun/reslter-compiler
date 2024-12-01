# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import json
import hashlib


class JsonSerialization:
    @staticmethod
    def serialize(data):
        return json.dumps(data, ensure_ascii=False,
                          indent=4,
                          separators=(",", ": "),
                          sort_keys=False, )

    @staticmethod
    def deserialize(json_data):
        return json.loads(json_data)

    @staticmethod
    def serialize_to_file(file, obj):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(obj, f,
                      ensure_ascii=False,
                      indent=4,
                      separators=(",", ": "),
                      sort_keys=False,
                      )
            f.close()

    @staticmethod
    def try_deeserialize_from_file(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                obj = json.load(f)
                f.close()
                return obj
        except:
            return None

    @staticmethod
    def try_deserialize(json_data):
        try:
            return json.loads(json_data)
        except:
            return None


def deterministic_short_hash(s):
    hash_length = 16  # bytes

    sha1 = hashlib.sha1()
    sha1.update(s.encode())
    hash_bytes = sha1.digest()[:hash_length]

    return ''.join(format(b, 'x') for b in hash_bytes)


def deterministic_short_stream_hash(stream):
    hash_length = 16  # bytes

    sha1 = hashlib.sha1()
    while True:
        chunk = stream.read(4096)  # Read in chunks of 4096 bytes
        if not chunk:
            break
        sha1.update(chunk)

    hash_bytes = sha1.digest()[:hash_length]

    return ''.join(format(b, 'x') for b in hash_bytes)
