# TODO: font tests (centre clock)
# TODO: screensave when no activity
# TODO: add audioscrobbler logo
# TODO: sdcard cache album images?
# TODO: psram cache?
# TODO: physical control support
# TODO: temperature display with time
# TODO: (maybe) fave on last.fm via button?
#       - would need to rethink touch / UI
# TODO: (maybe) more screens (user profile etc)

from picovector import ANTIALIAS_BEST, PicoVector, Polygon, Transform
from presto import Presto
import utime
import gc
import socket
import jpegdec, pngdec
import json
import secrets
import urequests as requests
import ntptime
import ssl
import sys, os

# Constants
LASTFM_API_KEY = secrets.LASTFM_API_KEY
LASTFM_USERNAME = secrets.LASTFM_USERNAME
TIMEZONE_OFFSET = secrets.TIMEZONE_OFFSET * 3600
TIMEOUT = 15

# Create a User-Agent identifier
__version__ = "0.1.0" # version of this program
mp_version  = ".".join(str(x) for x in sys.implementation.version)
machine     = os.uname().machine
USER_AGENT = f"lastfm_playing/{__version__} ({machine}; MicroPython/{mp_version})"

# Display modes
MODE_ALBUM_ART = 0
MODE_RECENT_TRACKS = 1
MODE_CLOCK = 2

# Initialize display
presto = Presto(ambient_light=True, full_res=True)
presto.set_backlight(0.2)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()
CX, CY = WIDTH // 2, HEIGHT // 2

# Colors
BLACK, WHITE, GRAY = (display.create_pen(r, g, b) 
                      for r, g, b in [(0, 0, 0), (255, 255, 255), (100, 100, 100)])

# Time constants
months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

# Initialize graphics
display.set_pen(BLACK)
display.clear()
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_BEST)
vector.set_font("Roboto-Medium.af", 14)
vector.set_font_letter_spacing(100)
vector.set_font_word_spacing(100)
vector.set_transform(Transform())

# Initialize decoders
jpd = jpegdec.JPEG(display)
pnd = pngdec.PNG(display)

# Initialize touch
touch = presto.touch

# Global state
current_mode = MODE_ALBUM_ART
recent_tracks_cache = []

def connect_to_wifi():
    print("Connecting to WiFi:", presto.connect())
    for i in range(3):
        try:
            ntptime.settime()
            break
        except:
            utime.sleep(2)

def fetch_data(url):
    try:
        proto, _, host, path = url.split('/', 3)
        addr = socket.getaddrinfo(host, 443)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s = ssl.wrap_socket(s, server_hostname=host)
        
        request = f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {USER_AGENT}\r\nConnection: close\r\n\r\n"
        s.write(request.encode('utf-8'))
        
        # Read the full response
        response = b''
        while True:
            chunk = s.read(1024)
            if not chunk:
                break
            response += chunk
        s.close()
        
        # Split headers and body
        headers, body = response.split(b'\r\n\r\n', 1)
        body_str = body.decode('utf-8')
        
        # DEBUG: print first part of response if it looks like an error
        if not body_str.startswith('{'):
            print("Response doesn't look like JSON:", body_str[:200])
        
        return body_str
    except Exception as e:
        print("Fetch error:", e)
        return "{}"

def fetch_album_art(art_url):
    if not art_url:
        return True
        
    gc.collect()
    # get art resized to 420x420 with a slight boost to contrast
    proxy_url = f"https://wsrv.nl/?url={art_url}&w=420&h=420&con=15"
    
    try:
        response = requests.get(proxy_url, timeout=TIMEOUT)
        if response.status_code != 200:
            return True
            
        display.set_pen(BLACK)
        display.clear()
        
        album_art = response.content
        if ".png" in art_url.lower():
            pnd.open_RAM(memoryview(album_art))
            pnd.decode(30, 0, pngdec.PNG)
        else:
            jpd.open_RAM(memoryview(album_art))
            jpd.decode(30, 0, jpegdec.JPEG_SCALE_FULL, dither=True)
        
        # round corners of album art
        rect = Polygon()
        display.set_pen(BLACK)
        rect.rectangle(20, -10, 440, 440, corners=(15, 15, 15, 15), stroke=10)
        vector.draw(rect)
        
        gc.collect()
        return False
    except Exception as e:
        print("Album art error:", e)
        return True

