import sys
import random
import math
import json
import os
import pygame
import pathlib
from datetime import datetime
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL import GL_PROJECTION, GL_MODELVIEW, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, \
    GL_DEPTH_TEST, GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL, GL_BLEND, GL_SRC_ALPHA, \
    GL_ONE_MINUS_SRC_ALPHA, GL_FRONT, GL_AMBIENT_AND_DIFFUSE, GL_FRONT_AND_BACK, \
    GL_SPECULAR, GL_SHININESS, GL_POSITION, GL_DIFFUSE, GL_CONSTANT_ATTENUATION, \
    GL_VIEWPORT, GL_LINE_SMOOTH, GL_POLYGON_OFFSET_LINE
################################################################################
#                               GLOBAL CONSTANTS                               #
################################################################################

GRID_SIZE = (8, 20, 8)    # (x, y, z) dimensions of the Tetris playfield
BLOCK_SIZE = 1.0         # Size of each cube in the Tetris blocks
FALL_INTERVAL_MS = 500   # How often (milliseconds) a piece falls one step
CAMERA_DIST_MIN = 15.0    # Minimum zoom distance
CAMERA_DIST_MAX = 80.0    # Maximum zoom distance


# Possible colors for newly spawned blocks
CYBER_COLORS = [
    (0.0, 1.0, 1.0),     # Light Blue/Cyan (I-piece)
    (1.0, 1.0, 0.0),     # Yellow (O-piece/Cube)
    (1.0, 0.647, 0.0),   # Orange (L-piece) [255/255, 165/255, 0/255]
    (0.0, 0.0, 1.0),     # Blue (J-piece)
    (0.5, 0.0, 0.5),     # Purple (T-piece) [128/255, 0/255, 128/255]
    (0.0, 1.0, 0.0),     # Green (S-piece)
    (1.0, 0.0, 0.0),     # Red (Z-piece)
]

# 3D Tetromino-like shapes (sample shapes).
# Each shape is a list containing tuples of offsets (x, y, z).
SHAPES_3D = [
    # I-shaped (4 blocks in a line)
    [(0,0,0), (1,0,0), (2,0,0), (3,0,0)],
    # Cube (2x2x2)
    [(0,0,0), (1,0,0), (0,1,0), (1,1,0),
     (0,0,1), (1,0,1), (0,1,1), (1,1,1)],
    # L-shaped
    [(0,0,0), (1,0,0), (2,0,0), (2,1,0)],
    # J-shaped (mirrored L)
    [(0,0,0), (1,0,0), (2,0,0), (0,1,0)],
    # T-shaped
    [(0,0,0), (1,0,0), (2,0,0), (1,1,0)],
    # S-shaped
    [(1,0,0), (2,0,0), (0,1,0), (1,1,0)],
    # Z-shaped
    [(0,0,0), (1,0,0), (1,1,0), (2,1,0)]
]

# Game states
STATE_LOADING   = 0
STATE_MAIN_MENU = 1
STATE_PLAYING   = 2
STATE_PAUSED    = 3
STATE_GAME_OVER = 4

# Loading screen settings
LOADING_DURATION = 3000   # Auto-advance after 3 seconds

# A convenient color for 2D text
TEXT_COLOR = (0.9, 0.9, 0.9)

# High score settings
HIGHSCORE_FILE = "highscores.json"
MAX_HIGHSCORES = 10  # Maximum number of high scores to keep


################################################################################
#                               GAMESTATE CLASS                                #
################################################################################
MUSIC_VOLUME_DEFAULT = 0.2
MUSIC_VOLUME_STEP = 0.1

class MusicManager:
    def __init__(self):
        pygame.init() 
        # Initialize mixer with high quality settings
        pygame.mixer.pre_init(44100, -16, 2, 2048)  # CD quality audio
        pygame.mixer.init(frequency=44100,  # Sample rate (44.1kHz - CD quality)
                         size=-16,          # 16-bit sound
                         channels=2,        # Stereo
                         buffer=2048)       # Lower buffer = less latency
        self.volume = MUSIC_VOLUME_DEFAULT
        self.is_muted = False
        self.played_songs = []  # Track recently played songs
        # Load sound effects
        sounds_dir = pathlib.Path(__file__).parent / "Sounds"
        self.click_sound = pygame.mixer.Sound(str(sounds_dir / "click.wav"))
        self.plop_sound = pygame.mixer.Sound(str(sounds_dir / "plop.wav"))
        
        self._load_and_play_music()

    def play_game_sound(self, action_type):
        """Play appropriate sound based on game action"""
        if not self.is_muted:
            if action_type in ('move', 'rotate'):
                self.click_sound.play()
            elif action_type in ('land', 'drop'):
                self.plop_sound.play()

    def next_song(self):
        """Skip to next song"""
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self._load_and_play_music()

    def _load_and_play_music(self):
        try:
            # Get music directory path
            music_dir = pathlib.Path(__file__).parent / "Songs"
            music_dir.mkdir(exist_ok=True)
            
            # Find all music files
            music_files = list(music_dir.glob("*.mp3")) + \
                         list(music_dir.glob("*.ogg")) + \
                         list(music_dir.glob("*.wav"))
            
            if music_files:
                # Choose a random song that wasn't recently played
                available_songs = [s for s in music_files if s not in self.played_songs]
                if not available_songs:  # If all songs were played, reset history
                    self.played_songs = []
                    available_songs = music_files
                    
                next_song = random.choice(available_songs)
                self.played_songs.append(next_song)
                
                pygame.mixer.music.load(str(next_song))
                pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
                pygame.mixer.music.play()
                
        except Exception as e:
            print(f"Could not load music: {e}")



    def toggle_mute(self):
        self.is_muted = not self.is_muted
        pygame.mixer.music.set_volume(0.0 if self.is_muted else self.volume)

    def adjust_volume(self, increase=True):
        if increase:
            self.volume = min(1.0, self.volume + MUSIC_VOLUME_STEP)
        else:
            self.volume = max(0.0, self.volume - MUSIC_VOLUME_STEP)
        
        if not self.is_muted:
            pygame.mixer.music.set_volume(self.volume)

    def cleanup(self):
        pygame.mixer.quit()
        pygame.quit() 

