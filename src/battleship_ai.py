"""Simple, rule-based AIs to play battleship against."""

import numpy as np
import random

random.seed(1)
np.random.seed(1)


def fool_AI(enemy_array, b_size):
    """
    Fool AI that shoots at random at unexplored tiles

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        b_size: int, size of the board, assumed to be square
        max_size: size of biggest boat not sunk in enemy array

    Returns:
        target: tuple of ints, 2D coordinates of recommended tile to fire at

    """
    while True:
        target = (random.randint(0, b_size - 1), random.randint(0, b_size - 1))
        if enemy_array[target] == "x":
            return target


def standard_AI(enemy_array, b_size, max_size):
    """
    AI that follows the lead on hit boats until they are sunk
    If no hit boats it fires randomly

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        b_size: int, size of the board, assumed to be square
        max_size: size of biggest boat not sunk in enemy array

    Returns:
        target: tuple of ints, 2D coordinates of recommended tile to fire at

    """
    hit = find_hit_squares(enemy_array)
    if hit is not None:
        return longest_x(
            enemy_array, hit, b_size
        )  # hit squares list of coorindate(s) with boats hit but not sunk
        # emptiest adjacent gives adjacent coord to square(s) with longest distance to unexplored tile. It adjusts for orientation of the boat known

    else:
        while True:
            target = (random.randint(0, b_size - 1), random.randint(0, b_size - 1))
            if enemy_array[target] == "x":
                return target


def hard_AI(enemy_array, b_size, max_size):
    """
    AI that follows the lead on hit boats until they are sunk
    If no hit boats it fires optimizing to discover biggest boat left with minimum shots

    Args:
        enemy_array: a numpy array representing a board, where:
            'x' are unexplored tiles
            'w' are explored water tiles
            'h' are explored hit tiles
            's' are explored sunk tiles
        b_size: int, size of the board, assumed to be square
        max_size: size of biggest boat not sunk in enemy array

    Returns:
        target: tuple of ints, 2D coordinates of recommended tile to fire at

    """
    hit = find_hit_squares(enemy_array)
    if hit is not None:
        return longest_x(enemy_array, hit, b_size)

    else:
        return optimal_spacing(enemy_array, b_size, max_size)


def optimal_spacing(enemy_array, b_size, max_size):
    """
    Args:
        enemy_array:
        b_size:
        max_size:

    Returns:

    """
    target = None
    for s in range(
        max_size, 0, -1
    ):  # try to optimize spacing for biggest boat, decrease if not possible
        for i in np.random.permutation(b_size):
            for j in np.random.permutation(b_size):

                if enemy_array[(i, j)] != "x":
                    continue

                u = spacing((i, j), np.array([-1, 0]), enemy_array, b_size)  # up
                d = spacing((i, j), np.array([1, 0]), enemy_array, b_size)  # down
                r = spacing((i, j), np.array([0, 1]), enemy_array, b_size)  # left
                l = spacing((i, j), np.array([0, -1]), enemy_array, b_size)  # right

                # primary condition, size of biggest boat // 2 unexplored on every direction
                if all(x >= s // 2 for x in [u, d, r, l]):
                    return i, j

                # secondary condition, border
                if i == 0 or i == b_size - 1:  # top or bottom row
                    if r >= max_size - 1 and l >= max_size - 1:
                        return (i, j)

                if j == 0 or j == b_size - 1:  # left- or right-most column
                    if u >= max_size - 1 and d >= max_size - 1:
                        return (i, j)

        # if a secondary condition was met for boat size s, return associated target instead of reducing s
        if target:
            return target


def spacing(coord, v, array, b_size):
    x_count = 0
    curs = np.array(coord) + v
    while all(0 <= i < b_size for i in curs) and array[tuple(curs)] == "x":
        x_count += 1
        curs += v
    return x_count


def find_hit_squares(array):
    if np.argwhere(array == "h").size == 0:
        return None
    return np.argwhere(array == "h")


def longest_x(array, hit, b_size):
    targets = {}
    for v in possible_vectors(hit):
        target, x_count = target_and_x(array, hit, v, b_size)
        targets[x_count] = target
    return targets[max(targets.keys())]


def possible_vectors(hit):
    if len(hit) == 1:
        return [(1, 0), (-1, 0), (0, 1), (0, -1)]
    else:
        if (
            hit[0][0] == hit[1][0]
        ):  # x coordinates of two hit squares are the same, so boat is horizontal
            return [(0, 1), (0, -1)]
        else:  # boat is horizontal
            return [(1, 0), (-1, 0)]


def target_and_x(array, hit, v, b_size):
    x_count = 0
    first_blank = True
    target = None
    curs = hit[0].copy()  # put cursor arbitrarily on first hit square

    # ensure not going out of bounds
    while curs[0] in range(0, b_size) and curs[1] in range(0, b_size):
        # update target based on first position of curs that is a potential blank
        tile = array[curs[0]][curs[1]]

        if array[curs[0]][curs[1]] == "x":
            if first_blank:
                target = curs.copy()
                first_blank = False
            x_count += 1
        elif tile == "w" or tile == "s":
            return target, x_count
        curs[0] += v[0]
        curs[1] += v[1]

    return target, x_count


def board_to_array(board, b_size):
    array = np.empty((b_size, b_size), dtype="str")
    for i in range(b_size):
        for j in range(b_size):
            sq = board.itemAtPosition(i, j).widget()
            if not sq.is_hit:  # not hit
                array[i, j] = "x"
            elif not sq.has_boat:  # is hit and doesn't have boat
                array[i, j] = "w"
            elif not sq.is_sunk:  # is hit and has a boat that is not sunk
                array[i, j] = "h"
            else:
                array[i, j] = "s"  # is hit and has a boat that is sunk
    return array
