from typing import List, Set

from FrontierData import FrontierData
from WordEdge import WordEdge
from WordVertex import WordVertex


class WordGraph:

    def __init__(self):
        self.vertices: List[WordVertex] = []  # all the words in the graph
        self.edges: List[WordEdge] = []  # all the edges in the graph
        self.visited: Set[int] = set()  # ids of words we'd like colored as "visited"
        self.visible_edges: Set[int] = set()  # ids of edges that we've found by way of get Neighbors
        self.frontier = List[FrontierData]  # FrontierData for all words we've seen but yet to visit.

    def load_words_from_file(self, word_filename: str) -> None:
        print(f"Loading Vertices from {word_filename}.")
        count = 0
        with open(word_filename, 'r') as ins:
            for line in ins:
                items = line.split("\t")
                if count % 100 == 0:  # show progress....
                    print(count)

                count += 1
                self.vertices.append(WordVertex(items[1].split("\n")[0]))
        print("Done Loading from file.\n-------------------------------------------")

    def num_mismatched_letters(self, word1: str, word2: str) -> int:
        """
        looks at the two words, character by character and returns the number of
        characters that don't match.
        :param word1: a string
        :param word2: another string, of the same length as word1
        :return: the number of characters that don't match. Two identical strings
        would return 0; "pack" and "pick" would return 1; "mate" and "meta" would return 2.
        """
        assert (len(word1) == len(word2))
        count = 0
        # -----------------------------------------
        # TODO: You need to write this method.
        for i in range(len(word1)):
            if word1[i] != word2[i]:
                count += 1
        # -----------------------------------------
        return count

    def build_edges(self):
        """
        loops through the list of words in self.vertices. Compares each word to the
        other words on the list. If they differ by exactly one letter, then this method records
        the words to the self.edges data structure.
        :return: None
        """
        print("Constructing Edges.")
        # -----------------------------------------
        # TODO: You should write this method!

        # Note: this method may take some time to run - it is likely to be O(N^2), and some lists have N = 10,000 words
        # or more. (I've had students decide that their program was "broken" and quit it before this process finished...
        # every time, not realizing that the program was working hard behind the scenes.)
        #
        # I recommend that you keep track of the number of edges you have added, and if it is a multiple of 1000, print
        # something so that you know your program is making progress. Or, if you have looked at a multiple of 100 words
        # in your outer loop, print that.
        n = len(self.vertices)
        step_size = int(n/20)
        print()
        for i in range(n):
            if i % step_size == 0:
                print(f"{100*i/n:3.2f}% words processed.")
            for j in range(i):
                if self.num_mismatched_letters(self.vertices[i].word, self.vertices[j].word) == 1:
                    self.edges.append(WordEdge(i, j))

        # -----------------------------------------
        print("Done Constructing Edges.\n------------------------------------")