from tools.eval import *
from sklearn.metrics import cohen_kappa_score, ConfusionMatrixDisplay, classification_report
import matplotlib.pyplot as plt
import argparse


###
# The following, until the next ###, is from 
# https://github.com/UniversalDependencies/tools/blob/master/eval.py
# (license: GPL-2.0 https://github.com/UniversalDependencies/tools/blob/master/LICENSE.txt)
# with changes indicated with '# VB'

# Evaluate the gold and system treebanks (loaded using load_conllu).
# VB: keyword args
def evaluate(gold_ud, system_ud,
             cohens_kappa=False, confusion_matrix=False, upos_only=False,
             eval_tsv=False):
    class Score:
        def __init__(self, gold_total, system_total, correct, aligned_total=None):
            self.correct = correct
            self.gold_total = gold_total
            self.system_total = system_total
            self.aligned_total = aligned_total
            self.precision = correct / system_total if system_total else 0.0
            self.recall = correct / gold_total if gold_total else 0.0
            self.f1 = 2 * correct / (system_total + gold_total) if system_total + gold_total else 0.0
            self.aligned_accuracy = correct / aligned_total if aligned_total else aligned_total
    class AlignmentWord:
        def __init__(self, gold_word, system_word):
            self.gold_word = gold_word
            self.system_word = system_word
    class Alignment:
        def __init__(self, gold_words, system_words):
            self.gold_words = gold_words
            self.system_words = system_words
            self.matched_words = []
            self.matched_words_map = {}
        def append_aligned_words(self, gold_word, system_word):
            self.matched_words.append(AlignmentWord(gold_word, system_word))
            self.matched_words_map[system_word] = gold_word

    def spans_score(gold_spans, system_spans):
        correct, gi, si = 0, 0, 0
        while gi < len(gold_spans) and si < len(system_spans):
            if system_spans[si].start < gold_spans[gi].start:
                si += 1
            elif gold_spans[gi].start < system_spans[si].start:
                gi += 1
            else:
                correct += gold_spans[gi].end == system_spans[si].end
                si += 1
                gi += 1

        return Score(len(gold_spans), len(system_spans), correct)

    def alignment_score(alignment, key_fn=None, filter_fn=None):
        if filter_fn is not None:
            gold = sum(1 for gold in alignment.gold_words if filter_fn(gold))
            system = sum(1 for system in alignment.system_words if filter_fn(system))
            aligned = sum(1 for word in alignment.matched_words if filter_fn(word.gold_word))
        else:
            gold = len(alignment.gold_words)
            system = len(alignment.system_words)
            aligned = len(alignment.matched_words)

        if key_fn is None:
            # Return score for whole aligned words
            return Score(gold, system, aligned)

        def gold_aligned_gold(word):
            return word
        def gold_aligned_system(word):
            return alignment.matched_words_map.get(word, 'NotAligned') if word is not None else None
        correct = 0
        for words in alignment.matched_words:
            if filter_fn is None or filter_fn(words.gold_word):
                if key_fn(words.gold_word, gold_aligned_gold) == key_fn(words.system_word, gold_aligned_system):
                    correct += 1

        return Score(gold, system, correct, aligned)

    def enhanced_alignment_score(alignment, EULAS):
        # count all matching enhanced deprels in gold, system GB
        # gold and system = sum of gold and predicted deps
        # parents are pointers to word object, make sure to compare system parent with aligned word in gold in cases where
        # tokenization introduces mismatches in number of words per sentence.
        gold = 0
        for gold_word in alignment.gold_words :
            gold += len(gold_word.columns[DEPS])
        system = 0
        for system_word in alignment.system_words :
            system += len(system_word.columns[DEPS])
        correct = 0
        for words in alignment.matched_words:
            gold_deps = words.gold_word.columns[DEPS]
            system_deps = words.system_word.columns[DEPS]
            for (parent, dep) in gold_deps :
                eulas_dep = [d.split(':')[0] for d in dep]
                for (sparent, sdep) in system_deps:
                    eulas_sdep = [d.split(':')[0] for d in sdep]
                    if dep == sdep or ( eulas_dep == eulas_sdep and EULAS ) :
                        if parent == alignment.matched_words_map.get(sparent, 'NotAligned') :
                            correct += 1
                        elif (parent == 0 and sparent == 0) :  # cases where parent is root
                            correct += 1
        return Score(gold, system, correct)

    def beyond_end(words, i, multiword_span_end):
        if i >= len(words):
            return True
        if words[i].is_multiword:
            return words[i].span.start >= multiword_span_end
        return words[i].span.end > multiword_span_end

    def extend_end(word, multiword_span_end):
        if word.is_multiword and word.span.end > multiword_span_end:
            return word.span.end
        return multiword_span_end

    def find_multiword_span(gold_words, system_words, gi, si):
        # We know gold_words[gi].is_multiword or system_words[si].is_multiword.
        # Find the start of the multiword span (gs, ss), so the multiword span is minimal.
        # Initialize multiword_span_end characters index.
        if gold_words[gi].is_multiword:
            multiword_span_end = gold_words[gi].span.end
            if not system_words[si].is_multiword and system_words[si].span.start < gold_words[gi].span.start:
                si += 1
        else: # if system_words[si].is_multiword
            multiword_span_end = system_words[si].span.end
            if not gold_words[gi].is_multiword and gold_words[gi].span.start < system_words[si].span.start:
                gi += 1
        gs, ss = gi, si

        # Find the end of the multiword span
        # (so both gi and si are pointing to the word following the multiword span end).
        while not beyond_end(gold_words, gi, multiword_span_end) or \
              not beyond_end(system_words, si, multiword_span_end):
            if gi < len(gold_words) and (si >= len(system_words) or
                                         gold_words[gi].span.start <= system_words[si].span.start):
                multiword_span_end = extend_end(gold_words[gi], multiword_span_end)
                gi += 1
            else:
                multiword_span_end = extend_end(system_words[si], multiword_span_end)
                si += 1
        return gs, ss, gi, si

    def compute_lcs(gold_words, system_words, gi, si, gs, ss):
        lcs = [[0] * (si - ss) for i in range(gi - gs)]
        for g in reversed(range(gi - gs)):
            for s in reversed(range(si - ss)):
                if gold_words[gs + g].columns[FORM].lower() == system_words[ss + s].columns[FORM].lower():
                    lcs[g][s] = 1 + (lcs[g+1][s+1] if g+1 < gi-gs and s+1 < si-ss else 0)
                lcs[g][s] = max(lcs[g][s], lcs[g+1][s] if g+1 < gi-gs else 0)
                lcs[g][s] = max(lcs[g][s], lcs[g][s+1] if s+1 < si-ss else 0)
        return lcs

    def align_words(gold_words, system_words):
        alignment = Alignment(gold_words, system_words)

        gi, si = 0, 0
        while gi < len(gold_words) and si < len(system_words):
            if gold_words[gi].is_multiword or system_words[si].is_multiword:
                # A: Multi-word tokens => align via LCS within the whole "multiword span".
                gs, ss, gi, si = find_multiword_span(gold_words, system_words, gi, si)

                if si > ss and gi > gs:
                    lcs = compute_lcs(gold_words, system_words, gi, si, gs, ss)

                    # Store aligned words
                    s, g = 0, 0
                    while g < gi - gs and s < si - ss:
                        if gold_words[gs + g].columns[FORM].lower() == system_words[ss + s].columns[FORM].lower():
                            alignment.append_aligned_words(gold_words[gs+g], system_words[ss+s])
                            g += 1
                            s += 1
                        elif lcs[g][s] == (lcs[g+1][s] if g+1 < gi-gs else 0):
                            g += 1
                        else:
                            s += 1
            else:
                # B: No multi-word token => align according to spans.
                if (gold_words[gi].span.start, gold_words[gi].span.end) == (system_words[si].span.start, system_words[si].span.end):
                    alignment.append_aligned_words(gold_words[gi], system_words[si])
                    gi += 1
                    si += 1
                elif gold_words[gi].span.start <= system_words[si].span.start:
                    gi += 1
                else:
                    si += 1

        return alignment

    # Check that the underlying character sequences match.
    if gold_ud.characters != system_ud.characters:
        # Identify the surrounding tokens and line numbers so the error is easier to debug.
        index = 0
        while index < len(gold_ud.characters) and index < len(system_ud.characters) and \
                gold_ud.characters[index] == system_ud.characters[index]:
            index += 1
        gtindex = 0
        while gtindex < len(gold_ud.tokens) and gold_ud.tokens[gtindex].end-1 < index:
            gtindex += 1
        stindex = 0
        while stindex < len(system_ud.tokens) and system_ud.tokens[stindex].end-1 < index:
            stindex += 1
        gtokenreport = "The error occurs right at the beginning of the two files.\n"
        stokenreport = ""
        if gtindex > 0:
            nprev = 10 if gtindex >= 10 else gtindex
            nnext = 10 if gtindex + 10 <= len(gold_ud.tokens) else len(gold_ud.tokens) - gtindex
            nfirst = gtindex - nprev
            prevtokens = ' '.join([''.join(gold_ud.characters[t.start:t.end]) for t in gold_ud.tokens[nfirst:gtindex]])
            nexttokens = ' '.join([''.join(gold_ud.characters[t.start:t.end]) for t in gold_ud.tokens[gtindex:gtindex + nnext]])
            gtokenreport = "File '{}':\n".format(gold_ud.path)
            gtokenreport += "  Token no. {} on line no. {} is the last one with all characters reproduced in the other file.\n".format(gtindex, gold_ud.tokens[gtindex-1].line)
            gtokenreport += "  The previous {} tokens are '{}'.\n".format(nprev, prevtokens)
            gtokenreport += "  The next {} tokens are '{}'.\n".format(nnext, nexttokens)
        if stindex > 0:
            nprev = 10 if stindex >= 10 else stindex
            nnext = 10 if stindex + 10 <= len(system_ud.tokens) else len(system_ud.tokens) - stindex
            nfirst = stindex - nprev
            prevtokens = ' '.join([''.join(system_ud.characters[t.start:t.end]) for t in system_ud.tokens[nfirst:stindex]])
            nexttokens = ' '.join([''.join(system_ud.characters[t.start:t.end]) for t in system_ud.tokens[stindex:stindex + nnext]])
            stokenreport = "File '{}':\n".format(system_ud.path)
            stokenreport += "  Token no. {} on line no. {} is the last one with all characters reproduced in the other file.\n".format(stindex, system_ud.tokens[stindex-1].line)
            stokenreport += "  The previous {} tokens are '{}'.\n".format(nprev, prevtokens)
            stokenreport += "  The next {} tokens are '{}'.\n".format(nnext, nexttokens)
        raise UDError(
            "The concatenation of tokens in gold file and in system file differ!\n" + gtokenreport + stokenreport +
            "First 20 differing characters in gold file: '{}' and system file: '{}'".format(
                "".join(map(_encode, gold_ud.characters[index:index + 20])),
                "".join(map(_encode, system_ud.characters[index:index + 20]))
            )
        )

    # Align words
    alignment = align_words(gold_ud.words, system_ud.words)

    ##
    # VB: Inter-annotator agreement + confusion matrices
    # Changes until the next ##
    n_matched = len(alignment.matched_words)
    n_gold = len(alignment.gold_words)
    n_system = len(alignment.system_words)
    n_total = n_gold + n_system - n_matched
    print("Aligned words")
    print(str(n_matched) + "/" + str(n_total) + " = " + str(
        n_matched / n_total))
    print()

    if cohens_kappa:
        print("Cohen's kappa (UPOS of aligned words)")
        print(cohen_kappa_score(
            [word.gold_word.columns[UPOS]
             for word in alignment.matched_words],
            [word.system_word.columns[UPOS]
             for word in alignment.matched_words],
        ))

        if not upos_only:
            print()
            print("Cohen's kappa (deprels of aligned words)")
            print(cohen_kappa_score(
                [word.gold_word.columns[DEPREL]
                 for word in alignment.matched_words],
                [word.system_word.columns[DEPREL]
                 for word in alignment.matched_words],
            ))

    if confusion_matrix or eval_tsv:
        upos_gold = [word.gold_word.columns[UPOS]
                     for word in alignment.matched_words]
        upos_pred = [word.system_word.columns[UPOS]
                     for word in alignment.matched_words]
        upos_labels = sorted(list(set(upos_gold + upos_pred)))
        print("UPOS of aligned words")
        print(classification_report(upos_gold, upos_pred, labels=upos_labels))
        if confusion_matrix:
            ConfusionMatrixDisplay.from_predictions(
                upos_gold, upos_pred, labels=upos_labels,
                xticks_rotation="vertical")
        if eval_tsv:
            upos2scores = classification_report(upos_gold, upos_pred,
                                                labels=upos_labels,
                                                output_dict=True)
            legend = ["test_size", "tokens_f1", "upos_acc", "upos_f1"]
            values = [upos2scores["macro avg"]["support"],
                      spans_score(gold_ud.tokens, system_ud.tokens).f1,
                      upos2scores["accuracy"],
                      upos2scores["macro avg"]["f1-score"]]
        if confusion_matrix:
            plt.show()

        if not upos_only:
            deprel_gold = [word.gold_word.columns[DEPREL]
                           for word in alignment.matched_words]
            deprel_pred = [word.system_word.columns[DEPREL]
                           for word in alignment.matched_words]
            deprel_labels = sorted(list(set(deprel_gold + deprel_pred)))
            print("DEPREL of aligned words")
            deprel2scores = classification_report(deprel_gold, deprel_pred,
                                                  labels=deprel_labels)
            print(deprel2scores)
            if confusion_matrix:
                ConfusionMatrixDisplay.from_predictions(
                    deprel_gold, deprel_pred, labels=deprel_labels,
                    xticks_rotation="vertical")
                plt.show()
            if eval_tsv:
                deprel2scores = classification_report(deprel_gold, deprel_pred,
                                                      labels=deprel_labels,
                                                      output_dict=True)
                legend += ["UAS", "LAS", "deprel_acc", "deprel_f1"]
                uas = alignment_score(alignment, lambda w, ga: ga(w.parent))\
                    .aligned_accuracy
                las = alignment_score(
                    alignment,
                    lambda w, ga: (ga(w.parent), w.columns[DEPREL]))\
                    .aligned_accuracy
                values += [uas, las, deprel2scores["accuracy"],
                           deprel2scores["macro avg"]["f1-score"]]
        elif eval_tsv:
            legend += ["UAS", "LAS", "deprel_acc", "deprel_f1"]
            values += ["--", "--", "--", "--"]

        if eval_tsv:
            upos_labels = ["ADJ", "ADP", "ADV", "AUX", "CCONJ",
                           "DET", "INTJ", "NOUN", "NUM", "PART",
                           "PRON", "PROPN", "PUNCT", "SCONJ", "SYM",
                           "VERB", "X"]
            for upos in upos_labels:
                legend += [upos + "_prec", upos + "_rec"]
                try:
                    values += [upos2scores[upos]["precision"],
                               upos2scores[upos]["recall"]]
                    # print(upos, upos2scores[upos])
                except KeyError:
                    values += ["--", "--"]
            if not upos_only:
                deprel_labels = [
                    "nsubj", "nsubj:pass", "obj", "iobj", "obl", "obl:arg",
                    "obl:agent", "expl", "expl:pv", "vocative", "csubj",
                    "csubj:pass", "ccomp", "xcomp", "advcl", "advcl:relcl",
                    "aux", "aux:pass", "cop", "mark", "compound:prt",
                    "dislocated", "discourse", "nmod", "nmod:poss", "appos",
                    "acl", "acl:relcl", "det", "det:poss", "case", "amod",
                    "nummod", "flat", "conj", "cc", "punct", "advmod", "root",
                    "fixed", "parataxis", "compound", "goeswith", "orphan",
                    "reparandum", "list", "dep"]
                for deprel in deprel_labels:
                    legend += [deprel + "_prec", deprel + "_rec"]
                    try:
                        values += [deprel2scores[deprel]["precision"],
                                   deprel2scores[deprel]["recall"]]
                        # print(deprel, deprel2scores[deprel])
                    except KeyError:
                        values += ["--", "--"]
            with open(eval_tsv, "w+", encoding="utf8") as f_out:
                f_out.write("\t".join(legend) + "\n")
                f_out.write("\t".join((str(v) for v in values)) + "\n")

    ##

    # Compute the F1-scores
    return {
        "Tokens": spans_score(gold_ud.tokens, system_ud.tokens),
        "Sentences": spans_score(gold_ud.sentences, system_ud.sentences),
        "Words": alignment_score(alignment),
        "UPOS": alignment_score(alignment, lambda w, _: w.columns[UPOS]),
        "XPOS": alignment_score(alignment, lambda w, _: w.columns[XPOS]),
        "UFeats": alignment_score(alignment, lambda w, _: w.columns[FEATS]),
        "AllTags": alignment_score(alignment, lambda w, _: (w.columns[UPOS], w.columns[XPOS], w.columns[FEATS])),
        "Lemmas": alignment_score(alignment, lambda w, ga: w.columns[LEMMA] if ga(w).columns[LEMMA] != "_" else "_"),
        "UAS": alignment_score(alignment, lambda w, ga: ga(w.parent)),
        "LAS": alignment_score(alignment, lambda w, ga: (ga(w.parent), w.columns[DEPREL])),
        "ELAS": enhanced_alignment_score(alignment, 0),
        "EULAS": enhanced_alignment_score(alignment, 1),
        "CLAS": alignment_score(alignment, lambda w, ga: (ga(w.parent), w.columns[DEPREL]),
                                filter_fn=lambda w: w.is_content_deprel),
        "MLAS": alignment_score(alignment, lambda w, ga: (ga(w.parent), w.columns[DEPREL], w.columns[UPOS], w.columns[FEATS],
                                                         [(ga(c), c.columns[DEPREL], c.columns[UPOS], c.columns[FEATS])
                                                          for c in w.functional_children]),
                                filter_fn=lambda w: w.is_content_deprel),
        "BLEX": alignment_score(alignment, lambda w, ga: (ga(w.parent), w.columns[DEPREL],
                                                          w.columns[LEMMA] if ga(w).columns[LEMMA] != "_" else "_"),
                                filter_fn=lambda w: w.is_content_deprel),
    }

