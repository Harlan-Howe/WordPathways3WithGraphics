import cv2

from WordGraph import WordGraph
from WordGraphVisualizer import WordGraphVisualizer


def main():
    global theGraph, theVisualizer

    theGraph = WordGraph()
    # theGraph.load_words_from_file("Four_letter_nodes.txt")
    theGraph.load_words_from_file("Four_letters_nodes_subset.txt")
    theGraph.build_edges()

    theVisualizer = WordGraphVisualizer(theGraph)

    print("Showing canvas.")
    theVisualizer.canvas_lock.acquire()
    cv2.imshow("Word Graph",theVisualizer.canvas)
    theVisualizer.canvas_lock.release()
    cv2.waitKey(0)
    print("Done.")


if __name__ == "__main__":
    main()