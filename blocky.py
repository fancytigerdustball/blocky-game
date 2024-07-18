''' Blocky '''

from time import perf_counter as time
from random import randint
from math import sin
import pygame as pg
import json


# Block related constants
BLOCK_EDGE = 60
BLOCK_RAD = BLOCK_EDGE // 6
BLOCKY_EDGE = int(BLOCK_EDGE * 0.8)
BLOCKY_RAD = BLOCKY_EDGE // 6
BLOCKY_EYE_RAD = int(BLOCKY_RAD * 0.8)

# Player movement related constants
# Falling
MAX_FALL_SPEED = BLOCK_RAD * 3
FALL_SPEEDUP = MAX_FALL_SPEED // 5
# Jumping
MAX_JUMP_SPEED = int(-MAX_FALL_SPEED * 0.8)
INIT_JUMP_SPEED = -BLOCK_RAD
JUMP_SPEED = INIT_JUMP_SPEED
# Running
MAX_RUN_SPEED = BLOCK_EDGE // 3
RUN_SPEED = BLOCKY_EDGE // 3
DRAG = 0.7

# Ball related constants
BALL_RAD = BLOCKY_EYE_RAD
BALL_SPEED = BALL_RAD * 5
BALL_ADD_SPEED = 0.3

# Other constants
TARGET_EDGE = 20
FILENAME = 'blockyHS.json'
WIDTH = 9
HEIGHT = 12
EMPTY_CHANCE = WIDTH
UPGRADE_CHANCE = WIDTH * 2
EXTRA_CHANCE = WIDTH
START_LAYERS = WIDTH // 2
FRAMERATE = 20


pg.init()
pg.mouse.set_visible(False)

win = pg.display.set_mode((BLOCK_EDGE * WIDTH, BLOCK_EDGE * HEIGHT))
pg.display.set_caption('Blocky')
win_rect = win.get_rect()
icon = pg.Surface((30, 30))
icon.set_colorkey((0, 0, 0))
pg.draw.circle(icon, (255, 255, 0), (14, 14), 15)
pg.display.set_icon(icon)

block_font = pg.font.SysFont('Comic Sans MS', int(BLOCK_EDGE * 0.6))
ball_font = pg.font.SysFont('Comic Sans MS', int(BLOCK_EDGE * 0.8))
game_over_font = pg.font.SysFont('Courier New', int(BLOCK_EDGE * 0.8), bold=True)

clock = pg.time.Clock()


def stop():

    if Score.score > highscore:
        save_highscore(Score.score)

    win.fill((255, 255, 255))
    image = game_over_font.render(f'Score: {Score.score:,}', True, (0, 0, 0))
    rect = image.get_rect()
    rect.x += 2
    rect.y += 2
    win.blit(image, rect)
    image = game_over_font.render(f'Highscore: {highscore:,}', True, (0, 0, 0))
    rect = image.get_rect()
    rect.bottomleft = win_rect.bottomleft
    rect.x += 2
    rect.y -= 2
    win.blit(image, rect)
    image = game_over_font.render(':)', True, (0, 0, 0))
    image = pg.transform.rotate(image, 270)
    rect = image.get_rect()
    rect.center = win_rect.center
    win.blit(image, rect)
    pg.display.flip()

    while True:
        for event in pg.event.get():
            if (event.type == pg.QUIT or
                (event.type == pg.KEYDOWN and
                    event.key == pg.K_q)):
                pg.quit()
                raise SystemExit(0)


def save_highscore(highscore):

    with open(FILENAME, 'w') as file:
        json.dump(highscore, file)


def get_block_image(color, edge, radius, rect):
    ''' Returns an image of a block based on arguments '''

    image = pg.Surface(rect.size)
    rect = image.get_rect()
    image.set_colorkey((0, 0, 0))

    small_edge = edge - (2 + (radius * 2))
    # Draw the main part of the block
    pg.draw.rect(image, color, pg.Rect((1 + radius, 1), (small_edge, edge - 2)))
    pg.draw.rect(image, color, pg.Rect((1, 1 + radius), (edge - 2, small_edge)))
    # With round edges
    pg.draw.circle(image, color, (1 + radius, 1 + radius), radius)
    pg.draw.circle(image, color, (1 + radius + small_edge, 1 + radius), radius)
    pg.draw.circle(image, color, (1 + radius, 1 + radius + small_edge), radius)
    pg.draw.circle(image, color, (1 + radius + small_edge, 1 + radius + small_edge), radius)

    # Draw the middle part
    pg.draw.circle(image, (255, 255, 255), rect.center, int(small_edge * 0.6))

    return image


