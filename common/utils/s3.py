from common.utils import replace_multiple


def parse(key):
    s3_char_map = {'&': 'and', ' ': '-', ',': '', '$': '', '(': '', ')': '', ';': '',
                   ':': '', '|': ''}
    return replace_multiple(key, s3_char_map)


def filename_from_url(url):
    filename = parse(url.split('/')[-1])
    return filename

