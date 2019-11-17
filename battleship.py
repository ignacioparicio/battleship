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
    6 - Two boards //X//
    7 - Turn-based features //X//
    8 - Need boats as a class to notify of sunk ship
    9 - Also coordinates as a class?
    
Big milestones:
    1 - AI
    2 - Internet
    3 - GUI <----- Go for this next!
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
          
    def __init__(self, board_width, board_height, boats):
        self.board_width = board_width
        self.board_height = board_height
        self.boats = boats
        self.board_spacing = 3
        
        # define symbols for own_board
        self.symbols_own = {'boat': unicodedata.lookup('WHITE DIAMOND'),
                            'boat_hit': unicodedata.lookup('BLACK DIAMOND'),
                            'water': unicodedata.lookup('Crossing lanes'),
                            'water_hit': unicodedata.lookup('Medium white circle')}
        
        # define symbols for enemy_board   
        self.symbols_enemy = {'boat': unicodedata.lookup('Crossing lanes'),
                             'boat_hit': unicodedata.lookup('Medium black circle'),
                             'water': unicodedata.lookup('Crossing lanes'),
                             'water_hit': unicodedata.lookup('Medium white circle')}
    
        # initialize squares in board
        self.squares = []
        for i in range(self.board_height):
            row = []
            for j in range(self.board_width):
                row.append(Square(i, j, True))
            self.squares.append(row)
            
    def print_as_enemy(self):
        print(self.printer(self.symbols_enemy))
    
    def print_as_own(self):
        print(self.printer(self.symbols_own))
    
    def printer(self, symbols):
        # first row with numbering for columns
        sep = (self.board_spacing + 1)  * ' '
        board = sep.join([str(x) for x in range(self.board_width)]) + '\n'
        # left indentation for first row
        board = (self.board_spacing + 1) * ' ' + board
        
        for i, row in enumerate(self.squares):
            # row numbering
            board += (str(i)) + (self.board_spacing + 1 - len(str(i))) * ' '
            for j in range(self.board_width):
                # get square and add it's symbol to board
                sq = self.get_square(i,j)
                sq.set_symbol(symbols)
                
                board += sq.symbol + self.board_spacing * ' '
            board += '\n'
        return board
    
    def get_square(self, row, col):
        return self.squares[row][col]
    
    def set_board(self, random=True):
        '''
        Places all boats on the board, either randomly or through user input
        
        Args:
            boats: dict, keys are boat size and values # of boats of that type
            random: if True, board is set randomly
        '''
        for boat_size in boats:
            # iterate through number of boats of that size
            for i in range(self.boats[boat_size]):
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
        '''
        Assumes valid boat coordinates passed to function
        Modifies board to add boat to coordinates
        
        Args:
            x, y: both int, coordinates to fire at
        
        Returns:
            True if it hit a boat, False if it missed
        '''
        
        # error handling for firing out of the board
        try:
            sq = self.get_square(x, y)
        except:
            print("That's out of range!")
            return False
            
        if not sq.is_hit:
            sq.hit_square()
            if sq.has_boat:
                return True
            else:
                return False            
        # error handling for firing at a square already hit
        else:
            print('You already hit that square!')      

class Square(object):
    def __init__(self, row, column, visible = True):
        self.row = row
        self.column = column
        self.has_boat = False
        self.is_hit = False
        self.symbol = None
    
    def place_boat(self):
        self.has_boat = True

    def get_symbol(self):
        return self.symbol
    
    def set_symbol(self, symbols):
        '''
        Sets square symbol depending on whether square has_boat and is_hit
        
        Args:
            symbols: a dict of symbols, where keys are:
                - 'water':      to be displayed if not has_boat and not is_hit
                - 'water_hit':  to be displayed if not has_boat and is_hit
                - 'boat':       to be displayed if has_boat and not is_hit
                - 'boat_hit':   to be displayed if has_boat and is_hit
        '''
        if not self.has_boat and not self.is_hit:
            self.symbol = symbols['water']
        elif not self.has_boat and self.is_hit:
            self.symbol = symbols['water_hit']
        elif self.has_boat and not self.is_hit:
            self.symbol = symbols['boat']
        elif self.has_boat and self.is_hit:
            self.symbol = symbols['boat_hit']
               
    def hit_square(self):
        self.is_hit = True
            
    def __str__(self):
        return f'({self.row}, {self.column})'    

