import pygame
import math
import time
import random
from Utils import scale_image, blit_rotate_center

pygame.init()

pygame.mixer.init()

BOUNCE_SOUND = [
    pygame.mixer.Sound("collision_sound1.mp3"),
    pygame.mixer.Sound("collision_sound2.mp3"),
    pygame.mixer.Sound("collision_sound3.mp3"),
]

FINISH_SOUND = [
    pygame.mixer.Sound("finish_sound1.mp3"),
    pygame.mixer.Sound("finish_sound2.mp3"),
    pygame.mixer.Sound("finish_sound3.mp3"),
]

for s in BOUNCE_SOUND:
    s.set_volume(0.7)
for s in FINISH_SOUND:
    s.set_volume(0.4)



FONT = pygame.font.SysFont("Gadugi", 18)
FONT2 = pygame.font.SysFont("Gadugi",28)
FONT3 = pygame.font.SysFont("Comic Sans MS", 22)
PINK = (255, 150, 235)
GREEN = (70, 255, 200)
YELLOW = (255, 230, 50)
WHITE = (255, 245, 252)
DARK = (10, 5, 10)

# load track and limits
TRACK = scale_image(pygame.image.load("track.png"), 1.5)

PLAYABLE_LIMIT = scale_image(pygame.image.load("playable-border.png"), 1.5)
PLAYABLE_LIMIT_MASK = pygame.mask.from_surface(PLAYABLE_LIMIT)

TRACK_LIMIT = scale_image(pygame.image.load("track-border.png"), 1.5)
TRACK_LIMIT_MASK = pygame.mask.from_surface(TRACK_LIMIT)

FINISH = pygame.transform.rotate(pygame.image.load("finish.png"), 65)
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POS = (556, 410)


# Checkpoints (in order)
CHECKPOINTS = [
    (scale_image(pygame.image.load("finish.png"), 1.5), (250, 200)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (270, 465)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (160, 150)),
    (scale_image(pygame.image.load("finish.png"), 1.5), (760, 160)),
]

CHECKPOINT_MASKS = [
    pygame.mask.from_surface(img) for img, _ in CHECKPOINTS
]

# Load Tanks (and other...)
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

# Window
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kawaii Tank Miniature !")

FPS = 60
clock = pygame.time.Clock()

# Tank specs, movements and collision
class AbstractTank:
    IMG = M48A1

    def __init__(self, vmax, vrotation, start_pos):
        self.img = self.IMG
        self.vmax = vmax
        self.v = 0
        self.vrotation = vrotation
        self.angle = 65
        self.x, self.y = start_pos
        self.acceleration = 0.08
        self.last_bounce_sound = 0

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

    def braking(self):
        self.v = max(self.v - self.acceleration / 1.5, 0)
        self.move()

    def reduce_speed(self):
        self.v = max(self.v - self.acceleration / 10, 0)
        self.move()

    def bounce(self):
        self.v = -self.v
        self.move()
        self.nya_until = time.time() + 0.5
        now = time.time()
        if now - self.last_bounce_sound > 0.1:
            random.choice(BOUNCE_SOUND).play()
            self.last_bounce_sound = now


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
        self.lap_start_time = time.time()
        self.sector_start_time = time.time()

        self.current_sectors = []
        self.best_sectors = []

        self.last_lap_time = None
        self.best_lap_time = None

        self.timer_flash_color = (255, 255, 255)
        self.timer_flash_until = 0

        self.nya_until = time.time() + 0.5
        self.last_bounce_sound = 0

        self.sector_sound_played = False
        


# Player inputs
def move_player(tank):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_q] or keys[pygame.K_LEFT]:
        tank.rotate(left=True)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        tank.rotate(right=True)
    if keys[pygame.K_z] or keys[pygame.K_UP]:
        moved = True
        tank.forward()
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        moved = True
        tank.braking()

    if not moved:
        tank.reduce_speed()

