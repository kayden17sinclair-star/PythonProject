import turtle

# ====== tweak these ======
ROWS = 12          # number of tile rows
COLS = 12          # tiles per row
TILE_W = 36        # tile width
TILE_H = 24        # tile height
MORTAR = 6         # thickness of the gray lines
OFFSET = TILE_W // 2   # horizontal offset every other row
BG = "white"       # background color
# =========================

screen = turtle.Screen()
screen.title("Café Wall Illusion")
screen.bgcolor(BG)
t = turtle.Turtle(visible=False)
t.speed()
t.penup()

def rect(x, y, w, h, color):
    t.goto(x, y)
    t.setheading(0)
    t.color(color)
    t.begin_fill()
    t.pendown()
    for _ in range(2):
        t.forward(w); t.right(90); t.forward(h); t.right(90)
    t.end_fill()
    t.penup()

# Compute total drawing size
total_w = COLS * TILE_W + OFFSET
total_h = ROWS * (TILE_H + MORTAR) + MORTAR

# Start in the upper-left corner
start_x = -total_w // 2
start_y = total_h // 2

# Draw rows: each row has a gray mortar stripe, then a staggered row of tiles
for r in range(ROWS + 1):
    y = start_y - r * (TILE_H + MORTAR)
    # Mortar (horizontal gray line band)
    rect(start_x, y, total_w, MORTAR, "#9a9a9a")

for r in range(ROWS):
    y = start_y - r * (TILE_H + MORTAR) - MORTAR
    # stagger every other row
    x0 = start_x + (OFFSET if r % 2 else 0)
    # draw alternating black/white rectangles
    for c in range(COLS + 1):  # +1 to cover the offset overhang
        x = x0 + c * TILE_W
        color = "black" if c % 2 == 0 else "white"
        rect(x, y, TILE_W, TILE_H, color)

# Optional: draw thin guidelines to prove they’re parallel
t.color("red")
t.pensize(1)
for r in range(ROWS + 1):
    y = start_y - r * (TILE_H + MORTAR)
    t.goto(start_x, y + MORTAR / 2)
    t.setheading(0)
    t.pendown()
    t.forward(total_w)
    t.penup()

turtle.done()

