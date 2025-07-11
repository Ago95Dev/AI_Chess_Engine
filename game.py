import pygame
import chess
from pygame.locals import *

# Configurazioni
WIDTH, HEIGHT = 600, 600
SQUARE_SIZE = WIDTH // 8
PIECE_SCALE = 0.8

# Colori
LIGHT_SQUARE_COLOR = (238, 238, 210)
DARK_SQUARE_COLOR = (118, 150, 86)
HIGHLIGHT_COLOR = (34, 139, 34)

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
        self.dragging_piece = None
        self.legal_moves_targets = [] # Nuova lista per memorizzare le caselle delle mosse legali

    def draw_board(self):
        # Disegna la scacchiera
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE_COLOR if (row + col) % 2 == 0 else DARK_SQUARE_COLOR
                pygame.draw.rect(screen, color, 
                    (col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
        # Disegna gli overlay delle mosse legali
        if self.selected_square:
            for target_square in self.legal_moves_targets:
                row, col = 7 - chess.square_rank(target_square), chess.square_file(target_square)
                
                # Crea una superficie temporanea per il cerchio con trasparenza
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA) 
                # Disegna un cerchio al centro della casella
                pygame.draw.circle(s, HIGHLIGHT_COLOR, 
                                   (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 
                                   SQUARE_SIZE // 6)
                screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

        # Disegna i pezzi
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            # Disegna il pezzo solo se non è quello attualmente trascinato
            if piece and square != self.selected_square:
                row, col = 7 - chess.square_rank(square), chess.square_file(square)
                image = pieces[(piece.color, piece.piece_type)]
                screen.blit(image, 
                    (col*SQUARE_SIZE + (SQUARE_SIZE*(1-PIECE_SCALE)/2),
                     row*SQUARE_SIZE + (SQUARE_SIZE*(1-PIECE_SCALE)/2))
                )
        
        # Disegna il pezzo trascinato per ultimo, sopra tutto il resto
        if self.dragging_piece:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            image = pieces[(self.dragging_piece.color, self.dragging_piece.piece_type)]
            # Centra l'immagine del pezzo sul cursore del mouse
            screen.blit(image, (mouse_x - image.get_width() // 2, mouse_y - image.get_height() // 2))

    def handle_click(self, pos):
        col = pos[0] // SQUARE_SIZE
        row = 7 - (pos[1] // SQUARE_SIZE)
        square = chess.square(col, row)
        
        if self.selected_square is None:
            # Seleziona un pezzo e calcola le mosse legali
            if self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
                self.dragging_piece = self.board.piece_at(square)
                self.legal_moves_targets = [move.to_square for move in self.board.legal_moves if move.from_square == self.selected_square]
        else:
            # Tenta di fare una mossa
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
            self.selected_square = None
            self.dragging_piece = None
            self.legal_moves_targets = [] # Resetta le mosse legali dopo il tentativo di mossa

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
                elif event.type == MOUSEBUTTONUP:
                    if self.selected_square is not None:
                        # Tenta di fare una mossa quando il pulsante del mouse viene rilasciato
                        self.handle_click(pygame.mouse.get_pos())
                
            screen.fill((0, 0, 0))
            self.draw_board()
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    gui = ChessGUI()
    gui.run()