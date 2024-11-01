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
# Edges between words attract at distance, but repel up close (like van der waals forces)
NEUTRAL_RADIUS = 30  # the inflection point between attraction and repulsion
EDGE_ATTRACTION_FACTOR = 4  # the strength of the attraction
EDGE_REPULSION_MODIFIER = -1.5  # the amount by which the force is multiplied to get the repulsion up close.
MAX_EFFECTIVE_D_FOR_EDGES = 50.0  # when calculating the distances of the edges, there is a max value we consider
                                  # to prevent overflow.

# All words have forces between themselves and all other forces.
MUTUAL_REPULSION_FACTOR =  0.5  # the strength of the repulsion between all cells... except:
VISITED_REPULSION_DISCOUNT = 1 #  an amount of attraction between cells that are both visited... if this is > MRF, then
                                  # they actually attract.

# The walls of the canvas also apply forces inwards:
BORDER_FORCE = 25  # the effective strength of the force... It is actually exponential trying to keep things in.
BORDER_RANGE = 10  # the effective internal distance from the border for the force from the borders.

min_movement = 0.0125  # a bit unlikely, but if nothing has more net force than this, we stop the simulation. This is
                       # only sensible for small graphs.

class WordGraphVisualizer:

    def __init__(self, graph: WordGraph):
        print("WGV initializing")
        self.graph = graph
        self.canvas = np.zeros(shape=(CANVAS_SIZE, CANVAS_SIZE, 3), dtype=float)
        self.canvas_lock = threading.Lock()
        self.needs_update: bool = True
        self.word_locs: List[List[float]] = []
        self.dirty_canvas: bool = True
        self.previously_drawn: List[int] = []

        for id in range(len(self.graph.vertices)):
            self.word_locs.append([CANVAS_SIZE/2, CANVAS_SIZE/2])
        print("WGV initialized.")

    def draw_graph(self):
        self.canvas_lock.acquire()
        self.canvas[:, :, :] = 0.0  # clear window to black.

        # draw edges (lines)
        for edge in self.graph.visible_edges:
            u: List[float] = self.word_locs[self.graph.edges[edge].u]
            v: List[float] = self.word_locs[self.graph.edges[edge].v]
            cv2.line(img=self.canvas, pt1=(int(u[0]), int(u[1])),
                     pt2=(int(v[0]), int(v[1])), color=(0.5, 0.5, 0.5), thickness=1)

        # draw vertices (words)
        for word_id in self.active_words:
            cv2.putText(img=self.canvas, text=self.graph.vertices[word_id].word, org=(int(self.word_locs[word_id][0] - 10),
                                                                   int(self.word_locs[word_id][1] - 5)),
                        fontFace=cv2.FONT_HERSHEY_PLAIN,
                        fontScale=1,
                        color=self.graph.vertices[word_id].color)

        # highlight current vertex (word) with a green circle
        if self.graph.current_word_id is not None:
            cv2.circle(img=self.canvas,
                       center=(int(self.word_locs[self.graph.current_word_id][0]),
                               int(self.word_locs[self.graph.current_word_id][1])),
                       radius=15,
                       color=(0.0, 1.0, 0.0),
                       thickness=2)
        self.canvas_lock.release()
        self.dirty_canvas = True

    def find_net_forces(self):
        """
        For each vertex, find the total of the forces from all other visible vertices and connected edges, as well as
        the borders of the canvas. Puts these into an array of forces, indexed on the same values as the vertices are.
        """
        self.net_forces:List[List[float]] = [[0, 0] for i in range(len(self.graph.vertices))]  # clear the forces.

        for i in range(len(self.active_words)):
            word_id = self.active_words[i]
            # find forces from all edges attached to this vertex.
            for edge_id in self.graph.visible_edges:
                if self.graph.edges[edge_id].u == word_id or self.graph.edges[edge_id].v == word_id:
                    F = self.force_from_edge(self.graph.edges[edge_id],
                                             attraction_factor=0.00075,
                                             repulsion_multiplier=-3,
                                             forward=True)
                    # apply force depending on which end of the edge this vertex is on...
                    if self.graph.edges[edge_id].u == word_id:
                        self.net_forces[word_id][0] += F[0]
                        self.net_forces[word_id][1] += F[1]
                    else:
                        self.net_forces[word_id][0] -= F[0]
                        self.net_forces[word_id][1] -= F[1]

            #  and calculate the force from all other vertices. This is roughly a 1/r force, outside of NEUTRAL_RADIUS.
            for j in range(i):
                word_id2 = self.active_words[j]
                dx = self.word_locs[word_id][0] - self.word_locs[word_id2][0]
                dy = self.word_locs[word_id][1] - self.word_locs[word_id2][1]
                d_squared = math.pow(dx, 2) + math.pow(dy, 2)
                if d_squared > NEUTRAL_RADIUS:
                    repulsion = MUTUAL_REPULSION_FACTOR
                    if word_id in self.graph.visited and word_id2 in self.graph.visited:
                        repulsion -= VISITED_REPULSION_DISCOUNT
                    self.net_forces[word_id][0] += dx / d_squared * repulsion
                    self.net_forces[word_id][1] += dy / d_squared * repulsion
                    self.net_forces[word_id2][0] -= dx / d_squared * repulsion
                    self.net_forces[word_id2][1] -= dy / d_squared * repulsion

            # calculate forces from the borders. This is proportional to exp(-d)
            self.net_forces[word_id][0] += BORDER_FORCE * math.exp(-self.word_locs[word_id][0] / BORDER_RANGE)
            self.net_forces[word_id][1] += BORDER_FORCE * math.exp(-self.word_locs[word_id][1] / BORDER_RANGE)
            self.net_forces[word_id][0] -= BORDER_FORCE * math.exp(
                -(CANVAS_SIZE - self.word_locs[word_id][0]) / BORDER_RANGE)
            self.net_forces[word_id][1] -= BORDER_FORCE * math.exp(
                -(CANVAS_SIZE - self.word_locs[word_id][1]) / BORDER_RANGE)

    def build_active_word_list(self):
        """
        generate a list of all the ids of words in the visited list, the frontier and the current word; essentially all
        the vertices we wish to draw and have interact graphically.
        :return: None
        """
        self.active_words: List[int] = []
        self.active_words.extend(self.graph.visited)
        for fd in self.graph.frontier:
            if fd.word_id not in self.active_words:
                self.active_words.append(fd.word_id)
        if self.graph.current_word_id is not None and self.graph.current_word_id not in self.active_words:
            self.active_words.append(self.graph.current_word_id)
            self.graph.vertices[self.graph.current_word_id].color = (0, 0, 1.0)

    def force_from_edge(self, edge: WordEdge,
                        attraction_factor: float,
                        repulsion_multiplier: float,
                        forward: bool) -> Tuple[float, float]:
        u: List[float] = self.word_locs[edge.u]
        v: List[float] = self.word_locs[edge.v]

        dx = u[0] - v[0]
        dy = u[1] - v[1]
        if abs(dx)+abs(dy) < 1.5 * MAX_EFFECTIVE_D_FOR_EDGES:
            # d = min(max_effective_d_for_edges, math.sqrt(math.pow(dx, 2) + math.pow(dy, 2)))
            d = min(MAX_EFFECTIVE_D_FOR_EDGES, math.pow(dx, 2) + math.pow(dy, 2))
        else:
            d = MAX_EFFECTIVE_D_FOR_EDGES
        F_mag = attraction_factor * math.pow(d - NEUTRAL_RADIUS, 2)
        if d < NEUTRAL_RADIUS:
            F_mag *= repulsion_multiplier
        if d > 0:
            fx = -F_mag * dx / d
            fy = -F_mag * dy / d
        else:
            fx = 0
            fy = 0

        if not forward:
            fx *= -1
            fy *= -1

        return fx, fy

    def update_locations_from_forces(self) -> bool:
        madeAChange = False
        if len(self.active_words) > 0:
            move_factor = 1  # math.log10(len(self.active_words))
        else:
            move_factor = 1
        for word_id in range(len(self.graph.vertices)):
            self.word_locs[word_id][0] += self.net_forces[word_id][0] * move_factor
            self.word_locs[word_id][1] += self.net_forces[word_id][1] * move_factor
            self.word_locs[word_id][0] = min(CANVAS_SIZE*1.0+25, max(-25., self.word_locs[word_id][0]))
            self.word_locs[word_id][1] = min(CANVAS_SIZE * 1.0+25, max(-25., self.word_locs[word_id][1]))
            if (self.net_forces[word_id][0] > min_movement or self.net_forces[word_id][1] > min_movement):
                madeAChange = True

        return madeAChange

    def update_loop(self):
        while True:
            self.build_active_word_list()
            self.put_new_words_near_current()
            self.graph.search_variables_lock.acquire()
            self.find_net_forces()
            moved = self.update_locations_from_forces()
            if moved:
                self.draw_graph()
            self.graph.search_variables_lock.release()
            time.sleep(0.01)

    def put_new_words_near_current(self):
        if len(self.previously_drawn) == 0 and self.graph.current_word_id is not None:
            self.word_locs[self.graph.current_word_id] = [CANVAS_SIZE/2, CANVAS_SIZE/2]
            self.previously_drawn.append(self.graph.current_word_id)
        for i in range(1,len(self.active_words)):
            word_id = self.active_words[i]
            if word_id == self.graph.current_word_id:
                continue
            if word_id not in self.previously_drawn:
                # angle = random.random()*math.pi
                if self.graph.current_word_id in self.previously_drawn:
                    self.word_locs[word_id][0] = self.word_locs[self.graph.current_word_id][0] + random.randrange(-30, 31)  # 20*math.cos(angle)
                    self.word_locs[word_id][1] = self.word_locs[self.graph.current_word_id][1] + random.randrange(-30, 31)  #20 * math.sin(angle)
                else:
                    self.word_locs[word_id][0] = self.word_locs[self.active_words[i-1]][0] + random.randrange(-30, 31)
                    self.word_locs[word_id][1] = self.word_locs[self.active_words[i - 1]][1] + random.randrange(-30, 31)
                self.previously_drawn.append(word_id)