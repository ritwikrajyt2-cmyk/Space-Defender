import cv2
import mediapipe as mp
import pygame
import random
import math
import struct
import sys


# =========================================================
# INITIALIZATION
# =========================================================

pygame.init()

try:
    pygame.mixer.init(44100, -16, 1, 512)
    SOUND_OK = True
except:
    SOUND_OK = False


# =========================================================
# SCREEN
# =========================================================

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

pygame.display.set_caption("SPACE DEFENDER - HAND CONTROL")

clock = pygame.time.Clock()

FPS = 60

WIDTH, HEIGHT = screen.get_size()


# =========================================================
# COLORS
# =========================================================

BLACK = (3, 5, 18)
WHITE = (255, 255, 255)

BLUE = (30, 130, 255)
CYAN = (0, 240, 255)

PURPLE = (150, 50, 255)
PINK = (255, 40, 190)

RED = (255, 50, 60)
DARK_RED = (120, 10, 20)

YELLOW = (255, 230, 50)
ORANGE = (255, 130, 20)

GREEN = (50, 255, 140)


# =========================================================
# FONTS
# =========================================================

font_small = pygame.font.Font(None, 28)
font_medium = pygame.font.Font(None, 44)
font_large = pygame.font.Font(None, 70)
font_title = pygame.font.Font(None, 85)


# =========================================================
# SOUND GENERATOR
# =========================================================

def make_sound(frequency, duration, volume):

    if not SOUND_OK:
        return None

    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = bytearray()

    for i in range(samples):

        t = i / sample_rate

        fade_in = min(1.0, t / 0.02)
        fade_out = min(1.0, (duration - t) / 0.05)

        envelope = min(fade_in, fade_out)

        value = int(
            32767
            * volume
            * envelope
            * math.sin(
                2 * math.pi * frequency * t
            )
        )

        data.extend(struct.pack("<h", value))

    try:
        return pygame.mixer.Sound(buffer=bytes(data))
    except:
        return None


laser_sound = make_sound(900, 0.07, 0.20)
enemy_sound = make_sound(180, 0.15, 0.45)
buff_sound = make_sound(700, 0.25, 0.45)
death_sound = make_sound(70, 0.8, 0.60)


# =========================================================
# BACKGROUND MUSIC
# =========================================================

def create_music():

    if not SOUND_OK:
        return None

    sample_rate = 44100

    notes = [
        220, 261, 330, 392,
        330, 261, 220, 196,
        220, 293, 349, 440,
        349, 293, 220, 196
    ]

    note_duration = 0.30

    data = bytearray()

    for frequency in notes:

        total_samples = int(
            sample_rate * note_duration
        )

        for i in range(total_samples):

            t = i / sample_rate

            fade = min(
                1.0,
                (note_duration - t) / 0.06
            )

            wave1 = math.sin(
                2 * math.pi * frequency * t
            )

            wave2 = math.sin(
                2 * math.pi * frequency * 2 * t
            )

            value = (
                wave1 * 0.30
                + wave2 * 0.08
            )

            sample = int(
                32767
                * value
                * fade
                * 0.18
            )

            data.extend(
                struct.pack("<h", sample)
            )

    try:
        return pygame.mixer.Sound(buffer=bytes(data))
    except:
        return None


music = create_music()

if music:

    music.set_volume(0.22)

    pygame.mixer.Channel(0).play(
        music,
        loops=-1
    )


# =========================================================
# MEDIAPIPE
# =========================================================

MODEL_PATH = "hand_landmarker.task"

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = mp.tasks.vision.HandLandmarker

HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions

RunningMode = mp.tasks.vision.RunningMode


options = HandLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),

    running_mode=RunningMode.IMAGE,

    num_hands=1,

    min_hand_detection_confidence=0.5,

    min_hand_presence_confidence=0.5,

    min_tracking_confidence=0.5
)


detector = HandLandmarker.create_from_options(
    options
)


# =========================================================
# CAMERA
# =========================================================

camera = cv2.VideoCapture(0)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    640
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    480
)

if not camera.isOpened():

    print("Camera open nahi ho raha.")

    detector.close()
    pygame.quit()

    sys.exit()


# =========================================================
# PLAYER
# =========================================================

PLAYER_W = 76
PLAYER_H = 85

player_x = WIDTH // 2
player_y = HEIGHT - 170

lives = 3
score = 0


# =========================================================
# LASERS
# =========================================================

lasers = []

laser_speed = 18

