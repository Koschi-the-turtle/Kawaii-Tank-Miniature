import pygame
import math
from Utils import scale_image, blit_rotate_center

pygame.init()

# =====================
# LOAD TRACK & LIMITS
# =====================
TRACK = scale_image(pygame.image.load("track.png"), 1.5)

PLAYABLE_LIMIT = scale_image(pygame.image.load("playable-border.png"), 1.5)
PLAYABLE_LIMIT_MASK = pygame.mask.from_surface(PLAYABLE_LIMIT)

TRACK_LIMIT = scale_image(pygame.image.load("track-border.png"), 1.5)
TRACK_LIMIT_MASK = pygame.mask.from_surface(TRACK_LIMIT)

FINISH = pygame.transform.rotate(pygame.image.load("finish.png"), 65)
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POS = (556, 410)


# =====================
# CHECKPOINTS (ORDERED)
# =====================
CHECKPOINTS = [
    (scale_image(pygame.image.load("finish.png"), 1.5), (280, 200)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (270, 410)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (150, 130)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (760, 130)),
]

CHECKPOINT_MASKS = [
    pygame.mask.from_surface(img) for img, _ in CHECKPOINTS
]

# =====================
# TANK IMAGES (UNCHANGED)
# =====================
KPFPZ70 = scale_image(pygame.image.load("KpfPz-70.png"), 0.07)
TIGERH1 = scale_image(pygame.image.load("TigerH1.png"), 0.07)
M48A1 = scale_image(pygame.image.load("M48A1-Pitbull.png"), 0.07)
ABRAM = scale_image(pygame.image.load("Abram.png"), 0.07)
M4SHERMAN = scale_image(pygame.image.load("M4Sherman.png"), 0.07)
DAVINCI = scale_image(pygame.image.load("DaVinciConcept.png"), 0.07)
TIGER2 = scale_image(pygame.image.load("TigerII.png"), 0.07)
T62 = scale_image(pygame.image.load("T-62.png"), 0.07)
MAUS = scale_image(pygame.image.load("Maus.png"), 0.07)
PANZERIV = scale_image(pygame.image.load("PanzerIV.png"), 0.07)
THOMAS = scale_image(pygame.image.load("Thomas.png"), 0.07)
LEOPARD1 = scale_image(pygame.image.load("Leopard1.png"), 0.07)
T90A = scale_image(pygame.image.load("T-90A.png"), 0.07)
LEOPARD2 = scale_image(pygame.image.load("Leopard2.png"), 0.07)
MULTIPLA = scale_image(pygame.image.load("1000tipla.png"), 0.07)

# =====================
# WINDOW
# =====================
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kawaii Tank Miniature!")

FPS = 60
clock = pygame.time.Clock()

# =====================
# TANK CLASSES
# =====================
class AbstractTank:
    IMG = MAUS

    def __init__(self, vmax, vrotation, start_pos):
        self.img = self.IMG
        self.vmax = vmax
        self.v = 0
        self.vrotation = vrotation
        self.angle = 65
        self.x, self.y = start_pos
        self.acceleration = 0.08

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.vrotation
        elif right:
            self.angle -= self.vrotation

    def move(self):
        radians = math.radians(self.angle)
        self.x -= math.sin(radians) * self.v
        self.y -= math.cos(radians) * self.v

    def forward(self):
        self.v = min(self.v + self.acceleration, self.vmax)
        self.move()

    def backward(self):
        self.v = max(self.v - self.acceleration / 1.5, 0)
        self.move()

    def reduce_speed(self):
        self.v = max(self.v - self.acceleration / 10, 0)
        self.move()

    def bounce(self):
        self.v = -self.v
        self.move()

    def draw(self, win):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def collide(self, mask, x=0, y=0):
        tank_mask = pygame.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        return mask.overlap(tank_mask, offset)

    def fully_on_mask(self, mask):
        tank_mask = pygame.mask.from_surface(self.img)
        overlap = mask.overlap_mask(tank_mask, (int(self.x), int(self.y)))
        return overlap.count() == tank_mask.count()


class PlayerTank(AbstractTank):
    def __init__(self):
        super().__init__(3, 2.4, (603, 380))
        self.lap = 0
        self.next_checkpoint = 0
        self.on_zone = False  # debounce flag


# =====================
# INPUT
# =====================
def move_player(tank):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_q]:
        tank.rotate(left=True)
    if keys[pygame.K_d]:
        tank.rotate(right=True)
    if keys[pygame.K_z]:
        moved = True
        tank.forward()
    if keys[pygame.K_s]:
        moved = True
        tank.backward()

    if not moved:
        tank.reduce_speed()


# =====================
# DRAW
# =====================
def draw(win, tank):
    win.blit(TRACK, (0, 0))
    win.blit(FINISH, FINISH_POS)
    win.blit(TRACK_LIMIT, (0, 0))

    # Uncomment to visualize checkpoints
    # for img, pos in CHECKPOINTS:
    #     win.blit(img, pos)

    tank.draw(win)
    pygame.display.update()


# =====================
# MAIN LOOP
# =====================
player = PlayerTank()
running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    move_player(player)

    # ---- TRACK LIMITS ----
    if player.collide(PLAYABLE_LIMIT_MASK) is None:
        player.bounce()

    if player.fully_on_mask(TRACK_LIMIT_MASK):
        player.bounce()


    # ---- CHECKPOINTS ----
    if player.next_checkpoint < len(CHECKPOINTS):
        cp_img, cp_pos = CHECKPOINTS[player.next_checkpoint]
        cp_mask = CHECKPOINT_MASKS[player.next_checkpoint]

        if player.collide(cp_mask, *cp_pos) and not player.on_zone:
            player.next_checkpoint += 1
            player.on_zone = True
            print(f"Checkpoint {player.next_checkpoint}/{len(CHECKPOINTS)}")

    # reset debounce when not touching any zone
    touching = False
    for (img, pos), mask in zip(CHECKPOINTS, CHECKPOINT_MASKS):
        if player.collide(mask, *pos):
            touching = True

    if not touching and player.collide(FINISH_MASK, *FINISH_POS) is None:
        player.on_zone = False

    # ---- FINISH ----
    if (
        player.collide(FINISH_MASK, *FINISH_POS)
        and player.next_checkpoint == len(CHECKPOINTS)
        and not player.on_zone
    ):
        player.lap += 1
        player.next_checkpoint = 0
        player.on_zone = True
        print(f"LAP {player.lap}")

    draw(WIN, player)

pygame.quit()
