import random
import sys


class Noiser:

    def __init__(self, noise_lvl):
        self.noise_lvl = noise_lvl
        alphabet = "qwertyuiopasdfghjklzxcvbnmäöüß"
        self.alphabet = list(alphabet + alphabet.upper())
        self.noise = ("add_char", "delete_char", "replace_char")

    def add_char(self, word):
        idx = random.randrange(-1, len(word))
        if idx == -1:
            return random.sample(self.alphabet, 1)[0] + word
        return word[:idx + 1] + random.sample(
            self.alphabet, 1)[0] + word[idx + 1:]

    def delete_char(self, word):
        idx = random.randrange(len(word))
        return word[:idx] + word[idx + 1:]

    def replace_char(self, word, idx=-1):
        if idx < 0:
            idx = random.randrange(len(word))
        return word[:idx] + random.sample(self.alphabet, 1)[0] + word[idx + 1:]

    def add_random_noise(self, tokens):
        """
        Aepli & Sennrich 2022
        """
        if noise_lvl < 0.0001:
            return
        n_changed = 0
        # Only include words with alphabetic content.
        poss_indices = [i for i, tok in enumerate(tokens)
                        if any(c.isalpha() for c in tok[1])]
        if not poss_indices:
            return tokens
        idx_noisy = random.sample(
            poss_indices, k=round(self.noise_lvl * len(poss_indices)))
        tokens_noised = []
        for i, tok in enumerate(tokens):
            if i in idx_noisy:
                word = getattr(self, random.sample(self.noise, 1)[0])(tok[1])
                tokens_noised.append((tok[0], word, tok[2]))
                n_changed += 1
            else:
                tokens_noised.append(tok)
        return tokens_noised


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE: python3 add_noise.py TRAIN_FILE")
        sys.exit(1)

    trainfile = sys.argv[1]
    devfile = trainfile.replace("train", "dev")

    for seed in (1234, 3456, 5678):
        random.seed(seed)

        for noise_lvl in range(10, 110, 10):
            noiser = Noiser(noise_lvl / 100)

            for infile in (trainfile, devfile):
                outfile = infile.replace(
                    ".conllu", f"_noise{noise_lvl}-{seed}.conllu")
                print(outfile)
                with open(outfile, "w+", encoding="utf8") as f_out:
                    with open(infile, encoding="utf8") as f_in:
                        tokens = []
                        for line in f_in:
                            if line == "\n":
                                if tokens:
                                    for tok in noiser.add_random_noise(tokens):
                                        f_out.write("\t".join(tok))
                                    tokens = []
                                f_out.write(line)
                                continue
                            if line[0] == "#":
                                f_out.write(line)
                                continue
                            tokens.append(line.split("\t", 2))
