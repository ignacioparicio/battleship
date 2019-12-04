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
import battleship_ai

random.seed(1)

# //Done Find a way to determine when boats are sunk (e.g. create new class Boat with attribute is_sunk)
# //Done Function to place boats randomly
# //Done Smart boat placement
# //Done Turn-based features:
#   -> implement self.is_over based of player.lost_game based on all boats.is_sunk
#   -> give a board and boats to player
#   -> linked to previous: give boat to board?
#   -> functionality to give turn to player/AI
#   -> fix bug AI stops shooting
#   -> functionality to know if last fire was a hit
# //Done Implementing an AI: how does it play without a board? same type of board but not shown? (sol: using sq.click())
# //Done functionality to delay AI actions to see a game AI vs AI 'live'
# //Done: AI algorithms - function/class outside, store board as array and create algorithm f(len_boats_left, squares hit)
# TODO: Fix AI bug
# TODO: way to test power of AIs over big sample size
# TODO: Add text/console explaining latest events (e.g. AI fires at (x,y) / Destroyer sank!)
# TODO: Animations and timing of events (e.g. squares change color gradually)
# TODO: User to define how many boats/size of board/placement of boats


class Square(QWidget):
    def __init__(self, x, y, *args, **kwargs):
        super(Square, self).__init__(*args, **kwargs)
        self.setFixedSize(QSize(30, 30))
        self.x = x
        self.y = y
        self.has_boat = False
        self.boat = None
        self.is_hit = False
        self.is_sunk = False
        self.is_p1 = None
        self.is_clickable = False

    def paintEvent(self, event):
        """
        paintEvent is called through update(); it repaints the squares of both own and enemy board
        
        Returns: None, but paints the squares as:
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
                if self.is_p1:
                    inner, outer = QColor('#019424'), QColor('#006e1a')  # own boat
                elif not self.is_p1:
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
        # if there is a boat on the square, update status of boat and then all squares attached to boat
        if self.has_boat:
            self.boat.update()
            for sq in self.boat.squares:
                sq.update()
        else:
            reverse_turns()
        self.update()

    def place_boat(self):
        self.has_boat = True

    def reset(self):
        self.has_boat = False
        self.is_hit = False
        self.is_sunk = False
        self.update()  # trigget a paintEvent

    def click(self):
        if self.is_clickable:
            if not self.is_hit:
                self.hit()
            # self.clicked.emit()

    def mouseReleaseEvent(self, event):
        """
        Standard PyQt function triggered when mouse released over square

        """
        # not used by AI
        if event.button() == Qt.LeftButton and not self.is_p1:
            self.click()


class MainWindow(QMainWindow):
    def __init__(self, b_size, boat_dict, players, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.b_size = b_size
        self.boat_dict = boat_dict
        self.players = players
        self.runthread = None

        self.setWindowTitle('Battleship')
        self.setWindowIcon(QIcon('icon5.png'))

        w = QWidget()
        hb = QHBoxLayout()

        # define player1 board
        vb_p1 = QVBoxLayout()
        title_p1 = QLabel()
        title_p1.setText(f'Board of {players[0].get_name()} - {players[0].get_nature()}')
        vb_p1.addWidget(title_p1)
        players[0].set_title_label(title_p1)

        self.board_p1 = QGridLayout()
        self.board_p1.setSpacing(3)
        vb_p1.addLayout(self.board_p1)

        # define player2 board
        vb_p2 = QVBoxLayout()
        title_p2 = QLabel()
        title_p2.setText(f'Board of {players[1].get_name()} - {players[1].get_nature()}')
        vb_p2.addWidget(title_p2)
        players[1].set_title_label(title_p2)

        self.board_p2 = QGridLayout()
        self.board_p2.setSpacing(3)
        vb_p2.addLayout(self.board_p2)

        # merge into layout
        v_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        hb.addLayout(vb_p1)
        hb.addItem(v_spacer)
        hb.addLayout(vb_p2)
        w.setLayout(hb)
        self.setCentralWidget(w)

        # initialize boards and give them to players
        self.init_board()
        self.players[0].set_board(self.board_p1)
        self.players[1].set_board(self.board_p2)

        # prepare for first turn and set boats
        for player in players:
            squares = get_all_board_squares(player.get_board())
            # if it is my turn, my squares are not clickable, and vice versa
            for sq in squares:
                sq.is_clickable = not player.get_turn()
            self.set_board(player)

        self.show()

        self.run_game()
        # self.reset_map()

    def run_game(self):
        self.runthread = RunGameThread()
        self.runthread.start()

    def init_board(self):
        """
        Adds squares both to boards of player1 and player2

        """
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                sq = Square(x, y)
                sq.is_p1 = True
                self.board_p1.addWidget(sq, y, x)

                sq = Square(x, y)
                sq.is_p1 = False
                self.board_p2.addWidget(sq, y, x)

    def reset_map(self):
        # Clear both boards
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                self.reset_square(self.board_p1, y, x)
                self.reset_square(self.board_p2, y, x)

    @staticmethod
    def reset_square(board, y, x):
        sq = board.itemAtPosition(y, x).widget()
        sq.reset()

    def set_board(self, player, random=True):
        """
        Places all boats on the board and gives them to the player

        Args:
            player: player for which the board is to be set

        '"""

        for boat_size in self.boat_dict:
            n_boats = self.boat_dict[boat_size]
            for i in range(n_boats):
                if random:
                    boat = self.place_boat_randomly(player.get_board(), boat_size)
                    player.add_boat(boat)
                    for sq in boat.squares:
                        sq.has_boat = True
                        sq.boat = boat
                else:  # to define how to place boats manually
                    pass

    def place_boat_randomly(self, board, boat_size, smart=True):
        """
        Places boat randomly by brute force. If smart, boats are never adjacent

        Args:
            board: PyQt grid on which boats are placed
            boat_size: int, number of squares taken by boat
            smart: bool, if True, boats are not placed adjacent to each other

        Returns:
            boat: Boat class instance, containing the squares to which to be placed
        """

        toggle_or = {'H': 'V', 'V': 'H'}

        squares = None
        while not squares:
            x = random.randint(0, self.b_size)
            y = random.randint(0, self.b_size)
            top_left = (x, y)
            ors = ['V', 'H']
            orientation = random.choice(ors)

            squares = self.get_squares(board, boat_size, top_left, orientation)
            if smart and squares is not None and self.has_adjacent_boat(board, squares):
                squares = None

            # try alternative orientation before new random attempt
            if not squares:
                squares = self.get_squares(board, boat_size, top_left, toggle_or[orientation])
            if smart and squares is not None and self.has_adjacent_boat(board, squares):
                squares = None

        return Boat(squares, boat_size)

    @staticmethod
    def get_squares(board, boat_size, top_left, orientation):
        """
        Returns potential squares for an unplaced boat given its size, top-left position and orientation
        If square doesn't exist on board or if any square already has a boat it returns None

        Args:
            board: PyQt grid on which boats are placed
            boat_size: int, number of squares taken by boat
            top_left: tuple, top-left coordinates of boat being place
            orientation: str, 'V' or 'H'

        Returns:
            List of squares if boat can be placed legally using given parameters
            None otherwise

        """

        x = top_left[0]
        y = top_left[1]

        squares = []
        try:
            # get squares where boat would be placed
            for i in range(boat_size):
                if orientation == 'V':
                    sq = board.itemAtPosition(y, x + i).widget()
                else:
                    sq = board.itemAtPosition(y + i, x).widget()
                if sq.has_boat:
                    return None
                squares.append(sq)
            return squares
        except:  # kicks in if a square is off the board
            return None

    @staticmethod
    def has_adjacent_boat(board, squares):
        """
        Args:
            board: PyQt grid on which boats are placed
            squares: list of potential squares for a boat to be placed; note - boat must not be actually placed yet

        Returns:
            True if, for any square of boat being placed, there would be an adjacent boat
            False otherwise

        """
        adj_list = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for sq in squares:
            coord = (sq.x, sq.y)

            # built list of tuples with adjacent squares to coord by adding tuples element wise
            adj_coords = [tuple(map(sum, zip(coord, adj))) for adj in adj_list]

            for adj_coord in adj_coords:
                # handles error of non-existent square if on board edge
                i = adj_coord[0]
                j = adj_coord[1]
                try:
                    adj_sq = board.itemAtPosition(j, i).widget()
                    if adj_sq.has_boat:
                        return True
                except:
                    pass
        return False


