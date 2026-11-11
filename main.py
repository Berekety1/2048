import math
from pathlib import Path

import pygame

from const import (
    BOARD_SIZE, TILE_SIZE, GAP, HEADER_HEIGHT, WINDOW_SIZE, CORNER_RADIUS, SCORE_BOX_WIDTH, FPS,
    EMPTY_COLOR, BG_COLOR, HEADER_COLOR,
    DARK_TEXT, LIGHT_TEXT, SCORE_LABEL_TEXT,
    OVERLAY_COLOR, OVERLAY_TEXT,
    SLIDE_TIME, POP_TIME, PULSE_SIZE, SCORE_POPUP_TIME, OVERLAY_DELAY, OVERLAY_FADE_TIME,
)
from game import Board

pygame.init()
pygame.display.set_caption("2048")
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

# Arrow keys and WASD both work.
KEY_DIRECTIONS = {
    pygame.K_LEFT: "left",   pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_UP: "up",       pygame.K_w: "up",
    pygame.K_DOWN: "down",   pygame.K_s: "down",
}

BEST_SCORE_FILE = Path(__file__).with_name("best_score.txt")


# ---------- Best score ----------

def load_best_score():
    try:
        return int(BEST_SCORE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        return 0


def save_best_score(score):
    BEST_SCORE_FILE.write_text(str(score))


# ---------- Animation helpers ----------

def progress(start_time, duration):
    """How far along an animation is: 0.0 at the start, 1.0 when it's finished."""
    elapsed = pygame.time.get_ticks() - start_time
    return min(max(elapsed / duration, 0.0), 1.0)


def ease_out(t):
    """Makes movement start fast and slow down at the end (t goes from 0 to 1)."""
    return 1 - (1 - t) ** 2


def lerp(start, end, t):
    """The point t of the way from start to end (t=0 is start, t=1 is end)."""
    x = start[0] + (end[0] - start[0]) * t
    y = start[1] + (end[1] - start[1]) * t
    return round(x), round(y)


# ---------- Drawing ----------

fonts = {}

def get_font(size):
    """Load each font size once and reuse it (loading fonts every frame is slow)."""
    if size not in fonts:
        fonts[size] = pygame.font.SysFont("arial", size, bold=True)
    return fonts[size]


def tile_font_size(value):
    """Smaller text for longer numbers so they fit inside the tile."""
    digits = len(str(value))
    if digits <= 2:
        return 55
    if digits == 3:
        return 45
    if digits == 4:
        return 35
    return 28


def draw_text(text, size, color, center, alpha=255):
    surface = get_font(size).render(text, True, color)
    surface.set_alpha(alpha)
    screen.blit(surface, surface.get_rect(center=center))


def draw_score_box(label, value, x):
    box = pygame.Rect(x, 20, SCORE_BOX_WIDTH, 60)
    pygame.draw.rect(screen, BG_COLOR, box, border_radius=CORNER_RADIUS)
    draw_text(label, 14, SCORE_LABEL_TEXT, (box.centerx, box.y + 16))
    draw_text(str(value), 24, LIGHT_TEXT, (box.centerx, box.y + 40))


def draw_header(score, best_score, score_popups):
    screen.fill(HEADER_COLOR, (0, 0, BOARD_SIZE, HEADER_HEIGHT))
    draw_text("2048", 56, DARK_TEXT, (75, HEADER_HEIGHT // 2))

    best_x = BOARD_SIZE - GAP - SCORE_BOX_WIDTH
    score_x = best_x - GAP - SCORE_BOX_WIDTH
    draw_score_box("SCORE", score, score_x)
    draw_score_box("BEST", best_score, best_x)

    # "+32" texts float up from the score box and fade out.
    for points, start_time in score_popups:
        t = progress(start_time, SCORE_POPUP_TIME)
        center = (score_x + SCORE_BOX_WIDTH // 2, round(60 - 50 * ease_out(t)))
        draw_text(f"+{points}", 22, DARK_TEXT, center, alpha=round(255 * (1 - t)))


def cell_center(row, col):
    """Pixel position of the middle of a cell on the board."""
    x = GAP + col * (TILE_SIZE + GAP) + TILE_SIZE // 2
    y = HEADER_HEIGHT + GAP + row * (TILE_SIZE + GAP) + TILE_SIZE // 2
    return x, y


def draw_tile(tile, center, scale=1.0):
    """Draw a tile (or an empty cell if tile is None). scale shrinks or grows it."""
    size = round(TILE_SIZE * scale)
    if size <= 0:
        return
    rect = pygame.Rect(0, 0, size, size)
    rect.center = center

    color = EMPTY_COLOR if tile is None else tile.color
    pygame.draw.rect(screen, color, rect, border_radius=CORNER_RADIUS)

    if tile is not None:
        text_color = DARK_TEXT if tile.value <= 4 else LIGHT_TEXT
        font_size = round(tile_font_size(tile.value) * scale)
        if font_size > 0:
            draw_text(str(tile.value), font_size, text_color, rect.center)


def draw_board(board, move_time):
    """Draw the grid. move_time is when the last move started, used for animations."""
    screen.fill(BG_COLOR, (0, HEADER_HEIGHT, BOARD_SIZE, BOARD_SIZE))
    for i in range(board.size):
        for j in range(board.size):
            draw_tile(None, cell_center(i, j))   # empty cells underneath everything

    slide = progress(move_time, SLIDE_TIME)
    pop = progress(move_time + SLIDE_TIME, POP_TIME)   # starts once the slide is done

    for i, row in enumerate(board.grid):
        for j, tile in enumerate(row):
            if tile is None:
                continue
            end = cell_center(i, j)

            if slide < 1:
                # Step 1: tiles slide from their old cells to their new ones.
                # New tiles aren't shown yet, and a merged tile is shown as
                # its two halves sliding into the same cell.
                if tile.is_new:
                    continue
                parts = tile.merged_from or [tile]
                for part in parts:
                    start = cell_center(*part.prev_pos) if part.prev_pos else end
                    draw_tile(part, lerp(start, end, ease_out(slide)))
            else:
                # Step 2: new tiles grow in from nothing, merged tiles pulse.
                if tile.is_new:
                    scale = ease_out(pop)
                elif tile.merged_from:
                    scale = 1 + PULSE_SIZE * math.sin(math.pi * pop)
                else:
                    scale = 1
                draw_tile(tile, end, scale)


def draw_overlay(title, lines, fade):
    """Fade out the board and show a message on top. fade goes from 0 (hidden) to 1."""
    r, g, b, a = OVERLAY_COLOR
    overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    overlay.fill((r, g, b, round(a * fade)))
    screen.blit(overlay, (0, HEADER_HEIGHT))

    alpha = round(255 * fade)
    center_x = BOARD_SIZE // 2
    center_y = HEADER_HEIGHT + BOARD_SIZE // 2
    draw_text(title, 60, OVERLAY_TEXT, (center_x, center_y - 40), alpha)
    for n, line in enumerate(lines):
        draw_text(line, 25, OVERLAY_TEXT, (center_x, center_y + 25 + n * 35), alpha)


# ---------- Game loop ----------

def win_screen_showing(board):
    """The "YOU WIN!" screen stays up until the player presses C or R."""
    return board.has_won() and not board.keep_playing


def main():
    board = Board()
    best_score = load_best_score()
    move_time = pygame.time.get_ticks()   # when the last move started (drives tile animations)
    score_popups = []                     # (points, start time) for each "+points" text
    overlay_time = None                   # when the win / game-over screen starts fading in
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board.reset()
                    move_time = now
                    score_popups = []

                elif event.key == pygame.K_c and win_screen_showing(board):
                    board.keep_playing = True

                elif event.key in KEY_DIRECTIONS and not win_screen_showing(board):
                    old_score = board.score
                    moved = board.move(KEY_DIRECTIONS[event.key])
                    if moved:   # only add a tile (and animate) if the move did something
                        board.spawn_tile()
                        move_time = now
                        if board.score > old_score:
                            score_popups.append((board.score - old_score, now))

        if board.score > best_score:
            best_score = board.score
            save_best_score(best_score)

        # Forget score popups that have finished floating away.
        score_popups = [(points, start) for points, start in score_popups
                        if now - start < SCORE_POPUP_TIME]

        draw_header(board.score, best_score, score_popups)
        draw_board(board, move_time)

        if win_screen_showing(board):
            overlay = ("YOU WIN!", ["Press C to keep going", "Press R to restart"])
        elif board.check_game_over():
            overlay = ("GAME OVER", ["Press R to restart"])
        else:
            overlay = None

        if overlay is None:
            overlay_time = None
        else:
            if overlay_time is None:
                overlay_time = now + OVERLAY_DELAY   # let the last move finish first
            title, lines = overlay
            draw_overlay(title, lines, progress(overlay_time, OVERLAY_FADE_TIME))

        pygame.display.flip()
        clock.tick(FPS)   # cap the frame rate so the game doesn't max out the CPU

    pygame.quit()


if __name__ == "__main__":
    main()
