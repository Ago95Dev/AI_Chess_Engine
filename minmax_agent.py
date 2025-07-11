import random
from enum import Enum
import chess # Importa la libreria python-chess

class Algorithms(Enum):
    """Enumeration for different search algorithms."""
    MIN_MAX = "min_max"
    FAIL_HARD_ALPHA_BETA = "fail_hard_alpha_beta"
    FAIL_SOFT_ALPHA_BETA = "fail_soft_alpha_beta"
    BRANCHING_LIMIT = "branching_limit"
    PRED_BLMINMAX = "pred_blminmax"
    MULTI_INPUT_PRED_BLMINMAX = "multi_input_pred_blminmax"

# --- Funzioni di gioco per gli scacchi (per essere passate all'AI Agent) ---
def get_chess_children(board: chess.Board):
    """
    Genera tutti gli stati successori (board) dalla board_state corrente
    applicando tutte le mosse legali.
    """
    children_boards = []
    for move in board.legal_moves:
        new_board = board.copy() # Crea una copia della board
        new_board.push(move)      # Applica la mossa
        children_boards.append(new_board)
    return children_boards

def is_chess_final(board: chess.Board):
    """
    Verifica se il gioco è terminato.
    """
    return board.is_game_over()

def chess_H0(board: chess.Board):
    """
    Una funzione euristica statica di base per gli scacchi.
    Assegna valori ai pezzi e considera gli stati finali.
    Valori positivi indicano un vantaggio per il Bianco, negativi per il Nero.
    """
    score = 0
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0 # Il re non ha valore materiale diretto, la sua cattura è il fine
    }

    # Valutazione dei pezzi
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    # Bonus per il controllo del centro (semplice)
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece:
            if piece.color == chess.WHITE:
                score += 10
            else:
                score -= 10
    
    # Gestione degli stati finali (molto importante per evitare che l'AI non veda i checkmate)
    if board.is_checkmate():
        # Se è scacco matto, il valore è infinito positivo o negativo a seconda di chi vince
        # `board.turn` è il giocatore il cui turno è, quindi se `board.turn` è WHITE e checkmate, BLACK ha vinto.
        if board.turn == chess.WHITE: # Il Bianco è in scacco matto
            return float('-inf') # Il valore per il Bianco è molto negativo
        else: # Il Nero è in scacco matto
            return float('inf') # Il valore per il Bianco è molto positivo
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_fivefold_repetition() or board.is_seventyfive_moves():
        return 0 # Pareggio

    # Se è il turno del nero, invertiamo il punteggio dalla prospettiva del bianco
    # Questo è FONDAMENTALE perché MinimaxAgent è progettato per massimizzare il valore
    # del giocatore che sta chiamando la funzione.
    if board.turn == chess.BLACK:
        score = -score

    return score


