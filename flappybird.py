from pygame.constants import KEYDOWN, K_SPACE
import pygame
import sys
import random
import os 
import time
import neat 
import pickle
import tkinter as tk
from tkinter import EventType, ttk,messagebox

#Initialize pygame
pygame.init()
root=tk.Tk()	#giving allias
root.title('Bird Selection Window')
root.geometry('601x338')
pygame.display.set_caption('Flappy Birds')
#Declare the width and Height of the screen
SCREEN=WIDTH,HEIGHT=288,512
CLOCK=pygame.time.Clock()

normal_speed=False
generation=0
alive=30

#intitialize class for bird
class BIRD:

	BIRD_VELOCITY=4
	def __init__(self,bird_color):

		# sounds
		self.bird_sounds=[pygame.mixer.Sound(f'Flappy/audio/die.wav'),pygame.mixer.Sound(f'Flappy/audio/point.wav'),pygame.mixer.Sound(f'Flappy/audio/wing.wav')]
		
		self.bird_images=[pygame.image.load(f'Flappy/sprites/{bird_color}bird-midflap.png').convert_alpha(),pygame.image.load(f'Flappy/sprites/{bird_color}bird-upflap.png').convert_alpha(),pygame.image.load(f'Flappy/sprites/{bird_color}bird-downflap.png').convert_alpha()]
		self.bird_position=[20,140]
		self.flapping=False
		self.tilt=0
		self.frame_count=0
		self.pressed=False
		self.bird_image_flap=0

	def move(self):

		#if player not pressed space
		if(not self.pressed):

			self.bird_position[1]+=BIRD.BIRD_VELOCITY
			self.tilt=-45
			self.flapping=False

		elif(self.pressed):

			if(self.frame_count<15):
				self.frame_count+=1
			
			if(self.frame_count<10):
				self.bird_position[1]-=BIRD.BIRD_VELOCITY
				self.tilt=25
			
			if(self.frame_count==15):
				self.frame_count=0
				self.pressed=False
			
			if(10<=self.frame_count<=15):
				self.tilt-=6
			
			self.flapping=True

		#Changing the animation of bird {  down_flap  ,  up_flap  ,  mid_flap  }

		if(self.bird_image_flap==2 or not self.flapping):
			self.bird_image_flap=0

		else:
			self.bird_image_flap+=1

	def draw(self):

		DISPLAY.blit(pygame.transform.rotate(self.bird_images[self.bird_image_flap],self.tilt),self.bird_position)
		
	@property
	def get_mask(self):

		return pygame.mask.from_surface(pygame.transform.rotate(self.bird_images[self.bird_image_flap],self.tilt))
		

class PIPE:

	PIPE_VELOCITY=2
	def __init__(self,pipe_color,pipe_position):
		
		self.bottom_pipe_image=pygame.image.load(f'Flappy/sprites/pipe-{pipe_color}.png').convert_alpha()
		self.top_pipe_image=pygame.transform.flip(self.bottom_pipe_image,False,True)
		self.pipe_position=pipe_position
	
	@staticmethod
	def new_pipe_position(pos,initial=False):

		temp=random.randint(140,350)
		if(initial):

			pipe_position=[[200,temp]]
			pipe_position.append([200,temp-440])
		
		else:

			PIPE_GAP=160 #horizontal gap between pipes
			pipe_position=[[pos+PIPE_GAP,temp]]
			pipe_position.append([pos+PIPE_GAP,temp-440])

		return pipe_position

	def draw(self):

		DISPLAY.blit(self.top_pipe_image,self.pipe_position[1])
		DISPLAY.blit(self.bottom_pipe_image,self.pipe_position[0])

	def move(self):

		#moving pipes with constant speed
		self.pipe_position[0][0]-=self.PIPE_VELOCITY
		self.pipe_position[1][0]-=self.PIPE_VELOCITY
	
	@staticmethod
	def collision(pipes,birds,background):
		if(birds.bird_position[1]+birds.BIRD_VELOCITY>background.base_position[1]-pygame.transform.rotate(birds.bird_images[birds.bird_image_flap],birds.tilt).get_height()+6 or birds.bird_position[1]+birds.BIRD_VELOCITY<0):
			return True
		if(len(pipes)>=2):
			for i in range(len(pipes)): 
				if(birds.get_mask.overlap(pipes[i].get_mask_bottom,(pipes[i].pipe_position[0][0]-birds.bird_position[0],pipes[i].pipe_position[0][1]-birds.bird_position[1]))!=None or birds.get_mask.overlap(pipes[i].get_mask_top,(pipes[i].pipe_position[1][0]-birds.bird_position[0],pipes[i].pipe_position[1][1]-birds.bird_position[1]))!=None):
					return True
			return False


	@property
	def get_mask_bottom(self):
		# taking area for collision
		return pygame.mask.from_surface(self.bottom_pipe_image)

	@property
	def get_mask_top(self):
		# taking area for collision
		return pygame.mask.from_surface(self.top_pipe_image)

