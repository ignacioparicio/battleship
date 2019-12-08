# -*- coding: utf-8 -*-
"""
Implements a game of battleship.

Created on Mon Nov 11 13:47:48 2019

@author: Ignacio Paricio
"""


# TODO:
# Implementation:
#    1 - Come up with better parallel runner
#   2 - Use decorators for getters/setters
#
# Big milestones:
#   1 - Improve AI, consider reinforcement learning
#   2 - Superpowers (e.g. nuke, burst)
#   3 - Deploy as app
#   4 - PvP over internet
#
# Possible cool analyses:
#   1 - Density heat map for position of random boats (visualize boundary conditions)
#   2 - Stats on AI battles
#   3 - Calibrating superpowers for a balanced game

from typing import Dict, List, Tuple
import unicodedata
import random


class BattleshipBoard:
    """Implements a Battleship Board."""

    def __init__(self, board_width: int, board_height: int, boats: Dict):
        """
        Instantiates the battleship board.
        Args:
            board_width: number of horizontal tiles.
            board_height: number of vertical tiles.
            boats: dictionary where keys are boat size and values # of boats.
        """
        self.board_width = board_width
        self.board_height = board_height
        self.boats = boats
        self.board_spacing = 3

        # Define symbols for own and enemy boards when using CLI
        self.symbols_own = {
            "boat": unicodedata.lookup("WHITE DIAMOND"),
            "boat_hit": unicodedata.lookup("BLACK DIAMOND"),
            "water": unicodedata.lookup("Crossing lanes"),
            "water_hit": unicodedata.lookup("Medium white circle"),
        }

        self.symbols_enemy = {
            "boat": unicodedata.lookup("Crossing lanes"),
            "boat_hit": unicodedata.lookup("Medium black circle"),
            "water": unicodedata.lookup("Crossing lanes"),
            "water_hit": unicodedata.lookup("Medium white circle"),
        }

        # Initialize squares in board
        self.squares = []
        for i in range(self.board_height):
            row = []
            for j in range(self.board_width):
                row.append(Square(i, j))
            self.squares.append(row)

    def print_as_enemy(self):
        """Prints an enemy board in CLI."""
        print(self.printer(self.symbols_enemy))

    def print_as_own(self):
        """Prints own board in CLI."""
        print(self.printer(self.symbols_own))

    def printer(self, symbols: Dict) -> str:
        """Returns a string containing a generic battleship board."""
        # Add column numbering on first row
        sep = (self.board_spacing + 1) * " "
        board = sep.join([str(x) for x in range(self.board_width)]) + "\n"
        # Add left indent for first row
        board = (self.board_spacing + 1) * " " + board

        for i, _ in enumerate(self.squares):
            # Number the rows
            board += (str(i)) + (self.board_spacing + 1 - len(str(i))) * " "
            for j in range(self.board_width):  # Add tile symbols to board
                sq = self.get_square(i, j)
                sq.set_symbol(symbols)
                board += sq.symbol + self.board_spacing * " "
            board += "\n"
        return board

    def get_square(self, row, col):
        """Returns a square given its coordinates."""
        return self.squares[row][col]

    def set_board(self, random: bool = True):
        """
        Places all boats on the board, either randomly or following user input.

        Args:
            random: if True, board is set randomly
        """
        for boat_size, count in self.boats.items():
            for _ in range(count):
                if random:
                    self.place_boat_randomly(boat_size)
                else:
                    self.place_boat(boat_size)
        print(self)

    def place_boat(self, boat_size: int):
        """
        Takes input from user to place boat, checks validity of location and,
        if valid, places the boat in the desired coordinates.

        Args:
            boat_size: length of the boat to be placed.
        """

        # Get user input
        print(f"Placing boat of size {boat_size}")
        orientation = input("V to place boat vertically, H horizontally\n")
        top_left = input("Top-left coordinates of boat as x, y\n").split(",")
        top_left = tuple([int(x) for x in top_left])

        # Transform user input into potential boat coordinates
        coords = self.get_coordinates(boat_size, top_left, orientation)

        if self.is_valid_position(coords):
            self.boat_to_squares(coords)
        else:
            print("Boat doesn't fit in indicated location!")
            print(f"Indicated boat coordinates were {coords}")
            print("Please try using different coordinates")
            self.place_boat(boat_size)
        print(self)

    def place_boat_randomly(self, boat_size: int, smart: bool = True):
        """
        Places boat randomly by brute force.

        Args:
            boat_size: length of the boat to be placed.
            smart: if True, boats will not be placed adjacent to one another.
        """
        is_valid = False
        toggle_or = {"H": "V", "V": "H"}

        # Brute force method to place boats randomly in valid position
        while not is_valid:
            x = random.randint(0, self.board_height)
            y = random.randint(0, self.board_width)
            top_left = (x, y)
            ors = ["V", "H"]
            orientation = random.choice(ors)

            coords = self.get_coordinates(boat_size, top_left, orientation)
            is_valid = self.is_valid_position(coords)

            if smart:
                is_valid = is_valid and not self.has_adjacent_boat(coords)

            # Try alternative orientation before new random attempt
            if not is_valid:
                coords = self.get_coordinates(
                    boat_size, top_left, toggle_or[orientation]
                )
                is_valid = self.is_valid_position(coords)

                # If smart, no adjacent boats as additional condition
                if smart:
                    is_valid = is_valid and not self.has_adjacent_boat(coords)

        self.boat_to_squares(coords)

    def has_adjacent_boat(self, coords: List[Tuple[int]]) -> bool:
        """
        Determines whether a boat would have another adjacent boat.

        Args:
            coords: coordinates of each tile occupied by the boat.

        Returns:
            True if any square has an adjacent boat
        """
        # Deltas to adjacent
        adj_list = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for coord in coords:
            # Build list of tuples with adjacent coords by adding tuples element wise
            adj_coords = [tuple(map(sum, zip(coord, a))) for a in adj_list]
            for adj_coord in adj_coords:
                # Handles error of non-existent square if on board edge
                try:
                    adj_sq = self.get_square(*adj_coord)
                    if adj_sq.has_boat:
                        return True
                except IndexError:
                    pass
        return False

    @staticmethod
    def get_coordinates(
        boat_size: int, top_left: Tuple[int], orientation: str
    ) -> List[Tuple[int]]:
        """
        Gets coordinates of a boat given its size, top-left position and orientation.

        Args:
            boat_size: length of the boat to be placed.
            top_left: top-left coordinates of boat being place.
            orientation: 'V' for vertical, 'H' for horizontal.

        Returns:
            coords: coordinates of each tile occupied by the boat.
        """
        coords = [top_left]
        x = top_left[0]
        y = top_left[1]
        for i in range(boat_size - 1):
            if orientation == "V":
                coord = (x + i + 1, y)
            else:
                coord = (x, y + i + 1)
            coords.append(coord)
        return coords

    def is_valid_position(self, coords: List[Tuple[int]]) -> bool:
        """
        Checks whether input coords are valid to place a boat.

        Args:
            coords: coordinates of each tile occupied by the boat.

        Returns:
            Whether coordinates are valid.
        """
        try:
            squares = [self.get_square(*coord) for coord in coords]
            for sq in squares:
                if sq.has_boat:
                    return False
            return True
        except IndexError:
            return False

    def boat_to_squares(self, coords: List[Tuple[int]]):
        """
        Adds boat coordinates to battleship board.

        Args:
            coords: coordinates of each tile occupied by the boat.
        """
        for coord in coords:
            sq = self.get_square(*coord)
            sq.place_boat()

    def fire(self, x: int, y: int) -> bool:
        """
        Hits a square. Assumes valid boat coordinates passed to function.

        Args:
            x: x-coordinate to hit.
            y: y-coordinate to hit.

        Returns:
            True if it hit a boat, False if it missed.
        """

        # Handle potential out-of-the-board fire
        try:
            sq = self.get_square(x, y)
        except IndexError:
            print("That's out of range!")
            return False

        if not sq.is_hit:
            sq.hit_square()
            return sq.has_boat

        else:
            print("You already hit that square!")