class MinMaxAgent:
    """
    A generic Minimax agent that can be configured with different
    search algorithms, including Alpha-Beta pruning and branch-limited search.
    """

    def __init__(self, algorithm_type: Algorithms, H0_function, get_children_function, is_final_function):
        """
        Initializes the MinMaxAgent with a specific search algorithm.

        Args:
            algorithm_type (Algorithms): The type of search algorithm to use.
            H0_function (callable): A function that takes a state and returns its static heuristic evaluation.
            get_children_function (callable): A function that takes a state and returns a list of its successor states.
            is_final_function (callable): A function that takes a state and returns True if it's a terminal state.
        """
        self.H_0 = H0_function
        self.get_children = get_children_function
        self.is_final = is_final_function

        self.engine = None
        match algorithm_type:
            case Algorithms.MIN_MAX:
                self.engine = self.minmax
            case Algorithms.FAIL_HARD_ALPHA_BETA:
                self.engine = self.fhabminmax
            case Algorithms.FAIL_SOFT_ALPHA_BETA:
                self.engine = self.fsabminmax
            case Algorithms.BRANCHING_LIMIT:
                self.engine = self.blminmax
            case Algorithms.PRED_BLMINMAX:
                self.engine = self.pred_blminmax
            case Algorithms.MULTI_INPUT_PRED_BLMINMAX:
                self.engine = self.mi_pred_blminmax
            case _:
                raise ValueError(
                    f"Invalid engine type. Choose between {', '.join([engine.value for engine in Algorithms])}")

    def find_best_move(self, current_state, depth):
        """
        Finds the best move from the current state using the selected engine.
        Returns the best value and the best successor state.
        """
        # Sempre chiamare l'algoritmo interno con True per il maximizing_player
        # in quanto il valore di H0 è già normalizzato rispetto al giocatore di turno.
        return self.engine(current_state, depth, True) 

    def minmax(self, state, L, maximizing_player=True):
        """
        Standard Minimax algorithm without pruning.
        """
        if L == 0 or self.is_final(state):
            return self.H_0(state), state

        children = self.get_children(state)
        if not children:
            return self.H_0(state), state

        best_value = float('-inf') if maximizing_player else float('inf')
        best_children_states = [] 

        for child in children:
            # Qui si passa `not maximizing_player` perché si sta passando al turno dell'avversario
            # per la prossima ricorsione. La H0 normalizzerà di nuovo.
            child_value, _ = self.minmax(child, L - 1, not maximizing_player)

            if maximizing_player:
                if child_value > best_value:
                    best_value = child_value
                    best_children_states = [child]
                elif child_value == best_value:
                    best_children_states.append(child)
            else: # Minimizing player
                if child_value < best_value:
                    best_value = child_value
                    best_children_states = [child]
                elif child_value == best_value:
                    best_children_states.append(child)

        best_child_state = random.choice(best_children_states) if best_children_states else None
        return best_value, best_child_state

    def fhabminmax(self, state, L, alpha=float('-inf'), beta=float('inf'), maximizing_player=True):
        """
        Fail-Hard Alpha-Beta Pruning Minimax.
        """
        if L == 0 or self.is_final(state):
            return self.H_0(state), state

        children = self.get_children(state)
        if not children:
            return self.H_0(state), state

        best_move_state = None

        if maximizing_player:
            value = float('-inf')
            for child in children:
                child_value, _ = self.fhabminmax(child, L - 1, alpha, beta, False)
                if child_value > value:
                    value = child_value
                    best_move_state = child 
                alpha = max(alpha, value)
                if alpha >= beta:
                    break 
            return value, best_move_state
        else: # Minimizing player
            value = float('inf')
            for child in children:
                child_value, _ = self.fhabminmax(child, L - 1, alpha, beta, True)
                if child_value < value:
                    value = child_value
                    best_move_state = child 
                beta = min(beta, value)
                if beta <= alpha:
                    break 
            return value, best_move_state

    def fsabminmax(self, state, L, alpha=float('-inf'), beta=float('inf'), maximizing_player=True):
        """
        Fail-Soft Alpha-Beta Pruning Minimax.
        """
        if L == 0 or self.is_final(state):
            return self.H_0(state), state

        children = self.get_children(state)
        if not children:
            return self.H_0(state), state

        best_move_state = None

        if maximizing_player:
            value = float('-inf')
            for child in children:
                child_value, _ = self.fsabminmax(child, L - 1, alpha, beta, False)
                if child_value > value:
                    value = child_value
                    best_move_state = child
                if value >= beta: 
                    return value, best_move_state 
                alpha = max(alpha, value)
            return value, best_move_state
        else: # Minimizing player
            value = float('inf')
            for child in children:
                child_value, _ = self.fsabminmax(child, L - 1, alpha, beta, True)
                if child_value < value:
                    value = child_value
                    best_move_state = child
                if value <= alpha: 
                    return value, best_move_state 
                beta = min(beta, value)
            return value, best_move_state

    def blminmax(self, state, L, branch_limit: int = 5, maximizing_player=True):
        """
        Branch-Limited Minimax (blMinMax).
        Explores only the 'branch_limit' most promising states based on H0 evaluation.
        """
        if L == 0 or self.is_final(state):
            return self.H_0(state), state

        all_children = self.get_children(state)
        if not all_children:
            return self.H_0(state), state

        evaluated_children = []
        for child in all_children:
            # Valuta i figli dalla prospettiva del giocatore attuale
            h0_val = self.H_0(child) 
            evaluated_children.append((h0_val, child))

        # Ordina i figli in base al valore H0.
        # Se siamo il giocatore massimizzante (cercando il valore più alto di H0), ordina in modo decrescente.
        # Se siamo il giocatore minimizzante (l'avversario sta cercando di minimizzare il nostro H0), ordina in modo crescente.
        # Poiché la nostra H0 è già normalizzata per il giocatore di turno, 
        # il giocatore corrente cerca sempre il valore più alto di H0 per i propri figli.
        evaluated_children.sort(key=lambda x: x[0], reverse=True) # Sempre decrescente per selezionare i migliori figli

        # Seleziona solo i primi 'branch_limit' figli più promettenti
        promising_children = [child_tuple[1] for child_tuple in evaluated_children[:branch_limit]]

        best_value = float('-inf') if maximizing_player else float('inf')
        best_children_for_move = []

        for child in promising_children:
            # Passa `not maximizing_player` per la ricorsione. La H0 sarà normalizzata per l'avversario.
            child_value, _ = self.blminmax(child, L - 1, branch_limit, not maximizing_player)

            if maximizing_player:
                if child_value > best_value:
                    best_value = child_value
                    best_children_for_move = [child]
                elif child_value == best_value:
                    best_children_for_move.append(child)
            else: # Minimizing player
                if child_value < best_value:
                    best_value = child_value
                    best_children_for_move = [child]
                elif child_value == best_value:
                    best_children_for_move.append(child)

        best_child = random.choice(best_children_for_move) if best_children_for_move else None
        return best_value, best_child

    def pred_blminmax(self, state, L, branch_limit: int = 5, maximizing_player=True):
        """
        Placeholder for Pred-BLMinMax.
        This would likely involve using a predictive model (e.g., a neural network)
        to evaluate states or guide the branching.
        """
        print("pred_blminmax not yet implemented. Falling back to blminmax.")
        return self.blminmax(state, L, branch_limit, maximizing_player)

    def mi_pred_blminmax(self, state, L, branch_limit: int = 5, maximizing_player=True):
        """
        Placeholder for Multi-Input Pred-BLMinMax.
        This would likely involve a predictive model that takes multiple inputs
        (e.g., board state + features) to guide the branching.
        """
        print("mi_pred_blminmax not yet implemented. Falling back to blminmax.")
        return self.blminmax(state, L, branch_limit, maximizing_player)

# (Rimuovi il blocco `if __name__ == "__main__":` da questo file,
# o lascialo solo per testare minmax_agent.py in isolamento.)