def update_clock():
    display.set_pen(BLACK)
    display.clear()
    
    timestamp = utime.mktime(utime.localtime()) + TIMEZONE_OFFSET
    tm = utime.localtime(timestamp)
    
    date_str = f"{days[tm[6]]} {tm[2]:02d} {months[tm[1]-1]} {tm[0]}"
    time_str = f"{tm[3]:02d}:{tm[4]:02d}"
    
    display.set_pen(WHITE)
    vector.set_font_size(200)
    vector.text(time_str, 20, 240)
    vector.set_font_size(60)
    vector.text(date_str, 40, 360)
    presto.update()

def update_album_display(artist, title):
    display.set_pen(BLACK)
    display.rectangle(0, 420, WIDTH, 60)
    display.set_pen(WHITE)
    vector.set_font_size(30)
    vector.text(artist, 30, CY + 205)
    vector.set_font_size(20)
    vector.text(title, 30, CY + 225)
    presto.update()

def update_recent_tracks_display():
    display.set_pen(BLACK)
    display.clear()
    
    display.set_pen(WHITE)
    vector.set_font_size(40)
    vector.text("Recent Tracks", 20, 60)
    
    if not recent_tracks_cache:
        vector.set_font_size(20)
        vector.text("No recent tracks", 20, 120)
    else:
        y_pos = 120
        for i, track in enumerate(recent_tracks_cache[:4]):  # Display 4 recent tracks
            # Track number
            vector.set_font_size(20)
            vector.text(f"{i+1}.", 20, y_pos)
            
            # Artist
            vector.set_font_size(24)
            artist_text = track['artist'][:30] + "..." if len(track['artist']) > 30 else track['artist']
            vector.text(artist_text, 50, y_pos)
            
            # Track name
            vector.set_font_size(18)
            track_text = track['name'][:35] + "..." if len(track['name']) > 35 else track['name']
            vector.text(track_text, 50, y_pos + 25)
            
            # Playing indicator
            if track.get('now_playing'):
                display.set_pen(WHITE)
                vector.set_font_size(12)
                vector.text("NOW PLAYING", 50, y_pos + 45)
            
            y_pos += 70  
    
    # Instructional text
    vector.set_font_size(16)
    vector.text("Tap to cycle modes", 20, HEIGHT - 20)
    
    # Draw waveform in bottom right corner
    display.set_pen(WHITE)
    text_width = 75  # Approximate width of "via last.fm" text
    x_start = WIDTH - 50  
    y_base = HEIGHT - 35
    for i in range(5):
        height = [3, 7, 4, 8, 2][i]
        display.rectangle(x_start + i * 6, y_base - height, 4, height)
    
    # last.fm attribution - bottom right corner, same line as instructions
    vector.set_font_size(16)
    vector.text("via last.fm", WIDTH - text_width, HEIGHT - 20)
    presto.update()

def check_touch():
    global current_mode
    
    touch.poll()
    
    if touch.state:
        print(f"Touch detected!")
        
        # Wait for touch release to prevent multiple triggers
        while touch.state:
            touch.poll()
            utime.sleep(0.01)
        
        current_mode = (current_mode + 1) % 3
        mode_names = ["Album Art", "Recent Tracks", "Clock"]
        print(f"Mode changed to: {mode_names[current_mode]}")
        return True
    return False

