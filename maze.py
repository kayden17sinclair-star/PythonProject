# maze_explore_live_controls_fixed.py
# Controls: Space=pause/resume, Left=undo, Right=redo, 1..9 (0=10)=speed.
# Auto closes shortly after reaching goal.

import turtle, random, time

# ==== Tunables ====
ROWS, COLS   = 20, 20
CELL         = 22
TURN_STEPS   = 10
BASE_STEP    = 2
BASE_SLEEP   = 0.008
TURTLE_SPEED = 6
END_DELAY_MS = 2500

# ==== Runtime ====
SPEED_LEVEL   = 5
PLAYING       = True
ACTIONS       = []          # list of ('forward'|'backtrack', (x,y))
ACTION_INDEX  = 0           # next action to apply
CUR_POS       = (0, 0)
FINISHED      = False
IS_MOVING     = False       # prevent overlapping moves
TICK_GEN      = 0           # invalidates queued timers

DIRS     = {"N": (0,-1), "S": (0,1), "E": (1,0), "W": (-1,0)}
OPP      = {"N":"S","S":"N","E":"W","W":"E"}
HEADING  = {"N":90,"S":270,"E":0,"W":180}
BG_COLOR = "black"
WALL_COLOR = "white"
FWD_COLOR  = "red"
BACK_COLOR = "gray"
PATH_THICK = 3
WALL_THICK = 2

def speed_mult(): return SPEED_LEVEL / 5.0

def set_speed_level(level):
    global SPEED_LEVEL
    SPEED_LEVEL = max(1, min(10, level))
    print(f"[speed] {SPEED_LEVEL}")

def bind_keys(screen):
    for n in "123456789":
        screen.onkeypress(lambda k=int(n): set_speed_level(k), n)
    screen.onkeypress(lambda: set_speed_level(10), "0")
    screen.onkeypress(toggle_pause, "space")
    screen.onkeypress(step_back_key, "Left")
    screen.onkeypress(step_forward_key, "Right")
    screen.listen()

def cell_center(x,y): return (x*CELL+CELL/2, -(y*CELL+CELL/2))

def snap_to_center(t, cell):
    cx, cy = cell_center(*cell)
    t.penup(); t.goto(cx, cy); t.pendown()

def smooth_turn(t, target):
    global IS_MOVING
    IS_MOVING = True
    cur = t.heading()
    diff = (target - cur + 540) % 360 - 180
    step = diff / max(1, TURN_STEPS)
    for _ in range(TURN_STEPS):
        t.setheading(t.heading() + step)
        turtle.update()
        time.sleep(BASE_SLEEP / speed_mult())
    IS_MOVING = False

def move_straight(t, dist, color=FWD_COLOR):
    global IS_MOVING
    IS_MOVING = True
    t.pendown(); t.pencolor(color); t.width(PATH_THICK)
    left = dist
    while left > 0:
        step = min(BASE_STEP * speed_mult(), left)
        t.forward(step); left -= step
        turtle.update()
        time.sleep(BASE_SLEEP / speed_mult())
    IS_MOVING = False

def generate_maze(r,c):
    m = {(x,y): {"N":True,"S":True,"E":True,"W":True}
         for y in range(r) for x in range(c)}
    stack=[(0,0)]; seen={(0,0)}
    while stack:
        x,y = stack[-1]
        opts=[]
        for d,(dx,dy) in DIRS.items():
            nx,ny=x+dx,y+dy
            if 0<=nx<c and 0<=ny<r and (nx,ny) not in seen:
                opts.append((d,nx,ny))
        if opts:
            d,nx,ny = random.choice(opts)
            m[(x,y)][d] = False
            m[(nx,ny)][OPP[d]] = False
            seen.add((nx,ny)); stack.append((nx,ny))
        else:
            stack.pop()
    m[(0,0)]["W"] = False
    m[(c-1,r-1)]["E"] = False
    return m

def draw_maze(t, m, r, c):
    t.color(WALL_COLOR); t.width(WALL_THICK)
    def seg(x1,y1,x2,y2):
        t.penup(); t.goto(x1,y1); t.pendown(); t.goto(x2,y2); t.penup()
    for y in range(r):
        for x in range(c):
            sx,sy = x*CELL, -y*CELL
            w = m[(x,y)]
            if w["N"]: seg(sx,sy, sx+CELL,sy)
            if w["E"]: seg(sx+CELL,sy, sx+CELL,sy-CELL)
            if w["S"]: seg(sx+CELL,sy-CELL, sx,sy-CELL)
            if w["W"]: seg(sx,sy-CELL, sx,sy)
    t.penup()