class BACKGROUND:

	BASE_VELOCITY=2
	def __init__(self,bg_time):

		self.bg_image=pygame.image.load(f'Flappy/sprites/background-{bg_time}.png').convert_alpha()
		self.base_image=pygame.image.load('Flappy/sprites/base.png').convert_alpha()
		self.base_position=[0,400]

	@property
	def bg_get_mask(self):
		return pygame.mask.from_surface(self.bg_image)
	

	def base_move(self):

		if(self.base_position[0]<=-48):
			self.base_position[0]=0

		else:
			self.base_position[0]-=self.BASE_VELOCITY

	def draw(self):
		
		DISPLAY.blit(self.base_image,(self.base_position))

	@property
	def base_get_mask(self):
		return pygame.mask.from_surface(self.base_image)

class SCORE:

	def __init__(self):
		
		self.score_image=[pygame.image.load(f"Flappy/sprites/{i}.png").convert_alpha() for i in range(10)]
		self.scores=0
	
	@staticmethod
	def score_counter(birds,pipes):

		if(len(pipes)>1):	
			if(birds.bird_position[0]==pipes[0].pipe_position[0][0]+pipes[0].bottom_pipe_image.get_width()-20):
				return True
		return False
	
	def display_score(self):

		score_position=288-self.score_image[0].get_width()
		for temp in str(self.scores)[::-1]:
			DISPLAY.blit(self.score_image[int(temp)],(score_position,0))
			score_position-=self.score_image[0].get_width()
	
	def generation_counter(self,generation):

		generation_position=0

		for temp in str(generation):
			DISPLAY.blit(self.score_image[int(temp)],(generation_position,0))
			generation_position+=self.score_image[0].get_width()

	def alive_counter(self,alive):

		alive_position=0

		for temp in str(alive):
			DISPLAY.blit(self.score_image[int(temp)],(alive_position,self.score_image[0].get_height()+5))
			alive_position+=self.score_image[0].get_width()

def draw(birds,pipes,background,score,generation=0,alive=30):

	DISPLAY.blit(background.bg_image,(0,0))
	for bird in birds:#only for ai because we have to handle mutiple birds
		bird.draw()

	for pipe in pipes:
		pipe.draw()

	background.draw()

	score.display_score()

	if generation and alive:
		score.generation_counter(generation)
		score.alive_counter(alive)


def move(birds,pipes,background):
	
	for bird in birds:
		bird.move()
	
	for pipe in pipes:
		pipe.move()
	
	background.base_move()

class GUI:

	def __init__(self):

		self.flappy_image=tk.PhotoImage(file='Flappy/sprites/Untitled.png')
		self.poster=tk.Label(root,image=self.flappy_image)
		self.poster.place(relwidth=1,relheight=1)
		self.label=[tk.Label(root,text='Which Color Of Bird You Want To Choose',bg='skyblue1'),tk.Label(root,text='AI mode',bg='skyblue1'),tk.Label(root,text='Which Pipe Color You Want To Choose',bg='skyblue1')]
		self.choices=[ttk.Combobox(root,width=30,textvariable=tk.StringVar()),ttk.Combobox(root,width=30,textvariable=tk.StringVar()),ttk.Combobox(root,width=30,textvariable=tk.StringVar())]
		self.choices[0]['values']=('blue','red','yellow')
		self.choices[1]['values']=('True','False')
		self.choices[2]['values']=('red','green')

		for i in range(3):

			self.label[i].place(x=10,y=30+i*60)
			self.choices[i].current(0)
			self.choices[i].place(x=250,y=30+i*60)
		
		self.start_button=tk.Button(text='Start',command=self.start,height=3,width=8,bg='pale green')
		self.start_button.place(x=520,y=280)

	def start(self):
		
		global DISPLAY,pipe_color,bird_color,bg_time
		bird_color,pipe_color,bg_time=self.choices[0].get(),self.choices[2].get(),'day'
		DISPLAY=pygame.display.set_mode(SCREEN)

		if self.choices[1].get()=='True':
			
			# calling config file options 
			config=neat.config.Config(neat.DefaultGenome,neat.DefaultReproduction,neat.DefaultSpeciesSet,neat.DefaultStagnation,'Flappy/config.txt')
			
			p=neat.Population(config)#setting the population on behalf of config file we made
			
			# adding report of every spiecies
			p.add_reporter(neat.StdOutReporter(True))

			# adding stats of each bird 
			stats=neat.StatisticsReporter()
			p.add_reporter(stats)
			p.add_reporter(neat.Checkpointer(10))

			# AI is the fitness function
			# 100 indicates how  many generation we are going to run
			# 100 ->  how many times its calling AI function
			best_species=p.run(AI,100)

			# dumping best species in winner . pickle
			with open('Winner.pickle','wb+') as f:
				pickle.dump(best_species,f)

		else:
			gameloop_for_normal_player()
		root.quit()

