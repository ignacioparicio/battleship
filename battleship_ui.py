# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 12:07:24 2019

@author: Ignacio Paricio
"""

#from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import random
import time
import os


'''
Ideas:
1 - Find a way to determine when boats are sunk (e.g. create new class Boat with attribute is_sunk)
2 - Function to place boats randomly
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
    ohno = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        super(Square, self).__init__(*args, **kwargs)
        self.setFixedSize(QSize(30, 30))
        self.x = x
        self.y = y
        self.has_boat = False
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
        self.update()

    def place_boat(self):
        self.has_boat = True

    def reset(self):
        self.has_boat = False
        self.is_hit = False
        self.is_sunk = False
        self.is_own = None
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
        self.b_size, self.n_mines = 10, 10
        
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
        self.reset_map()
        
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
                own = self.own_grid.itemAtPosition(y, x).widget()
                own.reset()
                
                enemy = self.enemy_grid.itemAtPosition(y, x).widget()
                enemy.reset()



if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()