class HighScoreManager:
    def __init__(self):
        self.highscores = []
        self.load_highscores()

    def load_highscores(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    self.highscores = json.load(f)
        except Exception as e:
            print(f"Error loading highscores: {e}")
            self.highscores = []

    def save_highscores(self):
        try:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump(self.highscores, f, indent=2)
        except Exception as e:
            print(f"Error saving highscores: {e}")

    def add_score(self, score):
        """Returns True if this is a new high score"""
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        score_entry = {"score": score, "date": date_str}
        
        # Check if it's a high score
        is_high_score = False
        if len(self.highscores) < MAX_HIGHSCORES:
            is_high_score = True
        elif self.highscores and score > min(entry["score"] for entry in self.highscores):
            is_high_score = True
        
        if is_high_score:
            self.highscores.append(score_entry)
            # Sort by score (highest first)
            self.highscores.sort(key=lambda x: x["score"], reverse=True)
            # Keep only top scores
            self.highscores = self.highscores[:MAX_HIGHSCORES]
            self.save_highscores()
            
        return is_high_score

    def get_highscores(self):
        return self.highscores

class GameState:
    """
    Holds the 3D Tetris board, scores, and references to pieces:
      - last_piece (the one just locked)
      - current_piece
      - next_piece
    The grid is a 3D array storing either None (empty) or (r, g, b) for a filled cell.
    """

    def __init__(self):
        self.reset_grid()
        self.score = 0
        self.game_over = False
        self.last_piece = None
        self.current_piece = None
        self.next_piece = None
        self.highscore_manager = HighScoreManager()
        self.is_new_highscore = False
        self.piece_bag = [] 
        self.music_manager = MusicManager()


    def reset_grid(self):
        self.grid = [
            [
                [None for _ in range(GRID_SIZE[2])]
                for _ in range(GRID_SIZE[1])
            ]
            for _ in range(GRID_SIZE[0])
        ]
        self.score = 0
        self.is_new_highscore = False


    def spawn_new_piece(self):
        """
        Move 'next_piece' -> 'current_piece', and generate a new 'next_piece'.
        Uses a bag system to ensure fair piece distribution.
        """
        # Refill bag if empty
        if not self.piece_bag:
            self.piece_bag = list(range(len(SHAPES_3D)))
            random.shuffle(self.piece_bag)
        
        if self.current_piece is None:
            # This is the very beginning
            shape_index = self.piece_bag.pop()
            self.current_piece = Tetromino()
            self.current_piece.shape = list(SHAPES_3D[shape_index])
            self.current_piece.color = CYBER_COLORS[shape_index]
            
            shape_index = self.piece_bag.pop()
            self.next_piece = Tetromino()
            self.next_piece.shape = list(SHAPES_3D[shape_index])
            self.next_piece.color = CYBER_COLORS[shape_index]
        else:
            self.current_piece = self.next_piece
            shape_index = self.piece_bag.pop()
            self.next_piece = Tetromino()
            self.next_piece.shape = list(SHAPES_3D[shape_index])
            self.next_piece.color = CYBER_COLORS[shape_index]

        # If new piece is colliding immediately, game over
        if self.check_collision(self.current_piece.position):
            self.game_over = True

    def check_collision(self, position):
        """
        Check if the current piece at 'position' goes out of bounds or hits a filled cell.
        """
        for (ox, oy, oz) in self.current_piece.shape:
            x = position[0] + ox
            y = position[1] + oy
            z = position[2] + oz
            if x < 0 or x >= GRID_SIZE[0]:
                return True
            if y < 0 or y >= GRID_SIZE[1]:
                return True
            if z < 0 or z >= GRID_SIZE[2]:
                return True
            if self.grid[x][y][z] is not None:
                return True
        return False

    def lock_piece_and_clear(self):
        """
        When a piece can no longer move, store its blocks in the grid,
        check for completed layers, update score, set last_piece,
        then spawn new piece.
        """
        # Lock the current piece into the grid
        cpos = self.current_piece.position
        ccol = self.current_piece.color
        for (ox, oy, oz) in self.current_piece.shape:
            x = cpos[0] + ox
            y = cpos[1] + oy
            z = cpos[2] + oz
            if 0 <= x < GRID_SIZE[0] and 0 <= y < GRID_SIZE[1] and 0 <= z < GRID_SIZE[2]:
                self.grid[x][y][z] = ccol

        # Set last_piece reference
        self.last_piece = self.current_piece.clone()

        # Check for full layers
        layers_cleared = 0
        y = 0
        while y < GRID_SIZE[1]:
            layer_full = True
            # Check if the current layer is full
            for x in range(GRID_SIZE[0]):
                for z in range(GRID_SIZE[2]):
                    if self.grid[x][y][z] is None:
                        layer_full = False
                        break
                if not layer_full:
                    break
                    
            if layer_full:
                layers_cleared += 1
                # Move all layers above down by one
                for move_y in range(y, GRID_SIZE[1] - 1):
                    for x in range(GRID_SIZE[0]):
                        for z in range(GRID_SIZE[2]):
                            self.grid[x][move_y][z] = self.grid[x][move_y + 1][z]
                
                # Clear the top layer
                for x in range(GRID_SIZE[0]):
                    for z in range(GRID_SIZE[2]):
                        self.grid[x][GRID_SIZE[1] - 1][z] = None
                
                # Don't increment y since we need to check the same level again
                # after moving everything down
            else:
                y += 1

        # Update score based on layers cleared
        if layers_cleared > 0:
            # Scoring system:
            # 1 layer = 100 points
            # 2 layers = 300 points
            # 3 layers = 500 points
            # 4 layers = 800 points
            scores = {
                1: 100,
                2: 300,
                3: 500,
                4: 800
            }
            self.score += scores.get(layers_cleared, layers_cleared * 100)

        # Also add points for placing a piece (10 points per block)
        self.score += len(self.current_piece.shape) * 10

        # Spawn next piece
        self.spawn_new_piece()

################################################################################
#                              TETROMINO CLASS                                 #
################################################################################

class Tetromino:
    """
    A 3D Tetris piece with:
      - shape: a list of (x,y,z) offsets
      - position: [x,y,z]
      - color
    Rotation is handled via Q and E keys.
    """

    # Class variable to keep track of color usage
    used_colors = []

    def __init__(self):
        # Get a random shape index
        shape_index = random.randrange(len(SHAPES_3D))
        
        # Assign the shape and its corresponding color
        self.shape = SHAPES_3D[shape_index]
        self.color = CYBER_COLORS[shape_index]
        
        # Set initial position
        self.position = [GRID_SIZE[0] // 2, GRID_SIZE[1] - 3, GRID_SIZE[2] // 2]

    def move(self, dx, dy, dz):
        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz

    def rotate(self, axis):
        """
        Rotate the piece 90 degrees around the specified axis (0=x, 1=y, 2=z).
        Uses right-hand rule for rotation direction.
        """
        rotated_shape = []
        for (x, y, z) in self.shape:
            if axis == 0:  # Rotate around X-axis
                rotated = (x, -z, y)
            elif axis == 1:  # Rotate around Y-axis
                rotated = (-z, y, x)  # Counter-clockwise around Y
            elif axis == 2:  # Rotate around Z-axis
                rotated = (-y, x, z)  # Counter-clockwise around Z
            rotated_shape.append(rotated)
        self.shape = rotated_shape


    def clone(self):
        """
        Simple clone: used for storing 'last_piece' reference.
        """
        clone_piece = Tetromino()
        clone_piece.shape = list(self.shape)
        clone_piece.position = list(self.position)
        clone_piece.color = self.color
        return clone_piece

################################################################################
#                            OPENGL / GLUT GLOBALS                             #
################################################################################

game_state = GameState()
current_mode = STATE_LOADING

previous_time = 0
time_accumulator_fall = 0

# Camera
mouse_down = False
mouse_last_x = 0
mouse_last_y = 0
camera_rot_x = 25.0    # up-down rotation
camera_rot_y = -45.0   # left-right rotation
camera_dist = 30.0     # zoom distance

loading_start_time = 0

################################################################################
#                                INIT OPENGL                                   #
################################################################################

def init_gl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glLightfv(GL_LIGHT0, GL_POSITION,  [5.0, 15.0, 5.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,   [0.5, 0.5, 0.5, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR,  [0.2, 0.2, 0.2, 1.0])
    glLightf(GL_LIGHT0,  GL_CONSTANT_ATTENUATION, 0.1)

    glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 50)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

################################################################################
#                                   DRAWING                                    #
################################################################################

def draw_text_2d(x, y, text, size=18, color=(1,1,1)):
    """
    Draw 2D text at (x, y) in window coords. (0,0)=bottom-left corner.
    """
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, glutGet(GLUT_WINDOW_WIDTH), 0, glutGet(GLUT_WINDOW_HEIGHT))
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glColor3f(*color)
    glRasterPos2f(x, y)

    font = GLUT_BITMAP_HELVETICA_18
    if size == 12:
        font = GLUT_BITMAP_HELVETICA_12
    elif size == 10:
        font = GLUT_BITMAP_HELVETICA_10

    for c in text:
        glutBitmapCharacter(font, ord(c))

    glEnable(GL_LIGHTING)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_grid():
    """
    Draw a more subtle grid with drop indicators for better spatial awareness.
    """
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw floor grid (slightly darker and more visible)
    glLineWidth(1.5)  # Increased line width
    glColor4f(0.4, 0.4, 0.8, 0.6)  # More visible grid color
    glBegin(GL_LINES)
    # Draw floor grid lines
    for x in range(GRID_SIZE[0] + 1):
        glVertex3f(x, 0, 0)
        glVertex3f(x, 0, GRID_SIZE[2])
    for z in range(GRID_SIZE[2] + 1):
        glVertex3f(0, 0, z)
        glVertex3f(GRID_SIZE[0], 0, z)
    glEnd()
    
    # Draw wall grids with increased visibility
    glColor4f(0.4, 0.4, 0.8, 0.3)  # More visible wall grid
    glBegin(GL_LINES)
    # Back wall
    for x in range(GRID_SIZE[0] + 1):
        glVertex3f(x, 0, 0)
        glVertex3f(x, GRID_SIZE[1], 0)
    for y in range(GRID_SIZE[1] + 1):
        glVertex3f(0, y, 0)
        glVertex3f(GRID_SIZE[0], y, 0)
    glEnd()

    glEnable(GL_LIGHTING)

    # Draw drop indicators if we have a current piece
    if game_state.current_piece and not game_state.game_over:
        draw_drop_indicators()

    glEnable(GL_LIGHTING)


def draw_drop_indicators():
    """
    Draw helpful indicators showing where the current piece will land.
    """
    if not game_state.current_piece:
        return

    # Find landing position
    landing_y = find_landing_position()
    
    # Draw vertical guide lines from piece to landing position
    glLineWidth(2.0)
    glColor4f(1.0, 1.0, 1.0, 0.3)  # White, semi-transparent
    
    cpos = game_state.current_piece.position
    for block in game_state.current_piece.shape:
        x = cpos[0] + block[0]
        y = cpos[1] + block[1]
        z = cpos[2] + block[2]
        
        # Draw vertical guide line
        glBegin(GL_LINES)
        glVertex3f(x + 0.5, y + 0.5, z + 0.5)
        glVertex3f(x + 0.5, landing_y + block[1] + 0.5, z + 0.5)
        glEnd()
        
        # Draw landing position indicator (outlined cube)
        draw_landing_block_indicator(
            (x, landing_y + block[1], z),
            game_state.current_piece.color
        )

def draw_landing_block_indicator(pos, color):
    """
    Draw a semi-transparent outline where the block will land.
    """
    x, y, z = pos
    glPushMatrix()
    glTranslatef(x + 0.5, y + 0.5, z + 0.5)
    
    # Draw semi-transparent face with improved visibility
    glColor4f(*color, 0.4)  # Increased alpha for better visibility
    glLineWidth(2.0)  # Thicker lines
    glutWireCube(BLOCK_SIZE * 0.95)
    
    # Add inner wireframe for better depth perception
    glColor4f(*color, 0.2)
    glLineWidth(1.0)
    glutWireCube(BLOCK_SIZE * 0.85)
    
    glPopMatrix()

def find_landing_position():
    """
    Find the Y position where the current piece will land.
    """
    if not game_state.current_piece:
        return 0
        
    test_pos = list(game_state.current_piece.position)
    while test_pos[1] > 0:
        test_pos[1] -= 1
        # Store current position
        current_pos = list(game_state.current_piece.position)
        # Temporarily move piece to test position
        game_state.current_piece.position = test_pos
        if game_state.check_collision(test_pos):
            # Restore position and return the last valid Y
            game_state.current_piece.position = current_pos
            return test_pos[1] + 1
        # Restore position for next iteration
        game_state.current_piece.position = current_pos
    return 0

def draw_block(pos, color):
    """
    Draw a single block with improved visual appearance.
    """
    glPushMatrix()
    glTranslatef(pos[0] + 0.5, pos[1] + 0.5, pos[2] + 0.5)
    
    # Draw main cube slightly smaller
    glColor3f(*color)
    glutSolidCube(BLOCK_SIZE * 0.9)  # Slightly smaller cube
    
    # Draw darker edges for definition
    glColor4f(color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, 1.0)
    glLineWidth(2.0)  # Thicker lines
    glutWireCube(BLOCK_SIZE * 0.91)  # Slightly larger than the solid cube
    
    # Draw bright highlights
    glColor4f(min(color[0] * 1.2, 1.0), min(color[1] * 1.2, 1.0), min(color[2] * 1.2, 1.0), 0.5)
    glLineWidth(1.0)
    glutWireCube(BLOCK_SIZE * 0.89)  # Slightly smaller than the solid cube
    
    glPopMatrix()

def draw_scene_3d():
    """
    Draw the main Tetris scene in 3D (grid, blocks, current piece).
    """
    # Center the grid in the scene
    glTranslatef(-GRID_SIZE[0]/2, -GRID_SIZE[1]/2, -GRID_SIZE[2]/2)

    # Draw the grid lines
    draw_grid()

    # Draw settled blocks
    for x in range(GRID_SIZE[0]):
        for y in range(GRID_SIZE[1]):
            for z in range(GRID_SIZE[2]):
                cell_color = game_state.grid[x][y][z]
                if cell_color is not None:
                    draw_block((x, y, z), cell_color)

    # Draw the current piece if present (and not game over, though we can keep showing it)
    if game_state.current_piece and not game_state.game_over:
        cpos = game_state.current_piece.position
        ccol = game_state.current_piece.color
        for (ox, oy, oz) in game_state.current_piece.shape:
            bx = cpos[0] + ox
            by = cpos[1] + oy
            bz = cpos[2] + oz
            draw_block((bx, by, bz), ccol)

def draw_piece_preview(piece, x_viewport, y_viewport, w_viewport, h_viewport, label):
    """
    Draw a small 3D preview of the given piece in a separate viewport region,
    typically at the top-right corner. Also draw a label above it.
    """
    if piece is None:
        return

    # Save main viewport
    main_viewport = glGetIntegerv(GL_VIEWPORT)

    # Set new viewport for the preview
    glViewport(x_viewport, y_viewport, w_viewport, h_viewport)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluPerspective(35.0, w_viewport / float(h_viewport), 0.1, 100.0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Position camera for the preview
    glTranslatef(0, 0, -10)
    glRotatef(30, 1, 0, 0)
    glRotatef(-30, 0, 1, 0)

    # Draw the piece in a small bounding box
    # Center it by finding the shape's bounds
    xs = [b[0] for b in piece.shape]
    ys = [b[1] for b in piece.shape]
    zs = [b[2] for b in piece.shape]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    cz = (minz + maxz) / 2.0

    for (ox, oy, oz) in piece.shape:
        bx = ox - cx
        by = oy - cy
        bz = oz - cz
        glPushMatrix()
        glTranslatef(bx, by, bz)
        glColor3f(*piece.color)
        glutSolidCube(0.9)  # Slightly smaller cubes
        glPopMatrix()

    # Reset back to main viewport
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glViewport(*main_viewport)

    # Draw label in 2D above that viewport (e.g., near x_viewport, y_viewport + h_viewport)
    draw_text_2d(x_viewport, y_viewport + h_viewport + 2, label, 12, TEXT_COLOR)

def display():
    """
    GLUT display function.
    """
    glClearColor(0.05, 0.05, 0.1, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 3D camera setup
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, glutGet(GLUT_WINDOW_WIDTH)/float(glutGet(GLUT_WINDOW_HEIGHT)), 0.1, 200.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -camera_dist)
    glRotatef(camera_rot_x, 1.0, 0.0, 0.0)
    glRotatef(camera_rot_y, 0.0, 1.0, 0.0)

    # If we're in a gameplay-related state, draw the Tetris scene
    if current_mode in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
        draw_scene_3d()

    # 2D overlays or separate screens:
    if current_mode == STATE_LOADING:
        elapsed = glutGet(GLUT_ELAPSED_TIME) - loading_start_time
        # Animate the LOADING text color
        r = abs(math.sin(elapsed * 0.005))
        g = abs(math.sin(elapsed * 0.003 + 2))
        b = abs(math.sin(elapsed * 0.004 + 4))
        draw_text_2d(100, 300, "LOADING...", 18, (r, g, b))
        draw_text_2d(100, 260, "Press ENTER to skip", 12, TEXT_COLOR)

    elif current_mode == STATE_MAIN_MENU:
        # Setup demo game if needed
        if not game_state.current_piece:
            game_state.reset_grid()
            game_state.piece_bag = list(range(len(SHAPES_3D)))
            random.shuffle(game_state.piece_bag)
            game_state.spawn_new_piece()
            game_state.game_over = False
        
        # Demo gameplay
        if game_state.current_piece:
            # Make random moves
            if random.random() < 0.02:
                move = random.choice(['move', 'rotate', 'drop'])
                if move == 'move':
                    direction = random.choice([(1,0,0), (-1,0,0), (0,0,1), (0,0,-1)])
                    game_state.current_piece.move(*direction)
                    if game_state.check_collision(game_state.current_piece.position):
                        game_state.current_piece.move(-direction[0], 0, -direction[2])
                elif move == 'rotate':
                    game_state.current_piece.rotate(random.choice([0,1,2]))
                elif move == 'drop':
                    while not game_state.check_collision(game_state.current_piece.position):
                        game_state.current_piece.move(0, -1, 0)
                    game_state.current_piece.move(0, 1, 0)
                    game_state.lock_piece_and_clear()

            # Normal falling
            if glutGet(GLUT_ELAPSED_TIME) % 500 < 16:
                old_pos = list(game_state.current_piece.position)
                game_state.current_piece.move(0, -1, 0)
                if game_state.check_collision(game_state.current_piece.position):
                    game_state.current_piece.position = old_pos
                    game_state.lock_piece_and_clear()

            # Reset if game over
            if game_state.game_over:
                game_state.reset_grid()
                game_state.piece_bag = list(range(len(SHAPES_3D)))
                random.shuffle(game_state.piece_bag)
                game_state.spawn_new_piece()
                game_state.game_over = False

        # Auto-rotate camera
        glRotatef(glutGet(GLUT_ELAPSED_TIME) * 0.01, 0, 1, 0)

        # Draw the game scene
        draw_scene_3d()
        
        # Draw menu text on top
        draw_text_2d(100, 400, "AIGleam 3D TETRIS", 18, (0.2, 0.8, 1.0))
        draw_text_2d(100, 350, "Press [S] to START", 14, TEXT_COLOR)
        draw_text_2d(100, 320, "Press [ESC] to QUIT", 14, TEXT_COLOR)

        # Draw high scores
        draw_text_2d(100, 280, "HIGH SCORES:", 14, (1.0, 0.8, 0.2))
        for i, entry in enumerate(game_state.highscore_manager.get_highscores()):
            score_text = f"{i+1}. {entry['score']:,} - {entry['date']}"
            draw_text_2d(100, 250 - (i * 20), score_text, 12, TEXT_COLOR)

    elif current_mode == STATE_PLAYING:
        score_str = f"SCORE: {game_state.score}"
        draw_text_2d(20, glutGet(GLUT_WINDOW_HEIGHT) - 40, score_str, 18, (0.2, 0.8, 1.0))

        # Draw next piece and last piece previews in the top-right corner
        screen_w = glutGet(GLUT_WINDOW_WIDTH)
        screen_h = glutGet(GLUT_WINDOW_HEIGHT)
        # Next piece preview
        draw_piece_preview(
            game_state.next_piece,
            screen_w - 220,  # x
            screen_h - 220,  # y
            200,             # w
            200,             # h
            "NEXT"
        )
        # Last piece preview
        draw_piece_preview(
            game_state.last_piece,
            screen_w - 220,
            screen_h - 440,
            200,
            200,
            "LAST"
        )

    elif current_mode == STATE_PAUSED:
        draw_text_2d(300, 360, "PAUSED", 18, (1.0, 1.0, 0.0))
        draw_text_2d(220, 320, "Press [P] to Resume   [ESC] to Quit to Menu", 14, TEXT_COLOR)
        score_str = f"SCORE: {game_state.score}"
        draw_text_2d(20, glutGet(GLUT_WINDOW_HEIGHT) - 40, score_str, 18, (0.2, 0.8, 1.0))

    elif current_mode == STATE_GAME_OVER:
        draw_text_2d(300, 380, "GAME OVER", 18, (1.0, 0.2, 0.2))
        score_str = f"Your Score: {game_state.score:,}"
        draw_text_2d(300, 340, score_str, 14, (1.0, 1.0, 0.0))
        
        # Check and display high score status
        if game_state.is_new_highscore:  # Use the flag instead of calling the method
            draw_text_2d(300, 320, "NEW HIGH SCORE!", 14, (1.0, 0.8, 0.2))
        
        # Display high scores
        draw_text_2d(300, 280, "HIGH SCORES:", 14, (1.0, 0.8, 0.2))
        for i, entry in enumerate(game_state.highscore_manager.get_highscores()[:5]):  # Show top 5 in game over
            score_text = f"{i+1}. {entry['score']:,} - {entry['date']}"
            draw_text_2d(300, 250 - (i * 20), score_text, 12, TEXT_COLOR)
            
        draw_text_2d(250, 120, "[R] Restart   [ESC] Main Menu", 14, TEXT_COLOR)


    glutSwapBuffers()

################################################################################
#                               STATE MACHINE                                  #
################################################################################

def set_mode(new_mode):
    global current_mode
    print(f"Setting mode from {current_mode} to {new_mode}")  # Debug print
    current_mode = new_mode
    if new_mode == STATE_GAME_OVER:
        game_state.is_new_highscore = game_state.highscore_manager.add_score(game_state.score)
    elif new_mode == STATE_LOADING:
        loading_start_time = glutGet(GLUT_ELAPSED_TIME)
    elif new_mode == STATE_MAIN_MENU:
        game_state.reset_grid()
        game_state.score = 0
        game_state.game_over = False
        game_state.last_piece = None
        game_state.current_piece = None
        game_state.next_piece = None

################################################################################
#                                 GLUT CALLBACKS                               #
################################################################################

def reshape(w, h):
    """
    When window is resized.
    """
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, w/float(h), 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard(key, x, y):
    """
    Update keyboard handler to use improved WASD movement and consistent rotations.
    Q: Always rotates counter-clockwise around Y axis
    E: Always rotates clockwise around Y axis
    R: Always rotates clockwise around Z axis
    """
    global current_mode, camera_dist

    # Handle pause state changes
    if key in (b'p', b'P'):
        if current_mode == STATE_PLAYING:
            current_mode = STATE_PAUSED
            glutPostRedisplay()
            return
        elif current_mode == STATE_PAUSED:
            current_mode = STATE_PLAYING
            glutPostRedisplay()
            return

    if key == b'm':  # Toggle music
        game_state.music_manager.toggle_mute()
    elif key == b'6':  # Volume down
        game_state.music_manager.adjust_volume(False)
    elif key == b'7':  # Volume up
        game_state.music_manager.adjust_volume(True)
    elif key == b'8':  # Skip to next song
        game_state.music_manager.next_song()

    glutPostRedisplay()

    # Handle space bar for hard drop - MOVED THIS SECTION BEFORE THE WASD CHECK
    if current_mode == STATE_PLAYING and not game_state.game_over and key == b' ':
        if game_state.current_piece:
            # Keep moving down until collision
            while True:
                old_pos = list(game_state.current_piece.position)
                game_state.current_piece.move(0, -1, 0)
                if game_state.check_collision(game_state.current_piece.position):
                    game_state.current_piece.position = old_pos
                    game_state.lock_piece_and_clear()
                    break
            glutPostRedisplay()
            return

    # Handle WASD movement if in playing state
    if current_mode == STATE_PLAYING and not game_state.game_over and game_state.current_piece:
        if key in (b'w', b'W', b'a', b'A', b's', b'S', b'd', b'D'):
            handle_wasd(key)
            glutPostRedisplay()
            return

        # Store original state before any rotation
        original_position = list(game_state.current_piece.position)
        original_shape = [list(block) for block in game_state.current_piece.shape]

        # Handle rotations
        if key in (b'q', b'Q'):
            # Single counter-clockwise rotation around Y axis
            game_state.current_piece.rotate(axis=1)
            if game_state.check_collision(game_state.current_piece.position):
                # Restore original state if collision occurs
                game_state.current_piece.position = original_position
                game_state.current_piece.shape = [tuple(block) for block in original_shape]
                
        elif key in (b'e', b'E'):
            # Single clockwise rotation around Y axis (three counter-clockwise rotations)
            for _ in range(3):
                game_state.current_piece.rotate(axis=1)
            if game_state.check_collision(game_state.current_piece.position):
                # Restore original state if collision occurs
                game_state.current_piece.position = original_position
                game_state.current_piece.shape = [tuple(block) for block in original_shape]
                
        elif key in (b'r', b'R'):
            # Single clockwise rotation around Z axis
            game_state.current_piece.rotate(axis=2)
            if game_state.check_collision(game_state.current_piece.position):
                # Restore original state if collision occurs
                game_state.current_piece.position = original_position
                game_state.current_piece.shape = [tuple(block) for block in original_shape]

        glutPostRedisplay()
        return

    # ESC: either quit or go back to main menu
    if key == b'\x1b':  # ESC
        if current_mode in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
            set_mode(STATE_MAIN_MENU)
        elif current_mode == STATE_MAIN_MENU:
            sys.exit(0)
        else:
            sys.exit(0)
        return

    if current_mode == STATE_LOADING:
        if key == b'\r':  # ENTER
            set_mode(STATE_MAIN_MENU)

    elif current_mode == STATE_MAIN_MENU:
        if key in (b's', b'S'):
            game_state.reset_grid()
            game_state.score = 0
            game_state.game_over = False
            game_state.current_piece = None
            game_state.next_piece = None
            game_state.spawn_new_piece()
            set_mode(STATE_PLAYING)


    elif current_mode == STATE_PLAYING:
        if game_state.game_over:
            set_mode(STATE_GAME_OVER)
            return

    elif current_mode == STATE_GAME_OVER:
        if key in (b'r', b'R'):
            # Reset game state
            game_state.reset_grid()
            game_state.score = 0
            game_state.game_over = False
            game_state.current_piece = None
            game_state.next_piece = None
            game_state.spawn_new_piece()
            game_state.is_new_highscore = False
            set_mode(STATE_PLAYING)

    glutPostRedisplay()

def special_input(key, x, y):
    """
    Handle special keys like WASD for movement.
    """
    if current_mode == STATE_PLAYING and not game_state.game_over and game_state.current_piece:
        # Calculate movement relative to camera orientation
        # Compute forward and right vectors based on camera_rot_y
        angle_rad = math.radians(camera_rot_y)
        forward_x = math.sin(angle_rad)
        forward_z = -math.cos(angle_rad)
        right_x = math.cos(angle_rad)
        right_z = math.sin(angle_rad)

        move_x, move_z = 0, 0

        if key == GLUT_KEY_UP or key == GLUT_KEY_RIGHT:
            pass  # Not used, since we're using WASD
        elif key == GLUT_KEY_DOWN or key == GLUT_KEY_LEFT:
            pass  # Not used, since we're using WASD

        # WASD mapping
        # Retrieve the last pressed key to handle continuous movement if desired
        # For simplicity, we'll handle discrete movement per key press

    glutPostRedisplay()

def special_keys(key, x, y):
    """
    Handle WASD keys for movement.
    """
    if current_mode == STATE_PLAYING and not game_state.game_over and game_state.current_piece:
        angle_rad = math.radians(camera_rot_y)
        forward_x = math.sin(angle_rad)
        forward_z = -math.cos(angle_rad)
        right_x = math.cos(angle_rad)
        right_z = math.sin(angle_rad)

        move_x, move_z = 0, 0

        if key in (GLUT_KEY_F1,):  # Not used
            pass
        # WASD keys
        elif key == GLUT_KEY_UP:
            # Equivalent to 'W'
            game_state.current_piece.move(int(round(forward_x)), 0, int(round(forward_z)))
            if game_state.check_collision(game_state.current_piece.position):
                game_state.current_piece.move(-int(round(forward_x)), 0, -int(round(forward_z)))
        elif key == GLUT_KEY_DOWN:
            # Equivalent to 'S'
            game_state.current_piece.move(-int(round(forward_x)), 0, -int(round(forward_z)))
            if game_state.check_collision(game_state.current_piece.position):
                game_state.current_piece.move(int(round(forward_x)), 0, int(round(forward_z)))
        elif key == GLUT_KEY_LEFT:
            # Equivalent to 'A'
            game_state.current_piece.move(-int(round(right_x)), 0, -int(round(right_z)))
            if game_state.check_collision(game_state.current_piece.position):
                game_state.current_piece.move(int(round(right_x)), 0, int(round(right_z)))
        elif key == GLUT_KEY_RIGHT:
            # Equivalent to 'D'
            game_state.current_piece.move(int(round(right_x)), 0, int(round(right_z)))
            if game_state.check_collision(game_state.current_piece.position):
                game_state.current_piece.move(-int(round(right_x)), 0, -int(round(right_z)))

    glutPostRedisplay()

def mouse_click(button, state, x, y):
    """
    Handle mouse button press/release for rotating camera.
    Also handle mouse wheel for zooming.
    """
    global mouse_down, mouse_last_x, mouse_last_y, camera_dist

    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_down = True
            mouse_last_x = x
            mouse_last_y = y
        else:
            mouse_down = False
    # Handle mouse wheel zoom
    elif button == 3 and state == GLUT_DOWN:  # Scroll up
        camera_dist = max(CAMERA_DIST_MIN, camera_dist - 2.0)
    elif button == 4 and state == GLUT_DOWN:  # Scroll down
        camera_dist = min(CAMERA_DIST_MAX, camera_dist + 2.0)

    glutPostRedisplay()

def mouse_motion(x, y):
    """
    Handle mouse dragging for camera rotation.
    """
    global mouse_down, mouse_last_x, mouse_last_y
    global camera_rot_x, camera_rot_y

    if mouse_down:
        dx = x - mouse_last_x
        dy = y - mouse_last_y
        camera_rot_y += dx * 0.3
        camera_rot_x += dy * 0.3
        # Clamp vertical rotation
        if camera_rot_x > 90:
            camera_rot_x = 90
        if camera_rot_x < -90:
            camera_rot_x = -90
        mouse_last_x = x
        mouse_last_y = y
        glutPostRedisplay()

def mouse_wheel(button, direction, x, y):
    """
    Handle mouse wheel for zooming in and out.
    """
    global camera_dist
    if direction > 0:
        camera_dist -= 2.0
        if camera_dist < CAMERA_DIST_MIN:
            camera_dist = CAMERA_DIST_MIN
    else:
        camera_dist += 2.0
        if camera_dist > CAMERA_DIST_MAX:
            camera_dist = CAMERA_DIST_MAX
    glutPostRedisplay()

################################################################################
#                                GAME LOOP                                     #
################################################################################

def game_loop(value):
    global previous_time, time_accumulator_fall

    current_time = glutGet(GLUT_ELAPSED_TIME)
    delta_time = current_time - previous_time
    previous_time = current_time

    # Always process music events regardless of game state
    for event in pygame.event.get():
        if event.type == pygame.USEREVENT:  # Music ended
            game_state.music_manager.next_song()

    # Only process game updates if in PLAYING state (not paused or other states)
    if current_mode == STATE_PLAYING and not game_state.game_over:
        time_accumulator_fall += delta_time
        if time_accumulator_fall >= FALL_INTERVAL_MS:
            time_accumulator_fall -= FALL_INTERVAL_MS
            if game_state.current_piece:  # Add safety check
                # Move piece down
                old_pos = list(game_state.current_piece.position)
                game_state.current_piece.move(0, -1, 0)
                if game_state.check_collision(game_state.current_piece.position):
                    game_state.current_piece.position = old_pos
                    game_state.lock_piece_and_clear()
                    if game_state.game_over:
                        set_mode(STATE_GAME_OVER)

    glutPostRedisplay()
    glutTimerFunc(16, game_loop, 0)

################################################################################
#                                HELPERS                                       #
################################################################################

def handle_wasd(key):
    """
    Handle WASD key presses for movement relative to camera perspective.
    Uses camera angle to determine the most intuitive movement direction.
    """
    if current_mode != STATE_PLAYING or game_state.game_over or not game_state.current_piece:
        return

    # Calculate movement direction based on camera orientation
    angle_rad = math.radians(camera_rot_y)
    
    # Calculate primary and secondary movement vectors based on camera angle
    # This creates 8 movement sectors for more intuitive control
    forward_x = math.sin(angle_rad)
    forward_z = -math.cos(angle_rad)
    right_x = math.cos(angle_rad)
    right_z = math.sin(angle_rad)

    # Normalize the movement vectors
    length = math.sqrt(forward_x * forward_x + forward_z * forward_z)
    if length != 0:
        forward_x /= length
        forward_z /= length
    
    length = math.sqrt(right_x * right_x + right_z * right_z)
    if length != 0:
        right_x /= length
        right_z /= length

    # Determine the dominant direction based on camera angle
    # This helps snap movement to the closest grid direction
    move_x, move_z = 0, 0
    
    key = key.lower()
    if key == b'w':  # Forward
        # Use the dominant direction for more intuitive forward movement
        if abs(forward_x) > abs(forward_z):
            move_x = 1 if forward_x > 0 else -1
        else:
            move_z = 1 if forward_z > 0 else -1
    elif key == b's':  # Backward
        # Opposite of forward
        if abs(forward_x) > abs(forward_z):
            move_x = -1 if forward_x > 0 else 1
        else:
            move_z = -1 if forward_z > 0 else 1
    elif key == b'a':  # Left
        # Use the dominant direction for more intuitive sideways movement
        if abs(right_x) > abs(right_z):
            move_x = -1 if right_x > 0 else 1
        else:
            move_z = -1 if right_z > 0 else 1
    elif key == b'd':  # Right
        # Opposite of left
        if abs(right_x) > abs(right_z):
            move_x = 1 if right_x > 0 else -1
        else:
            move_z = 1 if right_z > 0 else -1

    # Try to move the piece
    if move_x != 0 or move_z != 0:
        # First try the primary movement direction
        game_state.current_piece.move(move_x, 0, move_z)
        if game_state.check_collision(game_state.current_piece.position):
            # If primary movement fails, revert and try alternative direction
            game_state.current_piece.move(-move_x, 0, -move_z)
            
            # Try alternative movement based on secondary vector component
            alt_move_x = 0 if move_x != 0 else (1 if forward_x > 0 else -1)
            alt_move_z = 0 if move_z != 0 else (1 if forward_z > 0 else -1)
            
            game_state.current_piece.move(alt_move_x, 0, alt_move_z)
            if game_state.check_collision(game_state.current_piece.position):
                # If alternative also fails, revert
                game_state.current_piece.move(-alt_move_x, 0, -alt_move_z)

################################################################################
#                                 MAIN                                        #
################################################################################

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1280, 720)
    glutCreateWindow(b"3D Tetris - AIGleam")

    # Loading screen start
    set_mode(STATE_LOADING)
    global previous_time
    previous_time = glutGet(GLUT_ELAPSED_TIME)

    init_gl()

    # Register callbacks
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse_click)
    glutMotionFunc(mouse_motion)
    
    # Mouse wheel handling is already implemented in mouse_click
    # No need for separate glutMouseWheelFunc as we're using buttons 3 and 4
    # Remove these commented sections as they're not needed:
    # glutMouseWheelFunc = None
    # glutKeyboardUpFunc = None

    glutTimerFunc(16, game_loop, 0)  # Start the game loop

    try:
        glutMainLoop()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        game_state.music_manager.cleanup()
    except Exception as e:
        # Handle other exceptions
        print(f"Error: {e}")
        game_state.music_manager.cleanup()
        raise
    finally:
        # Ensure cleanup happens no matter what
        game_state.music_manager.cleanup()

if __name__ == "__main__":
    main()