normal_fire_delay = 170

buff_fire_delay = 55

fire_timer = 0


# =========================================================
# ENEMIES
# =========================================================

enemies = []

enemy_timer = 0

enemy_delay = 850


# =========================================================
# BUFF
# =========================================================

buff_exists = False

buff_x = 0
buff_y = 0

buff_speed = 1.5

buff_active = False

buff_timer = 0

BUFF_DURATION = 5000

next_buff_timer = 6000


# =========================================================
# STARS
# =========================================================

stars = []

for i in range(180):

    stars.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.uniform(0.5, 2.5),
        random.randint(1, 3)
    ])


# =========================================================
# HAND VARIABLES
# =========================================================

hand_detected = False

hand_x = 0.5
hand_y = 0.5

smooth_x = 0.5
smooth_y = 0.5

index_finger_up = False

fire_gesture = False

fire_stable_count = 0


# =========================================================
# TEXT
# =========================================================

def center_text(text, font, color, y):

    image = font.render(
        text,
        True,
        color
    )

    x = (
        WIDTH // 2
        - image.get_width() // 2
    )

    screen.blit(
        image,
        (x, y)
    )


# =========================================================
# BACKGROUND
# =========================================================

def draw_background():

    screen.fill(BLACK)

    for star in stars:

        pygame.draw.circle(
            screen,
            WHITE,
            (
                int(star[0]),
                int(star[1])
            ),
            star[3]
        )


def move_stars():

    for star in stars:

        star[1] += star[2]

        if star[1] > HEIGHT:

            star[1] = 0

            star[0] = random.randint(
                0,
                WIDTH
            )


# =========================================================
# PLAYER
# =========================================================

def draw_player():

    x = int(player_x)
    y = int(player_y)

    # Power glow

    if buff_active:

        glow = pygame.Surface(
            (180, 180),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (0, 255, 255, 55),
            (90, 90),
            70
        )

        pygame.draw.circle(
            glow,
            (255, 0, 255, 35),
            (90, 90),
            48
        )

        screen.blit(
            glow,
            (x - 52, y - 50)
        )

    # Engine flame

    flame = random.randint(20, 35)

    pygame.draw.polygon(
        screen,
        ORANGE,
        [
            (x + 18, y + 62),
            (x + 38, y + 62 + flame),
            (x + 58, y + 62)
        ]
    )

    pygame.draw.polygon(
        screen,
        YELLOW,
        [
            (x + 29, y + 60),
            (x + 38, y + 42 + flame),
            (x + 47, y + 60)
        ]
    )

    # Main craft

    body_color = PURPLE if buff_active else BLUE

    pygame.draw.polygon(
        screen,
        body_color,
        [
            (x + 38, y),
            (x + 5, y + 65),
            (x + 20, y + 76),
            (x + 38, y + 55),
            (x + 56, y + 76),
            (x + 71, y + 65)
        ]
    )

    # Cockpit

    pygame.draw.ellipse(
        screen,
        (10, 25, 70),
        (x + 26, y + 17, 24, 29)
    )

    pygame.draw.ellipse(
        screen,
        PINK if buff_active else CYAN,
        (x + 31, y + 21, 14, 18)
    )

    # Wings

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (x + 20, y + 45),
            (x - 8, y + 68),
            (x + 18, y + 64)
        ]
    )

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (x + 56, y + 45),
            (x + 84, y + 68),
            (x + 58, y + 64)
        ]
    )


# =========================================================
# LASER
# =========================================================

def fire_laser():

    lasers.append([
        player_x + PLAYER_W // 2,
        player_y - 15
    ])

    if laser_sound:
        laser_sound.play()


def draw_laser(laser):

    x = int(laser[0])
    y = int(laser[1])

    color = PINK if buff_active else CYAN

    pygame.draw.rect(
        screen,
        color,
        (x - 6, y, 12, 42),
        border_radius=5
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (x - 2, y, 4, 42)
    )


# =========================================================
# ENEMY
# =========================================================

def create_enemy():

    size = random.randint(40, 55)

    enemies.append([
        random.randint(
            20,
            WIDTH - size - 20
        ),
        -size,
        size,
        random.uniform(1.7, 2.8)
    ])


