# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 13:47:48 2019

@author: Ignacio Paricio
"""

'''
Short-term Milestones:
    1 - Create board using classes that can be printed //X//
    2 - Allow for representations of boats //X//
    3 - Let user decide where to place boats (and come up with system) //X//
    4 - Functionality to fire at boats //X//
    5 - Random boat placement + smart random boat placement //X//
    6 - Two boards
    7 - Turn-based features
    
Big milestones:
    1 - AI
    2 - Internet
    3 - GUI
    4 - Superpowers
    5 - Deploy
    

Cool analyses:
    1 - Density heat map for position of random boats (is it uniform?)
    2 - AI battles
    3 - Calibrating superpowers    
'''

import unicodedata
import random

class BattleshipBoard(object):
    """ Store a Battleship Board"""
          
    def __init__(self):
        self.board_width = 10
        self.board_height = 10
        # dictionary where keys are boat size and values # of boats
        self.boats = {2:1, 3:2, 4:1, 5:1}
        self.board_spacing = 3
        
        # initialize squares in board
        self.squares = []
        for i in range(self.board_height):
            row = []
            for j in range(self.board_width):
                row.append(Square(i, j, True))
            self.squares.append(row)
   
    def __str__(self):
        """ Return a string representation of this board """
        sep = (self.board_spacing+1)  * ' '
        # column numbering
        board = sep.join([str(x) for x in range(self.board_width)]) + '\n'
        # left indentation
        board = (self.board_spacing + 1) * ' ' + board
        
        for i, row in enumerate(self.squares):
            # row numbering
            board += (str(i)) + (4 - len(str(i))) * ' '
            for j in range(self.board_width):
                # get square and add it's symbol to board
                square = self.get_square(i,j)
                board += square.symbol + self.board_spacing * ' '
            board += '\n'
        return board
    
    def print_as_enemy(self):
        pass #define
    
    def print_as_own(self):
        pass #define
    
    def get_square(self, row, col):
        return self.squares[row][col]
    
    def set_board(self, boats=None, random=True):
        '''
        Places all boats on the board, either randomly or through user input
        
        Args:
            boats: dict, keys are boat size and values # of boats of that type
            random: if True, board is set randomly
        '''
        if  boats is None:
            boats = self.boats
        for boat_size in boats:
            # iterate through number of boats of that size
            for i in range(boats[boat_size]):
                if random:
                    self.place_boat_randomly(boat_size)
                else:
                    self.place_boat(boat_size)
        print(self)
            
    def place_boat(self, boat_size):
        '''
        Takes input from user to place boat, checks validity of location
        and places boat on board if valid
        
        Args:
            boat_size: int, length of the boat to be placed
        '''
        
        # get user input
        print(f'Placing boat of size {boat_size}')
        orientation = input('V to place boat vertically, H horizontally\n')
        top_left = input('Top-left coordinates of boat as x, y\n').split(',')
        top_left = tuple([int(x) for x in top_left])
        
        # transform user input into potential boat coordinates
        coords = self.get_coordinates(boat_size, top_left, orientation)
        
        if self.is_valid_position(coords):
            self.boat_to_squares(coords)
        else:
            print(f"Boat doesn't fit in indicated location!")
            print(f'Indicated boat coordinates were {coords}')
            print('Please try using different coordinates')
            self.place_boat(boat_size)    
        print(self)
        
    def place_boat_randomly(self, boat_size, smart=True):
        '''
        Places boat randomly by brute force. If smart, boats are never adjacent
        
        Args:
            boat_size: int, length of the boat to be placed
        '''
        is_valid = False
        toggle_or={'H':'V', 'V':'H'}
        
        # brute force method to place boats randomly in valid position
        while not is_valid:
            x = random.randint(0, self.board_height)
            y = random.randint(0, self.board_width)
            top_left = (x, y)
            ors = ['V', 'H']
            orientation = random.choice(ors)
            
            coords = self.get_coordinates(boat_size, top_left, orientation)
            is_valid = self.is_valid_position(coords)
            
            # if smart, no adjacent boats as additional condition
            if smart:
                is_valid = is_valid and not self.has_adjacent_boat(coords)
            
            # try alternative orientation before new random attempt
            if not is_valid:
                coords = self.get_coordinates(boat_size, top_left,
                                              toggle_or[orientation])
                is_valid = self.is_valid_position(coords)
                
                # if smart, no adjacent boats as additional condition
                if smart:
                    is_valid = is_valid and not self.has_adjacent_boat(coords)
                    
        self.boat_to_squares(coords)
                
    def has_adjacent_boat(self, coords):
        '''
        Places boat randomly by brute force. If smart, boats are never adjacent
        
        Args:
            coords: list of tuples, each of which contains x and y coordinates
            of each square as integers
        Returns:
            True if any square has an adjacent boat
        '''
        # deltas to adjacent
        adj_list = [(1,0), (-1,0), (0,1), (0,-1)]  
        
        for coord in coords:    
            # built list of tuples with adjacent coords by adding tuples element wise
            adj_coords = [tuple(map(sum, zip(coord, a))) for a in adj_list]
            for adj_coord in adj_coords:
                # handles error of non-existent square if on board edge
                try:
                    adj_sq = self.get_square(*adj_coord)
                    if adj_sq.has_boat:
                        return True
                except:
                    pass
        return False
            
        
    def get_coordinates(self, boat_size, top_left, orientation):
        '''
        Gets coordinates of a boat given its size, top-left position and
        orientation
        
        Args:
            boat_size: int, length of the boat to be placed
            top_left: tuple, top-left coordinates of boat being place
            orientation: str, 'V' or 'H'
            
        Returns:
            coords: list of tuples, each of which contains x and y coordinates
            of each square as integers
        '''      
        coords = [top_left]
        x = top_left[0]
        y = top_left[1]
        for i in range(boat_size - 1):
            if orientation == 'V':
                coord = (x + i + 1, y)
            else:
                coord = (x, y + i + 1)
            coords.append(coord)
        return coords
        
    def is_valid_position(self, coords):
        '''
        Takes input from user to place boat, checks validity of location
        and places boat on board if valid
        
        Args:
            coords: list of tuples, each of which contains x and y coordinates
            of each square as integers
            
        Returns:
            True/False
        '''        
        try:
            squares = [self.get_square(*coord) for coord in coords]
            for sq in squares:
                if sq.has_boat:
                    return False
            return True
        except:
            return False
        
    def boat_to_squares(self, coords):
        '''
        Assumes valid boat coordinates passed to function
        Modifies board to add boat to coordinates
        
        Args:
            coords: list of tuples, each of which contains x and y coordinates
            of each square as integers
        '''
        for coord in coords:
            sq = self.get_square(*coord)
            sq.place_boat()
    
    def fire(self, x, y): 
        try:
            sq = self.get_square(x, y)
        except:
            print("That's out of range!")
        if not sq.is_hit:
            sq.hit_square()
        else:
            print('You already hit that square!')      

class Square(object):
    def __init__(self, row, column, visible = True):
        self.row = row
        self.column = column
        self.has_boat = False
        self.is_hit = False
        self.symbols = {'own_boat': unicodedata.lookup('WHITE DIAMOND'),
           'own_boat_hit': unicodedata.lookup('BLACK DIAMOND'),
           'missed': unicodedata.lookup('Medium white circle'),
           'hit': unicodedata.lookup('Medium black circle'),
           'water': unicodedata.lookup('Crossing lanes')}
        
        ''' move somewhere else
            #own_board incorporates different symbols for boat and boat_hit
            self.own_board_symbols = 
            {'boat': unicodedata.lookup('WHITE DIAMOND'),
             'boat_hit': unicodedata.lookup('BLACK DIAMOND'),
             'water': unicodedata.lookup('Crossing lanes'),
             'water_hit': unicodedata.lookup('Medium white circle')}
            # enemy_board shows boats as water if not hit    
            self.enemy_board_symbols = 
            {'boat': unicodedata.lookup('Crossing lanes'),
             'boat_hit': unicodedata.lookup('Medium black circle'),
             'water': unicodedata.lookup('Crossing lanes'),
             'water_hit': unicodedata.lookup('Medium white circle')}
        '''
        self.symbol = self.symbols['water']
    
    def place_boat(self):
        self.has_boat = True
        self.symbol = self.symbols['own_boat']

    def get_symbol(self):
        return self.symbol
               
    def hit_square(self):
        if self.has_boat:
            self.symbol = self.symbols['hit']
        else:
            self.symbol = self.symbols['missed']
        self.is_hit = True
            
    def __str__(self):
        return f'({self.row}, {self.column})'    

class BattleshipRunner(object):
    ''' Runs a game of Battleship'''
   # def __init__(self,... #define)
   #    self.is_over = False
   #    self.to_move = player1
   #    set_board...
   #    self.timer
   
   
    def run_game(self):
       while not self.is_over:
           self.move(self.to_move)
               
    def move(self, player):
        pass
        # reminder: every time there is a move, two boards must be updated
        # this challenged with idea below
        
    def is_game_over(self):
        pass
        #define
        
class Player(object):
    ''' 
    Defines a player of the game Battleship
    '''
    
    def __init__(self):
        self.own_board = BattleshipBoard()
        self.enemy_board = None # to be set later
        # for enemy_board, simply copy other's board with boats and implement
        # a board function 'hide' that sets everything to water
        
        #  even better, create a subclass of Board (EnemyBoard) that hides
        # all and in addition has the appropriate symbols (e.g. circles for enemy
        # vs diamonds for own)
        
        # easier solution: there are only two boards, but board class has
        # a function to print as own_board and another to print as enemy_board
        # if own_board -> display has_boat, is_hit
        # if enemy_board -> display is_hit only
        # only problem that in the future it might not scale well if multiplayer?
        
       
       

board = BattleshipBoard()
#board.boat_to_squares([(3,4),(4,4)])
board.set_board()


    
