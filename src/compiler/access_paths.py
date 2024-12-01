# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Access path for property
class AccessPath:
    # 构造函数，初始化 'path' 属性
    def __init__(self, path: []):
        """ 初始化 AccessPath 对象并分配路径

        @param path: 代表访问路径的字符串列表
        @type  path: List[str]

        """
        self.path = path  # 存储传入的路径

    def __dict__(self):
        """
        返回 AccessPath 对象的字典表示

        @return: 包含路径的字典
        @rtype: dict
        """
        return {"path": self.path}

    def __str__(self):
        return "".join(self.path)

    def __eq__(self, other):
        """
        重载等于运算符，比较两个 AccessPath 对象是否相等
        比较当前对象与另一个 AccessPath 对象是否相等

        @param other: 另一个 AccessPath 对象
        @type  other: AccessPath

        @return: 如果两个对象的路径相等，返回 True，否则返回 False
        @rtype: bool
        """
        if other is None:  # 如果传入的对象为 None，则不相等
            return False
        else:
            # 如果路径长度相同，逐个元素进行比较
            if len(self.path) == len(other.path):
                for i in range(0, len(self.path)):
                    if self.path[i] != other.path[i]:
                        # 如果任一元素不同，则返回 False
                        return False
                # 如果所有元素相同，则返回 True
                return True
            else:
                # 如果路径长度不同，则返回 False
                return False

    def get_path_property_name_parts(self):
        """
        获取路径中的属性名称部分（排除数组索引 '[0]'）

        @return: 不包含数组索引 '[0]' 的路径部分列表
        @rtype: List[str]
        """
        from restler.utils import restler_logger as logger
        from compiler.config import ConfigSetting
        logger.write_to_main(f"self.path={self.path}", ConfigSetting().LogConfig.access_paths)
        return [x for x in self.path if x != "[0]"]  # 返回路径中不为 '[0]' 的部分

    def get_path_parts_for_name(self):
        """
        获取路径名称的部分，将 '[0]' 替换为 '0'

        @return: 转换后的路径部分列表
        @rtype: List[str]
        """
        return ["0" if x == "[0]" else x for x in self.path]  # 将 '[0]' 替换为 '0'

    def get_parent_path(self):
        """获取父级路径

        @return: 当前路径的父级路径（去掉最后一部分）
        @rtype: AccessPath
        """
        return AccessPath(self.path[:-1]) if self.path else self  # 返回去掉最后一部分的路径

    def get_json_pointer(self):
        """获取 JSON 指针形式的路径

        @return: 以 JSON 指针形式表示的路径字符串或 None
        @rtype: str or None
        """
        if len(self.path) == 0:  # 如果路径为空，返回 None
            return None
        else:
            return "".join(self.path)  # 否则将路径合并为字符串

    def get_name_part(self):
        """
        获取路径的最后一个名称部分

        @return: 路径中的最后一个属性名称部分或 None
        @rtype: str or None
        """
        path_property_name_parts = self.get_path_property_name_parts()  # 获取路径的名称部分
        return path_property_name_parts[-1] if path_property_name_parts else None  # 返回最后一个名称部分


    def length(self):
        """
        获取路径的长度

        @return: 路径的元素数量
        @rtype: int
        """
        return len(self.path)  # 返回路径的长度


# 空的 AccessPath 实例
EmptyAccessPath = AccessPath([])


# 验证 JSON 指针表示法: /parent/[0]/child/name
def try_get_access_path_from_string(string):
    """
    从字符串中尝试获取 AccessPath 对象

    @param string: 包含 JSON 指针格式路径的字符串
    @type  string: str

    @return: 解析后的 AccessPath 对象或 None
    @rtype: AccessPath or None
    """
    if string.startswith("/"):  # 如果字符串以 "/" 开头
        path = [part for part in string.split("/") if part]  # 将字符串按 "/" 分割
        if path:
            return AccessPath(path)  # 如果路径有效，返回 AccessPath 对象
    return None  # 如果字符串不是有效路径，返回 None