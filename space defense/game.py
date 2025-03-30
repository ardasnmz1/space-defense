import pygame, sys, random, json, math, os

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Uzay Savunması")
clock = pygame.time.Clock()


BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GREEN   = (0, 255, 0)
RED     = (255, 0, 0)
YELLOW  = (255, 255, 0)
BLUE    = (0, 0, 255)
PURPLE  = (128, 0, 128)
GOLD    = (212, 175, 55)

difficulty_settings = {
    "easy":   {"enemy_speed_multiplier": 1.0, "spawn_rate_factor": 1.2, "boss_health_multiplier": 1.0},
    "medium": {"enemy_speed_multiplier": 1.5, "spawn_rate_factor": 1.0, "boss_health_multiplier": 1.2},
    "hard":   {"enemy_speed_multiplier": 2.0, "spawn_rate_factor": 0.8, "boss_health_multiplier": 1.5}
}


mode = 1        
difficulty = "medium"
shop_coins = 0


controls1 = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "shoot": pygame.K_SPACE,
    "switch": pygame.K_q 
}
controls2 = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "shoot": pygame.K_RETURN,
    "switch": pygame.K_RSHIFT
}

weapons_list = ["basic", "spread"]

SAVE_FILE = "save_data.json"
def load_save_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}
def save_save_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)
save_data = load_save_data()
best_level = save_data.get("best_level", 0)

# Sınıflar
class Player(pygame.sprite.Sprite):
    def __init__(self, controls, start_pos):
        super().__init__()
        self.image = pygame.Surface((50, 40))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=start_pos)
        self.speed = 5
        self.health = 3
        self.controls = controls
        self.weapon = "basic"
        self.coin_count = 0
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls["left"]]:
            self.rect.x -= self.speed
        if keys[self.controls["right"]]:
            self.rect.x += self.speed
        if keys[self.controls["up"]]:
            self.rect.y -= self.speed
        if keys[self.controls["down"]]:
            self.rect.y += self.speed
        # Ekran sınırları
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > WIDTH: self.rect.right = WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT
    def shoot(self):
        if self.weapon == "basic":
            bullet = Bullet(self.rect.centerx, self.rect.top, 0)
            all_sprites.add(bullet)
            bullets.add(bullet)
        elif self.weapon == "spread":
            for angle in (-15, 0, 15):
                bullet = Bullet(self.rect.centerx, self.rect.top, angle)
                all_sprites.add(bullet)
                bullets.add(bullet)
    def switch_weapon(self):
        current_index = weapons_list.index(self.weapon)
        self.weapon = weapons_list[(current_index + 1) % len(weapons_list)]

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle=0):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10
        self.angle = math.radians(angle)
        self.dx = self.speed * math.sin(self.angle)
        self.dy = self.speed * math.cos(self.angle)
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(x, y))
        self.type = random.choice(["health", "speed", "weapon"])
    def update(self):
        self.rect.y += 2
        if self.rect.top > HEIGHT:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        self.image = pygame.Surface((100, 80))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect(center=(WIDTH/2, 100))
        base_health = 20
        self.health = int((base_health + level * 5) * difficulty_settings[difficulty]["boss_health_multiplier"])
        self.speed = 3 + level * 0.5
    def update(self):
        self.rect.x += self.speed
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.speed *= -1

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD, (10, 10), 10)
        self.rect = self.image.get_rect(center=(x, y))
    def update(self):
        self.rect.y += 2
        if self.rect.top > HEIGHT:
            self.kill()

# Sprite grupları
all_sprites   = pygame.sprite.Group()
players_group = pygame.sprite.Group()
enemies       = pygame.sprite.Group()
bullets       = pygame.sprite.Group()
powerups      = pygame.sprite.Group()
bosses        = pygame.sprite.Group()
coins         = pygame.sprite.Group()

score = 0
level = 1
enemy_spawn_timer = 0
boss_spawned = False
players = []

def draw_text(text, size, color, x, y):
    font_local = pygame.font.SysFont("Arial", size)
    surface = font_local.render(text, True, color)
    rect = surface.get_rect(center=(x, y))
    screen.blit(surface, rect)

