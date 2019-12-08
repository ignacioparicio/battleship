"""
Game of battleship with a dedicated GUI.

Created on Sun Nov 17 12:07:24 2019

@author: Ignacio Paricio
"""
# pylint: disable=no-name-in-module
# pylint: disable=invalid-name
from typing import Tuple, List
import random
import time
from PyQt5.QtWidgets import (
    QWidget,
    QSizePolicy,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSpacerItem,
    QLabel,
    QApplication,
)
from PyQt5.QtGui import QPaintEvent, QMouseEvent, QColor, QPainter, QBrush, QPen, QIcon
from PyQt5.QtCore import QSize, Qt, QThread

import battleship_ai

random.seed(1)

# TODO:
#   1 - Use decorators for getters/setters
#   2 - Find a way to run multiple instances of the game to collect AI data
#   3 - Add text/console explaining latest events (e.g. AI fires at (x,y) / Boat sunk!)
#   4 - Animations and timing of events (e.g. squares change color gradually)
#   5 - User to define how many boats/size of board/placement of boats


class Square(QWidget):
    """
    Main building block of battleship board. It contains info about its own
    coordinates, and whether it has a boat, has been hit, or has been sunk.
    """

    def __init__(self, x: int, y: int, *args, **kwargs):
        """Instantiates a square."""
        super().__init__(*args, **kwargs)
        self.setFixedSize(QSize(30, 30))
        self.x = x
        self.y = y
        self.has_boat = False
        self.boat = None
        self.is_hit = False
        self.is_sunk = False
        self.is_p1 = None
        self.is_clickable = False

    def paintEvent(self, event: QPaintEvent):
        """
        Repaints the squares of both own and enemy board. Called through update().
            - Unexplored: Gray in both boards
            - Own boats: Green in own board
            - Own or enemy boat hit: Red in both boards
            - Own or enemy boat sunk: Dark red in both boards
            - Explored and water: Blue in both boards
        """

        if self.has_boat:
            if self.is_hit:
                if self.is_sunk:
                    inner, outer = QColor("#820808"), QColor("#5e0606")  # Sunk
                elif not self.is_sunk:
                    inner, outer = (
                        QColor("#ff0000"),
                        QColor("#bd0000"),
                    )  # Hit but not sunk
            elif not self.is_hit:
                if self.is_p1:
                    inner, outer = QColor("#019424"), QColor("#006e1a")  # Own boat
                elif not self.is_p1:
                    inner, outer = (Qt.lightGray, Qt.gray)  # Unexplored
        elif not self.has_boat:
            if self.is_hit:
                inner, outer = QColor("#00bfff"), QColor("##008bba")  # Water
            elif not self.is_hit:
                inner, outer = (Qt.lightGray, Qt.gray)  # Unexplored

        # painter is a QPainter widget class, performs low-level painting on widgets
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Paint inside of rectangle
        rectangle = event.rect()
        painter.fillRect(rectangle, QBrush(inner))
        # Paint border of rectangle
        pen = QPen(outer)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(rectangle)

    def hit(self):
        """Update a square when it gets hit."""
        self.is_hit = True
        if self.has_boat:
            self.boat.update()
            # Update status of all boat tiles in case it was sunk
            for sq in self.boat.squares:
                sq.update()
        else:
            reverse_turns()
        self.update()

    def place_boat(self):
        """Sets a boat on a square."""
        self.has_boat = True

    def reset(self):
        """Sets square to default."""
        self.has_boat = False
        self.is_hit = False
        self.is_sunk = False
        self.update()  # Triggers a paintEvent

    def click(self):
        """Hits a square via user click."""
        if self.is_clickable:
            if not self.is_hit:
                self.hit()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Standard PyQt function triggered when mouse released over square."""
        if event.button() == Qt.LeftButton and not self.is_p1:
            self.click()


class MainWindow(QMainWindow):
    """Window where the game of battleship is played."""

    def __init__(self, board_size, boats_dict, players, *args, **kwargs):
        """Instantiates a window object."""
        super().__init__(*args, **kwargs)
        self.board_size = board_size
        self.boats_dict = boats_dict
        self.players = players
        self.runthread = None

        self.setWindowTitle("Battleship")
        self.setWindowIcon(QIcon("../resources/icons/icon1.png"))

        w = QWidget()
        hb = QHBoxLayout()

        # Define board of player1 ("own" board)
        vb_p1 = QVBoxLayout()
        title_p1 = QLabel()
        title_p1.setText(
            f"Board of {players[0].get_name()} - {players[0].get_nature()}"
        )
        vb_p1.addWidget(title_p1)
        players[0].set_title_label(title_p1)

        self.board_p1 = QGridLayout()
        self.board_p1.setSpacing(3)
        vb_p1.addLayout(self.board_p1)

        # Define player2 board ("enemy" board)
        vb_p2 = QVBoxLayout()
        title_p2 = QLabel()
        title_p2.setText(
            f"Board of {players[1].get_name()} - {players[1].get_nature()}"
        )
        vb_p2.addWidget(title_p2)
        players[1].set_title_label(title_p2)

        self.board_p2 = QGridLayout()
        self.board_p2.setSpacing(3)
        vb_p2.addLayout(self.board_p2)

        # Merge boards in single layout
        v_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        hb.addLayout(vb_p1)
        hb.addItem(v_spacer)
        hb.addLayout(vb_p2)
        w.setLayout(hb)
        self.setCentralWidget(w)

        # Initialize boards and give them to players
        self.init_board()
        self.players[0].set_board(self.board_p1)
        self.players[1].set_board(self.board_p2)

        # Prepare for first turn and set boats
        for player in players:
            squares = get_all_board_squares(player.get_board())
            # If it is my turn, my squares are not clickable, and vice versa
            for sq in squares:
                sq.is_clickable = not player.get_turn()
            self.set_board(player)

        self.show()

        self.run_game()

    def run_game(self):
        """Controls a game of battleship."""
        self.runthread = RunGameThread()
        self.runthread.start()

    def init_board(self):
        """Adds squares both to boards of player1 and player2."""
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                sq = Square(x, y)
                sq.is_p1 = True
                self.board_p1.addWidget(sq, y, x)

                sq = Square(x, y)
                sq.is_p1 = False
                self.board_p2.addWidget(sq, y, x)

    def reset_map(self):
        """Clears boards of both players."""
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                self.reset_square(self.board_p1, y, x)
                self.reset_square(self.board_p2, y, x)

    @staticmethod
    def reset_square(board: QGridLayout, y, x):
        """Sets a square back to its original state."""
        sq = board.itemAtPosition(y, x).widget()
        sq.reset()

    def set_board(self, player: "Player", random_board: bool = True):
        """Places all boats on the board and gives them to a player."""
        for boat_size, n_boats in self.boats_dict.items():
            for _ in range(n_boats):
                if random_board:
                    boat = self.place_boat_randomly(player.get_board(), boat_size)
                    player.add_boat(boat)
                    for sq in boat.squares:
                        sq.has_boat = True
                        sq.boat = boat
                else:  # TODO: implement manual boat positioning
                    pass

    def place_boat_randomly(
        self, board: QGridLayout, boat_size: int, smart=True
    ) -> "Boat":
        """
        Places boat randomly by brute force.

        Args:
            board: PyQt grid on which boats are placed.
            boat_size: number of squares taken by boat.
            smart: if True, boats are not placed adjacent to each other.

        Returns:
            boat: Boat class instance, containing the squares to which to be placed.
        """

        toggle_or = {"H": "V", "V": "H"}

        squares = None
        while not squares:
            x = random.randint(0, self.board_size)
            y = random.randint(0, self.board_size)
            top_left = (x, y)
            ors = ["V", "H"]
            orientation = random.choice(ors)

            squares = self.get_squares(board, boat_size, top_left, orientation)
            if smart and squares is not None and self.has_adjacent_boat(board, squares):
                squares = None

            # Try alternative orientation before new random attempt
            if not squares:
                squares = self.get_squares(
                    board, boat_size, top_left, toggle_or[orientation]
                )
            if smart and squares is not None and self.has_adjacent_boat(board, squares):
                squares = None

        return Boat(squares, boat_size)

    @staticmethod
    def get_squares(
        board: QGridLayout, boat_size: int, top_left: Tuple[int], orientation: str
    ) -> List[Square]:
        """
        Returns potential squares for an unplaced boat given its size, top-left position
        and orientation. If square doesn't exist on board or if any square already
        has a boat, it returns None.

        Args:
            board: PyQt grid on which boats are placed.
            boat_size: number of squares taken by boat.
            top_left: top-left coordinates of boat being place.
            orientation: 'V' for vertical or 'H' for horizontal.

        Returns:
            List of squares if boat can be placed legally using given parameters.
            None otherwise.

        """

        x, y = top_left
        squares = []
        try:
            # Get squares where boat would be placed
            for i in range(boat_size):
                if orientation == "V":
                    sq = board.itemAtPosition(y, x + i).widget()
                else:
                    sq = board.itemAtPosition(y + i, x).widget()
                if sq.has_boat:
                    return None
                squares.append(sq)
            return squares
        except AttributeError:  # Kicks in if a square is off the board
            return None

    @staticmethod
    def has_adjacent_boat(board: QGridLayout, squares: List[Square]) -> bool:
        """
        Determines whether there is an adjacent boat to any squares passed.

        Args:
            board: PyQt grid on which boats are placed.
            squares: list of potential squares for a boat to be placed.

        Returns:
            True if, for any square of boat being placed, there would be an adjacent
            boat, False otherwise.

        """
        adj_deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for sq in squares:
            coord = (sq.x, sq.y)

            # Build list of tuples with adjacent coords by adding tuples element wise
            adj_coords = [tuple(map(sum, zip(coord, adj))) for adj in adj_deltas]

            for adj_coord in adj_coords:
                # Handles error of non-existent square if on board edge
                i, j = adj_coord
                try:
                    adj_sq = board.itemAtPosition(j, i).widget()
                    if adj_sq.has_boat:
                        return True
                except AttributeError:
                    pass
        return False


class Boat:
    """A Battleship boat, represented as a collection of squares."""

    def __init__(self, squares, size):
        """Instantiates a boat."""
        self.squares = squares
        self.size = size
        self.is_sunk = False

    def update(self):
        """Updates all squares belonging to the boat in the event of being sunk."""
        self.is_sunk = all([sq.is_hit for sq in self.squares])
        if self.is_sunk:
            for sq in self.squares:
                sq.is_sunk = True

    def get_squares(self):
        """Retrieves all squares of a boat."""
        return self.squares


class Player:
    """A player playing the game Battleship."""

    def __init__(self, name, nature, AI_mode="fool", to_play=False):
        """Instantiates a player."""
        self.name = name
        self.my_turn = to_play
        self.nature = nature
        self.board = None
        self.boats = []
        self.title_label = None
        self.AI_mode = AI_mode

    def add_other_player(self, other_player):
        """Adds other player to player's 'knowledge'."""
        self.other_player = other_player

    def AI_move(self):
        """A game turn played by an AI."""
        if is_game_over():
            return None

        enemy_array = battleship_ai.board_to_array(
            self.other_player.get_board(), board_size
        )
        if self.AI_mode == "fool":
            target = battleship_ai.fool_AI(enemy_array, board_size)
        elif self.AI_mode == "standard":
            target = battleship_ai.standard_AI(enemy_array, board_size)
        elif self.AI_mode == "hard":
            target = battleship_ai.hard_AI(
                enemy_array, board_size, self.max_boat_size()
            )

        sq = self.other_player.get_board().itemAtPosition(*target).widget()
        sq.click()

    def set_turn(self, to_play: bool):
        """Gives the turn to the player."""
        self.my_turn = to_play

    def get_turn(self):
        """Retrieves whether it is a player's turn."""
        return self.my_turn

    def get_name(self):
        """Retrieves player's name."""
        return self.name

    def get_nature(self):
        """Retrieves player's nature (AI or HUMAN)."""
        return self.nature

    def set_board(self, board: QGridLayout):
        """Gives the player a board."""
        self.board = board

    def get_board(self):
        """Retrieves player's board."""
        return self.board

    def add_boat(self, boat: Boat):
        """Adds a boat to a player."""
        assert isinstance(boat, Boat)
        self.boats.append(boat)

    def set_title_label(self, title_label: str):
        """Gives a player a label, to be displayed in GUI."""
        self.title_label = title_label

    def has_lost(self):
        """Determines whether a player has lost the game."""
        return all([boat.is_sunk for boat in self.boats])

    def max_boat_size(self):
        """Return the max boat size of a player's non-sunk boats."""
        boats = [[boat_size] * n_boats for boat_size, n_boats in boats_dict.items()]
        boats_flat = [item for sublist in boats for item in sublist]
        for boat in self.boats:
            if boat.is_sunk:
                boats_flat.remove(boat.size)

        if len(boats_flat) > 0:
            return max(boats_flat)


