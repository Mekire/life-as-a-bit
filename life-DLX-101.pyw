#Written by Sean McKiernan (Mekire)
import sys,os
import pygame
from pygame.locals import *

#module that converts life pattern files into cartesian and also handles stamp transforms
import lif_converter

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()

SCREENSIZE = (1000,700)
SCREEN = pygame.display.set_mode(SCREENSIZE)

#graphics and fonts
bg        = pygame.image.load(os.path.join("graphics","lifedeluxe.png")).convert_alpha()
grid1     = pygame.image.load(os.path.join("graphics","zgrid1.png")).convert_alpha()
grid2     = pygame.image.load(os.path.join("graphics","zgrid2.png")).convert_alpha()
pressed   = pygame.image.load(os.path.join("graphics","pressed.png")).convert_alpha()
spressed   = pygame.image.load(os.path.join("graphics","spressed.png")).convert_alpha()
radial     = pygame.image.load(os.path.join("graphics","radial.png")).convert_alpha()
checkbox  = pygame.image.load(os.path.join("graphics","checkbox.png")).convert()
selected  = pygame.image.load(os.path.join("graphics","selected.png")).convert()
infowin   = pygame.image.load(os.path.join("graphics","info.png")).convert()
arial = pygame.font.Font(os.path.join('graphics','ArialNb.TTF'),11)

ADJACENTS = {(-1, 1),(0, 1),(1,1 ),
             (-1, 0),(1, 0),
             (-1,-1),(0,-1),(1,-1)}

FILEFORMATS = ("lif","rle")

#cursor stuff
pencilcurs = pygame.image.load(os.path.join("graphics","pencilcurs.png")).convert_alpha()
openhand  = pygame.image.load(os.path.join("graphics","grab_open.png")).convert()
closehand = pygame.image.load(os.path.join("graphics","grab_closed.png")).convert()
crosscurs = pygame.image.load(os.path.join("graphics","crosscurs.png")).convert()
o_hand = lif_converter.image2cursor(openhand)
c_hand = lif_converter.image2cursor(closehand)
crossy = lif_converter.image2cursor(crosscurs)
OPEN_CRS  = pygame.cursors.compile(o_hand,".","X")
CLOSE_CRS = pygame.cursors.compile(c_hand,".","X")
CROSS_CRS = pygame.cursors.compile(crossy,".","X")
DEFAULT_CURSOR = pygame.mouse.get_cursor()

#just a convenience
BaseOffset = ((0,0),(200,150),(320,240),(360,270))
BaseSize   = ((1,1),(2,2),(5,5),(10,10))
BaseGrid   = (None,None,grid1,grid2)