class Square:
    """A single square in a battleship board."""

    def __init__(self, row: int, column: int):
        """Instantiates a square within a battleship board."""
        self.row = row
        self.column = column
        self.has_boat = False
        self.is_hit = False
        self.symbol = None

    def place_boat(self):
        """Sets boat on square."""
        self.has_boat = True

    def get_symbol(self):
        """Returns own symbol."""
        return self.symbol

    def set_symbol(self, symbols: Dict):
        """
        Sets square symbol depending on whether square has_boat and is_hit.

        Args:
            symbols: mapping from square state to symbol, where keys are:
                - 'water':      to be displayed if not has_boat and not is_hit
                - 'water_hit':  to be displayed if not has_boat and is_hit
                - 'boat':       to be displayed if has_boat and not is_hit
                - 'boat_hit':   to be displayed if has_boat and is_hit
        """
        if not self.has_boat and not self.is_hit:
            self.symbol = symbols["water"]
        elif not self.has_boat and self.is_hit:
            self.symbol = symbols["water_hit"]
        elif self.has_boat and not self.is_hit:
            self.symbol = symbols["boat"]
        elif self.has_boat and self.is_hit:
            self.symbol = symbols["boat_hit"]

    def hit_square(self):
        """Marks a square as hit."""
        self.is_hit = True

    def __str__(self):
        return f"({self.row}, {self.column})"