### tools/validate.py excerpt over


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('gold_file', type=str,
                        help='CoNLL-U file with gold data '
                             '(or the first annotator\' file')
    parser.add_argument('pred_file', type=str,
                        help='CoNLL-U file with predictions '
                             '(or the second annotator\'s labels')
    parser.add_argument('--kappa', '-k', default=False, action='store_true',
                        help='Cohen\'s kappa')
    parser.add_argument('--matrix', '-cm', default=False, action='store_true',
                        help='Confusion matrix')
    parser.add_argument('--upos-only', '-p', default=False,
                        action='store_true', help='Ignore dependencies')
    parser.add_argument('--tab', '-t', default=False, action='store_true',
                        help='Format for comparison table')
    args = parser.parse_args()
    print(args)

    treebank_type = {'multiple_roots_okay': args.upos_only}

    ud_1 = load_conllu_file(args.gold_file, treebank_type)
    ud_2 = load_conllu_file(args.pred_file, treebank_type)
    if args.tab:
        eval_tsv = args.pred_file + ".eval.tsv"
    else:
        eval_tsv = None
    eval_ = evaluate(ud_1, ud_2, cohens_kappa=args.kappa,
                     confusion_matrix=args.matrix,
                     upos_only=args.upos_only, eval_tsv=eval_tsv)
    results = build_evaluation_table(eval_, True, False, False)
    print(results)