def draw_enemy(enemy):

    x = int(enemy[0])
    y = int(enemy[1])
    size = int(enemy[2])

    cx = x + size // 2
    cy = y + size // 2

    # Glow

    glow = pygame.Surface(
        (size * 2, size * 2),
        pygame.SRCALPHA
    )

    pygame.draw.circle(
        glow,
        (255, 30, 50, 45),
        (size, size),
        size
    )

    screen.blit(
        glow,
        (
            x - size // 2,
            y - size // 2
        )
    )

    # Body

    pygame.draw.polygon(
        screen,
        RED,
        [
            (cx, y),
            (x, y + size - 10),
            (cx, y + size - 20),
            (x + size, y + size - 10)
        ]
    )

    # Wings

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (x + 12, cy),
            (x - 7, y + size - 5),
            (x + 18, y + size - 15)
        ]
    )

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (x + size - 12, cy),
            (x + size + 7, y + size - 5),
            (x + size - 18, y + size - 15)
        ]
    )

    # Core

    pygame.draw.circle(
        screen,
        DARK_RED,
        (cx, cy),
        size // 4
    )

    pygame.draw.circle(
        screen,
        ORANGE,
        (cx, cy),
        size // 7
    )


# =========================================================
# BUFF
# =========================================================

def create_buff():

    global buff_exists
    global buff_x
    global buff_y

    buff_exists = True

    buff_x = random.randint(
        50,
        WIDTH - 50
    )

    buff_y = -40


def draw_buff():

    x = int(buff_x)
    y = int(buff_y)

    pulse = int(
        5 * math.sin(
            pygame.time.get_ticks() * 0.01
        )
    )

    pygame.draw.circle(
        screen,
        CYAN,
        (x, y),
        30 + pulse,
        4
    )

    pygame.draw.circle(
        screen,
        PURPLE,
        (x, y),
        21
    )

    pygame.draw.polygon(
        screen,
        YELLOW,
        [
            (x + 5, y - 18),
            (x - 8, y + 2),
            (x, y + 2),
            (x - 5, y + 18),
            (x + 12, y - 5),
            (x + 3, y - 5)
        ]
    )


# =========================================================
# HAND DETECTION
# =========================================================

