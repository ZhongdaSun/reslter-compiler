# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Access path for property
class AccessPath:

    def __init__(self, path: []):
        self.path = path

    def __dict__(self):
        return {"path": self.path}

    def __str__(self):
        return "".join(self.path)

    def __eq__(self, other):
        if other is None:
            return False
        else:
            if len(self.path) == len(other.path):
                for i in range(0, len(self.path)):
                    if self.path[i] != other.path[i]:
                        return False
                return True
            else:
                return False

    def get_path_property_name_parts(self):
        """
        get the property name of the path（except'[0]'）

        @return: the list of path excluding the '[0]'
        @rtype: List[str]
        """
        from restler.utils import restler_logger as logger
        from compiler.config import ConfigSetting
        logger.write_to_main(f"self.path={self.path}", ConfigSetting().LogConfig.access_paths)
        return [x for x in self.path if x != "[0]"]

    def get_path_parts_for_name(self):
        """
        get the path name，change '[0]' to '0'

        @return: the string list after changed
        @rtype: List[str]
        """
        return ["0" if x == "[0]" else x for x in self.path]

    def get_parent_path(self):
        """
        Get the father of path

        @return: father of path(remove the last part)
        @rtype: AccessPath
        """
        return AccessPath(self.path[:-1]) if self.path else self

    def get_json_pointer(self):
        """
        Get the path of Json's format

        @return: the path of json's format or None
        @rtype: str or None
        """
        if len(self.path) == 0:
            return None
        else:
            return "".join(self.path)

    def get_name_part(self):
        """
        Extract the last part of a path.

        @return: The last part of the path.
        @rtype: str
        """
        path_property_name_parts = self.get_path_property_name_parts()
        return path_property_name_parts[-1] if path_property_name_parts else None

    def length(self):
        return len(self.path)


EmptyAccessPath = AccessPath([])


# Validate JSON Pointer notation: /parent/[0]/child/name
def try_get_access_path_from_string(string):
    """
    Attempt to create an AccessPath object from a string

    @param string: A string containing a JSON pointer format path
    @type  string: str

    @return: The parsed AccessPath object or None
    @rtype: AccessPath or None
    """
    if string.startswith("/"):
        path = [part for part in string.split("/") if part]
        if path:
            return AccessPath(path)
    return None
