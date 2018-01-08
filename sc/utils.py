from random import choice


def levenshtein_dist(s: str, t: str):
    if s == "":
        return len(t)
    if t == "":
        return len(s)
    if s[-1] == t[-1]:
        cost = 0
    else:
        cost = 1

    res = min([levenshtein_dist(s[:-1], t) + 1,
               levenshtein_dist(s, t[:-1]) + 1,
               levenshtein_dist(s[:-1], t[:-1]) + cost])
    return res


def random_string(len: int = 8) -> str:
    return "".join(choice("0123456789ABCDEF") for _ in range(len))
