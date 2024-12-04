"""
    # PONG PLAYER EXAMPLE

    HOW TO CONNECT TO HOST AS PLAYER 1
    > python pong-audio-player.py p1 --host_ip HOST_IP --host_port 5005 --player_ip YOUR_IP --player_port 5007

    HOW TO CONNECT TO HOST AS PLAYER 2
    > python pong-audio-player.py p2 --host_ip HOST_IP --host_port 5006 --player_ip YOUR_IP --player_port 5008

    about IP and ports: 127.0.0.1 means your own computer, change it to play across computer under the same network. port numbers are picked to avoid conflits.

    DEBUGGING:
    
    You can use keyboards to send command, such as "g 1" to start the game, see the end of this file

"""
#native imports
import time
from playsound import playsound
import argparse

from pythonosc import osc_server
from pythonosc import dispatcher
from pythonosc import udp_client

# threading so that listenting to speech would not block the whole program
import threading
# speech recognition (default using google, requiring internet)
import speech_recognition as sr
# pitch & volume detection
import aubio
import numpy as num
import pyaudio
import wave

import os
from pocketsphinx import Endpointer, Decoder, set_loglevel
from ball_pitch import BallTone
import pyttsx3
import subprocess

mode = ''
debug = False
quit = False

host_ip = "127.0.0.1"
host_port_1 = 5005 # you are player 1 if you talk to this port
host_port_2 = 5006
player_1_ip = "127.0.0.1"
player_2_ip = "127.0.0.1"
player_1_port = 5007
player_2_port = 5008

player_ip = "127.0.0.1"
player_port = 0
host_port = 0

if __name__ == '__main__' :

    parser = argparse.ArgumentParser(description='Program description')
    parser.add_argument('mode', help='host, player (ip & port required)')
    parser.add_argument('--host_ip', type=str, required=False)
    parser.add_argument('--host_port', type=int, required=False)
    parser.add_argument('--player_ip', type=str, required=False)
    parser.add_argument('--player_port', type=int, required=False)
    parser.add_argument('--debug', action='store_true', help='show debug info')
    args = parser.parse_args()
    print("> run as " + args.mode)
    mode = args.mode
    if (args.host_ip):
        host_ip = args.host_ip
    if (args.host_port):
        host_port = args.host_port
    if (args.player_ip):
        player_ip = args.player_ip
    if (args.player_port):
        player_port = args.player_port
    if (args.debug):
        debug = True

# GAME INFO

# functions receiving messages from host
# TODO: add audio output so you know what's going on in the game


ball_tone = BallTone(base_freq=440)  
prev_x_pos = None
engine = pyttsx3.init()
welcome_played = False  # Global flag to track if welcome message was played

def on_receive_game(address, *args):
    print("> game state: " + str(args[0]))
    # 0: menu, 1: game starts
    welcome()
    if int(args[0]) == 1:  
        ball_tone.start()
    elif int(args[0]) == 0:
        ball_tone.stop()

def on_receive_ball(address, *args):
    # print("> ball position: (" + str(args[0]) + ", " + str(args[1]) + ")")
    global prev_x_pos

    x_pos, y_pos = args  # Current ball position
    player_side = "left" if mode == "p1" else "right"

    if prev_x_pos is not None:
        ball_tone.update_pitch(x_pos, y_pos, prev_x_pos, max_x=800, max_y=450, player_side=player_side)

    prev_x_pos = x_pos

def on_receive_paddle(address, *args):
    # print("> paddle position: (" + str(args[0]) + ", " + str(args[1]) + ")")
    pass

def on_receive_hitpaddle(address, *args):
    success()
    print("> ball hit at paddle " + str(args[0]) )

def on_receive_ballout(address, *args):
    miss()
    print("> ball went out on left/right side: " + str(args[0]) )

def on_receive_ballbounce(address, *args):
    bounce()
    print("> ball bounced on up/down side: " + str(args[0]) )

def on_receive_scores(address, *args):
    print("> scores now: " + str(args[0]) + " vs. " + str(args[1]))
    player1_score = args[0]
    player2_score = args[1]  
    score_message = f"say The score is now {player1_score} to {player2_score}."
    subprocess.run(score_message, shell=True)
    


def on_receive_level(address, *args):
    print("> level now: " + str(args[0]))

def on_receive_powerup(address, *args):
    if args[0] == 1:
        player1_frozen()
    elif args[0] == 2:
        player2_frozen()
    elif args[0] == 3:
        p1_paddle()
    elif args[0] == 4:
        p2_paddle()


