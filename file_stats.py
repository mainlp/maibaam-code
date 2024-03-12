import sys
from collections import Counter


if len(sys.argv) != 2:
    print("USAGE: python3 file_stats.py FILE")
    sys.exit(1)


if not sys.argv[1].endswith(".conllu"):
    print("Expected CONLLU file")
    sys.exit(1)

n_sents = 0
n_toks = 0
upos2forms = {}
upos2deprels = {}
deprels = []

cur_dialect = None
cur_location = None
cur_genre = None
cur_sent = None

dialect2upos, location2upos, genre2upos, source2upos = {}, {}, {}, {}
dialect2sentno, location2sentno, genre2sentno, source2sentno = {}, {}, {}, {}
dialect2genres, location2genres = {}, {}
genre2dialect = {}
with open(sys.argv[1], encoding="utf8") as in_file:
    for line in in_file:
        line = line.strip()
        if not line:
            if not cur_dialect:
                print("! Sentence w/o dialect info: " + str(cur_sent))
            if not cur_location:
                print("! Sentence w/o location info: " + str(cur_sent))
            if not cur_genre:
                print("! Sentence w/o genre info: " + str(cur_sent))
            cur_dialect = None
            cur_location = None
            cur_genre = None
            cur_sent = None
            cur_source = None
            continue
        if line[0] == "#":
            if line.startswith("# sent_id = "):
                cur_sent = line[12:]
                cur_source, _ = cur_sent.rsplit("_", 1)
                try:
                    source2sentno[cur_source] += 1
                except KeyError:
                    source2sentno[cur_source] = 1
            elif line.startswith("# dialect_group = "):
                cur_dialect = line[18:]
                try:
                    dialect2sentno[cur_dialect] += 1
                except KeyError:
                    dialect2sentno[cur_dialect] = 1
            elif line.startswith("# location = "):
                cur_location = line[13:]
                try:
                    location2sentno[cur_location] += 1
                except KeyError:
                    location2sentno[cur_location] = 1
            elif line.startswith("# genre = "):
                cur_genre = line[10:]
                try:
                    genre2sentno[cur_genre] += 1
                except KeyError:
                    genre2sentno[cur_genre] = 1
            continue
        cells = line.split("\t")
        if "-" in cells[0]:
            continue
        if cells[0] == "1":
            n_sents += 1
        n_toks += 1
        form = cells[1]
        upos = cells[3]
        deprel = cells[7]
        deprels.append(deprel)
        try:
            upos2forms[upos].append(form)
            upos2deprels[upos].append(deprel)
        except KeyError:
            upos2forms[upos] = [form]
            upos2deprels[upos] = [deprel]
        try:
            source2upos[cur_source].append(upos)
        except KeyError:
            source2upos[cur_source] = [upos]
        try:
            dialect2upos[cur_dialect].append(upos)
            dialect2genres[cur_dialect].add(cur_genre)
        except KeyError:
            dialect2upos[cur_dialect] = [upos]
            dialect2genres[cur_dialect] = {cur_genre}
        try:
            location2upos[cur_location].append(upos)
            location2genres[cur_location].add(cur_genre)
        except KeyError:
            location2upos[cur_location] = [upos]
            location2genres[cur_location] = {cur_genre}
        try:
            genre2upos[cur_genre].append(upos)
            genre2dialect[cur_genre].add(cur_dialect)
        except KeyError:
            genre2upos[cur_genre] = [upos]
            genre2dialect[cur_genre] = {cur_dialect}

# with open(sys.argv[1][:-6] + ".log", "w+", encoding="utf8") as out_file:
print("File: " + sys.argv[1])
print("Sentences: " + str(n_sents))
print("Tokens: " + str(n_toks))

print("\n\nDIALECT GROUP\tN_TOKENS\tN_SENTENCES\tGENRES")
total_sents, total_toks = 0, 0
# for dialect in dialect2upos:
for dialect in ("north", "northcentral", "central", "southcentral", "south",
                "unk (central/southcentral)",
                "unk (central/southcentral/south)",
                "unk (southcentral/south)", "unk"):
    n_sents = dialect2sentno[dialect]
    n_toks = len(dialect2upos[dialect])
    total_sents += n_sents
    total_toks += n_toks
    print(f"{dialect}\t{n_toks}\t{n_sents}\t{', '.join(dialect2genres[dialect])}")
print(f"TOTAL\t{total_toks}\t{total_sents}")

print("\nLOCATION\tN_TOKENS\tN_SENTENCES\tGENRES")
total_sents, total_toks = 0, 0
# for location in location2upos:
for location in ("Western North Bavarian area",
                 "Bavarian Forest",
                 "Munich", "Salzburg (city)", "Upper Austria", "Vienna",
                 "Berchtesgaden", "Bad Reichenhall", "Pongau", "Pinzgau",
                 "Carinthia", "South Tyrol",
                 "Upper Bavaria", "Austria",
                 "South East Upper Bavaria", "East Austria",
                 "Styria",
                 "unk"):
    n_sents = location2sentno[location]
    n_toks = len(location2upos[location])
    total_sents += n_sents
    total_toks += n_toks
    print(f"{location}\t{n_toks}\t{n_sents}\t{', '.join(location2genres[location])}")
print(f"TOTAL\t{total_toks}\t{total_sents}")

print("\nGENRE\tN_TOKENS\tN_SENTENCES\tDIALECTS")
total_sents, total_toks = 0, 0
# for genre in genre2upos:
for genre in ("wiki", "grammar-examples", "non-fiction", "social", "fiction"):
    n_sents = genre2sentno[genre]
    n_toks = len(genre2upos[genre])
    total_sents += n_sents
    total_toks += n_toks
    print(f"{genre}\t{n_toks}\t{n_sents}\t{', '.join(genre2dialect[genre])}")
print(f"TOTAL\t{total_toks}\t{total_sents}\n\n")

for source in sorted(source2sentno):
    print(f"{source}\t{len(source2upos[source])}\t{source2sentno[source]}")

print("\n")
for upos in upos2forms:
    c = Counter(upos2forms[upos])
    c2 = Counter(upos2deprels[upos])
    print(f"{upos}\t{len(upos2forms[upos])}\t{len(c)}\t{c.most_common(10)}\t{c2.most_common()}")

print("\n")
for c in Counter(deprels).most_common():
    print(f"{c[0]}\t{c[1]}")

print("\n")
for upos in ("ADP", "AUX", "CCONJ", "DET", "NUM", "PART", "PRON", "SCONJ"):
    types = Counter(upos2forms[upos]).most_common()
    print(f"{upos}\t{len(types)}\t{types}")