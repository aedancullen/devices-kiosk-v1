import os
import pygame

class pygameFramebuffer:
        screen = None

        def __init__(self):
                driver = 'fbcon'
                #print 'Trying driver:', driver, '...'
                os.putenv('SDL_VIDEODRIVER', driver)
                try:
                        pygame.display.init()
                except pygame.error:
                        print 'Failed.'
                        raise Exception('Cannot open display because no video driver that works could be found.')

                #print 'Video driver', driver, 'works.'
                #print 'Starting display...'
                size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
                self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
                #print 'Done!'