def on_receive_p1_bigpaddle(address, *args):
    print("> p1 has a big paddle now")
    # when p1 activates their big paddle

def on_receive_p2_bigpaddle(address, *args):
    print("> p2 has a big paddle now")
    # when p2 activates their big paddle

def on_receive_hi(address, *args):
    print("> opponent says hi!")

dispatcher_player = dispatcher.Dispatcher()
dispatcher_player.map("/hi", on_receive_hi)
dispatcher_player.map("/game", on_receive_game)
dispatcher_player.map("/ball", on_receive_ball)
dispatcher_player.map("/paddle", on_receive_paddle)
dispatcher_player.map("/ballout", on_receive_ballout)
dispatcher_player.map("/ballbounce", on_receive_ballbounce)
dispatcher_player.map("/hitpaddle", on_receive_hitpaddle)
dispatcher_player.map("/scores", on_receive_scores)
dispatcher_player.map("/level", on_receive_level)
dispatcher_player.map("/powerup", on_receive_powerup)
dispatcher_player.map("/p1bigpaddle", on_receive_p1_bigpaddle)
dispatcher_player.map("/p2bigpaddle", on_receive_p2_bigpaddle)
# -------------------------------------#

# CONTROL

# TODO add your audio control so you can play the game eyes free and hands free! add function like "client.send_message()" to control the host game
# We provided two examples to use audio input, but you don't have to use these. You are welcome to use any other library/program, as long as it respects the OSC protocol from our host (which you cannot change)


#pitch & volume detection & paddle move
# -------------------------------------#
p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paFloat32,
    channels=1, rate=44100, input=True,
    frames_per_buffer=1024, input_device_index=0)

