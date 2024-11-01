import copy
import threading
from typing import List, Set, Tuple, Optional
import time

from FrontierData import FrontierData
from WordEdge import WordEdge
from WordVertex import WordVertex

TAB = "\t"
POP_DELAY = 0.25
PUSH_DELAY = 0.1


class WordGraph:

    def __init__(self):
        self.vertices: List[WordVertex] = []  # all the words in the graph
        self.edges: List[WordEdge] = []  # all the edges in the graph
        self.visited: Set[int] = set()  # ids of words we'd like colored as "visited"
        self.visible_edges: Set[int] = set()  # ids of edges that we've found by way of get Neighbors
        self.frontier: List[FrontierData] = []  # FrontierData for all words we've seen but yet to visit.
        self.current_word_id: Optional[int] = None
        # threading lock for self.visited/self.visible_edges/self.frontier.
        self.search_variables_lock: threading.Lock = threading.Lock()

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

    def get_neighbors(self, node: int) -> Tuple[List[int], List[int]]:
        neighbor_word_ids: List[int] = []
        edge_ids_to_neighbors: List[int] = []
        for edge_id in range(len(self.edges)):
            edge = self.edges[edge_id]
            if edge.u == node:
                neighbor_word_ids.append(edge.v)
                edge_ids_to_neighbors.append(edge_id)
            elif edge.v == node:
                neighbor_word_ids.append(edge.u)
                edge_ids_to_neighbors.append(edge_id)

        return neighbor_word_ids, edge_ids_to_neighbors

    def id_for_word(self, word:str) -> int:
        for id in range(len(self.vertices)):
            if self.vertices[id].word == word:
                return id
        return -1

    def clear_search_variables(self):
        self.search_variables_lock.acquire()
        self.visible_edges.clear()
        self.visited.clear()
        self.frontier.clear()
        self.search_variables_lock.release()


    def find_path(self, word1_id: int, word2_id: int) -> Optional[List[int]]:
        self.clear_search_variables()
        self.frontier.append(FrontierData(word1_id,[word1_id]))
        while len(self.frontier) > 0:
            self.search_variables_lock.acquire()
            current_word_data: FrontierData = self.frontier.pop(0)
            self.search_variables_lock.release()
            self.current_word_id = current_word_data.word_id
            path_to_current_word: List[int] = current_word_data.word_ids_to_here
            if self.current_word_id in self.visited:
                continue
            print(f"Popped: {'|----'*(len(path_to_current_word)-1)}|{self.vertices[current_word_data.word_id].word}")
            time.sleep(POP_DELAY)
            if self.current_word_id == word2_id:
                return path_to_current_word

            neighbors, edges = self.get_neighbors(self.current_word_id)
            for neighbor_id, edge_id in zip(neighbors, edges):
                incremented_path = copy.deepcopy(path_to_current_word)
                incremented_path.append(neighbor_id)
                self.search_variables_lock.acquire()
                if neighbor_id not in self.visited:
                    self.frontier.append(FrontierData(neighbor_id, incremented_path))
                    self.vertices[neighbor_id].color = (1.0, 0.0, 0.8)
                    print(f"Pushed: {'     '*(len(incremented_path)-1)} {self.vertices[neighbor_id].word}\t\t{len(self.frontier)}+{len(self.visited)}")
                self.visible_edges.add(edge_id)
                self.search_variables_lock.release()
                time.sleep(PUSH_DELAY)
            self.search_variables_lock.acquire()
            self.visited.add(self.current_word_id)
            self.vertices[self.current_word_id].color = (0.0, 0.8, 1.0)
            self.search_variables_lock.release()

        return None

    def words_for_path(self, id_list: List[int]) -> List[str]:
        result: List[str] = []
        for id in id_list:
            result.append(self.vertices[id].word)
        return result

    def execute_search(self, word1_id: int, word2_id: int):
        result = self.find_path(word1_id, word2_id)
        print(result)
        print(self.words_for_path(result))