class Boat(object):
    """
    A boat is simply a collection of squares

    """

    def __init__(self, squares, size):
        self.squares = squares
        self.size = size
        self.is_sunk = False

    def update(self):
        """
        Updates all squares belonging to the boat in the event of being sunk

        """
        self.is_sunk = all([sq.is_hit for sq in self.squares])

        # if sunk, pass property to all boat squares
        if self.is_sunk:
            for sq in self.squares:
                sq.is_sunk = True

    def get_squares(self):
        return self.squares


class Player(object):
    """
    Defines a player of the game Battleship
    """

    def __init__(self, name, nature, AI_mode='fool', turn=False):
        self.name = name
        self.my_turn = turn
        self.nature = nature
        self.board = None
        self.boats = []
        self.title_label = None
        self.AI_mode = AI_mode

    def AI_move(self):

        # additional check before moving that game is still on
        if is_game_over():
            return None

        # if many modes, consider putting into dictionary
        enemy_array = battleship_ai.board_to_array(other_player[self].get_board(), b_size)
        if self.AI_mode == 'fool':
            target = battleship_ai.fool_AI(enemy_array, b_size, self.max_boat_size())
        elif self.AI_mode == 'standard':
            target = battleship_ai.standard_AI(enemy_array, b_size, self.max_boat_size())
        elif self.AI_mode == 'hard':
            target = battleship_ai.hard_AI(enemy_array, b_size, self.max_boat_size())

        sq = other_player[self].get_board().itemAtPosition(*target).widget()
        sq.click()

    def set_turn(self, turn):
        self.my_turn = turn

    def get_turn(self):
        return self.my_turn

    def get_name(self):
        return self.name

    def get_nature(self):
        return self.nature

    def set_board(self, board):
        self.board = board

    def get_board(self):
        return self.board

    def add_boat(self, boat):
        assert isinstance(boat, Boat)
        self.boats.append(boat)

    def set_title_label(self, title_label):
        self.title_label = title_label

    def has_lost(self):
        return all([boat.is_sunk for boat in self.boats])

    def max_boat_size(self):
        boat_sizes = [[k] * boat_dict[k] for k in boat_dict.keys()]
        boat_sizes_flat = [item for sublist in boat_sizes for item in sublist]
        for boat in self.boats:
            if boat.is_sunk:
                boat_sizes_flat.remove(boat.size)

        if len(boat_sizes_flat) > 0:
            return max(boat_sizes_flat)