def update_hand():

    global hand_detected
    global hand_x
    global hand_y

    global smooth_x
    global smooth_y

    global index_finger_up
    global fire_gesture
    global fire_stable_count

    success, frame = camera.read()

    if not success:

        hand_detected = False
        fire_gesture = False

        return None

    # Mirror camera

    frame = cv2.flip(
        frame,
        1
    )

    # RGB

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = detector.detect(
        mp_image
    )

    hand_detected = False
    index_finger_up = False

    if result.hand_landmarks:

        hand = result.hand_landmarks[0]

        hand_detected = True

        # -------------------------------------------------
        # LANDMARKS
        # -------------------------------------------------

        wrist = hand[0]

        thumb_tip = hand[4]

        index_mcp = hand[5]
        index_pip = hand[6]
        index_tip = hand[8]

        middle_pip = hand[10]
        middle_tip = hand[12]

        ring_pip = hand[14]
        ring_tip = hand[16]

        pinky_pip = hand[18]
        pinky_tip = hand[20]

        # -------------------------------------------------
        # MOVEMENT
        # Use wrist / palm position
        # -------------------------------------------------

        target_x = wrist.x
        target_y = wrist.y

        smooth_x = (
            smooth_x * 0.80
            + target_x * 0.20
        )

        smooth_y = (
            smooth_y * 0.80
            + target_y * 0.20
        )

        hand_x = smooth_x
        hand_y = smooth_y

        # -------------------------------------------------
        # INDEX FINGER EXTENSION
        # -------------------------------------------------

        index_extended = (
            index_tip.y
            < index_pip.y - 0.025
        )

        # -------------------------------------------------
        # OTHER FINGERS FOLDED
        # -------------------------------------------------

        middle_folded = (
            middle_tip.y
            > middle_pip.y - 0.01
        )

        ring_folded = (
            ring_tip.y
            > ring_pip.y - 0.01
        )

        pinky_folded = (
            pinky_tip.y
            > pinky_pip.y - 0.01
        )

        # -------------------------------------------------
        # FINAL FIRE GESTURE
        #
        # ☝️ Index up
        # Other fingers folded
        # -------------------------------------------------

        if (
            index_extended
            and middle_folded
            and ring_folded
            and pinky_folded
        ):

            index_finger_up = True

    # =====================================================
    # STABILITY FILTER
    # =====================================================

    if index_finger_up:

        fire_stable_count += 1

        if fire_stable_count >= 2:

            fire_gesture = True

    else:

        fire_stable_count -= 1

        if fire_stable_count <= 0:

            fire_stable_count = 0
            fire_gesture = False

    # =====================================================
    # DRAW HAND STATUS ON CAMERA
    # =====================================================

    if hand_detected:

        cv2.putText(
            frame,
            "HAND DETECTED",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        if fire_gesture:

            cv2.putText(
                frame,
                "FIRE!",
                (15, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3
            )

        else:

            cv2.putText(
                frame,
                "MOVE HAND",
                (15, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

    else:

        cv2.putText(
            frame,
            "SHOW YOUR HAND",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    return frame


# =========================================================
# RESET GAME
# =========================================================

def reset_game():

    global player_x
    global player_y

    global lives
    global score

    global fire_timer

    global buff_exists
    global buff_active
    global buff_timer
    global next_buff_timer

    player_x = WIDTH // 2
    player_y = HEIGHT - 170

    lives = 3
    score = 0

    lasers.clear()
    enemies.clear()

    fire_timer = 0

    buff_exists = False
    buff_active = False
    buff_timer = 0

    next_buff_timer = random.randint(
        5000,
        9000
    )


# =========================================================
# MAIN GAME
# =========================================================

running = True

reset_game()


while running:

    dt = clock.tick(FPS)

    # =====================================================
    # CAMERA / HAND
    # =====================================================

    camera_frame = update_hand()

    # =====================================================
    # EVENTS
    # =====================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_q:
                running = False

            if event.key == pygame.K_ESCAPE:
                running = False

    # =====================================================
    # PLAYER MOVEMENT
    # =====================================================

    if hand_detected:

        target_player_x = (
            hand_x * WIDTH
            - PLAYER_W // 2
        )

        target_player_y = (
            hand_y * HEIGHT
            - PLAYER_H // 2
        )

        # Keep craft inside screen

        target_player_x = max(
            0,
            min(
                WIDTH - PLAYER_W,
                target_player_x
            )
        )

        target_player_y = max(
            100,
            min(
                HEIGHT - PLAYER_H - 20,
                target_player_y
            )
        )

        # Smooth movement

        player_x += (
            target_player_x
            - player_x
        ) * 0.20

        player_y += (
            target_player_y
            - player_y
        ) * 0.20

    # =====================================================
    # FIRE
    # =====================================================

    if fire_timer > 0:

        fire_timer -= dt

    if fire_gesture:

        if fire_timer <= 0:

            fire_laser()

            if buff_active:

                fire_timer = buff_fire_delay

            else:

                fire_timer = normal_fire_delay

    # =====================================================
    # MOVE LASERS
    # =====================================================

    for laser in lasers[:]:

        laser[1] -= laser_speed

        if laser[1] < -70:

            lasers.remove(laser)

    # =====================================================
    # ENEMY SPAWN
    # =====================================================

    enemy_timer += dt

    if enemy_timer >= enemy_delay:

        create_enemy()

        enemy_timer = 0

    # =====================================================
    # MOVE ENEMIES
    # =====================================================

    for enemy in enemies[:]:

        enemy[1] += enemy[3]

        # Missed enemies do nothing

        if enemy[1] > HEIGHT + 100:

            enemies.remove(enemy)

    # =====================================================
    # BUFF SPAWN
    # =====================================================

    if (
        not buff_exists
        and not buff_active
    ):

        next_buff_timer -= dt

        if next_buff_timer <= 0:

            create_buff()

    # =====================================================
    # MOVE BUFF
    # =====================================================

    if buff_exists:

        buff_y += buff_speed

        if buff_y > HEIGHT + 80:

            buff_exists = False

            next_buff_timer = random.randint(
                6000,
                10000
            )

    # =====================================================
    # PLAYER RECT
    # =====================================================

    player_rect = pygame.Rect(
        int(player_x + 10),
        int(player_y + 10),
        PLAYER_W - 20,
        PLAYER_H - 15
    )

    # =====================================================
    # BUFF COLLISION
    # =====================================================

    if buff_exists:

        buff_rect = pygame.Rect(
            int(buff_x - 25),
            int(buff_y - 25),
            50,
            50
        )

        if player_rect.colliderect(
            buff_rect
        ):

            buff_exists = False

            buff_active = True

            buff_timer = BUFF_DURATION

            if buff_sound:

                buff_sound.play()

    # =====================================================
    # BUFF TIMER
    # =====================================================

    if buff_active:

        buff_timer -= dt

        if buff_timer <= 0:

            buff_active = False

            buff_timer = 0

            next_buff_timer = random.randint(
                6000,
                10000
            )

    # =====================================================
    # ENEMY VS PLAYER
    # =====================================================

    for enemy in enemies[:]:

        enemy_rect = pygame.Rect(
            int(enemy[0]),
            int(enemy[1]),
            int(enemy[2]),
            int(enemy[2])
        )

        if player_rect.colliderect(
            enemy_rect
        ):

            enemies.remove(enemy)

            lives -= 1

            if lives <= 0:

                if death_sound:

                    death_sound.play()

                reset_game()

    # =====================================================
    # LASER VS ENEMY
    # =====================================================

    for laser in lasers[:]:

        laser_rect = pygame.Rect(
            int(laser[0] - 6),
            int(laser[1]),
            12,
            42
        )

        for enemy in enemies[:]:

            enemy_rect = pygame.Rect(
                int(enemy[0]),
                int(enemy[1]),
                int(enemy[2]),
                int(enemy[2])
            )

            if laser_rect.colliderect(
                enemy_rect
            ):

                if laser in lasers:
                    lasers.remove(laser)

                if enemy in enemies:
                    enemies.remove(enemy)

                if buff_active:
                    score += 10
                else:
                    score += 2

                if enemy_sound:
                    enemy_sound.play()

                break

    # =====================================================
    # DRAW
    # =====================================================

    draw_background()

    draw_player()

    for laser in lasers:
        draw_laser(laser)

    for enemy in enemies:
        draw_enemy(enemy)

    if buff_exists:
        draw_buff()

    # =====================================================
    # HUD
    # =====================================================

    score_text = font_medium.render(
        f"SCORE: {score}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (20, 15)
    )

    lives_text = font_medium.render(
        f"LIVES: {lives}",
        True,
        GREEN
    )

    screen.blit(
        lives_text,
        (20, 60)
    )

    # Hand status

    if hand_detected:

        status_text = font_small.render(
            "HAND: READY",
            True,
            GREEN
        )

    else:

        status_text = font_small.render(
            "SHOW YOUR HAND",
            True,
            RED
        )

    screen.blit(
        status_text,
        (20, 105)
    )

    # Fire status

    if fire_gesture:

        fire_text = font_medium.render(
            "☝ FIRE!",
            True,
            PINK
        )

        screen.blit(
            fire_text,
            (20, 135)
        )

    else:

        fire_text = font_small.render(
            "☝ INDEX FINGER = FIRE",
            True,
            WHITE
        )

        screen.blit(
            fire_text,
            (20, 140)
        )

    # Buff

    if buff_active:

        seconds = math.ceil(
            buff_timer / 1000
        )

        power_text = font_medium.render(
            f"⚡ POWER {seconds}s",
            True,
            PINK
        )

        screen.blit(
            power_text,
            (
                WIDTH - 260,
                20
            )
        )

        point_text = font_small.render(
            "10 POINTS / KILL",
            True,
            YELLOW
        )

        screen.blit(
            point_text,
            (
                WIDTH - 220,
                65
            )
        )

    # =====================================================
    # CAMERA PREVIEW
    # =====================================================

    if camera_frame is not None:

        preview = cv2.resize(
            camera_frame,
            (280, 210)
        )

        preview = cv2.cvtColor(
            preview,
            cv2.COLOR_BGR2RGB
        )

        preview_surface = pygame.surfarray.make_surface(
            preview.swapaxes(0, 1)
        )

        preview_x = WIDTH - 300
        preview_y = HEIGHT - 250

        screen.blit(
            preview_surface,
            (
                preview_x,
                preview_y
            )
        )

        pygame.draw.rect(
            screen,
            CYAN,
            (
                preview_x,
                preview_y,
                280,
                210
            ),
            3
        )

    # =====================================================
    # HELP
    # =====================================================

    help_text = font_small.render(
        "MOVE HAND  |  ☝ INDEX UP = FIRE  |  Q = EXIT",
        True,
        WHITE
    )

    screen.blit(
        help_text,
        (
            WIDTH // 2
            - help_text.get_width() // 2,
            HEIGHT - 35
        )
    )

    # =====================================================
    # STARS
    # =====================================================

    move_stars()

    pygame.display.flip()


# =========================================================
# CLEANUP
# =========================================================

camera.release()

detector.close()

cv2.destroyAllWindows()

pygame.quit()

sys.exit()