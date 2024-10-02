import time as timemodule
import random
max_time = 100   # The highest time that can be achieved                    
verbose = True  # Step-by-step movement description

class LightPath():
    def __init__(self, source, destination, channel, start, end, name):
        self.source = source
        self.destination = destination
        self.channel = channel
        self.starttime = start
        self.endtime = end
        self.name = name
        self.hash = hash(self) #hash is used to identify each object in the code, this is done to save space and eases working with dictionaries

class Graph():
    connection_graph = [] #[edge, edge, ...] Holds nodes connection information
    bidirectional = [] #[[edge.id, edge.id], ...] Holds pairs of oppositely directed edge, This will help us to implement bi-directional edges

    def __init__(self, *conn):
        for con in conn:
            self.addConnection(con)

    def addConnection(self, edge):
        newedge = Edge(edge.end_node, edge.start_node, edge.channel) #Its oppositely directed edge
        if edge not in self.connection_graph:
            self.connection_graph.append(edge)
            if newedge not in self.connection_graph:
                self.connection_graph.append(newedge)
                self.bidirectional.append([edge.hash, newedge.hash])

class Node():
    def __init__(self, name):
        self.name = name
        self.hash = hash(self)

class Edge(): #Each edge object represents a directed edge
    def __init__(self, node1, node2, channel):
        self.start_node = node1
        self.end_node = node2
        self.name = self.start_node.name + "->" + self.end_node.name # node->node
        self.hash = hash(self)
        if isinstance(channel, int):
            self.channel = []
            for i in range(channel): self.channel.append(i)
        else:
            self.channel = channel

