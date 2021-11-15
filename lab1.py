#Author :- Rishabh Manish Sahlot

import sys
from PIL import Image
import heapq
import math

colorToTerrain = {(248, 148, 18): 'Open land', (255, 192, 0): 'Rough meadow', (255, 255, 255): 'Easy movement forest',
                  (2, 208, 60): 'Slow run forest', (2, 136, 40): 'Walk forest', (5, 73, 24): 'Impassible vegetation',
                  (0, 0, 255): 'Lake/Swamp/Marsh', (71, 51, 3): 'Paved Road', (0, 0, 0): 'Foot Path',
                  (205, 0, 101): 'Out of bounds'}


terrainToFrictionCoefficient = {'Open land': 0.85, 'Rough meadow': 0.45, 'Easy movement forest': 0.75, 'Slow run forest': 0.75,
                                'Walk forest': 0.75, 'Impassible vegetation': 0.00000001, 'Lake/Swamp/Marsh': 0.128, 'Paved Road': 1.2,
                                'Foot Path': 0.8, 'Out of bounds': 0.00000001}
terrainToDistanceCalculation = {'Open land': 6.381, 'Rough meadow': 6.381, 'Easy movement forest': 7.312, 'Slow run forest': 8.224,
                                'Walk forest': 10.107, 'Impassible vegetation': 6.381, 'Lake/Swamp/Marsh': 6.381, 'Paved Road': 6.381,
                                'Foot Path': 6.381, 'Out of bounds': 6.381}


