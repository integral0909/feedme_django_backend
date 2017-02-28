from collections import OrderedDict


class CustomOrderedDict(OrderedDict):
    def next_from_key(self, key):
        try:
            daycode = to_shortcode(key)
            return list(self.items())[list(self.keys()).index(daycode) + 1]
        except KeyError:
            return None
        except IndexError:
            return list(self.items())[0]

    def prev_from_key(self, key):
        try:
            daycode = to_shortcode(key)
            return list(self.items())[list(self.keys()).index(daycode) - 1]
        except KeyError:
            return None
        except IndexError:
            return list(self.items())[6]


DAYWEEK_MAP = CustomOrderedDict([('sun', 'Sunday'), ('mon', 'Monday'), ('tue', 'Tuesday'),
                                 ('wed', 'Wednesday'), ('thu', 'Thursday'),
                                 ('fri', 'Friday'), ('sat', 'Saturday')])


def convert(day_str):
    if len(day_str) == 3:
        return DAYWEEK_MAP.get(day_str, None)
    else:
        try:
            # list(mydict.keys())[list(mydict.values()).index(16)]
            return [daycode for daycode, day in DAYWEEK_MAP.items() if day == day_str][0]
        except KeyError:
            return None


def next(day_str):
    daycode = to_shortcode(day_str)
    return DAYWEEK_MAP.next_from_key(daycode)


def prev(day_str):
    daycode = to_shortcode(day_str)
    return DAYWEEK_MAP.prev_from_key(daycode)


def to_shortcode(day_str):
    if len(day_str) != 3:
        return convert(day_str)
    return day_str


def to_longcode(day_str):
    if len(day_str) == 3:
        return convert(day_str)
    return day_str


def day_to_index(day_str):
    daycode = to_shortcode(day_str)
    return list(DAYWEEK_MAP.keys()).index(daycode)


def index_to_day(idx):
    return list(DAYWEEK_MAP.values())[idx]
