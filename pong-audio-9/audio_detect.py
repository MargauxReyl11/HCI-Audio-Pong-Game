import pyaudio
from pocketsphinx import Endpointer, Decoder, set_loglevel

# Set log level for debugging
set_loglevel("INFO")

# Initialize PocketSphinx components
ep = Endpointer()
decoder = Decoder(samprate=ep.sample_rate)
decoder.add_kws("keywords", "keywords.list")
decoder.activate_search("keywords")

# Start utterance recognition
decoder.start_utt()

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=int(ep.sample_rate), input=True, frames_per_buffer=1024)
stream.start_stream()

print("Listening for keywords...")
try:
    while True:
        # Read audio frames from the microphone
        frame = stream.read(1024, exception_on_overflow=False)
        
        # Process the frame
        decoder.process_raw(frame, False, False)
        
        # Check for detected keywords
        if decoder.hyp() is not None:
            keyword = decoder.hyp().hypstr
            print(f"Detected keyword: {keyword}")
            
            # Restart utterance for the next detection
            decoder.end_utt()
            decoder.start_utt()
except KeyboardInterrupt:
    print("Stopping...")
finally:
    # Cleanup resources
    decoder.end_utt()
    stream.stop_stream()
    stream.close()
    p.terminate()
