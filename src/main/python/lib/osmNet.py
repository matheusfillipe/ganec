import xml.sax
import copy
import networkx
import shapefile
import numpy as np
from copy import deepcopy
import simplekml
from geojson import LineString, Feature, FeatureCollection, dump

CAT = 'motorway|trunk|primary|secondary|tertiary|road|residential|service|motorway_link|trunk_link|primary_link|secondary_link|teriary_link'
DISTANCE_CONVERT = 107978.4104537571    
TOLERANCE=250  #metros


import pyproj


_projections = {}


def zone(coordinates):
    if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
        return 32
    if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
        if coordinates[0] < 9:
            return 31
        elif coordinates[0] < 21:
            return 33
        elif coordinates[0] < 33:
            return 35
        return 37
    return int((coordinates[0] + 180) / 6) + 1


def letter(coordinates):
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]


def project(coordinates):
    z = zone(coordinates)
    l = letter(coordinates)
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    x, y = _projections[z](coordinates[0], coordinates[1])
    if y < 0:
        y += 10000000
    return z, l,[x, y]


def unproject(z, l, p):
    x,y=p
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    if l < 'N':
        y -= 10000000
    lng, lat = _projections[z](x, y, inverse=True)
    return [lng, lat]

def distance(a,b):
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def is_between(a,c,b):
    return distance(a,c) + distance(c,b) == distance(a,b)

def interLinePoint(p1, p2, p3):
     x1, y1 = p1
     x2, y2 = p2
     x3, y3 = p3
     dx, dy = x2-x1, y2-y1
     det = dx*dx + dy*dy
     a = (dy*(y3-y1)+dx*(x3-x1))/det
     return [x1+a*dx, y1+a*dy]

def collinear(p0, p1, p2):
    x1, y1 = p1[0] - p0[0], p1[1] - p0[1]
    x2, y2 = p2[0] - p0[0], p2[1] - p0[1]
    return abs(x1 * y2 - x2 * y1) < 1e-8

class Node:
    def __init__(self, id, lon, lat):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = {}
        
class Way:
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        self.nds = []
        self.tags = {}
        
    def split(self, dividers):
        # slice the node-array using this nifty recursive function
        def slice_array(ar, dividers):
            for i in range(1,len(ar)-1):
                if dividers[ar[i]]>1:
                    #print "slice at %s"%ar[i]
                    left = ar[:i+1]
                    right = ar[i:]
                    
                    rightsliced = slice_array(right, dividers)
                    
                    return [left]+rightsliced
            return [ar]
            


        slices = slice_array(self.nds, dividers)
        
        # create a way object for each node-array slice
        ret = []
        i=0
        for slice in slices:
            littleway = copy.copy( self )
            littleway.id += "-%d"%i
            littleway.nds = slice
            ret.append( littleway )
            i += 1
            
        return ret
        
    

class OSM:
    def __init__(self, filename_or_stream):
        """ File can be either a filename or stream/file object."""
        nodes = {}
        ways = {}
        
        superself = self
        
        class OSMHandler(xml.sax.ContentHandler):
            @classmethod
            def setDocumentLocator(self,loc):
                pass
            
            @classmethod
            def startDocument(self):
                pass
                
            @classmethod
            def endDocument(self):
                pass
                
            @classmethod
            def startElement(self, name, attrs):
                if name=='node':
                    self.currElem = Node(attrs['id'], float(attrs['lon']), float(attrs['lat']))
                elif name=='way':
                    self.currElem = Way(attrs['id'], superself)
                elif name=='tag':
                    self.currElem.tags[attrs['k']] = attrs['v']
                elif name=='nd':
                    self.currElem.nds.append( attrs['ref'] )
                
            @classmethod
            def endElement(self,name):
                if name=='node':
                    nodes[self.currElem.id] = self.currElem
                elif name=='way':
                    ways[self.currElem.id] = self.currElem
                
            @classmethod
            def characters(self, chars):
                pass

        xml.sax.parse(filename_or_stream, OSMHandler)
        
        self.nodes = nodes
        self.ways = ways
        #"""   
        #count times each node is used
        node_histogram = dict.fromkeys( self.nodes.keys(), 0 )
        for way in self.ways.values():
            if len(way.nds) < 2:       #if a way has only one node, delete it out of the osm collection
                del self.ways[way.id]
            else:
                for node in way.nds:
                    node_histogram[node] += 1
        
        #use that histogram to split all ways, replacing the member set of ways
        new_ways = {}
        for id, way in self.ways.items():
            split_ways = way.split(node_histogram)
            for split_way in split_ways:
                new_ways[split_way.id] = split_way
        self.ways = new_ways
        #"""



