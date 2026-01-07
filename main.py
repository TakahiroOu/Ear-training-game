import pygame
from random import choice

class AudioCreator:
    def __init__(self):
        pygame.mixer.init(frequency=44100,size=-16,channels=1)
        self.sample_rate=44100
        self.note_frequencies=[("C",261.63),("C#",277.18),("D",293.66),("D#",311.13),("E",329.63),("F",349.23),("F#",369.99),("G",392.00),("G#",415.30),("A",440.00),("A#",466.16),("B",493.88)]

    def make_octave(self,note:tuple):
        octave=choice([1,2,3])
        if octave==1:
            return note
        elif octave==2:
            new_freq=note[1]/2
            return (note[0],new_freq)
        else:
            new_freq=note[1]*2
            return (note[0],new_freq)

    def make_1note(self):
        chosen_notes=[]
        chosen_note=choice(self.note_frequencies)
        chosen_notes.append(self.make_octave(chosen_note))
        self.generate_sound_answer(chosen_notes)        

    def make_2notes(self):
        chosen_notes=[]
        while True:
            chosen_note1=choice(self.note_frequencies)
            chosen_note2=choice(self.note_frequencies)
            if chosen_note1==chosen_note2:
                continue
            else:
                chosen_notes.append(self.make_octave(chosen_note1))
                chosen_notes.append(self.make_octave(chosen_note2))
            self.generate_sound_answer(chosen_notes)         
            break       

    def make_3notes(self):
        chosen_notes=[]
        chosen_note1=choice(self.note_frequencies)
        note1_index=self.note_frequencies.index(chosen_note1)
        if choice([1,2])==1:
            chosen_note2=self.note_frequencies[(note1_index+3)%12]
            chosen_note3=self.note_frequencies[(note1_index+7)%12]
        else:
            chosen_note2=self.note_frequencies[(note1_index+4)%12]
            chosen_note3=self.note_frequencies[(note1_index+7)%12]
        chosen_notes.append(self.make_octave(chosen_note1))
        chosen_notes.append(self.make_octave(chosen_note2))
        chosen_notes.append(self.make_octave(chosen_note3))
        self.generate_sound_answer(chosen_notes)         

    def make_4notes(self):
        chosen_notes=[]
        chosen_note1=choice(self.note_frequencies)
        note1_index=self.note_frequencies.index(chosen_note1)
        if choice([1,2])==1:
            chosen_note2=self.note_frequencies[(note1_index+4)%12]
        else:
            chosen_note2=self.note_frequencies[(note1_index+3)%12]
        chosen_note3=self.note_frequencies[(note1_index+7)%12]
        chosen_note4=self.note_frequencies[(note1_index+10)%12]
        chosen_notes.append(self.make_octave(chosen_note1))
        chosen_notes.append(self.make_octave(chosen_note2))
        chosen_notes.append(self.make_octave(chosen_note3))
        chosen_notes.append(self.make_octave(chosen_note4))
        self.generate_sound_answer(chosen_notes)         

    def generate_sound_answer(self,chosen_notes:list):
        for item in chosen_notes:
            Sound.play(self.make_piano_sound(item[1]))
        answers=[]
        for item in chosen_notes:
            answers.append(item[1])
        return answers
        
    def make_piano_sound(self,frequency:float,):
        frequency will be close to piano sound


        








    def number_of_notes(self):
        if 1:
            self.make_1note()
        elif choice==2:
            self.make_2notes()
        elif choice==3:
            self.make_3notes()
            ??   (stage1=1note, stage2=2notes, stage3=3, stage4==4 notes)


