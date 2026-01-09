import pygame
from random import choice

class AudioCreator:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(50)
        fps=60
        timer=pygame.time.Clock()

        self.C3=pygame.mixer.Sound("sounds/piano/C3.wav")
        self.C3s=pygame.mixer.Sound("sounds/piano/C3s.wav")  
        self.D3=pygame.mixer.Sound("sounds/piano/D3.wav")
        self.D3s=pygame.mixer.Sound("sounds/piano/D3s.wav")  
        self.E3=pygame.mixer.Sound("sounds/piano/E3.wav")
        self.F3=pygame.mixer.Sound("sounds/piano/F3.wav")
        self.F3s=pygame.mixer.Sound("sounds/piano/F3s.wav")  
        self.G3=pygame.mixer.Sound("sounds/piano/G3.wav")
        self.G3s=pygame.mixer.Sound("sounds/piano/G3s.wav")  
        self.A3=pygame.mixer.Sound("sounds/piano/A3.wav")
        self.A3s=pygame.mixer.Sound("sounds/piano/A3s.wav")  
        self.B3=pygame.mixer.Sound("sounds/piano/B3.wav")

        self.C4=pygame.mixer.Sound("sounds/piano/C4.wav")
        self.C4s=pygame.mixer.Sound("sounds/piano/C4s.wav")
        self.D4=pygame.mixer.Sound("sounds/piano/D4.wav")
        self.D4s=pygame.mixer.Sound("sounds/piano/D4s.wav")
        self.E4=pygame.mixer.Sound("sounds/piano/E4.wav")
        self.F4=pygame.mixer.Sound("sounds/piano/F4.wav")
        self.F4s=pygame.mixer.Sound("sounds/piano/F4s.wav")
        self.G4=pygame.mixer.Sound("sounds/piano/G4.wav")
        self.G4s=pygame.mixer.Sound("sounds/piano/G4s.wav")
        self.A4=pygame.mixer.Sound("sounds/piano/A4.wav")
        self.A4s=pygame.mixer.Sound("sounds/piano/A4s.wav")
        self.B4=pygame.mixer.Sound("sounds/piano/B4.wav")

        self.C5=pygame.mixer.Sound("sounds/piano/C5.wav")
        self.C5s=pygame.mixer.Sound("sounds/piano/C5s.wav")
        self.D5=pygame.mixer.Sound("sounds/piano/D5.wav")
        self.D5s=pygame.mixer.Sound("sounds/piano/D5s.wav")
        self.E5=pygame.mixer.Sound("sounds/piano/E5.wav")
        self.F5=pygame.mixer.Sound("sounds/piano/F5.wav")
        self.F5s=pygame.mixer.Sound("sounds/piano/F5s.wav")
        self.G5=pygame.mixer.Sound("sounds/piano/G5.wav")
        self.G5s=pygame.mixer.Sound("sounds/piano/G5s.wav")
        self.A5=pygame.mixer.Sound("sounds/piano/A5.wav")
        self.A5s=pygame.mixer.Sound("sounds/piano/A5s.wav")
        self.B5=pygame.mixer.Sound("sounds/piano/B5.wav")

        self.note_sounds=[self.C3,self.C3s,self.D3,self.D3s,self.E3,self.F3,self.F3s,self.G3,self.G3s,self.A3,self.A3s,self.B3,
                          self.C4,self.C4s,self.D4,self.D4s,self.E4,self.F4,self.F4s,self.G4,self.G4s,self.A4,self.A4s,self.B4,
                          self.C5,self.C5s,self.D5,self.D5s,self.E5,self.F5,self.F5s,self.G5,self.G5s,self.A5,self.A5s,self.B5]
        
        self.white_sounds=[self.C3,self.D3,self.E3,self.F3,self.G3,self.A3,self.B3,
                           self.C4,self.D4,self.E4,self.F4,self.G4,self.A4,self.B4,
                           self.C5,self.D5,self.E5,self.F5,self.G5,self.A5,self.B5]
        
        self.black_sounds=[self.C3s,self.D3s,self.F3s,self.G3s,self.A3s,
                           self.C4s,self.D4s,self.F4s,self.G4s,self.A4s,
                           self.C5s,self.D5s,self.F5s,self.G5s,self.A5s]
        
        self.note_names=["C3","C#3","D3","D#3","E3","F3","F#3","G3","G#3","A3","A#3","B3",
                         "C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","A#4","B4",
                         "C5","C#5","D5","D#5","E5","F5","F#5","G5","G#5","A5","A#5","B5"]
        
        self.correct_answer=[]

    def make_octave(self,note):
        note_index=self.note_sounds.index(note)
        octave=choice([1,2,3])
        if octave==1:
            return note
        elif octave==2:
            return (self.note_sounds[(note_index+12)%36],(note_index+12)%36)
        else:
            return (self.note_sounds[(note_index-12)%36],(note_index+12)%36)

    def make_1note(self):
        chosen_note=choice(n for n in self.note_sounds if "4" in n)
        final_note,index=self.make_octave(chosen_note)
        final_note.play()
        self.correct_answer=[self.note_names[index]]

    def make_2notes(self):
        while True:
            chosen_note1=choice(n for n in self.note_sounds if "4" in n)
            chosen_note2=choice(n for n in self.note_sounds if "4" in n)
            final_note1,note1_index=self.make_octave(chosen_note1)
            final_note2,note2_index=self.make_octave(chosen_note2)
            if abs(note1_index-note2_index)<=1:
                continue
            else:
                final_note1.play()
                final_note2.play()
            break       
        self.correct_answer=[self.note_names[note1_index],self.note_names[note2_index]]

    def make_3notes(self):
        chosen_note1=choice(n for n in self.note_sounds if "4" in n)
        note1_index=self.note_sounds.index(chosen_note1)
        if choice([1,2])==1:
            chosen_note2=self.note_sounds[note1_index+3]
            chosen_note3=self.note_sounds[note1_index+7]
        else:
            chosen_note2=self.note_sounds[note1_index+4]
            chosen_note3=self.note_sounds[note1_index+7]

        final_note1,note1_index=self.make_octave(chosen_note1)
        final_note2,note2_index=self.make_octave(chosen_note2)
        final_note3,note3_index=self.make_octave(chosen_note3)

        final_note1.play()
        final_note2.play()
        final_note3.play()
        self.correct_answer=[self.note_names[note1_index],self.note_names[note2_index],self.note_names[note3_index]]

    def make_4notes(self):
        chosen_note1=choice(n for n in self.note_sounds if "4" in n)
        note1_index=self.note_sounds.index(chosen_note1)
        if choice([1,2])==1:
            chosen_note2=self.note_sounds[note1_index+4]
        else:
            chosen_note2=self.note_sounds[note1_index+3]
        chosen_note3=self.note_sounds[note1_index+7]
        chosen_note4=self.note_sounds[note1_index+10]

        final_note1,note1_index=self.make_octave(chosen_note1)
        final_note2,note2_index=self.make_octave(chosen_note2)
        final_note3,note3_index=self.make_octave(chosen_note3)
        final_note4,note4_index=self.make_octave(chosen_note4)

        final_note1.play()
        final_note2.play()
        final_note3.play()
        final_note4.play()
        self.correct_answer=[self.note_names[note1_index],self.note_names[note2_index],self.note_names[note3_index],self.note_names[note4_index]]


