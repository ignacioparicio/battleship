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

class Pos(QWidget):
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    ohno = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        super(Pos, self).__init__(*args, **kwargs)

        self.setFixedSize(QSize(30, 30))

        self.x = x
        self.y = y

    def reset(self):
        self.is_start = False
        self.is_mine = False
        self.adjacent_n = 0

        self.is_revealed = False
        self.is_flagged = False

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        if self.is_revealed:
            color = self.palette().color(QPalette.Background)
            outer, inner = color, color
        else:
            outer, inner = Qt.gray, Qt.lightGray

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_start:
                p.drawPixmap(r, QPixmap(IMG_START))

            elif self.is_mine:
                p.drawPixmap(r, QPixmap(IMG_BOMB))

            elif self.adjacent_n > 0:
                pen = QPen(NUM_COLORS[self.adjacent_n])
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignHCenter | Qt.AlignVCenter, str(self.adjacent_n))

        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(IMG_FLAG))

    def reveal(self):
        self.is_revealed = True
        self.update()

    def click(self):
        if not self.is_revealed:
            self.reveal()
            if self.adjacent_n == 0:
                self.expandable.emit(self.x, self.y)

        self.clicked.emit()

    def mouseReleaseEvent(self, e):
        if (e.button() == Qt.RightButton and not self.is_revealed):
            self.flag()

        elif (e.button() == Qt.LeftButton):
            self.click()

            if self.is_mine:
                self.ohno.emit()

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.b_size, self.n_mines = 10, 10
        
        w = QWidget()
        hb = QHBoxLayout()       
        
#        l = QLabel()
##        l.setPixmap(QPixmap.fromImage(IMG_BOMB))
#        l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
#        hb.addWidget(l)
#
#        l = QLabel()
##        l.setPixmap(QPixmap.fromImage(IMG_CLOCK))
#        l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#        hb.addWidget(l)

        vb = QVBoxLayout()
        vb.addLayout(hb)

        self.grid = QGridLayout()
        self.grid.setSpacing(3)

        vb.addLayout(self.grid)
        w.setLayout(vb)
        self.setCentralWidget(w)

        self.init_map()
        self.reset_map()
        

        self.show()
        
    def init_map(self):
        # Add positions to the map
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                sq = Pos(x, y)
                self.grid.addWidget(sq, y, x)
                # Connect signal to handle expansion.
#                w.clicked.connect(self.trigger_start)
#                w.expandable.connect(self.expand_reveal)
#                w.ohno.connect(self.game_over)
        
        # Place resize on the event queue, giving control back to Qt before.
        QTimer.singleShot(0, lambda: self.resize(1,1))

        
        w = QWidget()
        hb = QHBoxLayout()


    def reset_map(self):
        # Clear all mine positions
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reset()


    

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec_()