def reset_game():
    global score, level, enemy_spawn_timer, boss_spawned, players, shop_coins, best_level
    if level > best_level:
        best_level = level
        save_data["best_level"] = best_level
        save_save_data(save_data)
    score = 0
    level = 1
    enemy_spawn_timer = 0
    boss_spawned = False
    shop_coins = 0
    all_sprites.empty()
    enemies.empty()
    bullets.empty()
    powerups.empty()
    bosses.empty()
    coins.empty()
    players_group.empty()
    players.clear()
    if mode == 1:
        p1 = Player(controls1, (WIDTH/2, HEIGHT - 50))
        players.append(p1)
        all_sprites.add(p1)
        players_group.add(p1)
    elif mode == 2:
        p1 = Player(controls1, (WIDTH/3, HEIGHT - 50))
        p2 = Player(controls2, (2*WIDTH/3, HEIGHT - 50))
        players.extend([p1, p2])
        all_sprites.add(p1, p2)
        players_group.add(p1, p2)


def main_menu():
    screen.fill(BLACK)
    draw_text("Uzay Savunması", 50, WHITE, WIDTH/2, HEIGHT/2 - 150)
    draw_text("Tek oyuncu için 1, iki oyuncu için 2", 30, WHITE, WIDTH/2, HEIGHT/2 - 50)
    draw_text("Zorluk: E: Easy, M: Medium, H: Hard", 30, WHITE, WIDTH/2, HEIGHT/2)
    draw_text("Başlamak için herhangi bir tuşa basın", 25, WHITE, WIDTH/2, HEIGHT/2 + 50)
    pygame.display.flip()

def shop_menu():
    global shop_coins
    screen.fill(BLACK)
    draw_text("Mağaza", 50, WHITE, WIDTH/2, 50)
    draw_text("1: Sağlık +1 (10 coin)", 30, WHITE, WIDTH/2, 150)
    draw_text("2: Hız +1 (15 coin)", 30, WHITE, WIDTH/2, 200)
    draw_text("3: Silah Upgrade (Spread) (20 coin)", 30, WHITE, WIDTH/2, 250)
    draw_text("4: Çıkış", 30, WHITE, WIDTH/2, 300)
    draw_text("Toplam Coin: " + str(shop_coins), 30, YELLOW, WIDTH/2, 350)
    pygame.display.flip()

def pause_menu():
    screen.fill(BLACK)
    draw_text("Oyun Duraklatıldı", 50, WHITE, WIDTH/2, HEIGHT/2 - 50)
    draw_text("Devam etmek için C, Ana Menüye dönmek için M'ye basın.", 30, WHITE, WIDTH/2, HEIGHT/2 + 20)
    pygame.display.flip()


game_state = "main_menu"


