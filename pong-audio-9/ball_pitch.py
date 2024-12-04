import pysinewave
import math

BASE_DB = -10000

def ampl_to_db(ampl: float) -> float:
    """Convert amplitude (0.0 to 1.0) to decibels."""
    if ampl == 0:
        return BASE_DB
    return math.log2(ampl) * 10


class BallTone:
    """Handles continuous audio playback based on ball position."""

    def __init__(self, base_freq: float) -> None:
        self.base_freq = base_freq
        self.sine_wave = pysinewave.SineWave()  # Initialize a SineWave object
        self.sine_wave.set_frequency(base_freq)
        self.sine_wave.set_volume(ampl_to_db(0.5))  # Default volume
        self.is_playing = False  # Track whether the tone is playing

    def start(self):
        """Start playing the sine wave continuously."""
        if not self.is_playing:
            self.sine_wave.play()
            self.is_playing = True

    def stop(self):
        """Stop playing the sine wave."""
        if self.is_playing:
            self.sine_wave.stop()
            self.is_playing = False

    def update_pitch(self, x_pos: float, y_pos: float, prev_x_pos: float, max_x: float = 800, max_y: float = 450, player_side: str = "right"):
        """
        Used: https://github.com/daviddavini/pysinewave
        Update the sine wave frequency and volume based on ball position.
        Play sound only when the ball is moving toward the player's side.
        - x_pos: Current horizontal position of the ball.
        - y_pos: Current vertical position of the ball.
        - prev_x_pos: Previous horizontal position of the ball.
        - max_x: Maximum horizontal position.
        - max_y: Maximum vertical position.
        - player_side: "left" for Player 1, "right" for Player 2.
        """

        moving_toward_player = (
            (player_side == "right" and x_pos > prev_x_pos) or
            (player_side == "left" and x_pos < prev_x_pos)
        )

        if not moving_toward_player:
            # Stop the sine wave if moving away
            if self.is_playing:
                print("> Ball moving away, stopping tone.")
                self.stop()
            return

        # Ensure the sine wave is playing when the ball moves toward the player
        if not self.is_playing:
            print("> Ball moving toward player, starting tone.")
            self.start()

        # Normalize position for volume and pitch calculations
        norm_x = x_pos / max_x
        group_height = max_y / 12  # Divide height into 12 groups for pitch
        group_index = int(y_pos // group_height)  # Determine group index
        pitch = min(group_index, 12) + 6 # Cap pitch to 12

        # Map volume linearly based on horizontal position
        volume_factor = norm_x if player_side == "right" else (1 - norm_x)
        volume = volume_factor  

        # Update the sine wave pitch and volume
        print(f"> Updating tone: pitch={pitch}, volume={volume:.2f}, moving_toward_player={moving_toward_player}")
        self.sine_wave.set_pitch(pitch)
        self.sine_wave.set_volume(ampl_to_db(volume))
