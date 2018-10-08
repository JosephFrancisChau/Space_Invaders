import pygame
import sys
from pygame import *
from os.path import abspath, dirname
from random import randint, choice

# shortcut to file paths
BASE_PATH = abspath(dirname(__file__))
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)
PINK = (255, 192, 203)
SCREEN = display.set_mode((800, 600))
FONT = 'fonts/space_invaders.ttf'


class Ship(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


# used to store images
IMG_NAMES = ['ship', 'mystery',
             'alien1_1', 'alien1_2',
             'alien2_1', 'alien2_2',
             'alien3_1', 'alien3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'alienlaser']
IMAGES = {name: image.load('images/{}.png'.format(name)).convert_alpha()
          for name in IMG_NAMES}


class Aliens(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.direction = 1
        self.right_moves = 30
        self.left_moves = 30
        self.move_number = 15
        self.move_time = 600
        self.timer = time.get_ticks()

    def update(self, keys, current_time, aliens):
        if self.move_time < current_time - self.timer:
            if self.direction == 1:
                max_move = self.right_moves + aliens.right_add_move
            else:
                max_move = self.left_moves + aliens.left_add_move

            if self.move_number >= max_move:
                if self.direction == 1:
                    self.left_moves = 30 + aliens.right_add_move
                elif self.direction == -1:
                    self.right_moves = 30 + aliens.left_add_move
                self.direction *= -1
                self.move_number = 0
                self.rect.y += 35
            elif self.direction == 1:
                self.rect.x += 10
                self.move_number += 1
            elif self.direction == -1:
                self.rect.x -= 10
                self.move_number += 1

            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
            self.image = self.images[self.index]

            self.timer += self.move_time

        game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1_2', '1_1'],
                  1: ['2_2', '2_1'],
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }
        img1, img2 = (IMAGES['alien{}'.format(img_num)] for img_num in
                      images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class AlienGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.aliens = [[0] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.left_add_move = 0
        self.right_add_move = 0
        self._alive_columns = list(range(columns))
        self._left_alive_column = 0
        self._right_alive_column = columns - 1
        self._left_killed_columns = 0
        self._right_killed_columns = 0

    def add(self, *sprites):
        super(sprite.Group, self).add(*sprites)

        for s in sprites:
            self.aliens[s.row][s.column] = s

    def is_column_dead(self, column):
        for row in range(self.rows):
            if self.aliens[row][column]:
                return False
        return True

    @property
    def random_bottom(self):
        random_index = randint(0, len(self._alive_columns) - 1)
        col = self._alive_columns[random_index]
        for row in range(self.rows, 0, -1):
            enemy = self.aliens[row - 1][col]
            if enemy:
                return enemy
        return None

    def kill(self, alien):
        # on double hit calls twice for same enemy, so check before
        if not self.aliens[alien.row][alien.column]:
            return  # nothing to kill

        self.aliens[alien.row][alien.column] = None
        is_column_dead = self.is_column_dead(alien.column)
        if is_column_dead:
            self._alive_columns.remove(alien.column)

        if alien.column == self._right_alive_column:
            while self._right_alive_column > 0 and is_column_dead:
                self._right_alive_column -= 1
                self._right_killed_columns += 1
                self.right_add_move = self._right_killed_columns * 5
                is_column_dead = self.is_column_dead(self._right_alive_column)

        elif alien.column == self._left_alive_column:
            while self._left_alive_column < self.columns and is_column_dead:
                self._left_alive_column += 1
                self._left_killed_columns += 1
                self.left_add_move = self._left_killed_columns * 5
                is_column_dead = self.is_column_dead(self._left_alive_column)


class Bunker(sprite.Sprite):
    def __init__(self, size, colour, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = colour
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.move_time = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mystery_entered = mixer.Sound(SOUND_PATH + 'mysteryentered.wav')
        # self.mystery_entered.set_volume(0.5)
        self.play_sound = True

    def update(self, keys, current_time, *args):
        reset_timer = False
        passed = current_time - self.timer
        if passed > self.move_time:
            if (self.rect.x < 0 or self.rect.x > 800) and self.play_sound:
                self.mystery_entered.play()
                self.play_sound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mystery_entered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mystery_entered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.play_sound = True
            self.direction = -1
            reset_timer = True
        if self.rect.x < -90:
            self.play_sound = True
            self.direction = 1
            reset_timer = True
        if passed > self.move_time and reset_timer:
            self.timer = current_time


class Explosion(sprite.Sprite):
    def __init__(self, xpos, ypos, row, ship, mystery, score):
        sprite.Sprite.__init__(self)
        self.is_mystery = mystery
        self.is_ship = ship
        if mystery:
            self.text = Text(FONT, 20, str(score), WHITE, xpos + 20, ypos + 6)
        elif ship:
            self.image = IMAGES['ship']
            self.rect = self.image.get_rect(topleft=(xpos, ypos))
        else:
            self.row = row
            self.load_image()
            self.image = transform.scale(self.image, (40, 35))
            self.rect = self.image.get_rect(topleft=(xpos, ypos))
            game.screen.blit(self.image, self.rect)

        self.timer = time.get_ticks()

    def update(self, keys, current_time):
        passed = current_time - self.timer
        if self.is_mystery:
            if passed <= 200:
                self.text.draw(game.screen)
            elif 400 < passed <= 600:
                self.text.draw(game.screen)
            elif passed > 600:
                self.kill()
        elif self.is_ship:
            if 300 < passed <= 600:
                game.screen.blit(self.image, self.rect)
            elif passed > 900:
                self.kill()
        else:
            if passed <= 100:
                game.screen.blit(self.image, self.rect)
            elif 100 < passed <= 200:
                self.image = transform.scale(self.image, (50, 45))
                game.screen.blit(self.image,
                                 (self.rect.x - 6, self.rect.y - 6))
            elif passed > 400:
                self.kill()

    def load_image(self):
        imgColors = ['purple', 'blue', 'blue', 'green', 'green']
        self.image = IMAGES['explosion{}'.format(imgColors[self.row])]


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, colour, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, colour)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.caption = display.set_caption('Space Invaders')
        self.screen = SCREEN
        self.background = image.load('images/background.jpg').convert()
        self.start_game = False
        self.main_screen = True
        self.game_over = False
        # Initial value for a new game
        self.alien_position_default = 65
        # Counter for enemy starting position (increased each new round)
        self.alien_position_start = self.alien_position_default
        # Current enemy starting position
        self.alien_position = self.alien_position_start

    def reset(self, score, lives, new_game=False):
        self.player = Ship()
        self.player_group = sprite.Group(self.player)
        self.explosions_group = sprite.Group()
        self.bullets = sprite.Group()
        self.mystery_ship = Mystery()
        self.mystery_group = sprite.Group(self.mystery_ship)
        self.alien_bullets = sprite.Group()
        self.reset_lives(lives)
        self.alien_position = self.alien_position_start
        self.make_aliens()
        # Only create bunkers for a new game, not a new round
        if new_game:
            self.allBlockers = sprite.Group(self.make_bunkers(0),
                                            self.make_bunkers(1),
                                            self.make_bunkers(2),
                                            self.make_bunkers(3))
        self.keys = key.get_pressed()
        self.clock = time.Clock()
        self.timer = time.get_ticks()
        self.note_timer = time.get_ticks()
        self.ship_timer = time.get_ticks()
        self.score = score
        self.lives = lives
        self.create_audio()
        self.create_text()
        self.make_new_ship = False
        self.ship_alive = True

    @staticmethod
    def make_bunkers(number):
        bunker_group = sprite.Group()
        for row in range(4):
            for column in range(9):
                bunker = Bunker(10, PINK, row, column)
                bunker.rect.x = 50 + (200 * number) + (column * bunker.width)
                bunker.rect.y = 450 + (row * bunker.height)
                bunker_group.add(bunker)
        return bunker_group

    def reset_lives_sprites(self):
        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)

        if self.lives == 3:
            self.lives_group = sprite.Group(self.life1, self.life2, self.life3)
        elif self.lives == 2:
            self.lives_group = sprite.Group(self.life1, self.life2)
        elif self.lives == 1:
            self.lives_group = sprite.Group(self.life1)

    def reset_lives(self, lives):
        self.lives = lives
        self.reset_lives_sprites()

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                           'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(
                SOUND_PATH + '{}.wav'.format(sound_name))
            # self.sounds[sound_name].set_volume(0.2)

        self.music_notes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i
                            in range(4)]
        # for sound in self.musicNotes:
        #     sound.set_volume(0.5)

        self.note_index = 0

    def play_main_music(self, current_time):
        move_time = self.aliens.sprites()[0].move_time
        if current_time - self.note_timer > move_time:
            self.note = self.music_notes[self.note_index]
            if self.note_index < 3:
                self.note_index += 1
            else:
                self.note_index = 0

            self.note.play()
            self.note_timer += move_time

    def create_text(self):
        self.title_text = Text(FONT, 50, 'Space Invaders', WHITE, 164, 155)
        self.title_text2 = Text(FONT, 25, 'Press any key to continue', WHITE,
                                201, 225)
        self.game_over_text = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.next_round_text = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.alien1_text = Text(FONT, 25, '   =  10 pts', GREEN, 368, 270)
        self.alien2_text = Text(FONT, 25, '   =  20 pts', BLUE, 368, 320)
        self.alien3_text = Text(FONT, 25, '   =  30 pts', PURPLE, 368, 370)
        self.alien4_text = Text(FONT, 25, '   =  ?????', RED, 368, 420)
        self.score_text = Text(FONT, 20, 'Score', WHITE, 5, 5)
        self.lives_text = Text(FONT, 20, 'Lives ', WHITE, 640, 5)

    @staticmethod
    def should_exit(evt):
        # type: (pygame.event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) <= 3 and self.ship_alive:
                        # this allows us to set a score limit to when we can have dual lasers
                        # like galaga
                        # if self.score < 1000:
                        bullet = Bullet(self.player.rect.x + 23,
                                        self.player.rect.y + 5, -1,
                                        15, 'laser', 'center')
                        self.bullets.add(bullet)
                        self.all_sprites.add(self.bullets)
                        self.sounds['shoot'].play()
                    # Code below enables dual lasers
                    # else:
                    #     leftbullet = Bullet(self.player.rect.x + 8,
                    #                         self.player.rect.y + 5, -1,
                    #                         15, 'laser', 'left')
                    #     rightbullet = Bullet(self.player.rect.x + 38,
                    #                          self.player.rect.y + 5, -1,
                    #                          15, 'laser', 'right')
                    #     self.bullets.add(leftbullet)
                    #     self.bullets.add(rightbullet)
                    #     self.allSprites.add(self.bullets)
                    #     self.sounds['shoot2'].play()

    def make_aliens(self):
        aliens = AlienGroup(10, 5)
        for row in range(5):
            for column in range(10):
                alien = Aliens(row, column)
                alien.rect.x = 157 + (column * 50)
                alien.rect.y = self.alien_position + (row * 45)
                aliens.add(alien)

        self.aliens = aliens
        self.all_sprites = sprite.Group(self.player, self.aliens,
                                        self.lives_group, self.mystery_ship)

    def make_aliens_shoot(self):
        if (time.get_ticks() - self.timer) > 700:
            alien = self.aliens.random_bottom
            if alien:
                self.alien_bullets.add(
                    Bullet(alien.rect.x + 14, alien.rect.y + 20, 1, 5,
                           'alienlaser', 'center'))
                self.all_sprites.add(self.alien_bullets)
                self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30,
                  1: 20,
                  2: 20,
                  3: 10,
                  4: 10,
                  5: choice([50, 100, 150, 300])
                  }

        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.alien1 = IMAGES['alien3_1']
        self.alien1 = transform.scale(self.alien1, (40, 40))
        self.alien2 = IMAGES['alien2_2']
        self.alien2 = transform.scale(self.alien2, (40, 40))
        self.alien3 = IMAGES['alien1_2']
        self.alien3 = transform.scale(self.alien3, (40, 40))
        self.mystery = IMAGES['mystery']
        self.mystery = transform.scale(self.mystery, (80, 40))
        self.screen.blit(self.alien1, (318, 270))
        self.screen.blit(self.alien2, (318, 320))
        self.screen.blit(self.alien3, (318, 370))
        self.screen.blit(self.mystery, (299, 420))

        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYUP:
                self.start_game = True
                self.main_screen = False

    def update_alien_speed(self):
        if len(self.aliens) <= 10:
            for alien in self.aliens:
                alien.move_time = 400
        if len(self.aliens) == 1:
            for alien in self.aliens:
                alien.move_time = 200

    def check_collisions(self):
        collide_dict = sprite.groupcollide(self.bullets, self.alien_bullets,
                                          True, False)
        if collide_dict:
            for value in collide_dict.values():
                for current_sprite in value:
                    self.alien_bullets.remove(current_sprite)
                    self.all_sprites.remove(current_sprite)

        alien_dict = sprite.groupcollide(self.bullets, self.aliens,
                                         True, False)
        if alien_dict:
            for value in alien_dict.values():
                for current_sprite in value:
                    self.aliens.kill(current_sprite)
                    self.sounds['invaderkilled'].play()
                    score = self.calculate_score(current_sprite.row)
                    explosion = Explosion(current_sprite.rect.x, current_sprite.rect.y,
                                          current_sprite.row, False, False, score)
                    self.explosions_group.add(explosion)
                    self.all_sprites.remove(current_sprite)
                    self.aliens.remove(current_sprite)
                    self.game_timer = time.get_ticks()
                    break

        mystery_dict = sprite.groupcollide(self.bullets, self.mystery_group,
                                          True, True)
        if mystery_dict:
            for value in mystery_dict.values():
                for current_sprite in value:
                    current_sprite.mysteryEntered.stop()
                    self.sounds['mysterykilled'].play()
                    score = self.calculate_score(current_sprite.row)
                    explosion = Explosion(current_sprite.rect.x, current_sprite.rect.y,
                                          current_sprite.row, False, True, score)
                    self.explosions_group.add(explosion)
                    self.all_sprites.remove(current_sprite)
                    self.mystery_group.remove(current_sprite)
                    new_ship = Mystery()
                    self.all_sprites.add(new_ship)
                    self.mystery_group.add(new_ship)
                    break

        bullets_dict = sprite.groupcollide(self.alien_bullets, self.player_group,
                                          True, False)
        if bullets_dict:
            for value in bullets_dict.values():
                for playerShip in value:
                    if self.lives == 3:
                        self.lives -= 1
                        self.lives_group.remove(self.life3)
                        self.all_sprites.remove(self.life3)
                    elif self.lives == 2:
                        self.lives -= 1
                        self.lives_group.remove(self.life2)
                        self.all_sprites.remove(self.life2)
                    elif self.lives == 1:
                        self.lives -= 1
                        self.lives_group.remove(self.life1)
                        self.all_sprites.remove(self.life1)
                    elif self.lives == 0:
                        self.game_over = True
                        self.start_game = False
                    self.sounds['shipexplosion'].play()
                    explosion = Explosion(playerShip.rect.x, playerShip.rect.y,
                                          0, True, False, 0)
                    self.explosions_group.add(explosion)
                    self.all_sprites.remove(playerShip)
                    self.player_group.remove(playerShip)
                    self.make_new_ship = True
                    self.ship_timer = time.get_ticks()
                    self.ship_alive = False

        if sprite.groupcollide(self.aliens, self.player_group, True, True):
            self.game_over = True
            self.start_game = False

        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.alien_bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.aliens, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.ship_timer > 900):
            self.player = Ship()
            self.all_sprites.add(self.player)
            self.player_group.add(self.player)
            self.make_new_ship = False
            self.ship_alive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 750:
            self.game_over_text.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.game_over_text.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.main_screen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.main_screen:
                self.reset(0, 3, True)
                self.screen.blit(self.background, (0, 0))
                self.title_text.draw(self.screen)
                self.title_text2.draw(self.screen)
                self.alien1_text.draw(self.screen)
                self.alien2_text.draw(self.screen)
                self.alien3_text.draw(self.screen)
                self.alien4_text.draw(self.screen)
                self.create_main_menu()

            elif self.start_game:
                if len(self.aliens) == 0:
                    current_time = time.get_ticks()
                    if current_time - self.game_timer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score),
                                               GREEN, 85, 5)
                        self.score_text.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.next_round_text.draw(self.screen)
                        self.lives_text.draw(self.screen)
                        self.lives_group.update(self.keys)
                        self.check_input()
                    if current_time - self.game_timer > 3000:
                        # Move enemies closer to bottom
                        self.alien_position_start += 35
                        self.reset(self.score, self.lives)
                        self.game_timer += 3000
                else:
                    current_time = time.get_ticks()
                    self.play_main_music(current_time)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN,
                                           85, 5)
                    self.score_text.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.lives_text.draw(self.screen)
                    self.check_input()
                    self.all_sprites.update(self.keys, current_time,
                                            self.aliens)
                    self.explosions_group.update(self.keys, current_time)
                    self.check_collisions()
                    self.create_new_ship(self.make_new_ship, current_time)
                    self.update_alien_speed()

                    if len(self.aliens) > 0:
                        self.make_aliens_shoot()

            elif self.game_over:
                current_time = time.get_ticks()
                # Reset alien starting position
                self.alien_position_start = self.alien_position_default
                self.create_game_over(current_time)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
