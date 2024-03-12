merged_post_if_lowercase_basis = ("n")
merged_post_basis = ("s")
merged_pre_basis = ("z", "d", "s")
apostrophes = ("'", "’", "‘", "`", "´")
quotation_marks = ('"', '„', '“')

merged_post_if_lowercase = tuple((a + b for a in apostrophes
                                  for b in merged_post_if_lowercase_basis))
merged_post = tuple((a + b for a in apostrophes for b in merged_post_basis))
merged_pre = tuple((getattr(b, func)() + a
                    for a in apostrophes
                    for b in merged_pre_basis
                    for func in ("upper", "lower")))


def split_off(character):
    if character == "-":
        return False
    if character in apostrophes:
        return False
    return not character.isalnum()


def remove_punctuation(word, c_start, c_stop, cut_start, cut_stop):
    if not word:
        return [], ""
    affix = []
    while True:
        c = word[c_start:c_stop]
        if not split_off(c):
            break
        if affix and affix[-1][-1] == c:
            affix[-1] = affix[-1] + c
        else:
            affix.append(c)
        word = word[cut_start:cut_stop]
        if not word:
            break
    return affix, word


def spaceafter(spaceafter):
    if spaceafter:
        return "_"
    return "SpaceAfter=No"


def process_sentence(sent):
    tokens = []
    idx = 1
    for word in sent.split():
        # Split off punctuation marks
        pre, word = remove_punctuation(word, 0, 1, 1, None)
        post, word = remove_punctuation(word, -1, None, 0, -1)
        if pre or post:
            for pre_ in pre:
                tokens.append((idx, pre_, spaceafter(not word)))
                idx += 1
            if word:
                tokens.append((idx, word, spaceafter(not post)))
                idx += 1
            for post_idx in range(len(post) - 1, -1, -1):
                tokens.append((idx, post[post_idx], spaceafter(post_idx == 0)))
                idx += 1
            continue
        # Additional tokenization (contractions)
        if len(word) > 2:
            pre = ""
            if word[:2] in merged_pre:
                pre = word[:2]
                word = word[2:]
            post = ""
            if word[-2:] in merged_post_if_lowercase \
                    and word[0] == word[0].lower():
                post = word[-2:]
                word = word[:-2]
            elif word[-2:] in merged_post:
                post = word[-2:]
                word = word[:-2]
            if pre or post:
                if pre and post:
                    idx_ = str(idx) + "-" + str(idx + 2)
                else:
                    idx_ = str(idx) + "-" + str(idx + 1)
                tokens.append((idx_, pre + word + post, spaceafter(True)))
                if pre:
                    tokens.append((idx, pre, spaceafter(True)))
                    idx += 1
                tokens.append((idx, word, spaceafter(True)))
                idx += 1
                if post:
                    tokens.append((idx, post, spaceafter(True)))
                    idx += 1
                continue
        tokens.append((idx, word, spaceafter(True)))
        idx += 1
    return tokens