class BattleshipRunner:
    """Runs a game of Battleship."""

    def __init__(self, player1, player2, to_start, board_width, board_height, boats):
        """Instantiates a battleship runner."""
        self.players = [player1, player2]
        self.to_start = to_start
        self.board_width = board_width
        self.board_heights = board_height
        self.boats = boats

        self.other_player = {player1: player2, player2: player1}
        self.is_over = False
        self.timer = None  # TODO: potential feature to implement

        # Give each player their own board
        for p in self.players:
            p.set_own_board(BattleshipBoard(board_width, board_height, boats))
            p.place_boats()

        # Give each player a reference to enemy's board
        player1.set_enemy_board(player2.get_own_board())
        player2.set_enemy_board(player1.get_own_board())

        # Give turn to a player
        for p in self.players:
            if p == to_start:
                p.give_turn()

        self.run_game()

    def run_game(self):
        """Governs the game of battleship."""
        print(f"Battleship game is on!! {(self.to_start)} fires first!")
        while not self.is_over:
            for p in self.players:
                if p.get_turn():
                    if p.get_nature() == "HUMAN":
                        self.print_boards(p)
                    p.move()

                    if not p.get_turn():
                        print(f"Miss! {p} losses turn!")
                        self.other_player[p].give_turn()
                    else:
                        print(f"\nBoat hit! {p} to fire again!")

    @staticmethod
    def print_boards(player):
        """Shows both own and enemy board in CLI."""
        print(f"{player} to fire")
        print(f"\n{player} - View of enemy board")
        print(50 * "-")
        player.get_enemy_board().print_as_enemy()
        print(f"\n{player} - View of own board")
        print(50 * "-")
        player.get_own_board().print_as_own()

    def is_game_over(self):
        """Determines whether the game has finished."""
        pass
        # TODO: define


class Player:
    """Defines a player of the game Battleship."""

    def __init__(self, name, nature, random_placement):
        """Instantiates a player."""
        self.name = name
        self.nature = nature
        self.random_placement = random_placement
        self.own_board = None
        self.enemy_board = None
        self.my_turn = False

    def move(self):
        """Prompts player to act."""
        if self.nature == "HUMAN":
            target = input("Coordinates to fire as x, y\n").split(",")
            target = tuple([int(x) for x in target])
        elif self.nature == "AI":
            x = random.randint(0, self.enemy_board.board_height)
            y = random.randint(0, self.enemy_board.board_width)
            print(f"{self} fires at {x}, {y}")
            target = (x, y)

        hit_boat = self.enemy_board.fire(*target)
        if not hit_boat:
            self.my_turn = False

    def place_boats(self):
        """Places boats on the board."""
        self.own_board.set_board(self.random_placement)

    def give_turn(self):
        """Assigns turn to the player."""
        self.my_turn = True

    def get_turn(self):
        """Retrieves whether it's a player's turn."""
        return self.my_turn

    def set_own_board(self, board):
        """Sets player's board."""
        self.own_board = board

    def get_own_board(self):
        """Retrieves player's board."""
        return self.own_board

    def set_enemy_board(self, board):
        """Sets enemy's board."""
        self.enemy_board = board

    def get_enemy_board(self):
        """Retrieves enemy's board."""
        return self.enemy_board

    def get_nature(self):
        """Retrieves player's nature, human or AI."""
        return self.nature

    def __str__(self):
        return f"{self.name} ({self.nature})"


if __name__ == "__main__":
    # natures available are HUMAN and AI
    player1 = Player(name="player1", nature="AI", random_placement=True)
    player2 = Player(name="player2", nature="HUMAN", random_placement=True)

    to_start = player1  # Can be either player or 'random'

    board_width = 10
    board_height = 10

    boats = {2: 1, 3: 2, 4: 1, 5: 1}  # Keys are boat size and values # of boats

    game = BattleshipRunner(
        player1, player2, to_start, board_width, board_height, boats
    )
