# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 12:07:24 2019

@author: Ignacio Paricio
"""

# from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import random
import time
import os

'''
Ideas:
1 - Find a way to determine when boats are sunk (e.g. create new class Boat with attribute is_sunk) //Done
2a - Function to place boats randomly //Done
2b - Smart boat placement //Done
3 - Implementing an AI: how does it play without a board? same type of board but not shown?
4 - Turn-based features
5 - Add text/console explaining latest events (e.g. AI fires at (x,y) / Destroyer sank!)
6 - Animations and timing of events (e.g. squares change color gradually)
7 - User to define how many boats
8 - User to define size of board
9 - User to place boats
'''


class Square(QWidget):
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    #ohno = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        super(Square, self).__init__(*args, **kwargs)
        self.setFixedSize(QSize(30, 30))
        self.x = x
        self.y = y
        self.has_boat = False
        self.boat = None
        self.is_hit = False
        self.is_sunk = False
        self.is_own = None

    def paintEvent(self, event):
        """
        Paints square depending on whether it has_boat, is_hit, is_sunk and is_own
            -> Unexplored: Gray in both boards
            -> Own boats: Green in own board
            -> Own or enemy boat hit: Red in both boards
            -> Own or enemy boat sunk: Dark red in both boards
            -> Explored and water: Blue in both boards
        """

        if self.has_boat:
            if self.is_hit:
                if self.is_sunk:
                    inner, outer = QColor('#820808'), QColor('#5e0606')  # sunk
                elif not self.is_sunk:
                    inner, outer = QColor('#ff0000'), QColor('#bd0000')  # hit but not sunk
            elif not self.is_hit:
                if self.is_own:
                    inner, outer = QColor('#019424'), QColor('#006e1a')  # own boat
                elif not self.is_own:
                    inner, outer = Qt.lightGray, Qt.gray,  # unexplored
        elif not self.has_boat:
            if self.is_hit:
                inner, outer = QColor('#00bfff'), QColor('##008bba')  # water
            elif not self.is_hit:
                inner, outer = Qt.lightGray, Qt.gray,  # unexplored

        # p is a QPainter widget class; performs low-level painting on widgets
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # inside of rectangle
        r = event.rect()
        p.fillRect(r, QBrush(inner))
        # outside of rectangle
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

    def hit(self):
        self.is_hit = True
        if self.has_boat:
            self.boat.update()
            for sq in self.boat.squares:
                sq.update()
        self.update()

    def place_boat(self):
        self.has_boat = True

    def reset(self):
        self.has_boat = False
        self.is_hit = False
        self.is_sunk = False
        self.update()

    def click(self):
        if not self.is_hit:
            self.hit()
        self.clicked.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_own:
            self.click()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.b_size = 10

        w = QWidget()
        hb = QHBoxLayout()

        # define own board
        vb_own = QVBoxLayout()
        l_own = QLabel()
        l_own.setText('Own board')
        vb_own.addWidget(l_own)

        self.own_grid = QGridLayout()
        self.own_grid.setSpacing(3)
        vb_own.addLayout(self.own_grid)

        # define enemy board
        vb_enemy = QVBoxLayout()
        l_enemy = QLabel()
        l_enemy.setText('Enemy board')
        vb_enemy.addWidget(l_enemy)

        self.enemy_grid = QGridLayout()
        self.enemy_grid.setSpacing(3)
        vb_enemy.addLayout(self.enemy_grid)

        # merge into layout
        v_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        hb.addLayout(vb_own)
        hb.addItem(v_spacer)
        hb.addLayout(vb_enemy)
        w.setLayout(hb)
        self.setCentralWidget(w)

        self.init_map()
        #self.reset_map()

        self.show()

    def init_map(self):
        # Add positions to the map
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                sq = Square(x, y)
                sq.is_own = True
                self.own_grid.addWidget(sq, y, x)

                sq = Square(x, y)
                sq.is_own = False
                self.enemy_grid.addWidget(sq, y, x)

    def reset_map(self):
        # Clear both boards
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                self.reset_square(self.own_grid, y, x)
                self.reset_square(self.enemy_grid, y, x)

    def reset_square(self, grid, x, y):
        sq = grid.itemAtPosition(y, x).widget()
        sq.reset()


class Boat(object):
    def __init__(self, squares, size):
        self.squares = squares
        self.size = size
        self.is_sunk = False

    def update(self):
        self.is_sunk = True
        for sq in self.squares:
            if not sq.is_hit:
                self.is_sunk = False
        if self.is_sunk:
            for sq in self.squares:
                sq.is_sunk = True




class Player(object):
    pass


class BattleshipRunner(object):
    pass


def set_board(grid, boat_lst):
    '''
    Places all boats on the board, either randomly or through user input

    Args:
        boats: dict, keys are boat size and values # of boats of that type
        random: if True, board is set randomly
    '''
    for boat_size in boat_lst:
        for i in range(boat_lst[boat_size]):  # iterate through number of boats of that size
            if random:
                place_boat_randomly(grid, boat_size)
            else:
                pass

def place_boat_randomly(grid, boat_size, smart = True):
    '''
    Places boat randomly by brute force. If smart, boats are never adjacent

    Args:
        boat_size: int, length of the boat to be placed
    '''
    toggle_or = {'H': 'V', 'V': 'H'}

    # brute force method to place boats randomly in valid position
    squares = None
    while not squares:
        x = random.randint(0, window.b_size)
        y = random.randint(0, window.b_size)
        top_left = (x, y)
        ors = ['V', 'H']
        orientation = random.choice(ors)

        squares = get_squares(grid, boat_size, top_left, orientation)
        if smart and squares is not None and has_adjacent_boat(grid, squares):
            squares = None

        if not squares:  # try alternative orientation before new random attempt
            squares = get_squares(grid, boat_size, top_left, toggle_or[orientation])
        if smart and squares is not None and has_adjacent_boat(grid, squares):
            squares = None

    # place boat in squares
    new_boat = Boat(squares, boat_size)
    for sq in squares:
        sq.has_boat = True
        sq.boat = new_boat


def get_squares(grid, boat_size, top_left, orientation):
    '''
    Returns potential squares for an unplaced boat given its size, top-left position and orientation
    If square doesn't exist on board or if any square already has a boat it returns None

    Args:
        boat_size: int, length of the boat to be placed
        top_left: tuple, top-left coordinates of boat being place
        orientation: str, 'V' or 'H'

    Returns:
        coords: list of tuples, each of which contains x and y coordinates
        of each square as integers
    '''

    x = top_left[0]
    y = top_left[1]

    squares = []
    coords = []
    try:
        for i in range(boat_size):
            if orientation == 'V':
                sq = grid.itemAtPosition(y, x + i).widget()
            else:
                sq = grid.itemAtPosition(y + i, x).widget()
            if sq.has_boat:
                return None
            squares.append(sq)
        return squares
    except:
        return None

def has_adjacent_boat(grid, squares):
    adj_list = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for sq in squares:
        for y in range(10): #fix
            for x in range(10):
                # locate square in grid
                try:
                    if sq == grid.itemAtPosition(y, x).widget():
                        coord = (x, y)

                        # built list of tuples with adjacent coords by adding tuples element wise
                        adj_coords = [tuple(map(sum, zip(coord, adj))) for adj in adj_list]
                        for adj_coord in adj_coords:
                            # handles error of non-existent square if on board edge
                            try:
                                i = adj_coord[0]
                                j = adj_coord[1]
                                adj_sq = grid.itemAtPosition(j, i).widget()
                                if adj_sq.has_boat:
                                    return True
                            except:
                                pass
                except:
                    pass
    return False

# dictionary where keys are boat size and values # of boats of that size
boat_lst = {2: 1, 3: 2, 4: 1, 5: 1}

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    set_board(window.own_grid, boat_lst)
    set_board(window.enemy_grid, boat_lst)
    app.exec_()
    print('done')
