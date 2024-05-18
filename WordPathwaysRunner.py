from WordGraph import WordGraph


def main():
    global theGraph, theVisualizer

    theGraph = WordGraph()
    # theGraph.load_words_from_file("Four_letter_nodes.txt")
    theGraph.load_words_from_file("Four_letter_nodes_subset.txt")
    theGraph.build_edges()


if __name__ == "__main__":
    main()