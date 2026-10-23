import math
import random
import pygame

VIEW_W, VIEW_H = 800, 560
WORLD_W = 3200
RADAR_H = 56
PLAY_TOP = RADAR_H + 6
HUMANOID_COUNT = 6
FALL_LIMIT = 160
PHASES = [random.uniform(0, math.tau) for _ in range(3)]
POPUPS = []  # floating score popups: {"x", "y", "life"}


def sky_color(wave):
    """Return an (r, g, b) sky colour for the current wave, or None for the default."""
    if wave <= 1:
        return None  # keep the default near-black sky for the first wave
    # Each new wave shifts the hue and gets slightly brighter (capped so it stays dark).
    palette = [
        (10, 10, 45),   # deep blue
        (30, 10, 50),   # purple
        (45, 12, 30),   # crimson
        (10, 35, 40),   # teal
        (40, 28, 10),   # amber
    ]
    r, g, b = palette[(wave - 2) % len(palette)]
    boost = min(30, (wave - 2) // len(palette) * 10)
    return (min(255, r + boost), min(255, g + boost), min(255, b + boost))


def on_humanoid_rescued(humanoid):
    """Called when the player catches a falling humanoid; add a bonus or celebration here."""
    # Spawn a floating "+500" popup at the rescue spot (world coordinates).
    POPUPS.append({"x": humanoid.x, "y": humanoid.y - 20, "life": 1.2})


def bonus_life_threshold():
    """Return a score value at which the player earns an extra life, or None to disable bonus lives."""
    return 10000  # one extra life every 10,000 points


def wrap_delta(a, b):
    """Shortest signed distance from world x=a to world x=b on a wrapping world."""
    return (b - a + WORLD_W / 2) % WORLD_W - WORLD_W / 2


def ground_y(x):
    angle = math.tau * x / WORLD_W
    return 505 - 25 * math.sin(3 * angle + PHASES[0]) - 14 * math.sin(7 * angle + PHASES[1]) - 6 * math.sin(13 * angle + PHASES[2])


class Humanoid:
    def __init__(self, x):
        self.x, self.y = x, ground_y(x) - 8
        self.state = "ground"
        self.fall_from = self.y
        self.vy = 0.0

    def update(self, dt):
        if self.state == "falling":
            self.vy += 300 * dt
            self.y += self.vy * dt
            floor = ground_y(self.x) - 8
            if self.y >= floor:
                self.y = floor
                self.vy = 0
                self.state = "dead" if floor - self.fall_from > FALL_LIMIT else "ground"


class Lander:
    def __init__(self, x):
        self.x, self.y = x, PLAY_TOP + 20
        self.target = None
        self.mutant = False

    def pick_target(self, humanoids, landers):
        free = [h for h in humanoids if h.state == "ground" and not any(h is l.target for l in landers)]
        self.target = random.choice(free) if free else None

    def update(self, dt, player, humanoids, landers, wave):
        if self.mutant:
            dx = wrap_delta(self.x, player.x)
            dy = player.y - self.y
            dist = math.hypot(dx, dy) or 1
            speed = 110 + wave * 10
            self.x = (self.x + dx / dist * speed * dt + random.uniform(-40, 40) * dt) % WORLD_W
            self.y += dy / dist * speed * dt
            return
        if self.target is None or self.target.state not in ("ground", "carried"):
            self.target = None
            self.pick_target(humanoids, landers)
        target = self.target
        if target is None:
            dx, dy = wrap_delta(self.x, player.x), player.y - self.y
            dist = math.hypot(dx, dy) or 1
            self.x = (self.x + dx / dist * 60 * dt) % WORLD_W
            self.y += dy / dist * 60 * dt
        elif target.state == "carried":
            self.y -= 45 * dt
            target.x, target.y = self.x, self.y + 20
            if self.y <= PLAY_TOP + 8:
                humanoids.remove(target)
                self.target, self.mutant = None, True
        else:
            dx, dy = wrap_delta(self.x, target.x), target.y - 18 - self.y
            dist = math.hypot(dx, dy)
            if dist < 6:
                target.state = "carried"
            else:
                self.x = (self.x + dx / dist * 70 * dt) % WORLD_W
                self.y += dy / dist * 70 * dt


class Player:
    def __init__(self):
        self.x, self.y, self.vx, self.facing = WORLD_W / 2, 250.0, 0.0, 1
        self.invulnerable, self.cooldown = 1.5, 0.0

    def update(self, dt, keys):
        thrust = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        if thrust:
            self.facing = thrust
        self.vx = max(-520, min(520, self.vx + thrust * 900 * dt))
        self.vx *= 1 - min(1.0, 0.8 * dt)
        self.x = (self.x + self.vx * dt) % WORLD_W
        self.y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * 260 * dt
        self.y = max(PLAY_TOP + 10, min(VIEW_H - 30, self.y))
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.cooldown -= dt


class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.reset()

    def reset(self):
        self.player = Player()
        self.humanoids = [Humanoid(i * WORLD_W / HUMANOID_COUNT + 100) for i in range(HUMANOID_COUNT)]
        self.landers, self.bullets = [], []
        self.score, self.lives, self.wave, self.state = 0, 3, 1, "play"
        self.bonus_awarded = 0
        POPUPS.clear()
        self.start_wave()

    def start_wave(self):
        self.to_spawn = 3 + self.wave * 2
        self.spawn_timer = 1.0
        while len(self.humanoids) < HUMANOID_COUNT:
            self.humanoids.append(Humanoid(random.uniform(0, WORLD_W)))

    def shoot_lander(self, lander):
        self.landers.remove(lander)
        if lander.target is not None and lander.target.state == "carried":
            lander.target.state = "falling"
            lander.target.fall_from = lander.target.y
        self.score += 150

    def update(self, dt, keys):
        if self.state != "play":
            return
        player = self.player
        player.update(dt, keys)
        threshold = bonus_life_threshold()
        if threshold and self.score // threshold > self.bonus_awarded:
            self.bonus_awarded = self.score // threshold
            self.lives += 1
        if keys[pygame.K_SPACE] and player.cooldown <= 0:
            player.cooldown = 0.18
            self.bullets.append({"x": player.x + player.facing * 20, "y": player.y, "dir": player.facing, "life": 0.7})
        self.spawn_timer -= dt
        if self.to_spawn > 0 and self.spawn_timer <= 0:
            self.landers.append(Lander(random.uniform(0, WORLD_W)))
            self.to_spawn -= 1
            self.spawn_timer = 1.5
        for lander in self.landers:
            lander.update(dt, player, self.humanoids, self.landers, self.wave)
        for humanoid in self.humanoids[:]:
            humanoid.update(dt)
            if humanoid.state == "dead":
                self.humanoids.remove(humanoid)
            elif humanoid.state == "falling" and abs(wrap_delta(player.x, humanoid.x)) < 24 and abs(humanoid.y - player.y) < 24:
                humanoid.state, humanoid.y = "ground", ground_y(humanoid.x) - 8
                self.score += 500
                on_humanoid_rescued(humanoid)
        self.update_bullets(dt)
        for popup in POPUPS[:]:
            popup["y"] -= 40 * dt
            popup["life"] -= dt
            if popup["life"] <= 0:
                POPUPS.remove(popup)
        if player.invulnerable <= 0:
            for lander in self.landers:
                if abs(wrap_delta(player.x, lander.x)) < 22 and abs(lander.y - player.y) < 18:
                    self.lives -= 1
                    self.player = Player()
                    if self.lives <= 0:
                        self.state = "lose"
                    break
        if self.to_spawn == 0 and not self.landers:
            self.wave += 1
            self.start_wave()

    def update_bullets(self, dt):
        for bullet in self.bullets:
            bullet["x"] = (bullet["x"] + bullet["dir"] * 900 * dt) % WORLD_W
            bullet["life"] -= dt
            for lander in self.landers[:]:
                if abs(wrap_delta(bullet["x"], lander.x)) < 16 and abs(bullet["y"] - lander.y) < 12:
                    self.shoot_lander(lander)
                    bullet["life"] = 0
                    break
        self.bullets = [b for b in self.bullets if b["life"] > 0]

    def screen_x(self, x):
        return VIEW_W / 2 + wrap_delta(self.player.x, x)

    def draw_radar(self, screen):
        pygame.draw.rect(screen, (10, 10, 30), (0, 0, VIEW_W, RADAR_H))
        pygame.draw.rect(screen, (90, 90, 140), (0, 0, VIEW_W, RADAR_H), 1)
        blips = [(h.x, h.y, (90, 230, 120)) for h in self.humanoids]
        blips += [(l.x, l.y, (255, 90, 90) if l.mutant else (230, 200, 60)) for l in self.landers]
        blips.append((self.player.x, self.player.y, (255, 255, 255)))
        for x, y, color in blips:
            # Map absolute world x (0..WORLD_W) onto the full radar width (0..VIEW_W),
            # independent of where the player is.
            rx = (x % WORLD_W) / WORLD_W * VIEW_W
            ry = (y - PLAY_TOP) / (VIEW_H - PLAY_TOP) * (RADAR_H - 8) + 4
            pygame.draw.rect(screen, color, (rx - 2, ry - 2, 4, 4))

    def draw(self, screen):
        screen.fill(sky_color(self.wave) or (5, 5, 20))
        points = [(sx, ground_y(self.player.x + sx - VIEW_W / 2)) for sx in range(0, VIEW_W + 8, 8)]
        pygame.draw.polygon(screen, (110, 70, 40), points + [(VIEW_W, VIEW_H), (0, VIEW_H)])
        pygame.draw.lines(screen, (230, 150, 60), False, points, 2)
        for humanoid in self.humanoids:
            sx = self.screen_x(humanoid.x)
            if -20 < sx < VIEW_W + 20:
                pygame.draw.rect(screen, (90, 230, 120), (sx - 3, humanoid.y - 10, 6, 14))
        for lander in self.landers:
            sx = self.screen_x(lander.x)
            if -20 < sx < VIEW_W + 20:
                color = (255, 90, 90) if lander.mutant else (230, 200, 60)
                pygame.draw.ellipse(screen, color, (sx - 14, lander.y - 9, 28, 18))
        for bullet in self.bullets:
            sx = self.screen_x(bullet["x"])
            pygame.draw.line(screen, (255, 255, 200), (sx - 8, bullet["y"]), (sx + 8, bullet["y"]), 2)
        player = self.player
        if player.invulnerable <= 0 or int(player.invulnerable * 10) % 2 == 0:
            f, cx = player.facing, VIEW_W / 2
            pygame.draw.polygon(screen, (240, 240, 250), [(cx + f * 18, player.y), (cx - f * 14, player.y - 8), (cx - f * 14, player.y + 8)])
        for popup in POPUPS:
            sx = self.screen_x(popup["x"])
            if -40 < sx < VIEW_W + 40:
                label = self.font.render("+500", True, (255, 230, 90))
                screen.blit(label, label.get_rect(center=(sx, popup["y"])))
        self.draw_radar(screen)
        hud = self.font.render(f"Score {self.score}  Lives {self.lives}  Wave {self.wave}  Humanoids {len(self.humanoids)}", True, (240, 240, 240))
        screen.blit(hud, (10, RADAR_H + 4))
        if self.state == "lose":
            label = self.font.render("GAME OVER - Press R", True, (255, 255, 120))
            screen.blit(label, label.get_rect(center=(VIEW_W // 2, VIEW_H // 2)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((VIEW_W, VIEW_H))
    pygame.display.set_caption("Defender")
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        dt = min(clock.tick(60) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset()
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
