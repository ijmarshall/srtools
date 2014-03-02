#
#   example subclass of pipeline
#   which uses a local bag-of-words (using a window of k words forwards and backwards)
#

import pipeline


class bilearnPipeline(pipeline.Pipeline):

    def __init__(self, text):
        self.functions = [[{"w": word, "p": pos} for word, pos in pos_tagger.tag(self.word_tokenize(sent))] for sent in self.sent_tokenize(swap_num(text))]
        self.load_templates()        
        self.text = text  
        

    def load_templates(self):
        self.templates = (
                          (("w_int", 0),),
                          # (("w", 1),),
                          # (("w", 2),),
                          # (("w", 3),),
                          # # (("wl", 4),),
                          # (("w", -1),),
                          # (("w", -2),),
                          # (("w", -3),),
                          # (("wl", -4),),
                          # (('w', -2), ('w',  -1)),
                          # (('wl',  -1), ('wl',  -2), ('wl',  -3)),
                          # (('stem', -1), ('stem',  0)),
                          # (('stem',  0), ('stem',  1)),
                          # (('w',  1), ('w',  2)),
                          # (('wl',  1), ('wl',  2), ('wl',  3)),
                          # (('p',  0), ('p',  1)),
                          # (('p',  1),),
                          # (('p',  2),),
                          # (('p',  -1),),
                          # (('p',  -2),),
                          # (('p',  1), ('p',  2)),
                          # (('p',  -1), ('p',  -2)),
                          # (('stem', -2), ('stem',  -1), ('stem',  0)),
                          # (('stem', -1), ('stem',  0), ('stem',  1)),
                          # (('stem', 0), ('stem',  1), ('stem',  2)),
                          # (('p', -2), ),
                          # (('p', -1), ),
                          # (('p', 1), ),
                          # (('p', 2), ),
                          # (('num', -1), ), 
                          # (('num', 1), ),
                          # (('cap', -1), ),
                          # (('cap', 1), ),
                          # (('sym', -1), ),
                          # (('sym', 1), ),
                          (('div10', 0), ),
                          (('>10', 0), ),
                          (('numrank', 0), ),
                          # (('p1', 1), ),
                          # (('p2', 1), ),
                          # (('p3', 1), ),
                          # (('p4', 1), ),
                          # (('s1', 1), ),
                          # (('s2', 1), ),
                          # (('s3', 0), ),
                          # (('s4', 0), ),
                          (('wi', 0), ),
                          (('si', 0), ),
                          # (('next_noun', 0), ),
                          # (('next_verb', 0), ),
                          # (('last_noun', 0), ),
                          # (('last_verb', 0), ),
                          (('in_num_list', 0), ),
                          )

        self.answer_key = "w"
        self.w_pos_window = 6 # set 0 for no w_pos window features
 
    def run_functions(self, show_progress=False):

        # make dict to look up ranking of number in abstract
        num_list_nest = [[int(word["w"]) for word in sent if word["w"].isdigit()] for sent in self.functions]
        num_list = [item for sublist in num_list_nest for item in sublist] # flatten
        num_list.sort(reverse=True)
        num_dict = {num: rank for rank, num in enumerate(num_list)}

        for i, sent_function in enumerate(self.functions):

            last_noun_index = 0
            last_noun = "BEGINNING_OF_SENTENCE"

            last_verb_index = 0
            last_verb = "BEGINNING_OF_SENTENCE"

            for j, function in enumerate(sent_function):
                # print j
                word = self.functions[i][j]["w"]
                features = {"num": word.isdigit(),
                            "cap": word[0].isupper(),
                            "sym": not word.isalnum(),
                            "p1": word[0],
                            "p2": word[:2],
                            "p3": word[:3],
                            "p4": word[:4],
                            "s1": word[-1],
                            "s2": word[-2:],
                            "s3": word[-3:],
                            "s4": word[-4:],
                            # "stem": self.stem.stem(word),
                            "wi": j,
                            "si": i,
                            "wl": word.lower()}
                if word.isdigit():
                    num = int(word)
                    features[">10"] = num > 10
                    features["w_int"] = num
                    features["div10"] = ((num % 10) == 0)
                    features["numrank"] = num_dict[num]
                
                self.functions[i][j].update(features)


                # self.functions[i][j].update(words)

                # if pos is a noun, back fill the previous words with 'next_noun'
                # and the rest as 'last_noun'
                pos = self.functions[i][j]["p"]
                
                if re.match("NN.*", pos):

                    for k in range(last_noun_index, j):
                        self.functions[i][k]["next_noun"] = word
                        self.functions[i][k]["last_noun"] = last_noun
                    last_noun_index = j
                    last_noun = word
                    
                # and the same for verbs
                elif re.match("VB.*", pos):

                    for k in range(last_verb_index, j):
                        
                        self.functions[i][k]["next_verb"] = word
                        self.functions[i][k]["last_verb"] = last_verb
                    last_verb_index = j
                    last_verb = word

            for k in range(last_noun_index, len(sent_function)):
                self.functions[i][k]["next_noun"] = "END_OF_SENTENCE"
                self.functions[i][k]["last_noun"] = last_noun

            for k in range(last_verb_index, len(sent_function)):
                self.functions[i][k]["next_verb"] = "END_OF_SENTENCE"
                self.functions[i][k]["last_verb"] = last_verb
