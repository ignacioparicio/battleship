"""Simple, rule-based AIs to that play the game of battleship."""
from typing import Tuple, List
import random
import PyQt5
import numpy as np


random.seed(1)
np.random.seed(1)

# TODO:
#   - Implement AIs as classes
#   - Explore potential bias of hard AI not to find at edges


def fool_AI(enemy_array: np.array, board_size: int) -> Tuple[int]:
    """
    Fool AI that shoots at random at unexplored tiles.

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        board_size: size of the board, assumed to be square.

    Returns:
        2D coordinates of recommended tile to fire at.

    """
    while True:  # Find tile via brute force
        target = (random.randint(0, board_size - 1), random.randint(0, board_size - 1))
        if enemy_array[target] == "x":
            return target


def standard_AI(enemy_array: np.array, board_size: int) -> Tuple[int]:
    """
    AI that follows the lead on hit boats until they are sunk. If no hit boats it fires
    randomly.

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        board_size: size of the board, assumed to be square.

    Returns:
        2D coordinates of recommended tile to fire at.

    """
    hit = find_hit_squares(enemy_array)
    if hit is not None:
        return infer_next_hit(enemy_array, hit, board_size)
    else:
        return fool_AI(enemy_array, board_size)


def hard_AI(enemy_array, board_size, max_size):
    """
    AI that follows the lead on hit boats until they are sunk. If no hit boats it
    fires optimizing spacing to already-shot tiles.

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        board_size: size of the board, assumed to be square.
        max_size: size of biggest boat not sunk in enemy array.

    Returns:
        2D coordinates of recommended tile to fire at.

    """
    hit = find_hit_squares(enemy_array)
    if hit is not None:
        return infer_next_hit(enemy_array, hit, board_size)

    else:
        return find_optimal_spaced_tile(enemy_array, board_size, max_size)


def find_optimal_spaced_tile(enemy_array, board_size, max_size):
    """
    Finds potential tile to fire at in the absence of hit squares. It tries to find
    maximum spacing between to tiles to find the biggest alive boat. It also has some
    bias to favor shooting at the border.

    Args:
        enemy_array: a numpy array representing a board.
        board_size: size of the board, assumed to be square.
        max_size: size of biggest boat not sunk in enemy array.

    Returns:
        2D coordinates of recommended tile to fire at.
    """
    target = None

    # Optimize spacing to find biggest boat not sunk, decrease if not possible
    for space in range(max_size, 0, -1):
        for i in np.random.permutation(board_size):
            for j in np.random.permutation(board_size):

                if enemy_array[(i, j)] != "x":
                    continue

                # Get spacing to unexplored tile in all directions
                up = get_spacing((i, j), np.array([-1, 0]), enemy_array, board_size)
                down = get_spacing((i, j), np.array([1, 0]), enemy_array, board_size)
                right = get_spacing((i, j), np.array([0, 1]), enemy_array, board_size)
                left = get_spacing((i, j), np.array([0, -1]), enemy_array, board_size)

                # Primary condition, biggest boat size // 2 unexplored in all directions
                if all(x >= space // 2 for x in [up, down, right, left]):
                    return i, j

                # Secondary condition, relax first condition if close to a border
                if i in (0, board_size - 1):  # Top or bottom row
                    if right >= max_size - 1 and left >= max_size - 1:
                        return (i, j)

                if j in (0, board_size - 1):  # Left- or right-most column
                    if up >= max_size - 1 and down >= max_size - 1:
                        return (i, j)
        if target:
            return target


def get_spacing(
    coord: Tuple[int], direction: Tuple[int], array: np.array, board_size: int
) -> int:
    """Finds spacing (in # of tiles in a certain direction) to an unexplored tile."""
    x_count = 0
    curs = np.array(coord) + direction
    while all(0 <= i < board_size for i in curs) and array[tuple(curs)] == "x":
        x_count += 1
        curs += direction
    return x_count


def find_hit_squares(array: np.array) -> np.array:
    """Returns array of size equal to board size, marking hit squares."""
    if np.argwhere(array == "h").size == 0:
        return None
    return np.argwhere(array == "h")


def infer_next_hit(enemy_array: np.array, hit: bool, board_size: int) -> Tuple[int]:
    """
    Infers positioning of a boat (vertical/horizontal), and fires at an adjacent
    tile where the gap to an adjacent, unexplored tile is the biggest.
    """
    targets = {}
    for delta in get_deltas_to_targets(hit):
        target, unexplored_gap = get_unexplored_gap(enemy_array, hit, delta, board_size)
        targets[unexplored_gap] = target
    return targets[max(targets.keys())]


def get_deltas_to_targets(hit: np.array) -> List[Tuple[int]]:
    """
    Returns a list of potential targets to fire at. If a single tile is hit, it returns
    all adjacent tiles. If more than one tile is hit, it infers whether the boat is
    placed horizontally or vertically.

    Args:
        hit: array of size equal to board size, marking hit squares.

    Returns:
        Potential targets to fire at.
    """
    if len(hit) == 1:
        return [(1, 0), (-1, 0), (0, 1), (0, -1)]
    else:
        if hit[0][0] == hit[1][0]:  # Boat in vertical position
            return [(0, 1), (0, -1)]
        else:  # Boat in horizontal position
            return [(1, 0), (-1, 0)]


def get_unexplored_gap(
    enemy_array: np.array, hit: np.array, delta: Tuple[int], board_size: int
) -> Tuple[Tuple[int], int]:
    """
    Returns potentially coordinates to fire at, at its associated unexplored gap.
    Unexplored gap is an int counting the number of tiles of the potential target to
    the next unexplored tile. This is something worth maximizing.
    """
    unexplored_gap = 0
    first_blank = True
    target = None
    curs = hit[0].copy()  # Put a cursor arbitrarily on first hit square

    while is_on_board(curs, board_size):  # Ensure staying within board boundaries
        # Update target based on first position of curs that is a potential blank
        tile = enemy_array[curs[0]][curs[1]]

        if enemy_array[curs[0]][curs[1]] == "x":  # Unexplored tile
            if first_blank:
                target = curs.copy()
                first_blank = False
            unexplored_gap += 1

        elif tile in ("w", "s"):  # Already explored, either water or sunk
            return target, unexplored_gap

        curs[0] += delta[0]
        curs[1] += delta[1]

    return target, unexplored_gap


def is_on_board(coord: Tuple[int], board_size: int) -> bool:
    """Returns whether a coordinate is on the battleship board."""
    return coord[0] in range(0, board_size) and coord[1] in range(0, board_size)


def board_to_array(board: PyQt5.QtWidgets.QGridLayout, board_size: int) -> np.array:
    """
    Transforms a GUI board into a numpy array.

    Args:
        board: pyqt grid layout representing the GUI battleship board.
        board_size: size of the board, assumed to be square.

    Returns:
        Array equivalent to the GUI board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
    """
    array = np.empty((board_size, board_size), dtype="str")
    for i in range(board_size):
        for j in range(board_size):
            sq = board.itemAtPosition(i, j).widget()
            if not sq.is_hit:
                array[i, j] = "x"
            elif not sq.has_boat:
                array[i, j] = "w"
            elif not sq.is_sunk:
                array[i, j] = "h"
            else:
                array[i, j] = "s"
    return array
