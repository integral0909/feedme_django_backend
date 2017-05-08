from common.utils import replace_multiple


def parse(key):
    s3_char_map = {'&': 'and', ' ': '-', ',': '', '$': '', '(': '', ')': '', ';': '',
                   ':': '', '|': ''}
    return replace_multiple(key, s3_char_map)