class Instance(): #Our instance for each run
    def __init__(self, graph, *lightpaths):
        self.graph = graph
        self.lightpaths = lightpaths
        self.movetree = {} # {lightpath.name: [[channelpicked, []],...], ...} Represents the path and channel picked by each lightpath is currently taking, starting from the source
        self.backtrack = {} # {lightpath.name: [[],...], ...} Represents all the edges that were backtraked, this will ensure we never go back to them!
        for lightpath in self.lightpaths:
            self.movetree[lightpath.name] = []
            self.backtrack[lightpath.name] = []
            for i in range(lightpath.channel):
                self.movetree[lightpath.name].append([None, []])
                self.backtrack[lightpath.name].append({})
    
    def gettimes(self, start = True): #This returns all times that corresponds to startimes or endtimes of all lighpaths, this will help us know when to start or end a particular lightpath
        times = {} 
        for lightpath in self.lightpaths:
            if start:
                time = lightpath.starttime
            else:
                time = lightpath.endtime
            if time in times:
                times[time].append = lightpath.hash
            else:
                times[time] = [lightpath.hash]
        return times #{time : [lightpath.hash, lightpath.hash, ...]}

    def getneighbours(self, node): #Gets all the edges that are connected to given node
        neighbours = [] #[edge.id, ...]
        for edge in self.graph.connection_graph:
            if edge.start_node.hash == node:
                neighbours.append(edge.hash)
        return neighbours

    def bidirectional(self, edge1, edge2): #Checks if two edges makes a birectional edge
        for bidi in self.graph.bidirectional:
            if (edge1 in bidi) and (edge2 in bidi): return True
        return False
    
    def getbidirectional(self, edge): #Gets the other edge that makes a birectional edge from given edge
        for bidi in self.graph.bidirectional:
            if edge in bidi: return bidi[1 - bidi.index(edge)]
    
    def getvalidchannel(self, channels, invalidchannels):
        if set(channels) == set(invalidchannels): return None
        else:
            for i in invalidchannels:
                while i in channels: channels.remove(i)
        if channels:return random.choice(channels)
        else: return None
    
    def inbacktrack(self, nodeid, channel, backtrack):
        if nodeid in backtrack and channel in backtrack[nodeid]: return True
        return False
        
    def getnextedge(self, neighbours, movetree, backtrack):
        #using what algorithm?
        channel = movetree[0]
        previousedges = movetree[1]
        nextedge = None
        for neighbour in neighbours:
            connection = self.to_edge(neighbour)
            #first come first serve
            if channel is not None: #we have picked a channel
                #print("*", channel in connection.channel, neighbour not in previousedges, not self.inbacktrack(neighbour, channel, backtrack))
                if not self.inbacktrack(neighbour, channel, backtrack):
                    if channel in connection.channel and (neighbour not in previousedges):
                        if previousedges:
                            if not self.bidirectional(neighbour, previousedges[-1]): # This ensures we don't go back the last edge we moved on
                                if all(conn for conn in previousedges if self.to_edge(conn).start_node.hash != connection.end_node.hash): # This makes sure we don't move to any edges we have previously stepped on
                                    nextedge = [neighbour, channel]
                                    return nextedge  
                        else:
                            if neighbour not in backtrack:
                                nextedge = [neighbour, channel]
                            else:
                                if channel not in backtrack[neighbour]:
                                    nextedge = [neighbour, channel]
                                else:
                                    validchannel = self.getvalidchannel(connection.channel, backtrack[neighbour])
                                    if validchannel:
                                        nextedge = [neighbour, validchannel]
                                    else:
                                        nextedge = "BLOCKED"
                            return nextedge
                else:
                    if (connection.channel != []) and (neighbour not in previousedges) and (not movetree[1]):
                        validchannel = self.getvalidchannel(connection.channel, backtrack[neighbour])
                        if validchannel != None:
                            nextedge = [neighbour, validchannel]
                            return nextedge
                        else:
                            channel = None
                            continue   
            else:
                if (connection.channel != []) and (neighbour not in previousedges) and (not self.inbacktrack(neighbour, channel, backtrack)):
                    ch = random.choice(connection.channel)
                    nextedge = [neighbour, ch]
                    return nextedge
        return nextedge

    def visualise(self): #Views the graph
        for edge in self.graph.connection_graph:
            print(edge.name, edge.channel)
    def visualise_dot(self, name): #Views the graph as a dot file
        code = "".join(["graph ", name, " {"])
        addededges = []
        for edge in self.graph.connection_graph:
            if edge.hash not in addededges and self.getbidirectional(edge.hash) not in addededges:
                addededges.append(edge.hash)
                code += "".join(["\n", edge.start_node.name, " -- ", edge.end_node.name, ' [label="', str(len(edge.channel)), '"]', ";"])
        code += "\n}"
        return code

    def to_edge(self, idd): #converts hash to edge object
        for conn in self.graph.connection_graph:
            if conn.hash == idd: return conn
    
    def view_path(self, lightpath): #view paths of given lightpaths name
        print("=" * 20 + lightpath)
        for lp in self.movetree[lightpath]:
            for path in lp[1]:
                print(self.to_edge(path).name + "(" + str(lp[0]) + ")", end=", ")
            if lp: print()
    def view_path_dot(self, lightpath):
        code = "".join(["graph ", lightpath, " {"])
        addededges = []
        for lp in self.movetree[lightpath]:
            for path in lp[1]:
                edge = self.to_edge(path)
                if edge.hash not in addededges and self.getbidirectional(edge.hash) not in addededges:
                    addededges.append(edge.hash)
                    code += "".join(["\n", edge.start_node.name, " -- ", edge.end_node.name, ' [label="', str(len(edge.channel)), '" color=Red]', ";"])
        for edge in self.graph.connection_graph:
            if edge.hash not in addededges and self.getbidirectional(edge.hash) not in addededges:
                addededges.append(edge.hash)
                code += "".join(["\n", edge.start_node.name, " -- ", edge.end_node.name, ' [label="', str(len(edge.channel)), '"]', ";"])
        code += "\n}"
        return code

    def run(self): #run this instance
        ctime = 0
        starttimes = self.gettimes()
        endtimes = self.gettimes(False)
        while ctime < max_time:
            if ctime in starttimes:
                for idd in starttimes[ctime]:
                    for lightpath in self.lightpaths:
                        if lightpath.hash == idd:
                            #start each the ligthpath
                            for eachlightid in range(lightpath.channel):
                                source = lightpath.source
                                destination = lightpath.destination
                                if verbose: print(lightpath.name + "." + str(eachlightid) + " starts."+"-"*20)
                                while source.hash != destination.hash:
                                    neighbours = self.getneighbours(source.hash)
                                    nextedge = self.getnextedge(neighbours, self.movetree[lightpath.name][eachlightid], self.backtrack[lightpath.name][eachlightid])
                                    if isinstance(nextedge, list):
                                        self.movetree[lightpath.name][eachlightid][0] = nextedge[1]
                                        choosenchannel = self.movetree[lightpath.name][eachlightid][0]
                                        nextedge = nextedge[0]
                                        for connection in self.graph.connection_graph:
                                            if connection.hash == nextedge:
                                                if verbose: print("Next edge is: " + connection.name + ", picked " + str(choosenchannel))
                                                connection.channel.remove(choosenchannel)
                                                bedge = self.getbidirectional(nextedge)
                                                #for bconnection in self.graph.connection_graph:
                                                #    if bconnection.hash == bedge:
                                                #        bconnection.channel.remove(choosenchannel) #update its twin edge
                                                self.movetree[lightpath.name][eachlightid][1].append(nextedge) #update this move it in movetree
                                                source = connection.end_node
                                    else:
                                        #light can't move any further, so backtrack by one edge
                                        choosenchannel = self.movetree[lightpath.name][eachlightid][0]
                                        if nextedge == "BLOCKED":
                                            #Light don't know any channel to pick
                                            if verbose: print(lightpath.name + "." + str(eachlightid) + " has nowhere to move to.")
                                            return
                                        if self.movetree[lightpath.name][eachlightid][1]:
                                            lastedge = self.movetree[lightpath.name][eachlightid][1].pop()
                                        else:
                                            #light can't move to the destination using this channel and it's now in source node
                                            #It's possible that there can be ways of reaching the destination through other channels, choose another channel
                                            continue
                                        if lastedge not in self.backtrack[lightpath.name][eachlightid]:
                                            self.backtrack[lightpath.name][eachlightid][lastedge] = [choosenchannel] #update backtrack with last edge
                                        else:
                                            if choosenchannel not in self.backtrack[lightpath.name][eachlightid][lastedge]:
                                                self.backtrack[lightpath.name][eachlightid][lastedge].append(choosenchannel)
                                            else:
                                                #I think it's imposible to move to a backtracked edge, but what if it's possible?
                                                if verbose: print(lightpath.name + "." + str(eachlightid) + " stalked.")
                                                return
                                        for connection in self.graph.connection_graph:
                                            if connection.hash == lastedge:
                                                connection.channel.append(choosenchannel)
                                                bedge = self.getbidirectional(lastedge)
                                                #for bconnection in self.graph.connection_graph:
                                                #    if bconnection.hash == bedge:
                                                #        bconnection.channel.append(choosenchannel)
                                                source = connection.start_node
                                                if verbose: print(lightpath.name + "." + str(eachlightid) + " bactracked.")
                                if verbose: print(lightpath.name + "." + str(eachlightid) + " reached destination."+"-"*20)
                                #print(self.view_path_dot(lightpath.name.split(".")[0]))
            elif ctime in endtimes:
                if verbose: print("Now ending all paths ----------------------------------------------------------------")
                for idd in endtimes[ctime]:
                    for lightpath in self.lightpaths:
                        if lightpath.hash == idd:
                            for eachlightid in range(lightpath.channel):
                                #end each ligthpath
                                channelpicked = self.movetree[lightpath.name][eachlightid][0]
                                for eachedge in self.movetree[lightpath.name][eachlightid][1]:
                                    for connection in self.graph.connection_graph:
                                        if connection.hash == eachedge:
                                            connection.channel.append(channelpicked)
                                            #bedge = self.getbidirectional(eachedge)
                                            #for bconnection in self.graph.connection_graph:
                                            #    if bconnection.hash == bedge: bconnection.channel.append(channelpicked)
                                if verbose: print(lightpath.name + "." + str(eachlightid) + " ended.")
            #timemodule.sleep(0.05)
            ctime += 1

def simulator():
    A = Node("A")
    B = Node("B")
    C = Node("C")
    D = Node("D")
    E = Node("E")
    F = Node("F")
    
    AB = Edge(A, B, 10)
    BD = Edge(B, D, 10)
    EC = Edge(E, C, 10)
    AE = Edge(A, E, 10)
    CF = Edge(C, F, 10)
    BF = Edge(B, F, 10)

    lp0 = LightPath(A, D, 4, 70, 400, "lp0")
    lp1 = LightPath(C, D, 4, 50, 600, "lp1")

    graph = Graph( CF, EC, AB, BD, AE, BF)

    instance = Instance(graph, lp0, lp1)

    print(instance.visualise_dot("nn"))
    instance.run()
    print(instance.view_path_dot("lp0"))
    print(instance.view_path_dot("lp1"))


simulator()