from typing import List


class FrontierData:

    def __init__(self, word_id: int, edges_to_here: List[int]):
        self.word_id = word_id
        self.edges_to_here: edges_to_here