def draw_timer(win, player):
    now = time.time()
    lap_time = now - player.lap_start_time
    minutes = int(lap_time // 60)
    seconds = lap_time % 60

    text = f"{minutes:02d}:{seconds:06.3f}"
    color = ( 
        player.timer_flash_color
        if now < player.timer_flash_until
        else WHITE
    )

    surf = FONT2.render(text, True, color)
    rect = surf.get_rect(topright=(WIDTH - 20, 10))
    win.blit(surf, rect)

# Draw
def draw(win, tank):

    shake_x = random.randint(-2, 2) if player.last_bounce_sound > time.time() - 0.1 else 0
    shake_y = random.randint(-2, 2) if player.last_bounce_sound > time.time() - 0.1 else 0
    win.blit(TRACK, (shake_x, shake_y))
    win.blit(FINISH, FINISH_POS)
    win.blit(TRACK_LIMIT, (0, 0))

    pygame.draw.rect(win, DARK, (5, 5, 140, 140))
    pygame.draw.rect(win, WHITE, (5, 5, 140, 140), 2)
    pygame.draw.rect(win, DARK, (810, 10, 920, 40))
    draw_timer(win, tank)
    pygame.draw.rect(win, WHITE, (810, 10, 200, 40), 2)



    if time.time() < player.nya_until:
        txt = FONT3.render("NYA~!", True, PINK)
        win.blit(txt, (player.x + 35, player.y -15))
    
    tank.draw(win)

    y = 6

    # Lap times
    if tank.last_lap_time != None:
        txt = FONT.render (f"Last lap: {tank.last_lap_time:.2f}s", True, WHITE)
        win.blit(txt, (10, y))
        y += 22
    
    if tank.best_lap_time != None:
        txt = FONT.render(f"Best Lap: {tank.best_lap_time:.2f}s", True, WHITE)
        win.blit(txt, (10, y))
        y += 23

    # Sectors
    for i, sector_time in enumerate(tank.current_sectors):
        color = WHITE
        if i< len(tank.best_sectors):
            color = GREEN if sector_time <= tank.best_sectors[i] else YELLOW
        
        txt = FONT.render(f"S{i+1}: {sector_time:.2f}s", True, color)
        win.blit(txt, (10, y))
        y += 22

    # Uncomment to visualize checkpoints
    #for img, pos in CHECKPOINTS:
    #    win.blit(img, pos)

    pygame.display.update()


# Runnig loop
player = PlayerTank()
running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    move_player(player)

    # Track limits
    if player.collide(PLAYABLE_LIMIT_MASK) is None:
        player.bounce()

    if player.fully_on_mask(TRACK_LIMIT_MASK):
        player.bounce()


    # Checkpoints
    if player.next_checkpoint < len(CHECKPOINTS):
        cp_img, cp_pos = CHECKPOINTS[player.next_checkpoint]
        cp_mask = CHECKPOINT_MASKS[player.next_checkpoint]

        if player.collide(cp_mask, *cp_pos) and not player.on_zone:
            now = time.time()
            sector_time = now - player.sector_start_time
            player.current_sectors.append(sector_time)

            better = False
            if len(player.best_sectors) <= player.next_checkpoint:
                player.best_sectors.append(sector_time)
                better = True
            else :
                if sector_time < player.best_sectors[player.next_checkpoint]:
                    player.best_sectors[player.next_checkpoint] = sector_time
                    better = True

            player.timer_flash_color = GREEN if better else YELLOW
            player.timer_flash_until = time.time() + 0.6

            if better and not player.sector_sound_played:
                random.choice(FINISH_SOUND).play()
                player.sector_sound_played = True

            # compare to best sector
            if len(player.best_sectors) <= player.next_checkpoint:
                player.best_sectors.append(sector_time)
            else:
                player.best_sectors[player.next_checkpoint] = min(
                    player.best_sectors[player.next_checkpoint],
                    sector_time
                )

            player.sector_start_time = now
            player.next_checkpoint += 1
            player.on_zone = True
            player.sector_sound_played = False



    # reset debounce when not touching any zone
    touching = False
    for (img, pos), mask in zip(CHECKPOINTS, CHECKPOINT_MASKS):
        if player.collide(mask, *pos):
            touching = True

    if not touching and player.collide(FINISH_MASK, *FINISH_POS) is None:
        player.on_zone = False

    # Finish
    if (
        player.collide(FINISH_MASK, *FINISH_POS)
        and player.next_checkpoint == len(CHECKPOINTS)
        and not player.on_zone
    ):
        now = time.time()
        lap_time = now - player.lap_start_time
        player.last_lap_time = lap_time
        if player.best_lap_time is None or lap_time < player.best_lap_time:
            player.best_lap_time = lap_time
            random.choice(FINISH_SOUND).play()
            player.sector_sound_played = True
            

        # reset for next lap    
        player.lap += 1
        player.next_checkpoint = 0
        player.current_sectors = []
        player.lap_start_time = now
        player.sector_start_time = now
        player.on_zone = True
        print(f"LAP {player.lap}")

    draw(WIN, player)

pygame.quit()
