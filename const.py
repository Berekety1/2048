# ---------- Layout ----------
TILE_NUM = 4          
TILE_SIZE = 90        
GAP = 8              
BOARD_SIZE = TILE_NUM * TILE_SIZE + (TILE_NUM + 1) * GAP   
HEADER_HEIGHT = 100   
WINDOW_SIZE = (BOARD_SIZE, BOARD_SIZE + HEADER_HEIGHT)
CORNER_RADIUS = 6
SCORE_BOX_WIDTH = 95
FPS = 60

WIN_VALUE = 2048

# ---------- Animations (times in milliseconds) ----------
SLIDE_TIME = 100
POP_TIME = 150            # after the slide: new tiles grow in, merged tiles pulse
PULSE_SIZE = 0.15         # merged tiles grow 15% bigger at the peak
SCORE_POPUP_TIME = 600
OVERLAY_DELAY = 300       # pause before the win / game-over screen starts fading in
OVERLAY_FADE_TIME = 400

# ---------- Colors ----------
TILE_COLORS = {
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149, 99),
    32:   (246, 124, 95),
    64:   (246, 94, 59),
    128:  (237, 207, 114),
    256:  (237, 204, 97),
    512:  (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

BIG_TILE_COLOR = (60, 58, 50)      # anything above 2048
EMPTY_COLOR    = (205, 193, 180)   # empty cell
BG_COLOR       = (187, 173, 160)   # board background and score boxes
HEADER_COLOR   = (250, 248, 239)   # area behind the title and scores

DARK_TEXT        = (119, 110, 101)   # for 2 and 4, and the title
LIGHT_TEXT       = (249, 246, 242)   # for 8 and up, and score numbers
SCORE_LABEL_TEXT = (238, 228, 218)   # "SCORE" / "BEST" labels

OVERLAY_COLOR = (238, 228, 218, 180)   # RGBA, 180 = alpha (0-255)
OVERLAY_TEXT  = (119, 110, 101)