def dfs_exploration_steps(maze, start, goal):
    steps = []
    visited = set()
    stack = [start]
    while stack:
        cx,cy = stack[-1]
        visited.add((cx,cy))
        if (cx,cy) == goal:
            break
        dirs = list(DIRS.keys()); random.shuffle(dirs)
        moved=False
        for d in dirs:
            if maze[(cx,cy)][d]: continue
            dx,dy = DIRS[d]; nx,ny = cx+dx, cy+dy
            if not (0<=nx<COLS and 0<=ny<ROWS): continue
            if (nx,ny) in visited: continue
            steps.append(("forward",(nx,ny)))
            stack.append((nx,ny)); moved=True
            break
        if not moved:
            stack.pop()
            if not stack: break
            steps.append(("backtrack", stack[-1]))
    return steps

# ===== Controls & Playback =====
def invalidate_timers():
    global TICK_GEN
    TICK_GEN += 1  # any queued timer with old token is ignored

def toggle_pause():
    global PLAYING
    PLAYING = not PLAYING
    invalidate_timers()
    if PLAYING:
        schedule_next_frame()

def step_back_key():
    global PLAYING
    PLAYING = False
    invalidate_timers()
    step_back()

def step_forward_key():
    global PLAYING
    PLAYING = False
    invalidate_timers()
    step_forward()

def schedule_next_frame():
    if not PLAYING or FINISHED: return
    token = TICK_GEN
    delay = int(1000 * BASE_SLEEP / max(0.2, speed_mult()))
    turtle.getscreen().ontimer(lambda: step_forward(token), delay)

def step_forward(token=None):
    global ACTION_INDEX, CUR_POS, FINISHED
    if token is not None and token != TICK_GEN:
        return  # stale timer
    if not PLAYING or IS_MOVING or FINISHED:
        return
    if ACTION_INDEX >= len(ACTIONS):
        if not FINISHED:
            FINISHED = True
            scr = turtle.getscreen()
            scr.ontimer(lambda: scr.bye(), END_DELAY_MS)
        return
    kind, target = ACTIONS[ACTION_INDEX]
    move_to_cell(kind, CUR_POS, target)
    CUR_POS = target
    ACTION_INDEX += 1
    schedule_next_frame()

def step_back():
    global ACTION_INDEX, CUR_POS
    if IS_MOVING or ACTION_INDEX <= 0:
        return
    kind, target = ACTIONS[ACTION_INDEX - 1]
    prev_cell = CUR_POS_before_index(ACTION_INDEX - 1)
    move_to_cell_reverse(kind, CUR_POS, prev_cell)
    CUR_POS = prev_cell
    ACTION_INDEX -= 1
    snap_to_center(T, CUR_POS)

def CUR_POS_before_index(idx):
    pos = (0,0)
    for i in range(idx):
        _, target = ACTIONS[i]
        pos = target
    return pos

def move_to_cell(kind, from_cell, to_cell):
    fx,fy = from_cell; tx,ty = to_cell
    dx,dy = tx-fx, ty-fy
    if dx==1: d="E"
    elif dx==-1: d="W"
    elif dy==1: d="S"
    else: d="N"
    smooth_turn(T, HEADING[d])
    move_straight(T, CELL, color=(FWD_COLOR if kind=="forward" else BACK_COLOR))
    snap_to_center(T, to_cell)

def move_to_cell_reverse(kind, from_cell, to_cell):
    fx,fy = from_cell; tx,ty = to_cell
    dx,dy = tx-fx, ty-fy
    if dx==1: d="E"
    elif dx==-1: d="W"
    elif dy==1: d="S"
    else: d="N"
    smooth_turn(T, HEADING[d])
    # draw over the line with background color
    move_straight(T, CELL, color=BG_COLOR)
    snap_to_center(T, to_cell)

def main():
    global T, CUR_POS, ACTIONS
    screen = turtle.Screen()
    screen.title("DFS Maze — Space: Pause | ← Undo | → Redo | 1–9/0 Speed")
    screen.bgcolor(BG_COLOR)
    screen.setup(COLS*CELL+40, ROWS*CELL+40)
    screen.setworldcoordinates(0, -ROWS*CELL, COLS*CELL, 0)
    screen.tracer(0)

    bind_keys(screen)

    T = turtle.Turtle()
    T.shape("turtle"); T.color("white"); T.speed(TURTLE_SPEED); T.penup()

    maze = generate_maze(ROWS, COLS)
    draw_maze(T, maze, ROWS, COLS); turtle.update()

    ACTIONS = dfs_exploration_steps(maze, (0,0), (COLS-1, ROWS-1))

    # Start at entrance and step into start center
    sx, sy = cell_center(0,0)
    T.goto(0, sy); T.pendown()
    smooth_turn(T, HEADING["E"]); move_straight(T, sx, color=FWD_COLOR)
    snap_to_center(T, (0,0))
    CUR_POS = (0,0)

    schedule_next_frame()
    screen.mainloop()

if __name__ == "__main__":
    main()
    