class netHandler():   
    def __init__(self, osmpath=None, path=None, only_roads=True, linha_reta=False):   
        self.linha_reta=linha_reta
        if osmpath is not None:
            self.read_osm(osmpath, only_roads)
        if path is not None:
            self.read(path)
    
    def download_osm(self,left,bottom,right,top,highway_cat=CAT):
        """
        Downloads OSM street (only highway-tagged) Data using a BBOX, 
        plus a specification of highway tag values to use

        Parameters
        ----------
        left,bottom,right,top : BBOX of left,bottom,right,top coordinates in WGS84
        highway_cat : highway tag values to use, separated by pipes (|), for instance 'motorway|trunk|primary'

        Returns
        ----------
        stream object with osm xml data

        """

        #Return a filehandle to the downloaded data."""
        from urllib import urlopen
        #fp = urlopen( "http://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f"%(left,bottom,right,top) )
        #fp = urlopen( "http://www.overpass-api.de/api/xapi?way[highway=*][bbox=%f,%f,%f,%f]"%(left,bottom,right,top) )
        #print("trying to download osm data from "+str(left),str(bottom),str(right),str(top)+" with highways of categories"+highway_cat)
        try:    
            #print("downloading osm data from "+str(left),str(bottom),str(right),str(top)+" with highways of categories"+highway_cat)
            fp = urlopen( "http://www.overpass-api.de/api/xapi?way[highway=%s][bbox=%f,%f,%f,%f]"%(highway_cat,left,bottom,right,top) )
            #slooww only ways,and in ways only "highways" (i.e. roads)
            #fp = urlopen( "http://open.mapquestapi.com/xapi/api/0.6/way[highway=*][bbox=%f,%f,%f,%f]"%(left,bottom,right,top) )
            #return fp
            self.read_osm(fp)       
        except:
            print("osm data download unsuccessful")

    

    def read_osm(self, filename_or_stream, only_roads=True):
        """Read graph in OSM format from file specified by name or by stream object.

        Parameters
        ----------
        filename_or_stream : filename or stream object

        Returns
        -------
        G : Graph

        Examples
        --------
        >>> G=nx.read_osm(nx.download_osm(-122.33,47.60,-122.31,47.61))
        >>> plot([G.node[n]['data'].lat for n in G], [G.node[n]['data'].lon for n in G], ',')

        """
        osm = OSM(filename_or_stream)
        G = networkx.DiGraph()
    
        for w in osm.ways.values():
            if only_roads and 'highway' not in w.tags:
                continue
            if not "name" in  w.tags.keys():
                w.tags['name']="Sem Nome"
            G.add_path(w.nds, id=w.id, highway = w.tags['highway'], street= w.tags['name'])#{str(k): type(v) for k,v in w.tags.items()})
            
            if 'oneway' not in w.tags and  w.tags['highway'] != 'motorway':
                G.add_path(reversed(w.nds), id= '-' + str(w.id), highway = w.tags['highway'], street= w.tags['name'])

            elif w.tags['oneway'] != 'yes' and w.tags['oneway'] != '-1' and  w.tags['highway'] != 'motorway':
                G.add_path(reversed(w.nds), id=w.id, highway = w.tags['highway'], street= w.tags['name'])
            
        for n_id in G.nodes():
            n = osm.nodes[n_id]
            G.node[n_id].update(dict(lon=n.lon,lat=n.lat))
            
        self.G = G
        self.osm=osm
        self.original=deepcopy(self.G.nodes())
     
    def getPart(self, name):
        node=self.G.node[name]       
        return [float(node['lon']), float(node['lat'])]       
        
    def getCloserNodes(self, name):   
        '''Returns the two node names for a given name that are in the same edge and closer'''
    
        nodes=sorted(list(self.G.nodes()), key=lambda u: self.getLength(u,name))
        lenghs=[]
        for n1 in nodes[1:]:
            if n1 in self.original:
                break
        p3=self.getPart(name)                              
        p1=self.getPart(n1)       
      #  plotNode(n1)
        for n2 in self.G.neighbors(n1):    
            if not n2 in self.original:
                continue
            p2=self.getPart(n2)
            x,y=interLinePoint(p1, p2, p3)                      
            if is_between(p1,[x,y],p2):
                lenghs.append([np.linalg.norm(np.array([x,y])-np.array(p3))*DISTANCE_CONVERT, n1, n2, [x, y]])
            #plotNode(n2)    
                   
        lenghs.sort(key=lambda x: x[0])   
        if len(lenghs)>0 and lenghs[0][0]<TOLERANCE:
            n1=lenghs[0][1]
            n2=lenghs[0][2]
            x, y=lenghs[0][3]
            #plotNode(n1)
            #plotNode(n2)
            #print("Found inline point: ",x,",",y, "nodes:  ",n1," ",n2, " dist: ")                                
            
        else:       
            n2=nodes[2]
            x, y=self.getPart(name)
            #print("FAILED TO GET POINT ON HIGHWAY!!!")
            
        return n1, n2, x, y

    
    def addNode(self, coordinate, name):
        ''' Adds node in existing closest edge to the given lon and lat''' 
        lon,lat=coordinate
        self.G.add_node(name)        
        self.G.node[name].update(dict(lon=lon,lat=lat))
        c1, c2, lon, lat=self.getCloserNodes(name)    
        self.G.add_path([c1, name, c2], id=name)        
        self.G.add_path([c2, name, c1], id=name)               
        self.G.node[name].update(dict(lon=lon,lat=lat))                                             
        return name

    def getParts(self, shortest_path):
        parts=[]
        for i in shortest_path:
            node=self.G.node[i]
            parts.append([float(node['lon']),float(node['lat'])])         
        return parts
    
        
    def get_dist(self):
        d=[]   
        for i, p in enumerate(self.parts[:-1]):  
            z,j,p1=project(p)  
            z,j,p2=project(self.parts[i+1])
            dist=np.linalg.norm(np.array(p1)-np.array(p2))
            d.append(dist)
        # #print(dist*11319.490793)        
        return sum(d)

    def getLength(self, u, v, d=None):
        n1 = self.G.nodes[u]
        n2 = self.G.nodes[v]
        try:
            p1 = np.array([float(n1["lon"]), float(n1["lat"])])
            p2 = np.array([float(n2["lon"]), float(n2["lat"])])
            return np.linalg.norm(p2-p1)*DISTANCE_CONVERT
        except ValueError as e:
            #o que fazer quando o aluno ainda não foi georeferenciado?
            #Mostrar erro, ou coloar um valor bem alto já que isso é usaod em outras funções além de zoneamento
            return 100000
 
    def shortest_path(self, source, target):
        if not self.linha_reta:
            path=networkx.dijkstra_path(self.G, source=source, target=target, weight=lambda u,v,d: self.getLength(u,v,d))
            if path:
                parts=self.getParts(path)       
                self.parts=parts
                self.path=path
                return parts, self.get_dist()
            else:
                return False
        else:
            self.parts=parts=[[self.G.node[source]["lon"], self.G.node[source]["lat"]],
                    [self.G.node[target]["lon"], self.G.node[target]["lat"]]]
            return parts, self.get_dist()

            
    def save(self, path):
        networkx.write_gpickle(self.G, path)
    
    def read(self, path):
        self.G=networkx.read_gpickle(path)
        
    def save_shp(self, filepath):
        '''WRITE SHAPEFILE   '''
        w = shapefile.Writer(filepath, shapefile.POLYLINE)
        w.line([self.parts])
        w.field('FIRST_FLD','C','40')
        w.field('SECOND_FLD','C','40')
        w.record(FIRST_FLD='First', SECOND_FLD='Line')
        w.close()
    
    def save_kml(self, filepath, color='ff0000ff'):
        kml=simplekml.Kml()
        ls = kml.newlinestring(name="Caminho")
        ls.style.labelstyle.color=color
        for row in self.parts:
            ls.coords.addcoordinates([(row[0],row[1])]) #<-- IMPORTANT! Longitude first, Latitude second.            
        kml.save(filepath);
   
    def save_geojson(self, filepath, color='blue'):
        features = []
        ls=LineString(self.parts)
        features.append(Feature(geometry=ls, properties={"country": "Brazil", "color": color, 'distance': str(self.get_dist())}))

       # feature_collection = FeatureCollection(features)
        with open(filepath, 'w') as f:
            dump(features[0], f)
        return filepath
          
def test(filepath, ptA, ptB):
    net=netHandler(osmpath=filepath)        
    parts, dist = net.shortest_path(source=net.addNode(ptA, "aluno"), target=net.addNode(ptB, "escola"))
    #print("DIST: ", dist)
   