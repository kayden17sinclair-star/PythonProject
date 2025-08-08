# Chess GUI with simple AI — Kayden edition
# Needs: python-chess  (pip install python-chess)

import tkinter as tk
from tkinter import ttk, messagebox
import chess
import math
import time

# ------------ look & feel -------------
SQ = 78
BORDER = 18
LIGHT = "#EEEED2"
DARK  = "#769656"
HILITE_FROM = "#F6F669"
HILITE_TO   = "#BACA44"
HILITE_LAST = "#f7ec6d"
HILITE_CHECK= "#e06c75"

PIECE_FONT = ("Arial Unicode MS", int(SQ*0.68))
GLYPHS = {
    chess.PAWN:   ("♙", "♟"),
    chess.KNIGHT: ("♘", "♞"),
    chess.BISHOP: ("♗", "♝"),
    chess.ROOK:   ("♖", "♜"),
    chess.QUEEN:  ("♕", "♛"),
    chess.KING:   ("♔", "♚"),
}

# ------------- AI (minimax, alpha-beta) -------------
VAL = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
}

def material_eval(board: chess.Board) -> int:
    """Positive favors side to move’s perspective if we use negamax."""
    score = 0
    for piece_type, val in VAL.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * val
        score -= len(board.pieces(piece_type, chess.BLACK)) * val
    return score

def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    if depth == 0 or board.is_game_over():
        base = material_eval(board)
        # Small bonus for legal moves (mobility)
        base += 3 * board.legal_moves.count()
        return base if board.turn == chess.WHITE else -base

    best = -10**9
    for move in order_moves(board):
        board.push(move)
        score = -negamax(board, depth-1, -beta, -alpha)
        board.pop()
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def order_moves(board: chess.Board):
    # Captures first, then others — simple move ordering
    caps, others = [], []
    for m in board.legal_moves:
        caps.append(m) if board.is_capture(m) else others.append(m)
    return caps + others

def ai_best_move(board: chess.Board, depth: int) -> chess.Move | None:
    best_score = -10**9
    best = None
    for move in order_moves(board):
        board.push(move)
        score = -negamax(board, depth-1, -10**9, 10**9)
        board.pop()
        if score > best_score:
            best_score, best = score, move
    return best

