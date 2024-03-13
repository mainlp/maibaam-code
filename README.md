# MaiBaam code

This repository contains code used for annotating [UD Bavarian MaiBaam](https://github.com/UniversalDependencies/UD_Bavarian-MaiBaam) and for evaluating parsers on this dataset.

Clone with submodules:
```
git clone git@github.com:mainlp/bar-ud-annotation.git --recursive
```

## Annotations

Set up conllueditor:
```
cd conllueditor
mvn install
bin/installJQ.sh
cd ..
```

Check if it worked:
```
./launch.sh data/demo.conllu
```
and open http://localhost:8888/

If Mac has issues with `greadlines` in the conlluedit.sh script:
```
brew install coreutils
```

If you can't execute launch.sh:
```
chmod +x launch.sh
```

### Preprocessing

For each source, create a new txt file: `sourcename_Page-Title.txt` in the `preprocessing` folder, where `sourcename` is one of the following for any Wikipedia-based files:
- `wiki` -- normal article
- `wikisample` -- sentences explicitly marked as linguistic example sentences from a page like [this one](https://bar.wikipedia.org/wiki/Konjunktiv)
- `wikisource` -- prose or poetry from [here](https://bar.wikipedia.org/wiki/Text:Start)
- `wikitalk` -- talk page

Copy (part of) the article to your txt file and manually add linebreaks so that each sentence is on its own line.
Then convert it to the conllu format:
```
python3 preprocessing/to_conllu.py preprocessing/FILENAME.txt GENRE DIALECT_GROUP LOCATION

# or
cd preprocessing
python3 to_conllu.pu FILENAME.txt GENRE DIALECT_GROUP LOCATION
```

The `GENRE` can be either `wiki`, `grammar-examples`, `fiction`, `non-fiction` or `social`:
- `wiki`: articles from Bavarian Wikipedia
- `grammar-examples`: sentences from grammar books, grammar articles from Wikipedia, example sentences from tatoeba etc.
- `fiction`: stories 
- `non-fiction`: slot/intent data
- `social`: Wikipedia discussion pages

For the `DIALECT_GROUP`, you have the following options:
- `north` 
- `northcentral` 
- `central` 
- `southcentral` 
- `south`
- `UCS`: unk (central/southcentral)
- `UCSS`: unk (central/southcentral/south) 
- `USS`: unk (southcentral/south)
- `unk`

The options for the location tag are:
- `A`: Austria
- `B`: Berchtesgarden
- `BF`: Bavarian Forest
- `C`: Carinthia
- `EA`: East Austria
- `M`: Munich
- `P`: Pongau
- `SC`: Salzburg (city)
- `SEUB`: South East Upper Bavaria
- `SoT`: South Tyrol
- `ST`: Styria
- `UA`: Upper Austria
- `UB`: Upper Bavaria
- `V`: Vienna
- `WNBA`: Western North Bavarian area 
- `unk`

For example, [this article](https://bar.wikipedia.org/wiki/Haberertanz) would get the genre tag `wiki`, the dialect_group tag `unk (central/southcentral/south)`and the location tag `Upper Bavaria`, so the command looks like this:
```
python3 preprocessing/to_conllu.py preprocessing/files/wiki_Haberertanz.txt wiki UCSS UB
```

Running the script automatically creates a CoNLLU file in the `data` folder.

### Pre-annotations

We use two zero-shot transfer models (DEU->BAR) specialized for UD annotations. Both of them do relatively well when evaluating them on our already annotated data, but they produce slightly different predictions.
We pre-annotate new files by taking the predicted POS tags that 1. both models agree on, and 2. are for classes that were predicted with >=95% precision on our already annotated data.

To generate the predictions, go to https://lindat.mff.cuni.cz/services/udpipe/ and use the following settings:
- Model: UD 2.12; once with the german-gsd-2.12-... model and once with the german-hdt-2.12-... one
- Actions: Tag and lemmatize, parse
- Advanced options -- UDPipe version: UDPipe 2
- Advanced options -- Input: CoNLL-U
- Input file: the ConLL-U file created via to_conllu.py (see above)

Click "process input", wait for it to finish running, then "save output file" and add it to the `preprocessing` folder .
Run `python3 preprocessing/combine_agreeing_preds.py UDPIPE_GSD UDPIPE_HDT OUT_FILE` to generate the pre-annotated file.

### Annotations

All CoNLLU files should reside in the `data` folder.
Use `git add NEW_FILENAME` or `git add .` to index a new file.
Then launch the editor:

```
./launch.sh data/FILENAME.conllu
```
and open http://localhost:8888/

Before committing your annotations, run:
```
./precommit.sh
```
and check the validator's output.
If it complains about sentences that haven't been annotated yet, that's fine, but once the full file has been annotated, all tests should pass.

### Validation and stats

To validate an individual file's annotations, run:
```
python3 tools/validate.py FILE --lang de
``` 

To get the number of sentences and tokens in a file, as well as stats about the word forms and deprels associated with each UPOS tag, run:
```
python3 file_stats.py FILE
```

More validation/stats scripts:
```
cat FILE_PATTERN | perl tools/mwtoken-stats.pl 
cat FILE_PATTERN | perl tools/conllu-stats.pl > tmp-stats.xml
perl -I tools tools/evaluate_treebank.pl data/gold

# should be without output:
cat FILE_PATTERN | perl tools/check_sentence_ids.pl
cat FILE_PATTERN | perl tools/find_duplicate_sentences.pl 
```

## Predictions

Files with predicted labels are in `predict/predictions`.

### Training models with and without noise

See the README in `predict`.

### UDPipe

https://lindat.mff.cuni.cz/services/udpipe/
- UD 2.12 HDT and GSD

### Stanza

```
cd predict
python3 stanza_pred.py
```

## Evaluation

To get a tab-separated overview of class-wise precision and recall scores, including tokenization scores:
```
python3 eval_extra.py GOLD_FILE PRED_FILE --matrix --tab
# e.g.
python3 eval_extra.py data/bar_maibaam-ud-test.conllu predict/predictions/udpipe_gsd_textonly.conllu --tab
```

General eval (UAS, LAS, tag F1, tag accuracy) and eval per genre and dialect group
```
python3 tokenwise_eval.py PRED_FILE
```

## Surface tokenization

To convert the treebank to a surface-based tokenization scheme as currently used by the [Swiss German treebank](https://universaldependencies.org/gsw/) (rather than the classic UD tokenization), use the following command:
```
python3 gsw_style_tokenization.py data/bar_maibaam-ud-test.conllu data/bar_maibaam-ud-testgsw-style.conllu
```
This reverts the token splits, assigns tags to the unsplit tokens (e.g., DET+NOUN becomes NOUN and VERB+PRON becomes VERB) and adjusts the dependencies accordingly.