class Blocky:
    ''' The little blocky guy you control '''
    
    def __init__(self):

        self.rect = pg.Rect((0, 0), (BLOCKY_EDGE, BLOCKY_EDGE))
        self.rect.midtop = win_rect.midtop
        self.x = self.rect.x # We will have this attribute to keep track of fractional values
        self.y_speed = MAX_FALL_SPEED
        self.x_speed = 0
        self.jumping = False
        self.on_ground = False

    def update(self):

        if not self.jumping:
            self.y_speed += FALL_SPEEDUP
        if event_handler.w:
            if self.jumping:
                self.y_speed += JUMP_SPEED
            elif self.on_ground:
                self.on_ground = False
                self.jumping = True
                self.y_speed = INIT_JUMP_SPEED
                sound_handler.jump.play()
        else:
            self.jumping = False

        if self.y_speed > MAX_FALL_SPEED:
            self.y_speed = MAX_FALL_SPEED
        if self.y_speed < MAX_JUMP_SPEED:
            self.jumping = False

        self.rect.y += self.y_speed
        if self.collision():
            if self.y_speed > 0:
                increment = -1
                self.on_ground = True
            else:
                increment = 1
                self.jumping = False
            while self.collision():
                self.rect.y += increment
            self.y_speed = 0
        elif self.y_speed > 0:
            self.on_ground = False
        
        self.x_speed *= DRAG
        if event_handler.a:
            self.x_speed -= RUN_SPEED
        if event_handler.d:
            self.x_speed += RUN_SPEED
        if abs(self.x_speed) < 0.1:
            self.x_speed = 0
        if abs(self.x_speed) > MAX_RUN_SPEED:
            self.x_speed = MAX_RUN_SPEED if self.x_speed > 0 else -MAX_RUN_SPEED

        self.x += self.x_speed
        self.rect.x = self.x
        if self.collision():
            increment = -1 if self.x_speed > 0 else 1
            while self.collision():
                self.rect.x += increment
                self.x += increment
            self.x_speed = 0
        
        return self.rect.y >= win_rect.height
    
    def collision(self):
        ''' Returns True if any collision is detected '''

        if self.rect.x < 0 or self.rect.x + self.rect.width >= win_rect.width:
            return True
        collision = False
        for block in blocks:
            if self.rect.colliderect(block.rect):
                if block.extra:
                    block.remove = True
                    sound_handler.extra.play()
                else:
                    collision = True
        return collision


    def draw(self):

        image = get_block_image((255, 0, 0), BLOCKY_EDGE, BLOCKY_RAD, self.rect)
        # Draw the eye
        center = list(image.get_rect().center)
        center[0] += (self.x_speed // MAX_RUN_SPEED) * BLOCKY_EYE_RAD
        center[1] += (self.y_speed // MAX_FALL_SPEED) * BLOCKY_EYE_RAD
        pg.draw.circle(image, (0, 0, 1), center, BLOCKY_EYE_RAD)

        win.blit(image, self.rect)


class Block:
    ''' A block you must BREAK '''
    
    def __init__(self, x, number):

        self.rect = pg.Rect((x, win_rect.height), [BLOCK_EDGE] * 2)
        if not randint(0, EXTRA_CHANCE):
            self.extra = True
            self.upgrade = False
        elif not randint(0, UPGRADE_CHANCE):
            self.extra = False
            self.upgrade = True
        else:
            self.extra = False
            self.upgrade = False
            self.number = number
        self.remove = False

    def draw(self):

        if self.extra:
            color = (0, 255, 0)
        elif self.upgrade:
            color = (255, 0, 255)
        else:
            color = (80, abs(sin(self.number) * 255), 255)
        image = get_block_image(color, BLOCK_EDGE, BLOCK_RAD, self.rect)
        rect = image.get_rect()

        # Draw the inside font
        text = '+' if self.extra or self.upgrade else str(self.number)
        color = (0, 0, 1)
        font_image = block_font.render(text, True, color)
        font_rect = font_image.get_rect()
        font_rect.center = rect.center
        image.blit(font_image, font_rect)

        win.blit(image, self.rect)


class Ball:
    ''' A ball you shoot '''

    def __init__(self, x_speed, y_speed, center):

        self.x_speed = x_speed
        self.y_speed = y_speed
        self.center = list(center)
        self.life = BallLife.ball_life

    def update_axis(self, index, axis, x=False):

        self.center[index] += getattr(self, axis)
        collision = False
        if self.center[index] < 0 or (x and self.center[0] >= win_rect.width):
            collision = True
            self.life -= 1
        else:
            for block in blocks:
                if block.rect.collidepoint(self.center):
                    if block.extra:
                        block.remove = True
                        sound_handler.extra.play()
                    else:
                        if block.upgrade:
                            block.remove = 'UPGRADE'
                            sound_handler.extra.play()
                        else:
                            block.number -= 1
                            Score.score += 1
                            self.life -= 1
                            if not block.number:
                                Score.score += 3
                                blocks.remove(block)
                            sound_handler.hit.play()
                        collision = True
        if collision:
            setattr(self, axis, -getattr(self, axis))
            self.center[index] += getattr(self, axis)
        
        return self.center[1] >= win_rect.height or not self.life

    def update(self):
        ''' Moves and also returns if it should be deleted '''

        dead = self.update_axis(0, 'x_speed', True)
        if dead or self.update_axis(1, 'y_speed'):
            sound_handler.dead.play()
            return True
        return False

    def draw(self):

        pg.draw.circle(win, (255, 255, 0), self.center, BALL_RAD)


class SoundHandler:
    ''' Keeps track of all the sounds '''

    def __init__(self):

        self.dead = pg.mixer.Sound('sounds/dead.wav')
        self.extra = pg.mixer.Sound('sounds/get.wav')
        self.deploy = pg.mixer.Sound('sounds/deploy.wav')
        self.jump = pg.mixer.Sound('sounds/jump.wav')
        self.hit = pg.mixer.Sound('sounds/blip.wav')
        self.up = pg.mixer.Sound('sounds/wup.wav')


class EventHandler:
    ''' Keeps track of all the key-clicks and stuff '''

    def __init__(self):

        self.reset()

    def reset(self):

        self.w = False
        self.a = False
        self.s = False
        self.d = False

    def update_keys(self, key, boolean):

        if key in (pg.K_w, pg.K_UP):
            self.w = boolean
        elif key in (pg.K_a, pg.K_LEFT):
            self.a = boolean
        elif key in (pg.K_s, pg.K_DOWN):
            self.s = boolean
        elif key in (pg.K_d, pg.K_RIGHT):
            self.d = boolean


class Score:
    score = 0
class BallLife:
    ball_life = 10


def draw(balls=[]):
    ''' Draw all the stuff to the window '''

    win.fill((255, 255, 255))

    for block in blocks:
        block.draw()
    for ball in balls:
        ball.draw()
    blocky.draw()

    image = ball_font.render(f'Balls: {num_balls}', True, (0, 0, 0))
    rect = image.get_rect()
    rect.x += 2
    rect.y += 2
    win.blit(image, rect)

    if not shooting:
        # Draw a target where the mouse is
        image = pg.Surface((TARGET_EDGE, TARGET_EDGE))
        image.set_colorkey((0, 0, 0))
        pg.draw.circle(image, (255, 0, 0), (TARGET_EDGE // 2, TARGET_EDGE // 2), TARGET_EDGE // 2, width=1)
        pg.draw.circle(image, (255, 0, 0), (TARGET_EDGE // 2, TARGET_EDGE // 2), TARGET_EDGE // 4, width=1)
        pg.draw.circle(image, (255, 0, 0), (TARGET_EDGE // 2, TARGET_EDGE // 2), 1)
        pg.draw.line(image, (255, 0, 0), (0, TARGET_EDGE // 2), (TARGET_EDGE, TARGET_EDGE // 2), width=1)
        pg.draw.line(image, (255, 0, 0), (TARGET_EDGE // 2, 0), (TARGET_EDGE // 2, TARGET_EDGE), width=1)
        rect = image.get_rect()
        rect.center = pg.mouse.get_pos()
        win.blit(image, rect)

    pg.display.flip()


def gen_new_layer():
    ''' Generates a new layer of blocks '''

    layer = []
    for x in range(WIDTH):
        if not randint(0, EMPTY_CHANCE):
            continue
        rand_inc = randint(0, 1)
        layer.append(Block(x * BLOCK_EDGE, stage + rand_inc))
    return layer


# Try to load the highscore file
try:
    with open(FILENAME) as file:
        highscore = json.load(file)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    highscore = 1
    save_highscore(highscore)

stage = 1
num_balls = 2
shooting = False

blocks = []
for _ in range(START_LAYERS):
    for block in gen_new_layer():
        blocks.append(block)
    for block in blocks:
        block.rect.y -= BLOCK_EDGE

sound_handler = SoundHandler()
event_handler = EventHandler()
blocky = Blocky()

while True:

    for event in pg.event.get():
        if event.type == pg.QUIT:
            stop()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_q:
                stop()
            event_handler.update_keys(event.key, True)
        elif event.type == pg.KEYUP:
            event_handler.update_keys(event.key, False)
        elif event.type == pg.MOUSEBUTTONDOWN:
            event_handler.s = True

    if blocky.update():
        stop()
    for block in blocks:
        if block.remove:
            if block.remove == 'UPGRADE':
                BallLife.ball_life += 1
            else:
                num_balls += 1
            blocks.remove(block)

    if event_handler.s and blocky.on_ground:
        # Shoot the balls!
        # But first figure out the x and y speed for them
        # abs(x_speed) + abs(y_speed) = BALL_SPEED
        mx, my = pg.mouse.get_pos()
        dx, dy = mx - blocky.rect.center[0], my - blocky.rect.center[1]
        x_sign = 1 if dx > 0 else -1
        y_sign = 1 if dy > 0 else -1
        dx, dy = abs(dx), abs(dy)
        # x_speed/drop + y_speed/drop = BALL_SPEED so...
        # (x_speed + y_speed) / BALL_SPEED = drop
        drop = (dx + dy) / BALL_SPEED
        x_speed, y_speed = dx / drop, dy / drop
        x_speed *= x_sign
        y_speed *= y_sign

        balls_added = 0
        balls_to_add = num_balls
        balls = []
        last_added = time()
        event_handler.reset()
        shooting = True

        while shooting:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    stop()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        stop()
                    elif event.key == pg.K_SPACE:
                        shooting = False

            for ball in balls:
                if ball.update():
                    balls.remove(ball)
            if time() - last_added >= BALL_ADD_SPEED and balls_added < balls_to_add:
                balls.append(Ball(x_speed, y_speed, blocky.rect.center))
                last_added = time()
                balls_added += 1
                sound_handler.deploy.play()

            for block in blocks:
                if block.remove:
                    if block.remove == 'UPGRADE':
                        BallLife.ball_life += 1
                    else:
                        num_balls += 1
                    blocks.remove(block)
            if blocky.update():
                stop()
            
            draw(balls)
            clock.tick(FRAMERATE)

            if balls_added == balls_to_add and not balls:
                shooting = False
        
        # Generate a new layer
        stage += 1
        for block in gen_new_layer():
            blocks.append(block)
        for _ in range(BLOCK_EDGE):
            for block in blocks:
                block.rect.y -= 1
                if block.rect.y == -BLOCK_EDGE:
                    stop()
            blocky.rect.y -= 1
            draw()
        sound_handler.up.play()

        if Score.score > highscore:
            highscore = Score.score
            save_highscore(highscore)

    draw()
    clock.tick(FRAMERATE)
