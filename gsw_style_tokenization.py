import sys


def read_conllu(filename):
    sentences = []
    with open(filename, encoding="utf8") as f_in:
        comments = []
        tokens = []
        for line in f_in:
            line = line.strip()
            if not line:
                if tokens:
                    sentences.append((comments, tokens))
                comments = []
                tokens = []
                continue
            if line.startswith("#"):
                comments.append(line)
                continue
            tokens.append(line.split("\t"))
        if tokens:
            sentences.append((comments, tokens))
    return sentences


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 gsw_style_tokenization.py IN_FILE OUT_FILE")
        sys.exit(1)

    _, in_file, out_file = sys.argv
    sentences = read_conllu(in_file)
    with open(out_file, "w+", encoding="utf8") as f_out:
        for (comments, tokens) in sentences:
            for comment in comments:
                f_out.write(comment + "\n")

            # Find multi-word tokens that should be merged and keep track
            # of resulting ID changes
            id_map = {}
            deprel_map = {}
            cur_id_offset = 0
            i = 0
            while i < len(tokens):
                if not tokens[i]:
                    i += 1
                    continue
                id_ = tokens[i][0]
                i1, i2 = None, None
                if "-" in id_:
                    # Multi-word tokens
                    start, end = id_.split("-")
                    start = int(start)
                    end = int(end)
                    if end - start > 1:
                        print("!!!!!! TODO long MWT")
                        print(id_)
                        print(tokens)
                        sys.exit(1)
                    tokens[i] = None
                    i1 = i + 1
                    i2 = i + 2
                elif "SpaceAfter=No" in tokens[i][9] and\
                        "CorrectSpaceAfter=Yes" not in tokens[i][9] and\
                        tokens[i][3] != "PUNCT" and\
                        tokens[i + 1][3] != "PUNCT" and\
                        tokens[i + 1][1] != "–":
                    # Determiner-noun combinations etc.
                    i1 = i
                    i2 = i + 1
                if i1 and i2:
                    id1, form1, _, upos1, _, _, head1, deprel1, _, _ = tokens[i1]
                    id2, form2, _, upos2, _, _, head2, deprel2, _, misc2 = tokens[i2]
                    if (id2 == head1):
                        # id_map[id1] = int(id2) - cur_id_offset
                        deprel_map[id1] = (head1, deprel1)
                        if cur_id_offset > 0:
                            id_map[id2] = int(id2) - cur_id_offset
                        tokens[i1] = None
                        tokens[i2][1] = form1 + form2
                        # tokens[i2][3] = upos1  # per NOAH paper / UD-GSW-UZH
                        if misc2 == "_":
                            tokens[i2][9] = f"Orig={form1}_{upos1}+{form2}_{upos2}"
                        else:
                            tokens[i2][9] += f"|Orig={form1}_{upos1}+{form2}_{upos2}"
                    else:
                        # id_map[id2] = int(id1) - cur_id_offset
                        deprel_map[id2] = (head2, deprel2)
                        if cur_id_offset > 0:
                            id_map[id1] = int(id1) - cur_id_offset
                        tokens[i2] = None
                        tokens[i1][1] = form1 + form2
                        tokens[i1][9] = f"Orig={form1}_{upos1}+{form2}_{upos2}"
                        if "SpaceAfter=No" in misc2:
                            tokens[i1][9] += "|SpaceAfter=No"
                            if tokens[i2 + 1][3] != "PUNCT":
                                id_map[i2 + 1] = int(id1) - cur_id_offset
                                tokens[i1][1] = form1 + form2 + tokens[i2 + 1][1]
                                tokens[i1][9] = f"Orig={form1}_{upos1}+{form2}_{upos2}+{tokens[i2 + 1][1]}_{tokens[i2 + 1][3]}"
                                tokens[i2 + 1] = None
                                i += 1
                                cur_id_offset += 1
                                if "SpaceAfter=No" in tokens[i1][9]:
                                    print("!!!! Quadruple tokens currently unaccounted for")
                                    print(id_)
                                    print(tokens)
                    cur_id_offset += 1
                    i += i2 - i
                else:
                    if cur_id_offset > 0:
                        id_map[id_] = int(id_) - cur_id_offset
                    i += 1

            # Apply ID changes and write output
            for token in tokens:
                if not token:
                    continue
                id_, form, _, upos, _, _, head, deprel, _, misc = token
                if head in deprel_map:
                    head, deprel = deprel_map[head]
                id_ = id_map.get(id_, id_)
                head = id_map.get(head, head)
                f_out.write(f"{id_}\t{form}\t_\t{upos}\t_\t_\t{head}\t{deprel}\t_\t{misc}\n")

            f_out.write("\n")
