from tokenize import *
import sys


"""
dialects
"north", 
"northcentral", 
"central", 
"southcentral", 
"south",
"unk (central/southcentral)", UCS
"unk (central/southcentral/south)", UCSS
"unk (southcentral/south)", USS
"unk"

location
"Austria",  A
"Berchtesgaden",    B
"Carinthia",    C
"Munich",   M
"Pongau",   P
"Salzburg (city)", SC
"Styria",   ST
"Vienna",   V
"Bavarian Forest",  BF
"East Austria",     EA
"South Tyrol",      SoT
"Upper Austria",    UA
"Upper Bavaria",    UB
"South East Upper Bavaria",     SEUB
"Western North Bavarian area",  WNBA
"unk"

genre
"wiki", "grammar-examples", "fiction", "non-fiction", "social"
"""

if len(sys.argv) != 5:
    print("USAGE: python3 to_conllu.py TXT_FILE GENRE DIALECT LOCATION")
    print("Example: python3 to_conllu.py wiki_Lamma.txt wiki central SC")
    sys.exit(1)

in_file = sys.argv[1]
if not in_file.endswith(".txt"):
    print("Expected .txt file. Quitting.")
    sys.exit(1)

genre = sys.argv[2]
dialect_ab = sys.argv[3]
location_ab = sys.argv[4]

if dialect_ab == "UCS":
    dialect = "unk (central/southcentral)"
elif dialect_ab == "UCSS":
    dialect = "unk (central/southcentral/south)"
elif dialect_ab == "USS":
    dialect = "unk (southcentral/south)"
else:
    dialect = dialect_ab

if location_ab == "A":
    location = "Austria"
elif location_ab == "B":
    location = "Berchtesgaden"
elif location_ab == "C":
    location = "Carinthia"
elif location_ab == "M":
    location = "Munich"
elif location_ab == "P":
    location = "Pongau"
elif location_ab == "SC":
    location = "Salzburg (city)"
elif location_ab == "ST":
    location = "Styria"
elif location_ab == "V":
    location = "Vienna"
elif location_ab == "BF":
    location = "Bavarian Forest"
elif location_ab == "EA":
    location = "East Austria"
elif location_ab == "SoT":
    location = "South Tyrol"
elif location_ab == "UA":
    location = "Upper Austria"
elif location_ab == "UB":
    location = "Upper Bavaria"
elif location_ab == "SEUB":
    location = "South East Upper Bavaria"
elif location_ab == "WNBA":
    location = "Western North Bavarian area"
elif location_ab == "unk":
    location = "unk"

if "preprocessing/" in in_file:
    out_file = in_file[:-3].replace("preprocessing/", "data/") + "conllu"
    sent_id_pfx = in_file.split("/")[-1][:-4] + "_"
else:
    out_file = "../data/" + in_file[:-3] + "conllu"
    sent_id_pfx = in_file[:-4] + "_"
with open(in_file, encoding="utf8") as f_in:
    with open(out_file, "w+", encoding="utf8") as f_out:
        sent_idx = 1
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            f_out.write("# sent_id = " + sent_id_pfx + str(sent_idx) + "\n")
            f_out.write("# text = " + line + "\n")
            f_out.write("# genre = " + genre + "\n")
            f_out.write("# dialect_group = " + dialect + "\n")
            f_out.write("# location = " + location + "\n")
            for (idx, word, misc) in process_sentence(line):
                f_out.write(str(idx) + "\t" + word + "\t_\t_\t_\t_\t_\t_\t_\t")
                f_out.write(misc + "\n")
            f_out.write("\n")
            sent_idx += 1
        f_out.write("\n")

print("Wrote " + str(sent_idx - 1) + " sentences to " + out_file)
