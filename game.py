import pygame
import chess
from pygame.locals import *

# Configurazioni
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
PIECE_SCALE = 0.8

# Inizializza Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python-Chess GUI")

# Carica le immagini dei pezzi (puoi scaricare uno sprite sheet come questo:)
# https://github.com/mandrelbrotset/pygame-chess/tree/main/assets
def load_pieces():
    pieces = {}
    sprite_sheet = pygame.image.load("resources/pieces.png").convert_alpha()
    
    # Mappa pezzi a coordinate nello sprite sheet
    piece_map = {
        chess.WHITE: {
            chess.PAWN: (5, 0),
            chess.ROOK: (4, 0),
            chess.KNIGHT: (3, 0),
            chess.BISHOP: (2, 0),
            chess.QUEEN: (1, 0),
            chess.KING: (0, 0)
        },
        chess.BLACK: {
            chess.PAWN: (5, 1),
            chess.ROOK: (4, 1),
            chess.KNIGHT: (3, 1),
            chess.BISHOP: (2, 1),
            chess.QUEEN: (1, 1),
            chess.KING: (0, 1)
        }
    }
    
    for color in piece_map:
        for piece_type in piece_map[color]:
            x, y = piece_map[color][piece_type]
            size = 83
            rect = pygame.Rect(x*size, y*size, size, size)
            image = sprite_sheet.subsurface(rect)
            pieces[(color, piece_type)] = pygame.transform.smoothscale(
                image, (int(SQUARE_SIZE*PIECE_SCALE), int(SQUARE_SIZE*PIECE_SCALE))
            )
    return pieces

pieces = load_pieces()

class ChessGUI:
    def __init__(self):
        self.board = chess.Board()
        self.selected_square = None

    def draw_board(self):
        # Disegna la scacchiera
        for row in range(8):
            for col in range(8):
                color = (238, 238, 210) if (row + col) % 2 == 0 else (118, 150, 86)
                pygame.draw.rect(screen, color, 
                    (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
        # Disegna i pezzi
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row, col = 7 - chess.square_rank(square), chess.square_file(square)
                image = pieces[(piece.color, piece.piece_type)]
                screen.blit(image, 
                    (col*SQUARE_SIZE + (SQUARE_SIZE*(1-PIECE_SCALE)/2),
                     row*SQUARE_SIZE + (SQUARE_SIZE*(1-PIECE_SCALE)/2))
                )

    def handle_click(self, pos):
        col = pos[0] // SQUARE_SIZE
        row = 7 - (pos[1] // SQUARE_SIZE)
        square = chess.square(col, row)
        
        if self.selected_square is None:
            if self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
            self.selected_square = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())

            screen.fill((0, 0, 0))
            self.draw_board()
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    gui = ChessGUI()
    gui.run()