class MakePiano:
    def __init__(self):
        pygame.init()
        self.display=pygame.display.set_mode((800, 600))
        self.audio=AudioCreator()
        self.white_note_names=["C3","D3","E3","F3","G3","A3","B3",
                               "C4","D4","E4","F4","G4","A4","B4",
                               "C5","D5","E5","F5","G5","A5","B5"]
        self.black_note_names=["C#3","D#3","F#3","G3","G#3","A3","A#3","B3",
                               "C#4","D#4","F#4","G4","G#4","A4","A#4","B4",
                               "C#5","D#5","F#5","G5","G#5","A5","A#5","B5"]


    def draw_piano(self):
        self.white_keys=[]
        for i in range(27):
            rect=pygame.draw.rect(self.display,'white',[i*50,550,50,250],0,2)
            self.white_keys.append(rect)
            pygame.draw.rect(self.display,'black',[i*50,550,50,250],2,2)

        skip_count=0
        last_skip=3
        skip_track=0
        self.black_keys=[]
        for i in range(15):
            rect=pygame.draw.rect(self.display,'black',[27+i*50+skip_count*50,550,50,150],0,2)
            self.black_keys.append(rect)
            skip_track+=1
            if last_skip==2 and skip_track==3:
                last_skip=3
                skip_track=0
                skip_count+=1
            elif last_skip==3 and skip_track==2:
                last_skip=2
                skip_track=0
                skip_count+=1

    def choose_keys(self,mouse_pos):
        for i,rect in enumerate(self.black_rects):
            if rect.collidepoint(mouse_pos):
                return "black",i,rect
        for i,rect in enumerate(self.white_rects):
            if rect.collidepoint(mouse_pos):
                return "white",i,rect
        return None,None
    
    def answer(self):
        audio=AudioCreator()
        if event.type==pygame.MOUSEBUTTONDOWN:
            key_type,key_index,rect=self.choose_keys(event.pos)
        
            if key_type=="black":
                audio.self.black_sounds[key_index].play()
                pygame.draw.rect(self.display,'blue',self.black_keys[key_index],0,2)


            elif key_type=="white":
                audio.self.white_sounds[key_index].play()
                pygame.draw.rect(self.display,'blue',self.white_keys[key_index],0,2)




            
        

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ear Training")
        self.audio=AudioCreator() 



