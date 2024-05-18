import math
import random
import threading
import time
from typing import List, Tuple

import cv2

from WordEdge import WordEdge
from WordGraph import WordGraph
import numpy as np

CANVAS_SIZE = 800
NEUTRAL_RADIUS = 40
EDGE_ATTRACTION_FACTOR = 0.00075
EDGE_REPULSION_MODIFIER = 0
MUTUAL_REPULSION_FACTOR = 0.5
BORDER_FORCE = 15
BORDER_RANGE = 10
max_effective_d_for_edges = 100.0
min_movement = 0.0125

class WordGraphVisualizer:

    def __init__(self, graph: WordGraph):
        print("WGV initializing")
        self.graph = graph
        self.canvas = np.zeros(shape=(CANVAS_SIZE, CANVAS_SIZE, 3), dtype=float)
        self.canvas_lock = threading.Lock()
        self.needs_update: bool = True
        self.word_locs: List[List[float]] = []
        self.dirty_canvas: bool = True

        for id in range(len(self.graph.vertices)):
            self.word_locs.append([random.randint(10, CANVAS_SIZE-10), random.randint(10, CANVAS_SIZE-10)])
        print("WGV initialized.")

    def draw_graph(self):
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
        self.dirty_canvas = True

    def find_net_forces(self):
        self.active_words: List[int] = []
        self.active_words.extend(self.graph.visited)
        for fd in self.graph.frontier:
            self.active_words.append(fd.word_id)
        self.net_forces:List[List[float]] = [[0, 0] for i in range(len(self.active_words))]

        for word_id in range(len(self.active_words)):
            for edge in self.graph.visible_edges:
                if edge.u == word_id or edge.v == word_id:
                    F = self.force_from_edge(edge, attraction_factor=0.00075, repulsion_multiplier=-3, forward=True)
                    if edge.u == word_id:
                        self.net_forces[word_id][0] += F[0]
                        self.net_forces[word_id][1] += F[1]
                    else:
                        self.net_forces[word_id][0] -= F[0]
                        self.net_forces[word_id][1] -= F[1]
            for word_id2 in range(word_id):
                dx = self.word_locs[word_id][0] - self.word_locs[word_id2][0]
                dy = self.word_locs[word_id][1] - self.word_locs[word_id2][1]
                d_squared = math.pow(dx, 2) + math.pow(dy, 2)
                if d_squared > NEUTRAL_RADIUS:
                    self.net_forces[word_id][0] += dx / d_squared * MUTUAL_REPULSION_FACTOR
                    self.net_forces[word_id][1] += dy / d_squared * MUTUAL_REPULSION_FACTOR
                    self.net_forces[word_id2][0] -= dx / d_squared * MUTUAL_REPULSION_FACTOR
                    self.net_forces[word_id2][1] -= dy / d_squared * MUTUAL_REPULSION_FACTOR

            self.net_forces[word_id][0] += BORDER_FORCE * math.exp(-self.word_locs[word_id][0] / BORDER_RANGE)
            self.net_forces[word_id][1] += BORDER_FORCE * math.exp(-self.word_locs[word_id][1] / BORDER_RANGE)
            self.net_forces[word_id][0] -= BORDER_FORCE * math.exp(
                -(CANVAS_SIZE - self.word_locs[word_id][0]) / BORDER_RANGE)
            self.net_forces[word_id][1] -= BORDER_FORCE * math.exp(
                -(CANVAS_SIZE - self.word_locs[word_id][1]) / BORDER_RANGE)

    def force_from_edge(self, edge: WordEdge,
                        attraction_factor: float,
                        repulsion_multiplier: float,
                        forward: bool) -> Tuple[float, float]:
        u: List[float] = self.word_locs[edge.u]
        v: List[float] = self.word_locs[edge.v]

        dx = u[0] - v[0]
        dy = u[1] - v[1]

        d = min(max_effective_d_for_edges, math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)))
        F_mag = attraction_factor * math.pow(d - NEUTRAL_RADIUS, 2)
        if d < NEUTRAL_RADIUS:
            F_mag *= repulsion_multiplier

        fx = -F_mag * dx / d
        fy = -F_mag * dy / d

        if not forward:
            fx *= -1
            fy *= -1

        return fx, fy

    def update_locations_from_forces(self) -> bool:
        madeAChange = False
        for word_id in range(len(self.active_words)):
            self.word_locs[word_id][0] += self.net_forces[word_id][0]
            self.word_locs[word_id][1] += self.net_forces[word_id][1]
            if (self.net_forces[word_id][0] > min_movement or self.net_forces[word_id][1] > min_movement):
                madeAChange = True

        return madeAChange

    def update_loop(self):
        while True:
            self.graph.search_variables_lock.acquire()
            self.find_net_forces()
            moved = self.update_locations_from_forces()
            if moved:
                self.draw_graph()
            self.graph.search_variables_lock.release()
            time.sleep(0.01)

