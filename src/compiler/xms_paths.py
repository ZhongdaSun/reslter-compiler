# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# A path in x-ms-path format

def get_x_ms_path(endpoint):
    # Best-effort fallback - try to use the original endpoint
    path_part, query_part = endpoint.split('?') if "?" in endpoint else endpoint, ""
    return XMsPath(path_part=path_part, query_part=query_part)


# Transform x-ms-paths present in the specification into paths, so they can be parsed
# with a regular OpenAPI specification parser.
def convert_xms_paths_to_paths(xms_paths_endpoints):
    mapping = {}
    for ep in xms_paths_endpoints:
        x_ms_path = get_x_ms_path(ep)
        if x_ms_path:
            normalized_endpoint = x_ms_path.get_normalized_endpoint()
            mapping[ep] = normalized_endpoint
        else:
            mapping[ep] = ep
    return mapping


# for about x-ms-parth, please checking with the website.
# https://github.com/Azure/autorest/tree/main/docs.
# it should not be supported.
# todo
class XMsPath:
    def __init__(self, path_part, query_part):
        # The path part of the endpoint declared in the specification
        self.path_part = path_part
        # The query part of the endpoint
        self.query_part = query_part

    def get_endpoint(self):
        return f"{self.path_part}?{self.query_part}"

    def get_normalized_endpoint(self):
        transformed_query = self.query_part.replace("=", "/").replace("&", "/")
        if transformed_query == "":
            normalized_endpoint = f"{self.path_part}" \
                if self.path_part != "/" else f"{self.path_part}{transformed_query}"
        else:
            normalized_endpoint = f"{self.path_part}/{transformed_query}" \
                if self.path_part != "/" else f"{self.path_part}{transformed_query}"
        return normalized_endpoint

    def __dict__(self):
        return {
            "pathPart": self.path_part,
            "queryPart": self.query_part
        }