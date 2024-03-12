from sklearn.metrics import f1_score, accuracy_score, precision_recall_fscore_support
import sys

# Assumes that all sentences are in the same order
# and that the tokenization is the same.


def get_labels(file):
    pos_tags = []
    heads = []
    labelled_heads = []
    pos_tags_sent = []
    heads_sent = []
    labelled_heads_sent = []
    sent_idx = 0
    dialect = None
    genre = None
    dialect2sent = {}
    genre2sent = {}
    with open(file, encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                pos_tags.append(pos_tags_sent)
                heads.append(heads_sent)
                labelled_heads.append(labelled_heads_sent)
                try:
                    dialect2sent[dialect].append(sent_idx)
                except KeyError:
                    dialect2sent[dialect] = [sent_idx]
                try:
                    genre2sent[genre].append(sent_idx)
                except KeyError:
                    genre2sent[genre] = [sent_idx]
                pos_tags_sent = []
                heads_sent = []
                labelled_heads_sent = []
                sent_idx += 1
                dialect = None
                genre = None
                continue
            if line[0] == "#":
                if line.startswith("# genre"):
                    genre = line[10:]
                elif line.startswith("# dialect"):
                    dialect = line[18:]
                    if dialect.startswith("unk"):
                        dialect = "unk"
                continue
            idx, _, _, pos, _, _, head, deprel, _, _ = line.split("\t")
            if "-" in idx:
                continue
            pos_tags_sent.append(pos)
            heads_sent.append(head)
            # ignore subclasses, like the official eval script does
            deprel = deprel.split(":")[0]
            labelled_heads_sent.append(head + deprel)
    return pos_tags, heads, labelled_heads, dialect2sent, genre2sent


def scores(pos_gold, heads_gold, labelled_heads_gold,
           pos_pred, heads_pred, labelled_heads_pred, upos_labels):
    pos_acc = accuracy_score(pos_gold, pos_pred)
    pos_f1 = f1_score(pos_gold, pos_pred, average="macro")
    uas = accuracy_score(heads_gold, heads_pred)
    las = accuracy_score(labelled_heads_gold, labelled_heads_pred)
    prec, rec, _, _ = precision_recall_fscore_support(
        pos_gold, pos_pred, labels=upos_labels, zero_division=0)
    return las, uas, pos_acc, pos_f1, prec, rec


def flatten(list_, indices=None):
    if not indices:
        return [item for sublist in list_ for item in sublist]
    indexed_list = [list_[i] for i in indices]
    return [item for sublist in indexed_list for item in sublist]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE: python3 tokenwise_eval.py PRED_FILE")

    gold_file = "data/bar_maibaam-ud-test.conllu"
    # gold_file = "../UD_German-GSD/de_gsd-ud-test.conllu"
    pred_file = sys.argv[1]
    out_file = pred_file + ".eval.tsv"

    pos_gold, heads_gold, labelled_heads_gold, dialect2sent, genre2sent =\
        get_labels(gold_file)
    pos_pred, heads_pred, labelled_heads_pred, _, _ = get_labels(pred_file)
    upos_labels = ["ADJ", "ADP", "ADV", "AUX", "CCONJ",
                   "DET", "INTJ", "NOUN", "NUM", "PART",
                   "PRON", "PROPN", "PUNCT", "SCONJ", "SYM",
                   "VERB", "X"]
    dialects = ("north", "northcentral", "central", "southcentral", "south",
                "unk")
    genres = ("wiki", "grammar-examples", "fiction", "non-fiction", "social")
    dialect_scores = {}
    for dialect in dialects:
        idx = dialect2sent.get(dialect, "")
        las, uas, pos_acc, pos_f1, _, _ = scores(
            flatten(pos_gold, idx), flatten(heads_gold, idx),
            flatten(labelled_heads_gold, idx),
            flatten(pos_pred, idx), flatten(heads_pred, idx),
            flatten(labelled_heads_pred, idx),
            upos_labels)
        dialect_scores[dialect] = (pos_acc, pos_f1, uas, las)
    genre_scores = {}
    for genre in genres:
        idx = genre2sent.get(genre, "")
        las, uas, pos_acc, pos_f1, _, _ = scores(
            flatten(pos_gold, idx), flatten(heads_gold, idx),
            flatten(labelled_heads_gold, idx),
            flatten(pos_pred, idx), flatten(heads_pred, idx),
            flatten(labelled_heads_pred, idx),
            upos_labels)
        genre_scores[genre] = (pos_acc, pos_f1, uas, las)
    las, uas, pos_acc, pos_f1, prec, rec = scores(
        flatten(pos_gold), flatten(heads_gold), flatten(labelled_heads_gold),
        flatten(pos_pred), flatten(heads_pred), flatten(labelled_heads_pred),
        upos_labels)
    with open(out_file, "w+", encoding="utf8") as f:
        f.write("\t".join(("UPOS_acc", "UPOS_f1", "UAS", "LAS")))
        f.write("\t")
        for dialect in dialects:
            f.write("\t".join((dialect + "_UPOS_acc",
                               dialect + "_UPOS_f1",
                               dialect + "_UAS", dialect + "_LAS")))
            f.write("\t")
        for genre in genres:
            f.write("\t".join((genre + "_UPOS_acc",
                               genre + "_UPOS_f1",
                               genre + "_UAS", genre + "_LAS")))
            f.write("\t")
        f.write("\t".join(pos + "_prec\t" + pos + "_rec"
                          for pos in upos_labels))
        f.write("\n")
        f.write("\t".join(str(x) for x in (pos_acc, pos_f1, uas, las)))
        for dialect in dialects:
            f.write("\t")
            f.write("\t".join((str(i) for i in dialect_scores[dialect])))
        for genre in genres:
            f.write("\t")
            f.write("\t".join((str(i) for i in genre_scores[genre])))
        for p, r in zip(prec, rec):
            f.write(f"\t{p}\t{r}")
        f.write("\n")