pDetection = aubio.pitch("default", 2048,
    2048//2, 44100)

pDetection.set_unit("Hz")
pDetection.set_silence(-40)

def sense_microphone():
    global quit
    global debug
    while not quit:
        data = stream.read(1024,exception_on_overflow=False)
        samples = num.fromstring(data,
            dtype=aubio.float_type)

        pitch = pDetection(samples)[0]
        move_paddle(pitch)
        #volume = num.sum(samples**2)/len(samples)
        #volume = "{:.6f}".format(volume)

        if debug:
            print("pitch "+str(pitch))

def move_paddle(freq):
    """
    Move the paddle based on the given pitch, shifted up by half an octave (+6 semitones).
    New frequency range: 369 to 740 (adjusted for half-octave shift).
    Paddle height range: 0 to 450
    """
    position = 225 
    new_min_freq = 261  
    new_max_freq = 589 

    if new_min_freq <= freq <= new_max_freq:
        position = ((freq - new_min_freq) / (new_max_freq - new_min_freq)) * 450
        position = float(position) 
        client.send_message('/setpaddle', position)

# -------------------------------------#


#attempt to listen to words
# -------------------------------------#

"""
used as inspo: https://github.com/cmusphinx/pocketsphinx/blob/master/examples/live.py
and: https://cmusphinx.github.io/wiki/tutoriallm/#keyword-lists 
"""
def detect():
    """
    Continuously listens for keywords 'start game' and 'pause game'
    and sends corresponding OSC messages to control the game.
    """
    set_loglevel("INFO")

    ep = Endpointer()
    decoder = Decoder(samprate=ep.sample_rate)
    keywords_file = "keywords.list"

    decoder.add_kws("keywords", keywords_file)
    decoder.activate_search("keywords")
    decoder.start_utt()  

    # Setup PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=int(ep.sample_rate),
        input=True,
        frames_per_buffer=ep.frame_bytes // 2,
        input_device_index=0
    )
    stream.start_stream()

    while not quit:
            frame = stream.read(ep.frame_bytes // 2, exception_on_overflow=False)
            prev_in_speech = ep.in_speech
            speech = ep.process(frame)

            if speech is not None:
                #if not prev_in_speech and ep.in_speech:
                    #print(f"[DEBUG] Speech started at {ep.speech_start:.2f} seconds")

                decoder.process_raw(speech, False, False)

                if decoder.hyp() is not None:
                    keyword = decoder.hyp().hypstr.strip().lower()
                    print(f"Keyword detected: {keyword}")

                    if keyword == "start":
                        client.send_message('/setgame', 1)  # Send start game signal
                        start()
                    elif keyword == "pause":
                        client.send_message('/setgame', 0)
                        pause()
                    elif keyword == "easy level":
                        client.send_message('/setlevel', 1) 
                        easy()
                    elif keyword == "hard level":
                        client.send_message('/setlevel', 2) 
                        hard()
                    elif keyword == "insane level":
                        client.send_message('/setlevel', 3) 
                        insane()
                    elif keyword == "power up":
                        client.send_message('/setbigpaddle', 0) 
                        power()
                    elif keyword == "instructions":
                        client.send_message('/setgame', 0)
                        global welcome_played
                        welcome_played = False 
                        welcome()

                    decoder.end_utt()
                    decoder.start_utt()

                if prev_in_speech and not ep.in_speech:
                    print(f"[DEBUG] Speech ended at {ep.speech_end:.2f} seconds")
                    decoder.end_utt()
                    decoder.start_utt()
# -------------------------------------#


# pitch & volume detection
# -------------------------------------#
# start a thread to detect pitch and volume
microphone_thread = threading.Thread(target=sense_microphone, args=())
microphone_thread.daemon = True
microphone_thread.start()
# -------------------------------------#

#  keyword detection
# -------------------------------------#
keyword_thread = threading.Thread(target=detect, args=())
keyword_thread.daemon = True
keyword_thread.start()
# -------------------------------------#

# Play some fun sounds?
# -------------------------------------#
def hit():
    playsound('audio_files/hit.wav', False)

def success():
    playsound('audio_files/success.mp3', False)

def miss():
    playsound('audio_files/fail.mp3', False)

def bounce():
    playsound('audio_files/boing.mp3', False)

def player1_frozen():
    playsound('audio_files/player1_frozen.mp3', False)

def player2_frozen():
    playsound('audio_files/player2_frozen.mp3', False)

def start():
    playsound('audio_files/start_game.mp3', False)

def welcome():
    global welcome_played
    if not welcome_played:  # Check if welcome has not been played
        print("[DEBUG] Playing welcome message.")
        playsound('audio_files/welcome.mp3', False)
        welcome_played = True  # Mark as played
    else:
        print("[DEBUG] Welcome message already played.")


def pause():
    playsound('audio_files/pause.mp3', False)

def p1_paddle():
    playsound('audio_files/player1_big_paddle.mp3', False)

def p2_paddle():
    playsound('audio_files/player2_big_paddle.mp3', False)

def easy():
    playsound('audio_files/easy.mp3', False)

def hard():
    playsound('audio_files/hard.mp3', False)

def insane():
    playsound('audio_files/insane.mp3', False)

def power():
    playsound('audio_files/power_up.mp3', False)

# -------------------------------------#

#messages
# -------------------------------------#
#https://pypi.org/project/pyttsx3/ 

engine_lock = threading.Lock()

def output_message(message): 
    with engine_lock: 
        engine.say(message)
        engine.runAndWait()
# -------------------------------------#

# OSC connection
# -------------------------------------#
# used to send messages to host
if mode == 'p1':
    host_port = host_port_1
if mode == 'p2':
    host_port = host_port_2

if (mode == 'p1') or (mode == 'p2'):
    client = udp_client.SimpleUDPClient(host_ip, host_port)
    print("> connected to server at "+host_ip+":"+str(host_port))

# OSC thread
# -------------------------------------#
# Player OSC port
if mode == 'p1':
    player_port = player_1_port
if mode == 'p2':
    player_port = player_2_port

player_server = osc_server.ThreadingOSCUDPServer((player_ip, player_port), dispatcher_player)
player_server_thread = threading.Thread(target=player_server.serve_forever)
player_server_thread.daemon = True
player_server_thread.start()
# -------------------------------------#
client.send_message("/connect", player_ip)

# MAIN LOOP
# manual input for debugging
# -------------------------------------#
while True:
    m = input("> send: ")
    cmd = m.split(' ')
    if len(cmd) == 2:
        client.send_message("/"+cmd[0], int(cmd[1]))
    if len(cmd) == 1:
        client.send_message("/"+cmd[0], 0)
    
    # this is how client send messages to server
    # send paddle position 200 (it should be between 0 - 450):
    # client.send_message('/p', 200)
    # set level to 3:
    # client.send_message('/l', 3)
    # start the game:
    # client.send_message('/g', 1)
    # pause the game:
    # client.send_message('/g', 0)
    # big paddle if received power up:
    # client.send_message('/b', 0)