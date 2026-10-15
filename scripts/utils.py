import os
import sys

import pygame

def resource_path(relative_path):
    if hasattr(sys,"_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    return os.path.join(base_path, relative_path)

BASE_IMG_PATH = resource_path('data/images')

def load_image(path):
    img = pygame.image.load(os.path.join(BASE_IMG_PATH, path)).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []

    folder_path = os.path.join(BASE_IMG_PATH, path)

    for img_name in sorted(os.listdir(folder_path)):
        images.append(load_image(path + '/' + img_name))
    return images

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    def img(self):
        return self.images[int(self.frame / self.img_duration)]

        