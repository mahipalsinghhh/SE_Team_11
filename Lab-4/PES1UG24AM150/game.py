import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30,35,25)
MAX_HP = 3
INVINCIBILITY_MS = 1200
MAGAZINE_SIZE = 12
RELOAD_MS = 2000
BARREL_SIZE = 28
EXPLOSION_RADIUS = 115
EXPLOSION_DURATION_MS = 500
BARREL_POSITIONS = ((110, 110), (662, 110), (110, 422), (662, 422))


class Zombie:
    SPEED = 1.5
    SIZE = 30
    MAX_HP = 3
    COLOR = (60,140,60)

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = self.COLOR
        self.hp = self.MAX_HP
        self.position = pygame.Vector2(x, y)
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px-cx, py-cy
        dist = (dx**2+dy**2)**0.5
        if dist:
            self.position.x += dx/dist*self.SPEED
            self.position.y += dy/dist*self.SPEED
            self.rect.topleft = round(self.position.x), round(self.position.y)
        self.frame += 1

    def hit(self):
        return self.take_damage(1)

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*3)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(
            screen, self.color, draw_rect, border_radius=min(5, self.SIZE // 4))
        eye_radius = max(2, self.SIZE // 8)
        for eye_x in (0.25, 0.65):
            ex = draw_rect.x + int(self.SIZE * eye_x)
            ey = draw_rect.y + int(self.SIZE / 3)
            pygame.draw.circle(screen, (200,40,40), (ex, ey), eye_radius)


class FastZombie(Zombie):
    SPEED = 3.0
    SIZE = 20
    MAX_HP = 1
    COLOR = (105,190,70)


class TankZombie(Zombie):
    SPEED = 0.75
    SIZE = 42
    MAX_HP = 6
    COLOR = (95,105,55)


class ExplosiveBarrel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BARREL_SIZE, BARREL_SIZE)
        self.triggered_at = None

    def trigger(self, now):
        self.triggered_at = now

    def draw(self, screen, now):
        if self.triggered_at is None:
            pygame.draw.rect(screen, (170,75,35), self.rect, border_radius=5)
            pygame.draw.rect(screen, (220,160,75), self.rect, 2, border_radius=5)
            pygame.draw.line(
                screen, (75,65,45),
                (self.rect.left+3, self.rect.centery),
                (self.rect.right-3, self.rect.centery), 4)
            pygame.draw.circle(screen, (245,195,90), self.rect.center, 4)
            return

        elapsed = now - self.triggered_at
        if elapsed >= EXPLOSION_DURATION_MS:
            return
        progress = elapsed / EXPLOSION_DURATION_MS
        radius = int(EXPLOSION_RADIUS * (0.55 + 0.45 * progress))
        diameter = radius * 2
        effect = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (radius, radius)
        pygame.draw.circle(effect, (255,75,20,55), center, radius)
        pygame.draw.circle(effect, (255,175,35,190), center, radius, 5)
        pygame.draw.circle(effect, (255,235,120,220), center, max(8, radius // 4))
        screen.blit(effect, self.rect.center - pygame.Vector2(radius, radius))


def spawn_zombie(width, height, player_rect, margin=120, zombie_type=None):
    if zombie_type is None:
        zombie_type = random.choice((Zombie, FastZombie, TankZombie))
    size = zombie_type.SIZE
    while True:
        x = random.randint(0, width-size)
        y = random.randint(0, height-size)
        rect = pygame.Rect(x, y, size, size)
        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return zombie_type(x, y)


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60,160,220)
        self.bullets = []
        self.shoot_cooldown = 0
        self.hp = MAX_HP
        self.invulnerable_until = 0
        self.ammo = MAGAZINE_SIZE
        self.reload_until = None

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width-self.rect.width, self.rect.x+dx))
        self.rect.y = max(0, min(height-self.rect.height, self.rect.y+dy))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def update_reload(self, now):
        if self.reload_until is not None and now >= self.reload_until:
            self.ammo = MAGAZINE_SIZE
            self.reload_until = None

    def shoot(self, target_pos, now=None):
        if now is None:
            now = pygame.time.get_ticks()
        self.update_reload(now)
        if self.shoot_cooldown > 0 or self.ammo == 0: return
        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx-cx, ty-cy
        dist = (dx**2+dy**2)**0.5
        if dist == 0: return
        vx, vy = dx/dist*10, dy/dist*10
        self.bullets.append([cx-4, cy-4, vx, vy])
        self.shoot_cooldown = 15
        self.ammo -= 1
        if self.ammo == 0:
            self.reload_until = now + RELOAD_MS

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
            if 0 <= b[0] <= width and 0 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen, now):
        invulnerable = now < self.invulnerable_until
        if not invulnerable or now // 100 % 2 == 0:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        for b in self.bullets:
            pygame.draw.circle(screen, (255,220,60), (int(b[0]), int(b[1])), 5)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT//2)
        self.zombies = self.spawn_zombies(4)
        self.barrels = [ExplosiveBarrel(x, y) for x, y in BARREL_POSITIONS]
        self.score = 0
        self.score_bonus = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False
        self.start_time = time.time()

    def spawn_zombies(self, count):
        types = [Zombie, FastZombie, TankZombie][:count]
        while len(types) < count:
            types.append(random.choice((Zombie, FastZombie, TankZombie)))
        return [
            spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type=zombie_type)
            for zombie_type in types
        ]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.player.shoot(event.pos, pygame.time.get_ticks())
        return True

    def update(self):
        if self.game_over: return
        now = pygame.time.get_ticks()
        self.player.update_reload(now)
        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time) + self.score_bonus

        for z in self.zombies:
            z.update(self.player.rect.center)
            if (z.rect.colliderect(self.player.rect)
                    and now >= self.player.invulnerable_until):
                self.player.hp -= 1
                self.player.invulnerable_until = now + INVINCIBILITY_MS
                if self.player.hp == 0:
                    self.game_over = True
                break
        if self.game_over:
            return

        dead = set()
        for b in self.player.bullets[:]:
            bx, by = int(b[0]), int(b[1])
            hit_barrel = next((
                barrel for barrel in self.barrels
                if barrel.triggered_at is None and barrel.rect.collidepoint(bx, by)
            ), None)
            if hit_barrel is not None:
                hit_barrel.trigger(now)
                self.player.bullets.remove(b)
                for z in self.zombies:
                    dx = z.rect.centerx - hit_barrel.rect.centerx
                    dy = z.rect.centery - hit_barrel.rect.centery
                    if dx * dx + dy * dy <= EXPLOSION_RADIUS * EXPLOSION_RADIUS:
                        if z.take_damage(z.hp):
                            dead.add(z)
                continue

            for z in self.zombies:
                if z not in dead and z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.add(z)
                    self.player.bullets.remove(b)
                    break
        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score_bonus += 10
        self.score = int(time.time() - self.start_time) + self.score_bonus

        if self.kills >= self.kills_to_next:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = 8 + self.wave * 2
            self.zombies.extend(self.spawn_zombies(self.wave + 3))

    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40,45,35), (x,0), (x,HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (40,45,35), (0,y), (WIDTH,y), 1)
        for z in self.zombies: z.draw(self.screen)
        now = pygame.time.get_ticks()
        for barrel in self.barrels:
            barrel.draw(self.screen, now)
        self.player.draw(self.screen, now)
        hud_bg = pygame.Rect(0, 0, WIDTH, 54)
        pygame.draw.rect(self.screen, (15,20,15), hud_bg)
        health_color = (255,120,100) if self.player.hp == 1 else (160,220,120)
        hud = self.hud_font.render(
            f"HP: {self.player.hp}/{MAX_HP}  Wave: {self.wave}  "
            f"Score: {self.score}  Kills: {self.kills}/{self.kills_to_next}",
            True, health_color)
        controls = self.hud_font.render(
            "WASD/Arrows: Move  |  Click: Shoot  |  R: Restart",
            True, (160,220,120))
        self.screen.blit(hud, (8, 4))
        self.screen.blit(controls, (8, 29))
        ammo_text = f"Ammo: {self.player.ammo}/{MAGAZINE_SIZE}"
        if self.player.reload_until is not None:
            remaining = max(0, self.player.reload_until-now)
            ammo_text += f"  Reload: {math.ceil(remaining / 100) / 10:.1f}s"
        ammo = self.hud_font.render(ammo_text, True, (255,220,100))
        self.screen.blit(ammo, (WIDTH-ammo.get_width()-8, 29))
        if now < self.player.invulnerable_until:
            status = self.hud_font.render("INVULNERABLE", True, (255,220,60))
            self.screen.blit(status, (WIDTH-status.get_width()-8, 4))
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
            m = self.big_font.render("DEVOURED!", True, (180,40,40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R", True, (200,200,200))
            self.screen.blit(m, (WIDTH//2-m.get_width()//2, HEIGHT//2-40))
            self.screen.blit(s, (WIDTH//2-s.get_width()//2, HEIGHT//2+20))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
