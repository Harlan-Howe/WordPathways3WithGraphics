import threading

from WordGraph import WordGraph
import numpy as np

CANVAS_SIZE = 800

class WordGraphVisualizer:

    def __init__(self, graph: WordGraph):
        self.graph = WordGraph
        self.canvas = np.zeros(shape=(CANVAS_SIZE, CANVAS_SIZE, 3), dtype=float)
        self.canvas_lock = threading.Lock()