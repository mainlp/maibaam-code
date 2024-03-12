from stanza import Pipeline
from stanza.utils.conll import CoNLL

# lang = "en"  # very bad results
lang = "de"
for treebank in ("gsd", "hdt"):
    doc = CoNLL.conll2doc("../data/bar_maibaam-ud-test.conllu")
    tagger = Pipeline(
        lang=lang, processors={"tokenize": treebank, "pos": treebank},
        tokenize_pretokenized=True, package=None)
    tagger(doc)
    parser = Pipeline(
        lang=lang, processors={"depparse": treebank},
        depparse_pretagged=True, package=None)
    parser(doc)
    CoNLL.write_doc2conll(doc, "predictions/stanza_" + treebank + ".conllu")
