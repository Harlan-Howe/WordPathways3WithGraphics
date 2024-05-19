import threading

import cv2

from WordGraph import WordGraph
from WordGraphVisualizer import WordGraphVisualizer


def main():
    global theGraph, theVisualizer

    theGraph = WordGraph()
    theGraph.load_words_from_file("Four_letters_nodes.txt")
    # theGraph.load_words_from_file("Four_letters_nodes_subset.txt")
    theGraph.build_edges()

    word1_id = theGraph.id_for_word("fled")
    word2_id = theGraph.id_for_word("tint")



    theVisualizer = WordGraphVisualizer(theGraph)
    graph_solving_thread = threading.Thread(target=theGraph.execute_search, args=(word1_id, word2_id))
    visualizer_thread = threading.Thread(target=theVisualizer.update_loop)
    visualizer_thread.start()
    graph_solving_thread.start()

    while True:
        if theVisualizer.dirty_canvas:
            theVisualizer.canvas_lock.acquire()
            cv2.imshow("Word Graph",theVisualizer.canvas)
            theVisualizer.canvas_lock.release()
            theVisualizer.dirty_canvas = False
        cv2.waitKey(10)


if __name__ == "__main__":
    main()