# ---------------- GUI -----------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Kayden Chess")

        self.board = chess.Board()
        self.selected = None
        self.hl_items = []
        self.piece_items = {}
        self.last_move = None
        self.captured_white = []
        self.captured_black = []

        # Left: board canvas
        self.canvas = tk.Canvas(root, width=SQ*8 + BORDER*2, height=SQ*8 + BORDER*2)
        self.canvas.grid(row=0, column=0, rowspan=20, padx=8, pady=8)
        self.canvas.bind("<Button-1>", self.on_click)

        # Right: sidebar (move list, controls)
        side = ttk.Frame(root, padding=6)
        side.grid(row=0, column=1, sticky="ns")

        self.turn_var = tk.StringVar()
        self.turn_label = ttk.Label(side, textvariable=self.turn_var, font=("SF Pro", 13, "bold"))
        self.turn_label.grid(row=0, column=0, sticky="w", pady=(0,6))

        ttk.Label(side, text="Moves").grid(row=1, column=0, sticky="w")
        self.moves = tk.Text(side, width=24, height=20, state="disabled")
        self.moves.grid(row=2, column=0, sticky="nsew", pady=(0,8))

        # Captured trays
        cap_frame = ttk.Frame(side)
        cap_frame.grid(row=3, column=0, sticky="ew", pady=(0,8))
        ttk.Label(cap_frame, text="Captured by White:").grid(row=0, column=0, sticky="w")
        self.cap_by_w = ttk.Label(cap_frame, text="", font=PIECE_FONT)
        self.cap_by_w.grid(row=1, column=0, sticky="w")
        ttk.Label(cap_frame, text="Captured by Black:").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.cap_by_b = ttk.Label(cap_frame, text="", font=PIECE_FONT)
        self.cap_by_b.grid(row=3, column=0, sticky="w")

        # Controls
        btns = ttk.Frame(side)
        btns.grid(row=4, column=0, sticky="ew", pady=(8,0))
        ttk.Button(btns, text="New Game", command=self.new_game).grid(row=0, column=0, padx=2)
        ttk.Button(btns, text="Undo", command=self.undo).grid(row=0, column=1, padx=2)

        # AI options
        ai_frame = ttk.Frame(side)
        ai_frame.grid(row=5, column=0, sticky="ew", pady=(12,0))
        ttk.Label(ai_frame, text="Play as:").grid(row=0, column=0, sticky="w")
        self.side_var = tk.StringVar(value="White")
        side_pick = ttk.Combobox(ai_frame, textvariable=self.side_var, values=["White","Black","Human vs Human"], state="readonly", width=16)
        side_pick.grid(row=0, column=1, padx=4)

        ttk.Label(ai_frame, text="Difficulty:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.depth_var = tk.IntVar(value=2)
        depth_box = ttk.Combobox(ai_frame, textvariable=self.depth_var, values=[1,2,3], state="readonly", width=16)
        depth_box.grid(row=1, column=1, padx=4, pady=(6,0))

        self.root.bind("u", lambda e: self.undo())

        self.draw_board()
        self.refresh()

    # ---------- drawing ----------
    def draw_board(self):
        c = self.canvas
        c.delete("square")
        for r in range(8):
            for f in range(8):
                x0 = BORDER + f*SQ
                y0 = BORDER + (7-r)*SQ
                x1, y1 = x0 + SQ, y0 + SQ
                color = LIGHT if (r+f) % 2 == 0 else DARK
                c.create_rectangle(x0, y0, x1, y1, fill=color, outline=color, tags="square")
        # coords
        for f, letter in enumerate("abcdefgh"):
            x = BORDER + f*SQ + SQ//2
            self.canvas.create_text(x, BORDER + SQ*8 + 12, text=letter, tags="coord")
        for r in range(8):
            y = BORDER + (7-r)*SQ + SQ//2
            self.canvas.create_text(BORDER-10, y, text=str(r+1), tags="coord")

    def refresh(self):
        self.canvas.delete("piece")
        self.clear_highlights()

        # last move highlight
        if self.last_move:
            for sq in [self.last_move.from_square, self.last_move.to_square]:
                self.outline_square(sq, HILITE_LAST, 3)

        # check highlight
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                self.outline_square(king_sq, HILITE_CHECK, 4)

        # draw pieces
        self.piece_items.clear()
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if not p: continue
            glyph = GLYPHS[p.piece_type][0 if p.color == chess.WHITE else 1]
            x, y = self.center_of(sq)
            item = self.canvas.create_text(x, y, text=glyph, font=PIECE_FONT, tags="piece")
            self.piece_items[sq] = item

        self.turn_var.set(("White to move" if self.board.turn else "Black to move"))

        # captured trays
        self.cap_by_w.config(text=" ".join(GLYPHS[p][1] for p in self.captured_white))
        self.cap_by_b.config(text=" ".join(GLYPHS[p][0] for p in self.captured_black))

        # move list
        self.moves.config(state="normal")
        self.moves.delete("1.0", "end")
        san = []
        tmp = chess.Board()
        for m in self.board.move_stack:
            san.append(tmp.san(m))
            tmp.push(m)
        # format 1. e4 e5 2. Nf3 ...
        lines = []
        for i in range(0, len(san), 2):
            n = i//2 + 1
            if i+1 < len(san):
                lines.append(f"{n}. {san[i]} {san[i+1]}")
            else:
                lines.append(f"{n}. {san[i]}")
        self.moves.insert("1.0", "\n".join(lines))
        self.moves.config(state="disabled")

        self.root.update_idletasks()
        self.maybe_let_ai_play()

    # ---------- helpers ----------
    def center_of(self, sq):
        f = chess.square_file(sq); r = chess.square_rank(sq)
        return BORDER + f*SQ + SQ//2, BORDER + (7-r)*SQ + SQ//2

    def clear_highlights(self):
        for i in self.hl_items: self.canvas.delete(i)
        self.hl_items.clear()

    def outline_square(self, sq, color, width):
        f = chess.square_file(sq); r = chess.square_rank(sq)
        x0 = BORDER + f*SQ; y0 = BORDER + (7-r)*SQ
        x1, y1 = x0 + SQ, y0 + SQ
        self.hl_items.append(self.canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=width))

    # ---------- events ----------
    def on_click(self, e):
        sq = self.xy_to_square(e.x, e.y)
        if sq is None: return

        if self.is_ai_turn():  # ignore clicks while AI is thinking
            return

        if self.selected is None:
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn:
                self.selected = sq
                self.clear_highlights()
                self.outline_square(sq, HILITE_FROM, 3)
                for m in self.board.legal_moves:
                    if m.from_square == sq:
                        f = chess.square_file(m.to_square); r = chess.square_rank(m.to_square)
                        cx = BORDER + f*SQ + SQ//2; cy = BORDER + (7-r)*SQ + SQ//2
                        self.hl_items.append(self.canvas.create_oval(cx-7, cy-7, cx+7, cy+7,
                                                                     fill=HILITE_TO, outline=""))
        else:
            move = chess.Move(self.selected, sq)
            legal = move in self.board.legal_moves
            self.clear_highlights()
            if legal:
                self.make_move(move)
                self.selected = None
            else:
                # reselect if clicked own piece
                p = self.board.piece_at(sq)
                if p and p.color == self.board.turn:
                    self.selected = sq
                    self.outline_square(sq, HILITE_FROM, 3)
                else:
                    self.selected = None

    def xy_to_square(self, x, y):
        if not (BORDER <= x <= BORDER+SQ*8 and BORDER <= y <= BORDER+SQ*8):
            return None
        f = (x - BORDER) // SQ
        r_from_bottom = (y - BORDER) // SQ
        r = 7 - int(r_from_bottom)
        return chess.square(int(f), int(r))

    # ---------- gameplay ----------
    def make_move(self, move: chess.Move):
        # record capture for trays
        if self.board.is_capture(move):
            victim_sq = move.to_square if self.board.piece_at(move.to_square) else chess.square(chess.square_file(move.to_square),
                                                                                                chess.square_rank(move.from_square))
            victim = self.board.piece_at(victim_sq)
            if victim:
                if self.board.turn == chess.WHITE:
                    self.captured_white.append(victim.piece_type)
                else:
                    self.captured_black.append(victim.piece_type)

        self.board.push(move)
        self.last_move = move
        self.refresh()
        self.check_end()

    def undo(self):
        if not self.board.move_stack: return
        # undo capture trays if needed
        last = self.board.pop()
        # If that move was a capture, pop from trays
        if last.drop is None and (last.capture or last.promotion or True):
            # Easiest reliable way: recompute trays from scratch
            self.recompute_captures()
        self.last_move = self.board.move_stack[-1] if self.board.move_stack else None
        self.selected = None
        self.refresh()

    def recompute_captures(self):
        self.captured_white, self.captured_black = [], []
        tmp = chess.Board()
        for m in self.board.move_stack:
            if tmp.is_capture(m):
                victim_sq = m.to_square if tmp.piece_at(m.to_square) else chess.square(
                    chess.square_file(m.to_square), chess.square_rank(m.from_square))
                victim = tmp.piece_at(victim_sq)
                if victim:
                    (self.captured_white if tmp.turn == chess.WHITE else self.captured_black).append(victim.piece_type)
            tmp.push(m)

    def new_game(self):
        self.board.reset()
        self.selected = None
        self.last_move = None
        self.captured_white, self.captured_black = [], []
        self.refresh()

    def check_end(self):
        if self.board.is_game_over():
            out = self.board.outcome()
            if out is None:
                msg = "Game over."
            elif out.termination == chess.Termination.CHECKMATE:
                msg = "Checkmate! " + ("White wins!" if out.winner else "Black wins!")
            elif out.termination == chess.Termination.STALEMATE:
                msg = "Stalemate."
            else:
                msg = "Draw."
            messagebox.showinfo("Result", msg)

    # ---------- AI integration ----------
    def is_ai_turn(self):
        mode = self.side_var.get()
        if mode == "Human vs Human": return False
        ai_color = chess.BLACK if mode == "White" else chess.WHITE
        return self.board.turn == ai_color

    def maybe_let_ai_play(self):
        if not self.is_ai_turn(): return
        if self.board.is_game_over(): return

        self.root.after(50, self.ai_play)

    def ai_play(self):
        depth = int(self.depth_var.get())
        t0 = time.time()
        move = ai_best_move(self.board, depth)
        if move is None:
            return
        self.make_move(move)
        # tiny delay to feel “human”
        elapsed = time.time() - t0
        if elapsed < 0.2:
            time.sleep(0.2 - elapsed)

# ------------- run -------------
if __name__ == "__main__":
    root = tk.Tk()
    # Use platform default light theme for ttk if available
    try:
        from tkinter import ttk
        style = ttk.Style()
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
    except Exception:
        pass
    App(root)
    root.mainloop()
    