import hashlib

UTF8 = 'utf-8'


def str_to_hex_def(val_str):
    """ Creates a hex definition from a specified string

    @param val_str: The string to convert to a hex definition
    @type  val_str: Str

    @return: The hex definition of the string
    @rtype : Int

    """
    return hashlib.sha1(val_str.encode(UTF8)).hexdigest()