def reverse_turns():
    """
    Reverses the turns of both players by:
        - Setting the player.turn attribute to the opposite
        - Making all squares of player who lost turn clickable, and vice versa
        - Updating text labels on each player's board

    """
    for player in players:
        player.set_turn(not player.get_turn())  # reverse turn
        squares = get_all_board_squares(player.get_board())  # get player's squares

        # if it is my turn, my square are not clickable, and vice versa
        for sq in squares:
            sq.is_clickable = not player.get_turn()

        # update player's label on the board
        text = (f'Board of {player.get_name()} - {player.get_nature()}')
        if player.get_turn():
            text = text + ' - Your turn!'
        player.title_label.setText(text)


def get_all_board_squares(board):
    """

    Args:
        board: PyQt grid on which boats are placed

    Returns:
        squares: list, colletion of PyQt widgets acting as squares of the board

    """
    squares = []
    for x in range(0, b_size):
        for y in range(0, b_size):
            squares.append(board.itemAtPosition(y, x).widget())
    return squares


def is_game_over():
    for player in players:
        if player.has_lost():
            text = f'Game is over! {other_player[player].get_name()} won the game!!!'
            player.title_label.setText(text)
            other_player[player].title_label.setText(text)
            return True
    return False


class RunGameThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def run(self):
        while not is_game_over():
            for p in players:
                if p.get_nature() == 'AI':
                    time.sleep(delay_AI)
                    p.AI_move()


# dictionary where keys are boat size and values # of boats of that size
boat_dict = {2: 1, 3: 2, 4: 1, 5: 1}
b_size = 10
delay_AI = 0.05 # delay in seconds before AI move

player1 = Player(name='AI hard', nature='AI', AI_mode='hard', turn=True)
player2 = Player(name='AI hard', nature='AI', AI_mode='hard', turn=False)
players = [player1, player2]
other_player = {players[0]: players[1], players[1]: players[0]}

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow(b_size, boat_dict, players)
    app.exec_()