class Node:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.parent = None
        self.gn = 100000000000
        self.hn = 0
        self.distance = 0
        self.current_terrain = ""
        self.current_speed = -1

    def __lt__(self, other):
        return self.gn + self.hn < other.gn + self.hn

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Orienteering:

    def __init__(self, terrain, elevation, stopPoints, season):
        self.terrain = terrain
        self.elevation = elevation
        self.stopPoints = stopPoints
        self.season = season
        self.pixelWidth = 10.29
        self.pixelLength = 7.55
        self.currentGoal = None
        self.expanded = dict()  # Nodes whose children you have already expanded
        self.to_visit = []  # Stores x, y & z component
        self.cost = {}
        self.current_speed = -1
        self.current_terrain = -1
        self.muddy_edges_water_level = {}  # height of the muddy water above water level in case of Spring Season

    def scan_for_lake_edges(self):
        edges = set()
        for x in range(395):
            for y in range(500):
                if self.terrain[x, y] == (0, 0, 255):  # is water
                    is_edge = False
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if (not(i == 0 and j == 0)) and (0 <= x + i < 395 and 0 <= y + j < 500):
                                if self.terrain[x+i, y+j] != (0, 0, 255):  # is not water
                                    is_edge = True
                    if is_edge:
                        edges.add((x, y))
        return edges

    def add_ice_edge_ring(self, edgePoints):
        edges = set()
        for (x, y) in edgePoints:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (not (i == 0 and j == 0)) and (0 <= x + i < 395 and 0 <= y + j < 500):
                        if self.terrain[x + i, y + j] == (0, 0, 255):  # is water
                            edges.add((x+i, y+j))
        return edges

    def add_mud_edge_ring(self, edgePoints):
        edges = set()
        for (x, y, z) in edgePoints:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if (not (i == 0 and j == 0)) and (0 <= x + i < 395 and 0 <= y + j < 500):
                        if self.elevation[x+i][y+j]-z <= 1 and self.terrain[x + i, y + j] not in [(0, 0, 255), (101, 67, 33), (205, 0, 101)]:  # is not water, muddy water or out of bounds
                            edges.add((x+i, y+j, z))
                            self.muddy_edges_water_level[(x+i, y+j)] = self.elevation[x+i][y+j]-z
        return edges

    def color_edges(self, edgePoints, to_color):
        for edge in edgePoints:
            self.terrain[(edge[0], edge[1])] = to_color

    def add_ice_path(self, ice_color):
        edge_points = self.scan_for_lake_edges()
        self.color_edges(edge_points, ice_color)
        for i in range(6):
            edge_points = self.add_ice_edge_ring(edge_points)
            self.color_edges(edge_points, ice_color)

    def add_muddy_path(self, mud_color):
        temp = self.scan_for_lake_edges()
        edge_points = []
        for edge in temp:
            edge_points.append((edge[0], edge[1], self.elevation[edge[0]][edge[1]]))
        for i in range(15):
            edge_points = self.add_mud_edge_ring(edge_points)
            if len(edge_points) == 0:
                break
            self.color_edges(edge_points, mud_color)

    def make_seasonal_changes(self):
        if self.season == 'fall':
            for path in terrainToFrictionCoefficient.keys():
                if path.__contains__("forest"):
                    terrainToFrictionCoefficient[path] *= 0.5
        elif self.season == 'winter':
            colorToTerrain[(173, 216, 230)] = "Ice Path"
            terrainToFrictionCoefficient["Ice Path"] = 0.25
            terrainToDistanceCalculation["Ice Path"] = 6.381
            self.add_ice_path((173, 216, 230))

        elif self.season == 'spring':
            colorToTerrain[(101, 67, 33)] = "Muddy Water"
            terrainToFrictionCoefficient["Muddy Water"] = 0.128  # (Same as any other water body)
            terrainToDistanceCalculation["Muddy Water"] = 6.381
            self.add_muddy_path((101, 67, 33))

    def calculate_distance(self, pos1, pos2):  # gives manhattan distance
        return (terrainToDistanceCalculation[pos2.current_terrain] ** 2 * (abs(pos1.x - pos2.x) ** 2 + abs(pos1.y - pos2.y) ** 2) + abs(pos1.z - pos2.z) ** 2) ** 0.5

    def calculate_cost(self, pos1, pos2):
        terrain1 = pos1.current_terrain
        terrain2 = self.terrain[pos2.x, pos2.y]
        mew = -1
        if terrain2 == "Muddy Water" and self.muddy_edges_water_level[(pos2.x, pos2.y)] < 1:
            mew = 0.128*self.muddy_edges_water_level[(pos2.x, pos2.y)]+0.8*self.muddy_edges_water_level[(pos2.x,pos2.y)]
        else:
            mew = terrainToFrictionCoefficient[colorToTerrain[terrain2]]
        new_speed = 5.783*mew
        distance = self.calculate_distance(pos1, pos2)
        pos2.distance = pos1.distance+distance
        theta = math.atan2(pos2.z - pos1.z, distance)
        cot_inverse_mew = math.atan2(1, mew)
        radian_converter = 180 / math.pi
        if (math.cos(theta) >= 0 and cot_inverse_mew > 35 * radian_converter - theta) or (math.cos(theta) < 0 and cot_inverse_mew < 100 * radian_converter - theta):
            if terrain1 == terrain2:  # same terrain
                new_speed = math.sqrt(pos1.current_speed ** 2 - 2 * distance * 10 * (math.cos(35) / math.sin(35 - theta)- (mew * math.cos(theta) - math.sin(theta))))
            else:  # change in terrain
                new_speed = math.sqrt(new_speed ** 2 - 2 * distance * 10 * (math.cos(35) / math.sin(35 - theta) - (mew * math.cos(theta) - math.sin(theta))))
        pos2.current_speed = new_speed*math.cos(theta)
        # print(distance/pos2.current_speed)
        return distance/pos2.current_speed

    def calculate_heuristic(self, currentPosition):
        speed = 5.783*terrainToFrictionCoefficient[colorToTerrain[self.terrain[currentPosition.x, currentPosition.y]]]
        return self.calculate_distance(currentPosition, self.currentGoal)/speed  # using manhattan distance here

    def color_stop_points(self):
        for e in self.stopPoints:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if 0 <= e[1] + i < 395 and 0 <= e[1] + j < 500:
                        self.terrain[e[0]+i, e[1]+j] = (75, 0, 130)

    def start_navigation_a_star(self):
        x, y = self.stopPoints[0][0], self.stopPoints[0][1]
        final_path = [(x, y)]
        final_path_length = 0
        self.currentGoal = Node(x, y, self.elevation[x][y])
        self.currentGoal.current_terrain = colorToTerrain[self.terrain[x, y]]
        self.currentGoal.current_speed = 2.59*terrainToFrictionCoefficient[self.currentGoal.current_terrain]
        for i in range(1, len(self.stopPoints)):
            start = self.currentGoal
            x, y = self.stopPoints[i][0], self.stopPoints[i][1]
            self.currentGoal = Node(x, y, self.elevation[x][y])
            self.currentGoal.current_terrain = colorToTerrain[self.terrain[x,y]]
            self.currentGoal.current_speed = 5.783*terrainToFrictionCoefficient[self.currentGoal.current_terrain]
            start.gn, start.hn = 0, self.calculate_heuristic(start)
            path,path_length = self.reach_next_goal(start)
            path.reverse()
            final_path += path
            final_path_length += path_length
            self.to_visit = []
            self.expanded = {}

        for e in final_path:
            self.terrain[e] = (255, 0, 0)
        return final_path_length

    def generate_and_add_children(self, parent):
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (not(i == 0 and j == 0)) and (0 <= parent.x + i < 395 and 0 <= parent.y + j < 500):
                    child = Node(parent.x+i, parent.y+j, self.elevation[parent.x+i][parent.y+j])
                    child.parent = parent
                    child.current_terrain = colorToTerrain[self.terrain[parent.x+i, parent.y+j]]
                    child.current_speed = 2.59 * terrainToFrictionCoefficient[child.current_terrain]
                    if (child.x, child.y) not in self.expanded.keys():
                        child.gn = parent.gn + self.calculate_cost(parent, child)
                        child.hn = self.calculate_heuristic(child)
                        pos = -1
                        try:
                            pos = self.to_visit.index(child)
                        except ValueError:
                            pos = -1
                        if pos == -1:
                            self.to_visit.append(child)
                        elif self.to_visit[pos].gn > child.gn:
                            self.to_visit.pop(pos)
                            self.to_visit.append(child)
                            heapq.heapify(self.to_visit)

    def reach_next_goal(self, start):
        self.to_visit = [start]
        heapq.heapify(self.to_visit)
        path_length = 0
        while len(self.to_visit) > 0:
            cur = heapq.heappop(self.to_visit)
            self.expanded[(cur.x, cur.y)] = cur.parent
            if cur.x == self.currentGoal.x and cur.y == self.currentGoal.y:
                path_length = cur.distance
                break
            self.generate_and_add_children(cur)
        cur = self.currentGoal
        path = []
        while (cur.x,cur.y) != (start.x, start.y):
            path.append((cur.x, cur.y))
            cur = self.expanded[(cur.x, cur.y)]
        return path, path_length


def main():
    px = Image.open(sys.argv[1]).convert("RGB")
    terrain = px.load()
    lines = open(sys.argv[2]).readlines()
    temp = []
    for line in lines:
        temp.append(list(map(float, line.split()[:-5])))
    elevation = []
    for i in range(395):
        t=[]
        for j in range(500):
            t.append(temp[j][i])
        elevation.append(t)

    lines = open(sys.argv[3]).readlines()
    stop_points = []
    for line in lines:
        stop_points.append(tuple(map(int, line.split())))
    season = sys.argv[4]
    marathon = Orienteering(terrain, elevation, stop_points, season)
    marathon.make_seasonal_changes()
    path_length = marathon.start_navigation_a_star()
    marathon.color_stop_points()
    print("Distance Travelled:", path_length," meters calculated using length,width and height and some extra length in some cases")
    print("Red line is the path and the violet points on it are check points")
    if marathon.season == "Winter":
        print("Light blue is for the ice that has been frozen")
    if marathon.season == "Spring":
        print("Dark brown is for the muddy water ")
    px.save(sys.argv[5])


if __name__ == '__main__':
    main()
