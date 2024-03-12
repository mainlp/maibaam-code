import sys


def read_conllu(filename):
    sentences = []
    with open(filename, encoding="utf8") as f_in:
        # sent_id = None
        comments = []
        tokens = []
        for line in f_in:
            line = line.strip()
            if not line:
                if tokens:
                    sentences.append((comments, tokens))
                # sent_id = None
                comments = []
                tokens = []
                continue
            if line.startswith("#"):
                comments.append(line)
                # if line.startswith("# sent_id"):
                #     sent_id = line.split("=")[1].strip()
                continue
            tokens.append(line.split("\t"))
        if tokens:
            sentences.append((comments, tokens))
    return sentences


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Expected args: UDPIPE_GSD UDPIPE_HDT OUT_FILE")
        sys.exit(1)
    udpipe_212gsd = sys.argv[1]
    udpipe_212hdt = sys.argv[2]
    out_file = sys.argv[3]

    pred_primary = read_conllu(udpipe_212hdt)
    pred_secondary = read_conllu(udpipe_212gsd)

    with open(out_file, "w+", encoding="utf8") as f_out:
        for sent_idx, (comments, sent_primary212) in enumerate(pred_primary):
            for comment in comments:
                if comment.startswith("# generator") or comment.startswith("# udpipe"):
                    continue
                f_out.write(comment + "\n")
            idx_secondary = 0
            skip_secondary = 0
            sent_secondary = pred_secondary[sent_idx][1]
            for idx_primary, entry in enumerate(sent_primary212):
                tok_idx, word, _, upos = entry[:4]
                misc = entry[-1]
                if skip_secondary:
                    skip_secondary -= 1
                    upos = "_"
                else:
                    try:
                        entry_secondary = sent_secondary[idx_secondary]
                        word_secondary = entry_secondary[1]
                        idx_secondary += 1
                        if word_secondary == word:
                            upos_secondary = entry_secondary[3]
                            if upos_secondary != upos:
                                upos = "_"
                        else:
                            upos = "_"
                            if "SpaceAfter=No" in misc and word_secondary.startswith(word):
                                combined_word = word
                                extra_indices = 0
                                while word_secondary.startswith(combined_word):
                                    extra_indices += 1
                                    combined_word += sent_primary212[idx_primary + extra_indices][1]
                                skip_secondary += extra_indices - 1
                            elif "SpaceAfter=No" in entry_secondary[-1] and word.startswith(word_secondary):
                                combined_word = word_secondary
                                extra_indices = 0
                                while word.startswith(combined_word):
                                    extra_indices += 1
                                    combined_word += sent_secondary[idx_secondary - 1 + extra_indices][1]
                                idx_secondary += extra_indices - 1
                        diff_primary, diff_secondary = None, None
                        if tok_idx != entry_secondary[0]:
                            if "-" in tok_idx:
                                start_primary, stop_primary = tok_idx.split("-")
                                diff_primary = int(stop_primary) - int(start_primary)
                            if "-" in entry_secondary[0]:
                                start_secondary, stop_secondary = entry_secondary[0].split("-")
                                diff_secondary = int(stop_secondary) - int(start_secondary)
                            if diff_primary:
                                if diff_primary == diff_secondary:
                                    pass
                                    # all good, same MWT prediction
                                else:
                                    skip_secondary = diff_primary
                            if diff_secondary:
                                idx_secondary += diff_secondary
                    except IndexError:
                        upos = "_"
                lemma, xpos, feats, deprel, morph = 5 * ["_"]
                # only tags with 95+ % precision
                if upos not in ("AUX", "CCONJ", "DET", "NOUN", "NUM",
                                "PART", "PRON", "PUNCT"):
                    upos = "_"
                if "-" in tok_idx:
                    head = "_"
                else:
                    # head = "0"
                    head = "_"
                if "SpaceAfter=No" in misc:
                    misc = "SpaceAfter=No"
                else:
                    misc = "_"
                f_out.write("\t".join((tok_idx, word, lemma, upos, xpos, feats,
                                       head, deprel, morph, misc)))
                f_out.write("\n")
            f_out.write("\n")
