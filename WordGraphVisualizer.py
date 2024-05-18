import random
import threading
from typing import List

import cv2

from WordGraph import WordGraph
import numpy as np

CANVAS_SIZE = 800

class WordGraphVisualizer:

    def __init__(self, graph: WordGraph):
        self.graph = WordGraph
        self.canvas = np.zeros(shape=(CANVAS_SIZE, CANVAS_SIZE, 3), dtype=float)
        self.canvas_lock = threading.Lock()
        self.needs_update: bool = True
        self.word_locs: List[List[float]] = []

        for id in range(len(self.graph.vertices)):
            self.word_locs.append([random.randint(10,CANVAS_SIZE-10), random.randint(10,CANVAS_SIZE-10)])

    def draw_self(self):
        self.canvas_lock.acquire()
        self.canvas = np.zeros(shape=(CANVAS_SIZE, CANVAS_SIZE, 3), dtype=float)

        for edge in self.graph.visible_edges:
            u: List[float] = self.word_locs[edge[0]]
            v: List[float] = self.word_locs[edge[1]]
            cv2.line(img=self.canvas, pt1=(int(u[0]), int(u[1])),
                     pt2=(int(v[0]), int(v[1])), color=(1.0, 1.0, 1.0), thickness=1)

            for frontier_item in self.graph.frontier:
                word_id = frontier_item[0]
                cv2.putText(img=self.canvas, text=self.graph.vertices[word_id].word, org=(int(self.word_locs[word_id][0] - 10),
                                                                       int(self.word_locs[word_id][1] - 5)),
                            fontFace=cv2.FONT_HERSHEY_PLAIN,
                            fontScale=1,
                            color=self.graph.vertices[word_id].color)

        self.canvas_lock.release()