while True:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_state == "main_menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    mode = 1
                elif event.key == pygame.K_2:
                    mode = 2
                elif event.key == pygame.K_e:
                    difficulty = "easy"
                elif event.key == pygame.K_m:
                    difficulty = "medium"
                elif event.key == pygame.K_h:
                    difficulty = "hard"
                else:
                    reset_game()
                    game_state = "play"
        elif game_state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "pause"
                else:
                    for p in players:
                        if event.key == p.controls["shoot"]:
                            p.shoot()
                        if event.key == p.controls["switch"]:
                            p.switch_weapon()
        elif game_state == "pause":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    game_state = "play"
                elif event.key == pygame.K_m:
                    game_state = "main_menu"
        elif game_state == "shop":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    if shop_coins >= 10:
                        for p in players:
                            p.health += 1
                        shop_coins -= 10
                elif event.key == pygame.K_2:
                    if shop_coins >= 15:
                        for p in players:
                            p.speed += 1
                        shop_coins -= 15
                elif event.key == pygame.K_3:
                    if shop_coins >= 20:
                        for p in players:
                            p.weapon = "spread"
                        shop_coins -= 20
                elif event.key == pygame.K_4:
                    game_state = "play"
        elif game_state == "game_over":
            if event.type == pygame.KEYDOWN:
                game_state = "main_menu"
                

    if game_state == "main_menu":
        main_menu()
    elif game_state == "play":
        enemy_spawn_timer += 1
        spawn_threshold = max(50, int(150 - level * 5 * difficulty_settings[difficulty]["spawn_rate_factor"]))
        if enemy_spawn_timer > spawn_threshold:
            enemy_spawn_timer = 0
            x = random.randint(0, WIDTH - 40)
            enemy_speed = (1 + level * 0.5) * difficulty_settings[difficulty]["enemy_speed_multiplier"]
            enemy = Enemy(x, -30, speed=enemy_speed)
            all_sprites.add(enemy)
            enemies.add(enemy)
        if level % 20 == 0 and level != 0 and not boss_spawned:
            boss = Boss(level)
            all_sprites.add(boss)
            bosses.add(boss)
            boss_spawned = True
        if random.random() < 0.005:
            x = random.randint(20, WIDTH - 20)
            powerup = PowerUp(x, -20)
            all_sprites.add(powerup)
            powerups.add(powerup)
        if random.random() < 0.003:
            x = random.randint(20, WIDTH - 20)
            coin = Coin(x, -20)
            all_sprites.add(coin)
            coins.add(coin)
        all_sprites.update()
        # Çarpışmalar
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit in hits:
            score += 10
            if score // 10 + 1 > level:
                level = score // 10 + 1
        boss_hits = pygame.sprite.groupcollide(bosses, bullets, False, True)
        for boss_hit in boss_hits:
            boss.health -= 1
            if boss.health <= 0:
                score += 50
                boss.kill()
                boss_spawned = False
                for p in players:
                    shop_coins += p.coin_count
                    p.coin_count = 0
                game_state = "shop"
        for p in players:
            if pygame.sprite.spritecollide(p, enemies, True):
                p.health -= 1
                if p.health <= 0:
                    if p in players:
                        players.remove(p)
                        players_group.remove(p)
            if pygame.sprite.spritecollide(p, bosses, False):
                p.health = 0
                if p in players:
                    players.remove(p)
                    players_group.remove(p)
            collected = pygame.sprite.spritecollide(p, powerups, True)
            for power in collected:
                if power.type == "health":
                    p.health += 1
                elif power.type == "speed":
                    p.speed += 1
                elif power.type == "weapon":
                    p.weapon = "spread"
            coin_collected = pygame.sprite.spritecollide(p, coins, True)
            for c in coin_collected:
                p.coin_count += 1
        if len(players) == 0:
            game_state = "game_over"
        screen.fill(BLACK)
        all_sprites.draw(screen)
        draw_text("Skor: " + str(score), 20, WHITE, 60, 10)
        draw_text("Seviye: " + str(level), 20, WHITE, WIDTH/2, 10)
        if mode == 1 and players:
            draw_text("Can: " + str(players[0].health), 20, WHITE, WIDTH - 60, 10)
            draw_text("Silah: " + players[0].weapon, 20, WHITE, WIDTH - 60, 30)
            draw_text("Coin: " + str(players[0].coin_count), 20, WHITE, WIDTH - 60, 50)
        elif mode == 2:
            if len(players) >= 1:
                draw_text("P1 Can: " + str(players[0].health), 20, WHITE, WIDTH - 150, 10)
                draw_text("P1 Silah: " + players[0].weapon, 20, WHITE, WIDTH - 150, 30)
                draw_text("P1 Coin: " + str(players[0].coin_count), 20, WHITE, WIDTH - 150, 50)
            if len(players) == 2:
                draw_text("P2 Can: " + str(players[1].health), 20, WHITE, WIDTH - 60, 10)
                draw_text("P2 Silah: " + players[1].weapon, 20, WHITE, WIDTH - 60, 30)
                draw_text("P2 Coin: " + str(players[1].coin_count), 20, WHITE, WIDTH - 60, 50)
    elif game_state == "pause":
        pause_menu()
    elif game_state == "shop":
        shop_menu()
    elif game_state == "game_over":
        screen.fill(BLACK)
        draw_text("Oyun Bitti", 50, RED, WIDTH/2, HEIGHT/2 - 50)
        draw_text("Skor: " + str(score), 30, WHITE, WIDTH/2, HEIGHT/2 + 20)
        draw_text("En yüksek seviye: " + str(best_level), 25, WHITE, WIDTH/2, HEIGHT/2 + 50)
        draw_text("Yeniden başlamak için herhangi bir tuşa basın", 25, WHITE, WIDTH/2, HEIGHT/2 + 80)
    pygame.display.flip()
