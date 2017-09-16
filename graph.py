import networkx as nx
import os
import json
import sys
import matplotlib.pyplot as plt

from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges, EdgesAndLinkedNodes
from bokeh.models import ColumnDataSource, Circle, Plot, Range1d, HoverTool, TapTool, BoxSelectTool, WheelZoomTool, MultiLine
from bokeh.palettes import Spectral4
from bokeh.models.renderers import GraphRenderer


class Data:
    def __init__(self, datadir='newdata', MIN_RELEVANCE=0.6, MIN_SCORE=0.9):
        self.all_entities = []
        self.all_relevant_topics = []
        self.entities_relevant_appearances = {}
        self.entities_relevant_topics = {}
        self.entities_relevant_cooccurences = {}
        self.graph = None
        self.MIN_RELEVANCE = MIN_RELEVANCE
        self.MIN_SCORE = MIN_SCORE
        self.parse(datadir)

    def parse(self, datadir):
        for article_file in os.listdir(datadir):
            article_data = json.load(open(datadir+"/"+article_file))
            article_entities = []
            article_topics = []

            for tag in article_data.values():

                try:
                    type_group = tag['_typeGroup']
                except KeyError:
                    continue

                if type_group == 'entities' and tag["relevance"] >= self.MIN_RELEVANCE:

                    entity = tag["name"]
                    article_entities.append(entity)

                    if entity not in self.all_entities:
                        self.all_entities.append(entity)

                        self.entities_relevant_appearances.update({entity: 1})
                    else:
                        count = self.entities_relevant_appearances[entity]
                        self.entities_relevant_appearances.update({entity: count+1})

                if type_group == "topics" and tag["score"] >= self.MIN_SCORE:
                    topic = tag["name"]
                    article_topics.append(topic)
                    if topic not in self.all_relevant_topics:
                        self.all_relevant_topics.append(topic)

            for topic in article_topics:

                for entity in article_entities:
                    try:
                        topics = self.entities_relevant_topics[entity]
                        try:
                            count = topics[topic]
                            self.entities_relevant_topics[entity].update({topic: count+1})
                        except KeyError:
                            self.entities_relevant_topics[entity].update({topic: 1})
                    except KeyError:
                        self.entities_relevant_topics.update({entity: {topic: 1}})

            for entity1 in article_entities:
                for entity2 in article_entities:
                    if entity1 is not entity2:

                        if entity1 not in self.entities_relevant_cooccurences:
                            self.entities_relevant_cooccurences.update({entity1: {entity2: 1}})
                        else:
                            try:
                                count = self.entities_relevant_cooccurences[entity1][entity2]
                                self.entities_relevant_cooccurences[entity1].update({entity2: count+1})
                            except KeyError:
                                self.entities_relevant_cooccurences[entity1].update({entity2: 1})

                        if entity2 not in self.entities_relevant_cooccurences:
                            self.entities_relevant_cooccurences.update({entity2: {entity1: 1}})
                        else:
                            try:
                                count = self.entities_relevant_cooccurences[entity2][entity1]
                                self.entities_relevant_cooccurences[entity2].update({entity1: count+1})
                            except KeyError:
                                self.entities_relevant_cooccurences[entity2].update({entity1: 1})

    def print_info(self):
        for entity, count in self.entities_relevant_appearances.items():
            print(entity+": {}".format(count))

        for entity, relevant_topics in self.entities_relevant_topics.items():
            print(entity+ ": {}".format(relevant_topics))

        for entity, relevant_cooccurences in self.entities_relevant_cooccurences.items():
            print(entity + ": {}".format(relevant_cooccurences))

        print("Number of relevant entities: {}".format(len(self.all_entities)))
        print("Number of relevant topics: {}".format(len(self.all_relevant_topics)))

    def build_graph(self):
        map_entity_to_id = dict(zip(self.all_entities,
                                    range(len(self.all_entities))))
        map_id_to_entity = dict(zip(range(len(self.all_entities)),
                                    self.all_entities))

        dod = {}
        for entity1 in self.all_entities:
            id1 = map_entity_to_id[entity1]
            dod.update({id1: {}})
            try:
                for entity2, count in self.entities_relevant_cooccurences[entity1].items():
                    id2 = map_entity_to_id[entity2]
                    dod[id1].update({id2: {"weight": count}})
            except KeyError:
                continue

        self.graph = nx.from_dict_of_dicts(dod)

    def draw_graph(self, topics):
        plot = Plot(plot_width=1000, plot_height=1000, x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))

        plot.add_tools(HoverTool(tooltips=[("entity", "@entity")]), TapTool(), BoxSelectTool(), WheelZoomTool())

        graph = from_networkx(self.graph, nx.spring_layout, scale=2,
                              center=(0, 0))

        graph.node_renderer.glyph = Circle(size=15, fill_color=Spectral4[0])

        graph.node_renderer.data_source.column_names.append("entity")
        graph.node_renderer.data_source.data.update({"entity":
                                                         self.all_entities})

        graph.node_renderer.glyph = Circle(size=8, fill_color=Spectral4[0])
        graph.node_renderer.selection_glyph = Circle(size=8,
                                                     fill_color=Spectral4[2])
        graph.node_renderer.hover_glyph = Circle(size=12,
                                                 fill_color=Spectral4[1])

        graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC",
                                              line_alpha=0.8, line_width=1.5)
        graph.edge_renderer.selection_glyph = MultiLine(line_color=Spectral4[2],
                                                        line_width=1.5)
        graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[1],
                                                    line_width=2)

        graph.selection_policy = NodesAndLinkedEdges()
        graph.inspection_policy = NodesAndLinkedEdges()

        plot.renderers.append(graph)

        #output_file("networkx_graph.html")
        show(plot)


if __name__ == '__main__':

    MIN_RELEVANCE = 0.8
    MIN_SCORE = 0.9

    datadir = 'data'

    data_graph = Data(datadir)
    data_graph.build_graph()
    data_graph.draw_graph()