def get_recent_tracks(limit=4):
    """Get recent tracks from last.fm"""
    url = f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={LASTFM_USERNAME}&api_key={LASTFM_API_KEY}&format=json&limit={limit}"
    
    try:
        response_text = fetch_data(url)
        
        # DEBUG: show response if it looks problematic
        if not response_text.strip().startswith('{'):
            print("Invalid JSON response:", response_text[:300])
            return []
        
        data = json.loads(response_text)
        tracks = data.get('recenttracks', {}).get('track', [])
        
        if isinstance(tracks, dict):
            tracks = [tracks]
        
        result = []
        for track in tracks:
            # Get URL of largest image
            images = track.get('image', [])
            art_url = ''
            if images:
                for img in reversed(images):
                    if img.get('#text'):
                        art_url = img['#text']
                        break
            
            result.append({
                'name': track.get('name', 'Unknown'),
                'artist': track.get('artist', {}).get('#text', 'Unknown'),
                'art_url': art_url,
                'now_playing': '@attr' in track and 'nowplaying' in track.get('@attr', {})
            })
        
        return result
    except json.JSONDecodeError as e:
        print("JSON parse error:", e)
        print("Response was:", response_text[:500] if 'response_text' in locals() else "No response")
        return []
    except Exception as e:
        print("last.fm error:", e)
        return []

def main():
    global recent_tracks_cache, current_mode
    
    connect_to_wifi()
    print(f"Starting last.fm monitor for: {LASTFM_USERNAME}")
    print("Tap screen to cycle through: Album Art -> Recent Tracks -> Clock")
    
    last_track = None
    error_count = 0
    last_mode = current_mode
    api_call_count = 0
    
    # Get initial recent tracks, show most recent
    recent_tracks_cache = get_recent_tracks(4)
    if recent_tracks_cache:
        recent = recent_tracks_cache[0]
        print(f"Startup: {recent['name']} by {recent['artist']}")
        if current_mode == MODE_ALBUM_ART:
            if recent['art_url']:
                fetch_album_art(recent['art_url'])
            update_album_display(recent['artist'], recent['name'])
        last_track = (recent['name'], recent['artist'])
    
    while True:
        # Check for touch input every iteration
        if check_touch() or current_mode != last_mode:
            last_mode = current_mode
            
            if current_mode == MODE_CLOCK:
                update_clock()
            elif current_mode == MODE_RECENT_TRACKS:
                update_recent_tracks_display()
            elif current_mode == MODE_ALBUM_ART and recent_tracks_cache:
                recent = recent_tracks_cache[0]
                if recent['art_url']:
                    fetch_album_art(recent['art_url'])
                update_album_display(recent['artist'], recent['name'])
            
            # Reset counter and continue
            api_call_count = 0
            utime.sleep(0.5)
            continue
        
        # Make API calls every 60 iterations (roughly 30 seconds with 0.5-second sleeps)
        if api_call_count >= 60 and current_mode in [MODE_ALBUM_ART, MODE_RECENT_TRACKS]:
            api_call_count = 0
            
            try:
                recent_tracks_cache = get_recent_tracks(4)
                
                if not recent_tracks_cache:
                    error_count += 1
                    if error_count > 3:
                        connect_to_wifi()
                        error_count = 0
                    utime.sleep(5)
                    continue
                
                error_count = 0
                current = recent_tracks_cache[0]
                current_track = (current['name'], current['artist'])
                
                # Handle album art mode
                if current_mode == MODE_ALBUM_ART:
                    if current['now_playing'] and current_track != last_track:
                        print(f"Now playing: {current['name']} by {current['artist']}")
                        if current['art_url']:
                            fetch_album_art(current['art_url'])
                        update_album_display(current['artist'], current['name'])
                        last_track = current_track
                
                # Handle recent tracks mode
                elif current_mode == MODE_RECENT_TRACKS:
                    update_recent_tracks_display()
                    
            except Exception as e:
                print("Monitor error:", e)
                error_count += 1
        
        # In clock mode, update periodically
        elif api_call_count >= 60 and current_mode == MODE_CLOCK:
            api_call_count = 0
            update_clock()
        
        # Increment counter and sleep
        api_call_count += 1
        utime.sleep(0.3)  # touch detection delay

# Start the main loop
main()