def reverse_turns():
    """Reverses the turns of the player to play."""
    for player in players:
        player.set_turn(not player.get_turn())

        squares = get_all_board_squares(player.get_board())  # Get player's squares
        for sq in squares:
            # If it is my turn, my squares are not clickable, and vice versa
            sq.is_clickable = not player.get_turn()

        # Update player's label on the board
        text = f"Board of {player.get_name()} - {player.get_nature()}"
        if player.get_turn():
            text = text + " - Your turn!"
        player.title_label.setText(text)


def get_all_board_squares(board: QGridLayout) -> List[Square]:
    """
    Return all squares of a board.

    Args:
        board: PyQt grid on which boats are placed

    Returns:
        All squares of a board.

    """
    squares = []
    for x in range(0, board_size):
        for y in range(0, board_size):
            squares.append(board.itemAtPosition(y, x).widget())
    return squares


def is_game_over():
    """Determines whether a game has finished."""
    other_player = {players[0]: players[1], players[1]: players[0]}
    for player in players:
        if player.has_lost():
            # sys.exit(app.exec_()) # with this the loop doesn't continue TODO explore
            text = f"Game is over! {other_player[player].get_name()} won the game!!!"
            player.title_label.setText(text)
            other_player[player].title_label.setText(text)
            return True
    return False


class RunGameThread(QThread):
    """Running thread, an instance of it must be active for the game to be playable."""

    def __init__(self):
        """Instantiates the thread."""
        QThread.__init__(self)

    @staticmethod
    def run():
        """Governs the game of battleship."""
        while not is_game_over():
            for player in players:
                if player.get_nature() == "AI":
                    time.sleep(delay_AI)
                    player.AI_move()


if __name__ == "__main__":
    boats_dict = {2: 1, 3: 2, 4: 1, 5: 1}  # Keys are boat size and values # of boats
    board_size = 10
    delay_AI = 0.1  # Delay in seconds before AI move

    # Natures available are HUMAN and AI. AI can be fool, standard, hard
    player1 = Player(name="Ignacio", nature="human", to_play=True)
    player2 = Player(name="AI hard", nature="AI", AI_mode="hard", to_play=False)
    player1.add_other_player(player2)
    player2.add_other_player(player1)
    players = [player1, player2]

    app = QApplication([])
    window = MainWindow(board_size, boats_dict, players)
    app.exec_()
    # app.quit() # TODO: explore how to best quit the app for parallel runs
