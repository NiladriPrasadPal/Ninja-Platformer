import os
import sys
import math
import random

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Ninja Platformer')
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            12
        )

        self.small_font = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            8
        )

        self.big_font = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            16
        )

        self.movement = [False, False]

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'),img_dur=6),
            'player/run': Animation(load_images('entities/player/run'),img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0
        self.shop_open = False

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.player.health = self.player.max_health

    def draw_shop(self):
        overlay = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.display.blit(overlay, (0, 0))

        shop_x = 35
        shop_y = 20
        shop_width = 250
        shop_height = 200

        pygame.draw.rect(
            self.display,
            (25, 25, 35),
            (shop_x, shop_y, shop_width, shop_height)
        )

        pygame.draw.rect(
            self.display,
            (120, 120, 140),
            (shop_x, shop_y, shop_width, shop_height),
            2
        )

        title = self.big_font.render(
            "UPGRADE SHOP", 
            True, 
            (255, 255, 255)
        )

        self.display.blit(
            title,
            (
                shop_x + shop_width // 2 - title.get_width() // 2,
                shop_y + 12
            )
        )

        coins = self.font.render(
            f"Coins: {self.player.coins}",
            True,
            (255, 220, 60)
        )

        self.display.blit(
            coins,
            (
                shop_x + 12,
                shop_y + 38
            )
        )

        speed_cost = 10 + self.player.speed_level * 10
        dash_cost = 15 + self.player.dash_level * 15
        health_cost = 20 + self.player.health_level * 20

        upgrades = [
            (
                "1",
                "Speed",
                "Move faster",
                speed_cost,
                self.player.speed_level
            ),
            (
                "2",
                "Dash Cooldown",
                "Lower cooldown",
                dash_cost,
                self.player.dash_level
            ),
            (
                "3",
                "HEALTH",
                "Increase max HP",
                health_cost,
                self.player.health_level
            )
        ] 

        card_y = shop_y + 80

        for key, name, description, cost, level in upgrades:
            card_x = shop_x + 10
            card_width = shop_width - 20
            card_height = 38

            pygame.draw.rect(
                self.display,
                (40, 40, 55),
                (card_x, card_y, card_width, card_height)
            )

            pygame.draw.rect(
                self.display,
                (80, 80, 100),
                (card_x, card_y, card_width, card_height)
            )

            pygame.draw.rect(
                self.display,
                (65, 65, 85),
                (card_x + 5, card_y + 7, 22, 22)
            )

            key_text = self.font.render(
                key,
                True,
                (255, 255, 255)
            )

            self.display.blit(
                key_text,
                (
                    card_x + 12,
                    card_y + 11
                )
            )

            name_text = self.font.render(
                name,
                True,
                (255, 255, 255)
            )

            self.display.blit(
                name_text,
                (
                    card_x + 35,
                    card_y + 5
                )
            )

            self.display.blit(
                name_text,
                (
                    card_x + 35,
                    card_y + 5
                )
            )

            description_text = self.small_font.render(
                description,
                True,
                (170, 170, 180)
            )

            self.display.blit(
                description_text,
                (
                    card_x + 35,
                    card_y + 21
                )
            )

            price_text = self.small_font.render(
                f"Cost: {cost} C",
                True,
                (255, 220, 60)
            )

            self.display.blit(
                price_text,
                (
                    card_x + card_width - price_text.get_width() - 7,
                    card_y + 5
                )
            )

            level_text = self.small_font.render(
                f"LV {level}",
                True,
                (130, 200, 255)
            )

            self.display.blit(
                level_text,
                (
                    card_x + card_width - level_text.get_width() - 7,
                    card_y + 20
                )
            )

            card_y += 43

        close_text = self.small_font.render(
            "M - CLOSE",
            True,
            (150, 150, 150)
        )

        self.display.blit(
            close_text,
            (
                shop_x + shop_width // 2 - close_text.get_width() // 2,
                shop_y + shop_height - 15
            )
        )

    def draw_hud(self):
        health_x = 10
        health_y = 10
        health_width = 80
        health_height = 10

        pygame.draw.rect(
            self.display,
            (35, 35, 40),
            (health_x, health_y, health_width, health_height)
        )

        health_width_current = int(
            health_width * 
            (self.player.health / self.player.max_health)
        )

        pygame.draw.rect(
            self.display,
            (220, 60, 60),
            (health_x, health_y, health_width_current, health_height)
        )

        health_text = self.small_font.render(
            f"{self.player.health}/{self.player.max_health}",
            True,
            (255, 255, 255)
        )

        self.display.blit(
            health_text,
            (health_x + health_width + 5, health_y)
        )

        coin_text = self.font.render(
            f"{self.player.coins}",
            True,
            (255, 220, 50)
        )

        self.display.blit(
            coin_text,
            (10, 27)
        )

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'],(0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(0)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.clouds.update()
            self.clouds.render(self.display, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                if not self.shop_open:
                    kill = enemy.update(self.tilemap, (0, 0))
                else:
                    kill = False
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                if not self.shop_open:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.player.take_damage(1)
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))  

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_silhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.shop_open = not self.shop_open
                        self.movement = [False, False]
                    if self.shop_open:
                        if event.key == pygame.K_1:
                            cost = 10 + self.player.speed_level * 10
                            if self.player.coins >= cost:
                                self.player.coins -= cost
                                self.player.speed_level += 1
                        if event.key == pygame.K_2:
                            cost = 15 + self.player.dash_level * 15
                            if self.player.coins >= cost:
                                self.player.coins -= cost
                                self.player.dash_level += 1
                                self.player.dash_cooldown = max(
                                    20,
                                    60 - self.player.dash_level * 10
                                )
                        if event.key == pygame.K_3:
                            cost = 20 + self.player.health * 20
                            if self.player.coins >= cost:
                                self.player.coins = cost
                                self.player.health_level += 1

                                self.player.max_health += 1
                                self.player.health = self.player.max_health

                        continue

                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        self.player.jump()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = False

            self.draw_hud()

            if self.shop_open:
                self.draw_shop()

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))
            
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

Game().run()