class LetThereBe():
    def __init__(self):
        self.screen = SCREEN
        self.state     = "START"
        self.living    = set()
        self.temp      = set()
        self.clipboard = set()
        
        self.cell_size = (5,5) 
        self.zoom = 2 #default to 5x5 pixel cells
        self.grid = grid1
        self.gridon = True
        self.offset = BaseOffset[2]
        self.target = (0,0)

        self.pan = [0,0]

        self.birthmin   = 3
        self.birthmax   = 3
        self.survivemin = 2
        self.survivemax = 3
 
        self.gen  = 1
        self.pop  = 0

        #pans
        self.pright = False
        self.pleft  = False
        self.pup    = False
        self.pdown  = False
        
        self.fps         = 20
        self.lastupdated = 0.0
        self.panupdate   = 0.0
        self.calced      = False
        self.lastcalced  = 0.0

        self.adding_cell  = False
        self.killing_cell = False
        
        self.mode     = "DRAW"

        #stamp directory stuff
        self.place_stamp = set()
        self.stampdir = "classic"
        self.dirlist  = []
        self.dirindex = 0
        self.highlight = None
        self.stampinfo = []
        self.stamp_dirlist()

        #stamp and info scroll bar stuff
        self.stampmouse = (0,0)
        self.showinfo  = False
        self.infoindex = 0
        self.infodrag  = False
        self.infoscroll,self.infoindsize = self.scroll_bar(self.stampinfo)

        #drag pan stuff
        self.grab = False
        self.drag_start = None

        #rectangle select mode
        self.start_corner = (0,0)
        self.stop_corner  = (0,0)
        self.rect_on = False
        self.rect_done = True
        
        #pencil cursor flag and buttons
        self.pencil = False
        self.reset_presses()
        self.ctrl_pressed = False

    def event_loop(self):
        self.target = pygame.mouse.get_pos()
        for click in pygame.event.get():
            if click.type == MOUSEBUTTONDOWN:
                hit = pygame.mouse.get_pressed()
                if hit[0]:
                    self.target = pygame.mouse.get_pos()
                    if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
                        if not self.showinfo or not ((160 < self.target[0] < 590) and (7 < self.target[1] < 216)):
                            if self.mode == "DRAW":
                                #add cells
                                self.adding_cell = True
                            elif self.mode == "STAMP":
                                #add currently selected stamp
                                self.add_stamp()
                            elif self.mode == "GRAB":
                                self.grab = True
                                self.drag_start = ((self.target[0]-150)//self.cell_size[0],
                                                   (self.target[1])//self.cell_size[1])
                            elif self.mode == "SELECT":
                                self.start_corner = (self.offset[0]+(self.target[0]-150)//self.cell_size[0],
                                                     self.offset[1]+(self.target[1])//self.cell_size[1])
                                self.rect_on = True
                                self.rect_done = False
                    elif (150 < self.target[0] < 250) and (625 < self.target[1] < 675):
                        #Start button
                        self.state = "RUN"
                        self.start_press = True
                        self.rect_on = False
                        self.rect_done = True
                    elif (25 < self.target[0] < 125) and (625 < self.target[1] < 675):
                        #reset button
                        self.reset()
                    elif (275 < self.target[0] < 375) and (625 < self.target[1] < 675):
                        #pause button
                        self.state  = "START"
                        self.pause_press = True
                    elif (965 < self.target[0] < 986):
                        if (103 < self.target[1] < 139):
                            #turn grid on and off
                            self.gridon = (False if self.gridon else True)
                        elif (187 < self.target[1] < 223):
                            self.mode = "DRAW"
                            self.rect_on = False
                            self.rect_done = True
                        elif (239 < self.target[1] < 275):
                            self.mode = "STAMP"
                            self.rect_on = False
                            self.rect_done = True
                        elif (290 < self.target[1] < 326):
                            self.mode = "GRAB"
                            self.rect_on = False
                            self.rect_done = True
                        elif (341 < self.target[1] < 377):
                            self.mode = "SELECT"
                    if (958 < self.target[0] < 993) and (407 < self.target[1] < 457):
                        self.showinfo = (False if self.showinfo else True)
                        
                    elif (25 < self.target[0] < 113) and (367 < self.target[1] < 511):
                        #select stamp from the directory list
                        if self.highlight != None:
                            try:
                                self.stampname = self.dirlist[self.dirindex+self.highlight]
                                mystamp = os.path.join(self.stampdir,self.stampname)
                                self.infoindex = 0
                                self.stamp,self.stampinfo = lif_converter.converter(mystamp)
                                self.infoscroll,self.infoindsize = self.scroll_bar(self.stampinfo)
                                self.mode = "STAMP"
                                self.rect_on = False
                                self.rect_done = True
                            except IndexError: pass

                    elif (116 < self.target[0] < 129):
                        #switch stamp directory
                        if   (528 < self.target[1] < 541):
                            self.stampdir = "classic"
                            self.stamp_dirlist()
                        elif (549 < self.target[1] < 562):
                            self.stampdir = "lifep"
                            self.stamp_dirlist()

                    if (325 < self.target[1] < 350):
                        #stamp transformations
                        if   (19 < self.target[0] < 44):
                            self.stamp = lif_converter.rot_clockwise(self.stamp)
                            self.rot_r = True
                        elif (48 < self.target[0] < 73):
                            self.stamp = lif_converter.rot_counter(self.stamp)
                            self.rot_l = True
                        elif (77 < self.target[0] < 102):
                            self.stamp = lif_converter.mirror_V(self.stamp)
                            self.mir_v = True
                        elif (106 < self.target[0] < 131):
                            self.stamp = lif_converter.mirror_H(self.stamp)
                            self.mir_h = True

                    #change zoom
                    if 10 < self.target[0] < 140:
                        if   50  < self.target[1] < 77  :
                            self.zoom      = 0
                        elif 94  < self.target[1] < 121 :
                            self.zoom      = 1
                        elif 138 < self.target[1] < 165 :
                            self.zoom = 2
                        elif 182 < self.target[1] < 209 :
                            self.zoom = 3
                        self.cell_size = BaseSize[self.zoom]
                        self.grid      = BaseGrid[self.zoom]
                        self.offset    = (BaseOffset[self.zoom][0]+self.pan[0],BaseOffset[self.zoom][1]+self.pan[1])

                    if 966 < self.target[0] < 986:
                        #change desired framerate (note this is not necessarily the actual framerate if computation can't keep up)
                        if 30 < self.target[1] < 50:
                            if self.fps < 5: self.fps += 1
                            elif self.fps < 65: self.fps +=5
                        elif 68 < self.target[1] < 88:
                            if self.fps > 5: self.fps -= 5
                            elif self.fps > 1: self.fps -= 1
                    elif 113 < self.target[0] < 125:
                        #scroll up and down stamp selection directory (why here? why not?)
                        if   367 < self.target[1] < 379:
                            if self.dirindex > 0:
                                self.dirindex -= 1
                            elif len(self.dirlist)>12:
                                self.dirindex = (len(self.dirlist)-12)
                        elif 499 < self.target[1] < 511:
                            if self.dirindex < len(self.dirlist)-12:
                                self.dirindex += 1
                            else:
                                self.dirindex = 0
                        elif 379 < self.target[1] < 499:
                            barplace = self.dirindex*self.stampindsize
                            if barplace+self.stampscroll > 120:
                                barplace = 120-self.stampscroll
                            if   379+barplace > self.target[1]:
                                if self.dirindex > 12: self.dirindex -= 12
                                else: self.dirindex = 0
                            elif 379+barplace+self.stampscroll < self.target[1]:
                                if self.dirindex < len(self.dirlist)-24: self.dirindex += 12
                                else: self.dirindex = len(self.dirlist)-12
                            elif 379+barplace < self.target[1] < 379+barplace+self.stampscroll:
                                if len(self.dirlist)>12:
                                    self.stampdrag = True
                                    self.lastmouse = self.target[1]-(379+self.dirindex*self.stampindsize)
                                
                    if self.showinfo and (563 < self.target[0] < 575) and (56 < self.target[1] < 200):
                        #scroll up and down info window
                        if   56 < self.target[1] < 68:
                            if self.infoindex > 0:
                                self.infoindex -= 1
                            elif len(self.stampinfo)>12:
                                self.infoindex = (len(self.stampinfo)-12)
                        elif 188 < self.target[1] < 200:
                            if self.infoindex < len(self.stampinfo)-12:
                                self.infoindex += 1
                            else:
                                self.infoindex = 0
                        elif 68 < self.target[1] < 188:
                            if   68+self.infoindex*self.infoindsize > self.target[1]:
                                if self.infoindex > 12: self.infoindex -= 12
                                else: self.infoindex = 0
                            elif 68+self.infoindex*self.infoindsize+self.infoscroll < self.target[1]:
                                if self.infoindex < len(self.stampinfo)-24: self.infoindex += 12
                                else: self.infoindex = len(self.stampinfo)-12
                            elif 68+self.infoindex*self.infoindsize < self.target[1] < 68+self.infoindex*self.infoindsize+self.infoscroll:
                                if len(self.stampinfo)>12:
                                    self.infodrag = True
                                    self.lastmouse = self.target[1]-(379+self.infoindex*self.infoindsize)  

                    #You know the rules and so do I.  Change them here.
                    #try birth (3,3) and survival (1,5) for an interesting maze-like generator
                    #birth (4,8) and survival (1,7) creates closed seemingly aperiodic oscillators
                    if   640 < self.target[1] < 652:  
                        if   504 < self.target[0] < 516 and self.birthmin > 1: self.birthmin -= 1
                        elif 528 < self.target[0] < 540 and self.birthmin < 8: self.birthmin += 1
                        elif 677 < self.target[0] < 689 and self.birthmax > 1: self.birthmax -= 1
                        elif 701 < self.target[0] < 713 and self.birthmax < 8: self.birthmax += 1
                    elif 665 < self.target[1] < 677:
                        if   504 < self.target[0] < 516 and self.survivemin > 1: self.survivemin -= 1
                        elif 528 < self.target[0] < 540 and self.survivemin < 8: self.survivemin += 1
                        elif 677 < self.target[0] < 689 and self.survivemax > 1: self.survivemax -= 1
                        elif 701 < self.target[0] < 713 and self.survivemax < 8: self.survivemax += 1
                    elif (724 < self.target[0] < 779) and (650 < self.target[1] < 669):
                        #set back to Conway defaults
                        self.birthmin   = 3
                        self.birthmax   = 3
                        self.survivemin = 2
                        self.survivemax = 3
                          
                elif hit[2]:
                    #delete cells
                    self.target = pygame.mouse.get_pos()
                    if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
                        self.killing_cell = True

                #events triggered by scroll wheel here
                self.target = pygame.mouse.get_pos()
                if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
                    #zoom with scroll wheel, autocentering on the mouse cursor location
                    if   click.button == 4:
                        if not self.showinfo or not ((160 < self.target[0] < 590) and (7 < self.target[1] < 216)):
                            if self.zoom != 3:
                                self.pan[0] += ((self.target[0]-150-400)//BaseSize[self.zoom][0])
                                self.pan[1] += ((self.target[1]-300)//BaseSize[self.zoom][1])
                                self.zoom += 1
                                self.cell_size = BaseSize[self.zoom]
                                self.grid      = BaseGrid[self.zoom]
                                self.offset    = (BaseOffset[self.zoom][0]+self.pan[0],BaseOffset[self.zoom][1]+self.pan[1])
                                pygame.mouse.set_pos([550,300])
                        elif self.infoindex > 0:
                            self.infoindex -= 1
                    elif click.button == 5:
                        if not self.showinfo or not ((160 < self.target[0] < 590) and (7 < self.target[1] < 216)):
                            if self.zoom != 0:
                                self.pan[0] += ((self.target[0]-150-400)//BaseSize[self.zoom][0])
                                self.pan[1] += ((self.target[1]-300)//BaseSize[self.zoom][1])
                                self.zoom -= 1
                                self.cell_size = BaseSize[self.zoom]
                                self.grid      = BaseGrid[self.zoom]
                                self.offset    = (BaseOffset[self.zoom][0]+self.pan[0],BaseOffset[self.zoom][1]+self.pan[1])
                                pygame.mouse.set_pos([550,300])
                        elif self.infoindex < len(self.stampinfo)-12:
                            self.infoindex += 1
                elif (25 < self.target[0] < 113) and (367 < self.target[1] < 511):
                    #scroll through stamp directory with scroll wheel
                    if   click.button == 4:
                        if self.dirindex > 0:
                                self.dirindex -= 1
                    elif click.button == 5:
                        if self.dirindex < len(self.dirlist)-12:
                                self.dirindex += 1

            #stop adding or deleting cells if button no longer pressed            
            if click.type == pygame.MOUSEBUTTONUP:
                self.reset_presses()
                self.rect_done = True
                hit = pygame.mouse.get_pressed()
                if not hit[0]:
                    self.adding_cell  = False
                    self.stampdrag    = False
                    self.infodrag     = False
                if not hit[2]:
                    self.killing_cell = False
                self.grab = False
            if click.type == pygame.QUIT: self.state = "QUIT"

            #hotkeys
            if click.type == pygame.KEYDOWN:
                #ctrl
                if click.key in (K_LCTRL,K_RCTRL):
                    self.ctrl_pressed = True
                #panning events
                if   click.key == K_RIGHT: self.pright = True
                elif click.key == K_LEFT : self.pleft  = True
                elif click.key == K_UP   : self.pup    = True
                elif click.key == K_DOWN : self.pdown  = True
                #changeing modes
                elif click.key == K_1 :
                    self.mode = "DRAW"
                    self.rect_on = False
                    self.rect_done = True
                elif click.key == K_2 :
                    self.mode = "STAMP"
                    self.rect_on = False
                    self.rect_done = True
                elif click.key == K_3 :
                    self.mode = "GRAB"
                    self.rect_on = False
                    self.rect_done = True
                elif click.key == K_4 :
                    self.mode = "SELECT"
                #minor controls
                elif click.key == K_i : self.showinfo = (False if self.showinfo else True)
                elif click.key == K_g : self.gridon = (False if self.gridon else True)
                elif click.key in (K_PLUS,K_EQUALS,K_KP_PLUS):
                    if self.fps < 5: self.fps += 1
                    elif self.fps < 65: self.fps +=5
                elif click.key in (K_MINUS,K_KP_MINUS):
                    if self.fps > 5: self.fps -= 5
                    elif self.fps > 1: self.fps -= 1
                elif click.key in (K_DELETE,K_KP_PERIOD):
                    if self.rect_on and self.rect_done:
                        self.del_rect()
                elif click.key == K_c:
                    if self.ctrl_pressed:
                        if self.rect_on and self.rect_done:
                            self.copy_rect()
                elif click.key == K_x:
                    if self.ctrl_pressed:
                        if self.rect_on and self.rect_done:
                            self.cut_rect()
                elif click.key == K_v:
                    if self.ctrl_pressed:
                        self.paste_rect()
                elif click.key == K_s:
                    if self.ctrl_pressed:
                        self.save_screen()
                #main controls
                elif click.key == K_p :
                    self.state = "START"
                    self.pause_press = True
                elif click.key == K_BACKSPACE : self.reset()
                elif click.key == K_SPACE  :
                    self.state = "RUN"
                    self.start_press = True
                    self.rect_on = False
                    self.rect_done = True
                elif click.key == K_RETURN:
                    if self.rect_on:
                        self.rect_on = False
                        self.rect_done = True
                elif click.key == K_ESCAPE :
                    if self.rect_on:
                        self.rect_on = False
                        self.rect_done = True
                #stamp controls
                elif click.key == K_q:
                    if self.ctrl_pressed:
                        self.state = "QUIT"
                    else:
                        self.stamp = lif_converter.rot_clockwise(self.stamp)
                        self.rot_r = True
                elif click.key == K_w:
                    self.stamp = lif_converter.rot_counter(self.stamp)
                    self.rot_l = True
                elif click.key == K_e:
                    self.stamp = lif_converter.mirror_V(self.stamp)
                    self.mir_v = True
                elif click.key == K_r:
                    self.stamp = lif_converter.mirror_H(self.stamp)
                    self.mir_h = True
            if click.type == pygame.KEYUP:
                if click.key in (K_LCTRL,K_RCTRL):
                    self.ctrl_pressed = False
                self.reset_presses()
                if   click.key == K_RIGHT  : self.pright = False
                elif click.key == K_LEFT   : self.pleft  = False
                elif click.key == K_UP     : self.pup    = False
                elif click.key == K_DOWN   : self.pdown  = False
        self.changes()

    def changes(self):
        #adding and deleting cell logic
        if   self.adding_cell == True:
            self.target = pygame.mouse.get_pos()
            self.living |= set(((self.offset[0]+(self.target[0]-150)//self.cell_size[0],self.offset[1]+(self.target[1])//self.cell_size[1]),))
        elif self.killing_cell == True:
            self.target = pygame.mouse.get_pos()
            self.living -= set(((self.offset[0]+(self.target[0]-150)//self.cell_size[0],self.offset[1]+(self.target[1])//self.cell_size[1]),))

        if self.stampdrag:
            self.target = pygame.mouse.get_pos()
            next_index  = int((self.target[1]-self.lastmouse-379)//self.stampindsize)
            if next_index <= 0:
                self.dirindex = 0
            elif next_index > len(self.dirlist)-12:
                self.dirindex = len(self.dirlist)-12
            else:
                self.dirindex = next_index
                
        elif self.infodrag:
            self.target = pygame.mouse.get_pos()
            next_index  = int((self.target[1]-self.lastmouse-379)//self.infoindsize)
            if   next_index <= 0:
                self.infoindex = 0
            elif next_index > len(self.stampinfo)-12:
                self.infoindex = len(self.stampinfo)-12
            else:
                self.infoindex = next_index

        #grab panning
        if self.mode == "GRAB" and self.grab:
            self.grab_pull()

        #panning logic
        if pygame.time.get_ticks() - self.panupdate > 1000/65:
            if   self.pright: self.pan[0] += 1
            if self.pleft : self.pan[0] -= 1
            if self.pup   : self.pan[1] -= 1
            if self.pdown : self.pan[1] += 1
            self.panupdate = pygame.time.get_ticks()
            self.offset = (BaseOffset[self.zoom][0]+self.pan[0],BaseOffset[self.zoom][1]+self.pan[1])

        #directory highlighting
        if (25 < self.target[0] < 113) and (367 < self.target[1] < 511):
            self.highlight = (self.target[1]-367)//12
        else: self.highlight = None

        #change cursors
        if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
            if not self.showinfo or not ((160 < self.target[0] < 590) and (7 < self.target[1] < 216)):
                if self.mode == "GRAB":
                    if not self.grab and pygame.mouse.get_cursor() != ((24,24),(12,12),OPEN_CRS[0],OPEN_CRS[1]):
                        pygame.mouse.set_cursor((24,24),(12,12),*OPEN_CRS)
                    elif self.grab and pygame.mouse.get_cursor() != ((24,24),(12,12),CLOSE_CRS[0],CLOSE_CRS[1]):
                        pygame.mouse.set_cursor((24,24),(12,12),*CLOSE_CRS)
                    self.pencil = False
                elif self.mode in ("STAMP","DRAW"):
                    if pygame.mouse.get_cursor() != ((8,8),(0,7),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)):
                        pygame.mouse.set_cursor((8,8),(0,7),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
                    self.pencil = (True if self.mode == "DRAW" else False)
                elif self.mode == "SELECT":
                    if pygame.mouse.get_cursor() != ((16,16),(8,8),CROSS_CRS[0],CROSS_CRS[1]):
                        pygame.mouse.set_cursor((16,16),(8,8),*CROSS_CRS)
                    self.pencil = False
                else: self.cursor2default(); self.pencil = False          
            else: self.cursor2default(); self.pencil = False
        else: self.cursor2default(); self.pencil = False
        
        #for rectangle in select mode
        if self.rect_on and not self.rect_done and (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
            self.stop_corner = (self.offset[0]+(self.target[0]-150)//self.cell_size[0],
                                self.offset[1]+(self.target[1])//self.cell_size[1])
            
        #buttons pressed
        if   self.start_press:
            self.screen.blit(pressed,(150,625))
        elif self.reset_press:
            self.screen.blit(pressed,(25,625))
        elif self.pause_press:
            self.screen.blit(pressed,(275,625))
        elif self.rot_r:
            self.screen.blit(spressed,(19,325))
        elif self.rot_l:
            self.screen.blit(spressed,(48,325))
        elif self.mir_v:
            self.screen.blit(spressed,(77,325))
        elif self.mir_h:
            self.screen.blit(spressed,(106,325))
                    
    def cursor2default(self):
        if pygame.mouse.get_cursor() != DEFAULT_CURSOR:
            pygame.mouse.set_cursor(*DEFAULT_CURSOR)

    def reset(self):
        self.state  = "START"
        self.calced = False
        self.living = set()
        self.gen    = 1
        self.reset_press = True
        self.rect_on = False
        self.rect_done = True

    def reset_presses(self):
        self.pause_press = False
        self.reset_press = False
        self.start_press = False
        self.rot_r = False
        self.rot_l = False
        self.mir_v = False
        self.mir_h = False

    def grab_pull(self):
        here_now = ((self.target[0]-150)//self.cell_size[0],(self.target[1])//self.cell_size[1])
        if self.drag_start != here_now:
            self.pan[0] += (self.drag_start[0]-here_now[0])
            self.pan[1] += (self.drag_start[1]-here_now[1])
            self.drag_start = here_now
            
    def add_stamp(self):
        self.get_stamp()
        self.living |= self.place_stamp

    def get_stamp(self):
        targx = ((self.target[0]-150)//BaseSize[self.zoom][0])
        targy = ((self.target[1])//BaseSize[self.zoom][1])
        for a,b in self.stamp: 
            self.place_stamp |=set(((self.offset[0]+targx+a,self.offset[1]+targy+b),))

    def stamp_dirlist(self):
        self.dirlist = os.listdir(self.stampdir)
        for item in self.dirlist:
            if item.lower()[-3:] not in FILEFORMATS:
                self.dirlist.remove(item)
        if "PYGAME.LIF" in self.dirlist:
            self.stampname = "PYGAME.LIF"
            mystamp = os.path.join(self.stampdir,self.stampname)
            self.stamp,self.stampinfo = lif_converter.converter(mystamp)
        else:
            self.stampname = self.dirlist[0]
            mystamp = os.path.join(self.stampdir,self.stampname)
            self.stamp,self.stampinfo = lif_converter.converter(mystamp)
        self.highlight = None
        self.stampdrag = False
        self.dirindex  = 0
        self.stampscroll,self.stampindsize = self.scroll_bar(self.dirlist)

    def scroll_bar(self,content):
        #scroll bars should really be a seperate usable class.  This would cut down on redundant code.
        bartotal = 120
        if len(content) > 12:
            barsize  = 120*(12/float(len(content)))
            perindex = 120/float(len(content))
        else:
            barsize  = 120
            perindex = 10
        if barsize < 10:
            barsize = 10
        return barsize,perindex
         
    def stats(self):
        #updates all the numbers and selection boxes on screen
        self.pop = len(self.living)
        self.screen.blit(arial.render(str(self.pop).zfill(7),1,(255,255,255)),(915,634))
        self.screen.blit(arial.render(str(self.gen).zfill(7),1,(255,255,255)),(915,658))
        self.screen.blit(arial.render(str(self.fps).zfill(2),1,(255,255,255)),(970,52))
        self.screen.blit(arial.render(str(self.birthmin),1,(255,255,255)),(520,639))
        self.screen.blit(arial.render(str(self.birthmax),1,(255,255,255)),(693,639))
        self.screen.blit(arial.render(str(self.survivemin),1,(255,255,255)),(520,664))
        self.screen.blit(arial.render(str(self.survivemax),1,(255,255,255)),(693,664))
        self.screen.blit(radial,(97,51+44*self.zoom))
        if not self.gridon:
            self.screen.blit(checkbox,(969,126))
        if not self.showinfo:
            self.screen.blit(checkbox,(969,444))
        if   self.mode == "DRAW":
            self.screen.blit(selected,(969,210))
        elif self.mode == "STAMP":
            self.screen.blit(selected,(969,262))
        elif self.mode == "GRAB":
            self.screen.blit(selected,(969,313))
        elif self.mode == "SELECT":
            self.screen.blit(selected,(969,364))
        if self.stampdir == "lifep":
            self.screen.blit(selected,(116,549))
        else:
            self.screen.blit(selected,(116,528))

        #scroll bar display here
        barplace = self.dirindex*self.stampindsize
        if barplace+self.stampscroll > 120:
            barplace = 120-self.stampscroll
        self.screen.fill((255,255,255),(114,379+barplace,6,self.stampscroll))
        self.screen.fill((220,220,220),(120,379+barplace,4,self.stampscroll))

        #displays the list of stamps in the given directory
        if len(self.stampname)<=12:
            self.screen.blit(arial.render(self.stampname,1,(255,255,255)),(35,299))
        else:
            self.screen.blit(arial.render(self.stampname[0:12],1,(255,255,255)),(35,299))
        for i,item in enumerate(self.dirlist[self.dirindex:(self.dirindex+12)]):
            if len(item)<=12:
                self.screen.blit(arial.render(item,1,(0,0,0)),(30,366+12*i))
            else:
                self.screen.blit(arial.render(item[0:12],1,(0,0,0)),(30,366+12*i))
        if self.highlight != None:
            self.screen.fill((0,0,0),(25,367+12*self.highlight,88,12))
            try:
                item = self.dirlist[self.dirindex+self.highlight]
                if len(item)<=12:
                    self.screen.blit(arial.render(item,1,(255,255,255)),(30,366+12*self.highlight))
                else:
                    self.screen.blit(arial.render(item[0:12],1,(255,255,255)),(30,366+12*self.highlight))
            except IndexError: pass
        #shows the info associated with the selected stamp
        if self.showinfo:
            self.screen.blit(infowin,(160,7))
            self.screen.fill((255,255,255),(564,68+self.infoindex*self.infoindsize,6,self.infoscroll))
            self.screen.fill((220,220,220),(570,68+self.infoindex*self.infoindsize,4,self.infoscroll))
            for i,item in enumerate(self.stampinfo[self.infoindex:(self.infoindex+12)]):
                self.screen.blit(arial.render(item,1,(0,0,0)),(180,55+12*i))

        if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
            targ = (self.offset[0]+(self.target[0]-150)//self.cell_size[0],self.offset[1]+(self.target[1])//self.cell_size[1])
            self.screen.blit(arial.render("X,Y: " + str(targ),1,(0,0,0)),(875,603)) 

        if self.pencil:
            targ = pygame.mouse.get_pos()
            self.screen.blit(pencilcurs,(targ[0],targ[1]-24))
            
    def draw(self):
        #handles the drawing of all the cells and the stamp ghost image when applicable
        if self.mode == "STAMP":
            self.target = pygame.mouse.get_pos()
            if (150 < self.target[0] < 950) and (0 < self.target[1] < 600):
                self.get_stamp()
                for cell in self.place_stamp:
                    self.screen.fill((0,100,255),((150+(cell[0]-self.offset[0])*self.cell_size[0],(cell[1]-self.offset[1])*self.cell_size[1]),self.cell_size))
                self.place_stamp = set()
        for cell in self.living:
            self.screen.fill((255,255,0),((150+(cell[0]-self.offset[0])*self.cell_size[0],(cell[1]-self.offset[1])*self.cell_size[1]),self.cell_size))

    def select_rect(self):
        #handles drawing the rectangle in select mode
        start = (150+(self.start_corner[0]-self.offset[0])*self.cell_size[0],(self.start_corner[1]-self.offset[1])*self.cell_size[1])
        stop  = (150+(self.stop_corner[0]-self.offset[0])*self.cell_size[0],(self.stop_corner[1]-self.offset[1])*self.cell_size[1])
        height = stop[1]-start[1]
        width  = stop[0]-start[0]
        if height > 0:
            height += self.cell_size[1]
        else:
            start   = (start[0],start[1]+self.cell_size[1])
            height -= self.cell_size[1]
        if width  > 0:
            width  += self.cell_size[0]
        else:
            start   = (start[0]+self.cell_size[0],start[1])
            width  -= self.cell_size[0]
        pygame.draw.rect(self.screen,(0,0,255),(start,(width,height)),2)

    #rectangel selection mode related functions here
    def get_rect_set(self):
        #creates a set of all the points contained with in the selection rectangle
        first = [0,0] ; second = [0,0]
        self.temp = set()
        if self.start_corner[0] >= self.stop_corner[0]:
            first[0]  = self.stop_corner[0]
            second[0] = self.start_corner[0]
        else:
            first[0]  = self.start_corner[0]
            second[0] = self.stop_corner[0]
        if self.start_corner[1] >= self.stop_corner[1]:
            first[1]  = self.stop_corner[1]
            second[1] = self.start_corner[1]
        else:
            first[1]  = self.start_corner[1]
            second[1] = self.stop_corner[1]
        living_copy = self.living.copy()
        for cell in living_copy:
            if (first[0] <= cell[0] <= second[0]) and (first[1] <= cell[1] <= second[1]):
                self.temp |= set((cell,))
    def del_rect(self,accessed=False):
        #pressing delete in rectangle select mode
        if not accessed:
            self.get_rect_set()
            self.rect_on = False
            self.rect_done = True
        for cell in self.temp:
            self.living.discard(cell)
    def copy_rect(self,accessed=False):
        #pressing ctrl+c in rectangle select mode
        self.get_rect_set()
        self.clipboard = lif_converter.recenter(self.temp)
        self.stamp = self.clipboard.copy()
        self.stampname = "Clip Board"
        self.stampinfo = ["Clip Board"]
        self.rect_on = False
        self.rect_done = True
    def cut_rect(self):
        #pressing ctrl+x in rectangle select mode
        self.copy_rect()
        self.del_rect(True)
        self.rect_on = False
        self.rect_done = True
    def paste_rect(self):
        #pressing ctrl+v
        if self.clipboard:
            self.stamp = self.clipboard.copy()
            self.stampname = "Clip Board"
            self.stampinfo = ["Clip Board"]
            self.mode = "STAMP"
            self.rect_on = False
            self.rect_done = True

    def save_screen(self):
        #Triggered by pressing ctrl+s
        #A rudamentary save function.  Saves all living cells in a pattern file.
        #This will overwrite the last file saved in this manner, so if you would like to keep a file,
        #change its filename to something else before reusing.
        #(by default file will be saved in the 'classic' folder and will be named "savescreen.lif")
        lif_converter.convert2lif(self.living,"classic")
        self.stamp_dirlist()
        
    def get_next(self):
        #primary logic for calculating generations
        self.neighbors = {}
        for j,k in self.living:
            for x,y in ADJACENTS:
                check = ((j+x),(k+y))
                self.neighbors[check] = self.neighbors.setdefault(check,0)+1
        
        self.next = set()
        for i in self.neighbors:
            if (self.birthmin <= self.neighbors[i] <= self.birthmax) and i not in self.living:
                self.next |= set([i])
            elif (self.survivemin <= self.neighbors[i] <= self.survivemax) and i in self.living:
                self.next |= set([i])
                
        self.living = self.next
        self.calced = True
        self.gen += 1
        
    def update(self):
        if self.state == "START":
            self.screen.fill((0,0,0))
            self.draw()
            if self.gridon and self.grid:
                self.screen.blit(self.grid,(150,0))
            if self.rect_on:
                self.select_rect()
            self.screen.blit(bg,(0,0))
            self.stats()
            self.event_loop()
            pygame.display.update()
        elif self.state == "RUN":
            if not self.calced:
                self.get_next()
            if pygame.time.get_ticks() - self.lastcalced > 1000/self.fps:
                self.lastcalced = pygame.time.get_ticks()
                self.calced = False
            if pygame.time.get_ticks() - self.lastupdated > 1000/70:
                self.screen.fill((0,0,0))
                self.draw()
                if self.gridon and self.grid:
                    self.screen.blit(self.grid,(150,0))
                if self.rect_on:
                    self.select_rect()
                self.screen.blit(bg,(0,0))
                self.stats()
                self.lastupdated = pygame.time.get_ticks()
            self.event_loop()
            pygame.display.update()
        elif self.state == "QUIT":
            pygame.quit();sys.exit()

def main():
    Life.update()

#####
if __name__ == "__main__":
    Life = LetThereBe()
    while 1:
        main()
