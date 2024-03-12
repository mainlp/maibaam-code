from transformers import AutoTokenizer

file2score = {}
infiles = ["../data/bar_maibaam-ud-test_subset10perc.conllu",
           "../data/bar_maibaam-ud-test.conllu",
           "UD_German-GSD/de_gsd-ud-train.conllu"
           ]
for noise in range(10, 110, 10):
    for seed in (1234, 3456, 5678):
        infiles.append(
            f"UD_German-GSD/de_gsd-ud-train_noise{noise}-{seed}.conllu")

for modelname, tokenizername in (
        ("mbert", "bert-base-multilingual-cased"),
        ("gbert", "deepset/gbert-base"),
        ("xlmr", "xlm-roberta-base")):
    print(modelname, tokenizername)

    tokenizer = AutoTokenizer.from_pretrained(tokenizername)

    for file in infiles:
        n_words, n_split_words = 0, 0
        with open(file, encoding="utf8") as f_in:
            for line in f_in:
                if line == "\n" or line[0] == "#":
                    continue
                cells = line.split("\t")
                if "-" in cells[0]:
                    continue  # multi-word token
                word = cells[1]
                n_words += 1
                try:
                    tokenizer.tokenize(word)[1]
                    n_split_words += 1
                except IndexError:
                    pass
        file2score[file] = (n_words, n_split_words, n_split_words / n_words)
        print(file, n_split_words / n_words)

    with open("split_tokens_" + modelname + ".tsv", "w+") as f_out:
        for file in file2score:
            f_out.write(file + "\t" + "\t".join(
                [str(x) for x in file2score[file]]) + "\n")