def gameloop_for_normal_player():

	birds=[BIRD(bird_color)]#making list only for ai because draw and move function are common on both
	pipes=[PIPE(pipe_color,PIPE.new_pipe_position(0,True))]
	background=BACKGROUND(bg_time)
	score=SCORE()
	while True:
		for event in pygame.event.get():
			if event.type==pygame.QUIT:
				sys.exit()

			elif event.type==pygame.KEYDOWN:
				if event.key==pygame.K_SPACE:
					birds[0].pressed=True
					birds[0].bird_position[1]-=8
					birds[0].frame_count=0
					
					# adding wing sound 
					pygame.mixer.Sound.play(birds[0].bird_sounds[2])
		draw(birds,pipes,background,score)
		move(birds,pipes,background)
		
		if len(pipes)<3:
			pipes.append(PIPE(pipe_color,PIPE.new_pipe_position(pipes[len(pipes)-1].pipe_position[0][0])))
		
		if pipes[0].pipe_position[0][0]<-52:
			pipes.pop(0)

		pygame.display.update()
		
		if PIPE.collision(pipes, birds[0],background):

			# adding die sound
			pygame.mixer.Sound.play(birds[0].bird_sounds[0])
			break

		if score.score_counter(birds[0],pipes):
			pygame.mixer.Sound.play(birds[0].bird_sounds[1])
			score.scores+=1

		CLOCK.tick(30)

	# making font to display after losing game
	DISPLAY.blit(background.bg_image,(0,0))
	font1,font2=pygame.font.Font("Font/AlloyInk-nRLyO.ttf",32),pygame.font.Font("Font/AlloyInk-nRLyO.ttf",20)
	lose,retry=font1.render("You Lose",1,(0,0,0)),font2.render("PRESS SPACE TO RESTART",1,(0,0,0))
	DISPLAY.blit(lose,(WIDTH/2-lose.get_width()/2,HEIGHT/2-lose.get_height()/2))
	DISPLAY.blit(retry,(WIDTH/2-retry.get_width()/2,HEIGHT/2+lose.get_height()*2-retry.get_height()/2))	
	pygame.display.update()

	pygame.event.clear()

	while True:

		event = pygame.event.wait()
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE:
				gameloop_for_normal_player()

	# 	pygame.time.delay(3000)

	# for event in pygame.event.get():

	# 	if event.type==pygame.KEYDOWN:
	# 		if event.key==pygame.K_SPACE:
	# 			gameloop_for_normal_player()


# by default we need to pass these parameters
def AI(genomes,config):

	global generation
	generation+=1

	global alive
	alive=30
	

	global normal_speed
	bird_genome,net,birds,night_mode=[],[],[],0
	# genome gives 2 value genome id and genome of birds
	for genome_id,genome in genomes:
		
		# giving fitness 0 to new birds
		genome.fitness=0
		# and append it after wards
		bird_genome.append(genome)

		# making neural network, parameter here are genome and config
		net.append(neat.nn.FeedForwardNetwork.create(genome,config))

		birds.append(BIRD(bird_color))
	
	# changing bg_color
	if night_mode>1000:
		
		bg_time='night'
		night_mode=0
	
	else:
		bg_time='day'

	background=BACKGROUND(bg_time)
	pipes=[PIPE(pipe_color,PIPE.new_pipe_position(0,True))]
	score=SCORE()
	

	while True:

		if(len(birds)==0):break

		for event in pygame.event.get():
			
			if event.type==pygame.QUIT:
				sys.exit()

			if event.type==pygame.KEYDOWN:
				if event.key==pygame.K_SPACE:
					
					if normal_speed:normal_speed=False
					else:normal_speed=True
		
		draw(birds,pipes,background,score,generation,alive)
		move(birds,pipes,background)

		# birds see two pipes 0 and 1 so 
		if birds[0].bird_position[0]>pipes[0].pipe_position[0][0]+pipes[0].bottom_pipe_image.get_width()-20:
			current_pipe=1
		else:current_pipe=0

		for i in range(len(birds)):
			
			# making birds jump
			jump=net[i].activate((birds[i].bird_position[1],abs(birds[i].bird_position[0]-pipes[current_pipe].pipe_position[0][1])))
			
			if(jump[0]>0.5):

				birds[i].pressed=True
		night_mode+=0.2

		if len(pipes)<3:
			pipes.append(PIPE(pipe_color,PIPE.new_pipe_position(pipes[len(pipes)-1].pipe_position[0][0])))
		
		if pipes[0].pipe_position[0][0]<-52:
			pipes.pop(0)

		pygame.display.update()
		
		to_delete=[]
		score_register=False
		for i in range(len(birds)):
		
			if PIPE.collision(pipes, birds[i],background):
				bird_genome[i].fitness-=5
				to_delete.append(i)
				alive-=1
			
			else:
				bird_genome[i].fitness+=0.1
				if(bird_genome[i].fitness>5000):
					return				
				if(score.score_counter(birds[i],pipes)):
					bird_genome[i].fitness+=5
					score_register=True
		
		for i in to_delete[::-1]:
			birds.pop(i)
			bird_genome.pop(i)
			net.pop(i)
		
		if score_register:score.scores+=1
		if normal_speed:CLOCK.tick(30)
	


GUI()
root.mainloop()
			


