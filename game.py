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

        self.font_big = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            11
        )

        self.font = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            6
        )

        self.font_small = pygame.font.Font(
            'data/fonts/PressStart2P-Regular.ttf',
            5
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
        self.shop_animation = 0
        self.shop_selected = 0
        self.shop_flash = 0

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
        if self.shop_open:
            self.shop_animation = min(10, self.shop_animation + 1)
        else:
            self.shop_animation = max(0, self.shop_animation - 1)
        progress = self.shop_animation / 10

        if progress <= 0:
            return
        
        overlay = pygame.Surface(self.display.get_size(), pygame.SRCALPHA)
        overlay.fill(
            (0, 0, 0, int(150 * progress))
        )

        self.display.blit(overlay, (0, 0))

        shop_width = 286
        shop_height = 224
        shop_x = 17
        shop_y = int(-224 + 14 + 210 * progress)

        pygame.draw.rect(
            self.display,
            (22, 24, 32),
            (shop_x, shop_y, shop_width, shop_height)
        )

        pygame.draw.rect(
            self.display,
            (110, 115, 135),
            (shop_x, shop_y, shop_width, shop_height),
            2
        )

        pygame.draw.rect(
            self.display,
            (55, 60, 75),
            (
                shop_x + 4,
                shop_y + 4,
                shop_width - 8,
                shop_height - 8
            ),
            1
        )

        title = self.font_big.render(
            "UPGRADE SHOP", 
            True, 
            (255, 255, 255)
        )

        self.display.blit(
            title,
            (
                shop_x + shop_width // 2 - title.get_width() // 2,
                shop_y + 10
            )
        )

        pygame.draw.circle(
            self.display, 
            (255, 210, 50),
            (shop_x + 15, shop_y + 34),
            5
        )

        pygame.draw.circle(
            self.display,
            (180, 130, 20),
            (shop_x + 15, shop_y + 34),
            5, 
            1
        )

        coin_text = self.font.render(
            str(self.player.coins),
            True,
            (255, 220, 70)
        )

        self.display.blit(
            coin_text,
            (
                shop_x + 25,
                shop_y + 30
            )
        )

        upgrades = self.get_upgrade_info()

        card_x = shop_x + 9
        card_width = shop_width - 18
        card_height = 48

        first_card_y = shop_y + 45
        card_gap = 5

        for i, upgrade in enumerate(upgrades):
            card_offset = int((1 - progress) * 30)

            card_y = (
                first_card_y + 
                i * (card_height + card_gap) + 
                card_offset
            )

            selected = (
                i == self.shop_selected
            )

            affordable = (
                self.player.coins >= upgrade['cost']
            )

            if selected:
                card_background = (48, 52, 68)
                border_color = (255, 220, 70)
            else:
                card_background = (32, 35, 45)
                border_color = (65, 70, 85)

            if not affordable:
                name_color = (130, 130, 140)
            else:
                name_color = (255, 255, 255)

            pygame.draw.rect(
                self.display,
                card_background,
                (card_x, card_y, card_width, card_height)
            )

            pygame.draw.rect(
                self.display,
                border_color,
                (card_x, card_y, card_width, card_height),
                2 if selected else 1
            )

            key_box_x = card_x + 5
            key_box_y = card_y + 5

            pygame.draw.rect(
                self.display,
                (55, 58, 72),
                (key_box_x, key_box_y, 22, 22)
            )

            key_text = self.font.render(
                str(i + 1),
                True, 
                (255, 255, 255)
            )

            self.display.blit(
                key_text,
                (
                    key_box_x + 8,
                    key_box_y + 7
                )
            )

            self.draw_upgrade_icon(
                upgrade['icon'],
                card_x + 32,
                card_y + 5
            )

            name_text = self.font.render(
                upgrade['name'],
                True,
                name_color
            )

            self.display.blit(
                name_text,
                (
                    card_x + 60,
                    card_y + 5
                )
            )

            description_text = self.font_small.render(
                upgrade['description'],
                True,
                (150, 155, 170)
            )

            self.display.blit(
                description_text,
                (
                    card_x + 60,
                    card_y + 18
                )
            )

            current_text = self.font_small.render(
                f"NOW {upgrade['current']}",
                True,
                (170, 175, 190)
            )

            next_text = self.font_small.render(
                f"NEXT {upgrade['next']}",
                True,
                (100, 210, 150)
            )

            self.display.blit(
                current_text,
                (
                    card_x + 60,
                    card_y + 30
                )
            )

            self.display.blit(
                next_text,
                (
                    card_x + 112,
                    card_y + 30
                )
            )

            price_color = (
                (255, 220, 70)
                if affordable
                else
                (120, 120, 125)
            )

            price_text = self.font.render(
                f"{upgrade['cost']} C",
                True,
                price_color
            )

            self.display.blit(
                price_text,
                (
                    card_x + card_width -
                    price_text.get_width() - 
                    6,
                    card_y + 6
                )
            )

            level_text = self.font_small.render(
                f"LV {upgrade['level']}",
                True, 
                (120, 180, 230)
            )

            self.display.blit(
                level_text,
                (
                    card_x + card_width - 
                    level_text.get_width() - 
                    6,
                    card_y + 19
                )
            )

        footer = self.font_small.render(
            '1-3 SELECT     ENTER BUY      M CLOSE',
            True,
            (150, 150, 165)
        )

        self.display.blit(
            footer,
            (
                shop_x + shop_width // 2 - footer.get_width() // 2,
                shop_y + 210
            )
        )

        if self.shop_flash > 0:
            flash = pygame.Surface(
                self.display.get_size(),
                pygame.SRCALPHA
            )

            flash.fill(
                (255, 255, 255, self.shop_flash * 15)
            )

            self.display.blit(
                flash,
                (0, 0)
            )

            self.shop_flash -= 1

    def draw_hud(self):
        x = 8
        y = 8
        bar_width = 75
        bar_height = 9

        pygame.draw.rect(
            self.display,
            (30, 30, 35),
            (x, y, bar_width, bar_height)
        )

        health_ratio = (
            self.player.health / 
            self.player.max_health
        )

        pygame.draw.rect(
            self.display,
            (220, 60, 70),
            (x, y, int(bar_width * health_ratio), bar_height)
        )

        pygame.draw.rect(
            self.display,
            (100, 100, 110),
            (
                x,
                y,
                bar_width,
                bar_height
            ),
            1
        )

        health_text = self.font_small.render(
            f"{self.player.health}/{self.player.max_health}",
            True,
            (255, 255, 255)
        )

        self.display.blit(
            health_text,
            (x, y + 12)
        )

        pygame.draw.circle(
            self.display,
            (255, 215, 50),
            (12, 36),
            4
        )

        coin_text = self.font.render(
            str(self.player.coins),
            True,
            (255, 220, 50)
        )

        self.display.blit(
            coin_text,
            (21, 31)
        )

        if self.player.dash_timer > 0:
            dash_text = self.font_small.render(
                f"DASH {self.player.dash_timer}",
                True,
                (150, 190, 255)
            )

            self.display.blit(
                dash_text,
                (8, 45)
            )

        else:
            dash_text = self.font_small.render(
                "DASH READY",
                True,
                (100, 230, 150)
            )

            self.display.blit(
                dash_text,
                (8, 45)
            )

    def draw_upgrade_icon(self, icon, x, y):
        if icon == 'speed':
            color = (255, 220, 55)

            pygame.draw.rect(
                self.display,
                color,
                (x + 10, y + 1, 7, 5)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 8, y + 6, 7, 5)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 6, y + 11, 7, 5)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 3, y + 16, 7, 6)
            )

            pygame.draw.rect(
                self.display,
                (32, 35, 45),
                (x + 3, y + 1, 7, 4)
            )

            pygame.draw.rect(
                self.display,
                (32, 35, 45),
                (x + 13, y + 11, 7, 5)
            )

        elif icon == 'dash':
            color = (80, 200, 255)
            pygame.draw.rect(
                self.display,
                color,
                (x + 2, y + 9, 15, 6)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 17, y + 6, 5, 12)
            )

            pygame.draw.rect(
                self.display,
                color, 
                (x + 20, y + 9, 4, 6)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 20, y + 9, 4, 6)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 1, y + 5, 7, 2)
            )

            pygame.draw.rect(
                self.display,
                color,
                (x + 1, y + 17, 5, 2)
            )

            pygame.draw.rect(
                self.display,
                (32, 35, 45),
                (x + 17, y + 6, 3, 3)
            )

            pygame.draw.rect(
                self.display,
                (32, 35, 45),
                (x + 17, y + 15, 3, 3)
            )

        elif icon == 'health':
            color = (235, 65, 75)
            pixels = [
                (7, 3),
                (8, 3),
                (9, 3),
                (15, 3),
                (16, 3),
                (17, 3),
                (5, 5),
                (6, 5),
                (7, 5),
                (8, 5),
                (9, 5),
                (10, 5),
                (14, 5),
                (15, 5),
                (16, 5),
                (17, 5),
                (18, 5),
                (19, 5),
                (4, 7),
                (5, 7),
                (6, 7),
                (7, 7),
                (8, 7),
                (9, 7),
                (10, 7),
                (11, 7),
                (12, 7),
                (13, 7),
                (14, 7),
                (15, 7),
                (16, 7),
                (17, 7),
                (18, 7),
                (19, 7),
                (20, 7),
                (5, 9),
                (6, 9),
                (7, 9),
                (8, 9),
                (9, 9),
                (10, 9),
                (11, 9),
                (12, 9),
                (13, 9),
                (14, 9),
                (15, 9),
                (16, 9),
                (17, 9),
                (18, 9),
                (19, 9),
                (6, 11),
                (7, 11),
                (8, 11),
                (9, 11),
                (10, 11),
                (11, 11),
                (12, 11),
                (13, 11),
                (14, 11),
                (15, 11),
                (16, 11),
                (17, 11),
                (18, 11),
                (8, 13),
                (9, 13),
                (10, 13),
                (11, 13),
                (12, 13),
                (13, 13),
                (14, 13),
                (15, 13),
                (16, 13),
                (10, 15),
                (11, 15),
                (12, 15),
                (13, 15),           
                (14, 15),
                (11, 17),
                (12, 17),
                (13, 17),
            ]

            for px, py in pixels:
                pygame.draw.rect(
                    self.display,
                    color,
                    (x + px, y + py, 2, 2)
                )

    def get_upgrade_info(self):
        return [
            {
                'name': 'SPEED',
                'description': 'MOVE FASTER',
                'icon': 'speed',
                'level': self.player.speed_level,
                'cost': 10 + self.player.speed_level * 10,
                'current': f'{1 + self.player.speed_level * 0.25:.2f}',
                'next': f'{1 + (self.player.speed_level + 1) * 0.25:.2f}',
            },

            {
                'name': 'DASH',
                'description': 'LOWER COOLDOWN',
                'icon': 'dash',
                'level': self.player.dash_level,
                'cost': 15 + self.player.dash_level * 15,
                'current': f'{self.player.dash_cooldown / 60:.1f}s',
                'next': f'{max(20, self.player.dash_cooldown - 10) / 60:.1f}s',
            },

            {
                'name': 'HEALTH',
                'description': 'INCREASE MAX HP',
                'icon': 'health',
                'level': self.player.health_level,
                'cost': 20 + self.player.health_level * 20,
                'current': f'{self.player.max_health}',
                'next': f'{self.player.max_health + 1}',
            }
        ]

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

            if not self.shop_open:
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
                            self.shop_selected = 0
                        elif event.key == pygame.K_2:
                            self.shop_selected = 1
                        elif event.key == pygame.K_3:
                            self.shop_selected = 2
                        elif event.key == pygame.K_RETURN:
                            upgrades = self.get_upgrade_info()
                            upgrade = upgrades[self.shop_selected]

                            if self.player.coins >= upgrade['cost']:
                                self.player.coins -= upgrade['cost']
                                if self.shop_selected == 0:
                                    self.player.speed_level += 1

                                elif self.shop_selected == 1:
                                    self.player.dash_level += 1

                                    self.player.dash_cooldown = max(
                                        20, 60 - 
                                        self.player.dash_level * 10
                                    )

                                elif self.shop_selected == 2:
                                    self.player.health_level += 1
                                    self.player.max_health += 1
                                    self.player.health = self.player.max_health

                                self.shop_flash = 5

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