class BattleshipRunner(object):
    ''' Runs a game of Battleship'''
  
    def __init__(self, player1, player2, to_start, board_width, board_height, boats):
       self.players = [player1, player2]
       self.to_start = to_start
       self.board_width = board_width
       self.board_heights = board_height
       self.boats = boats
       
       self.other_player = {player1: player2, player2:player1}
       self.is_over = False
       self.timer = None # to be implemented
       
       # give each player their own board
       for p in self.players:
           p.set_own_board(BattleshipBoard(board_width, board_height, boats))
           p.place_boats()
           
       # give each player a reference to enemy's board
       player1.set_enemy_board(player2.get_own_board())
       player2.set_enemy_board(player1.get_own_board())
       
       # give turn to a player
       [p.give_turn() for p in self.players if p==to_start]
       
       self.run_game()
     
    def run_game(self):
        print(f'Battleship game is on!! {(self.to_start)} fires first!')
        while not self.is_over:
            for p in self.players:
                if p.get_turn():
                    if p.get_nature() == 'HUMAN':
                        self.print_boards(p)
                    p.move()
                        
                    if not p.get_turn():
                        print(f'Miss! {p} losses turn!')
                        self.other_player[p].give_turn()
                    else:
                        print(f'\n')
                        print(f'Boat hit! {p} to fire again!')
    
    def print_boards(self, player):
        print(f'{player} to fire')
        print(f'\n')
        print(f'{player} - View of enemy board')
        print(50 * '-')
        player.get_enemy_board().print_as_enemy()
        print(f'\n')
        print(f'{player} - View of own board')
        print(50 * '-')
        player.get_own_board().print_as_own()  
        
    def is_game_over(self):
        pass
        #define
        
class Player(object):
    ''' 
    Defines a player of the game Battleship
    '''
    
    def __init__(self, name, nature, random_placement):
        self.name = name
        self.nature = nature
        self.random_placement = random_placement
        self.own_board = None
        self.enemy_board = None
        self.my_turn = False
        
    def move(self):
        if self.nature == 'HUMAN':
            target = input('Coordinates to fire as x, y\n').split(',')
            target = tuple([int(x) for x in target])
        elif self.nature == 'AI':
            x = random.randint(0, self.enemy_board.board_height)
            y = random.randint(0, self.enemy_board.board_width)
            print(f'{self} fires at {x}, {y}')
            target = (x, y)
            
        hit_boat = self.enemy_board.fire(*target)
        if not hit_boat:
            self.my_turn = False
        
    
    def place_boats(self):
        self.own_board.set_board(self.random_placement)
                
    def give_turn(self):
        self.my_turn = True
    def get_turn(self):
        return self.my_turn
    
    def set_own_board(self, board):
        self.own_board = board
    def get_own_board(self):
        return self.own_board

    def set_enemy_board(self, board):
        self.enemy_board = board
    def get_enemy_board(self):
        return self.enemy_board

    def get_nature(self):
        return self.nature
    
    def __str__(self):
        return f'{self.name} ({self.nature})'
       
       

if __name__ == "__main__":
    # players can be HUMAN or AI       
    player1 = Player(name = 'player1', nature='AI', random_placement=True)
    player2 = Player(name = 'player2', nature='HUMAN', random_placement=True)
    
    # to_start can be either player or 'random'
    to_start = player1
    
    board_width = 10
    board_height = 10
    # dictionary where keys are boat size and values # of boats
    boats = {2:1, 3:2, 4:1, 5:1}
    
    game = BattleshipRunner(player1, player2, to_start,
                            board_width, board_height, boats)


    
