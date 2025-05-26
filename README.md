# Last.fm Playing Display for Pimoroni Presto

A MicroPython application that displays your Last.fm "now playing" information on a Pimoroni Presto device. 
Features album art display, recent tracks list, and a clock with touch navigation between modes.

Inspired by the [WiiM Now Playing](https://github.com/retired-guy/WiiM-Presto) app.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Configuration](#configuration)
- [Features](#features)
- [API](#api)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Background

This project transforms your Pimoroni Presto into a Last.fm display that shows:

- **Album Art Mode**: Full-screen album artwork for currently playing tracks
- **Recent Tracks Mode**: List of your 4 most recent Last.fm scrobbles
- **Clock Mode**: Digital clock with date display

The display automatically updates when you start listening to new music and provides an elegant way to see your music listening activity at a glance.

## Install

### Prerequisites

- [Pimoroni Presto](https://shop.pimoroni.com/products/presto)
- Pimoroni MicroPython firmware installed
- WiFi network connection
- Last.fm account with API access

### Hardware Setup

1. Set up your Pimoroni Presto according to the [official documentation](https://github.com/pimoroni/presto)
2. Ensure MicroPython is installed and the device is connected to your computer

### Software Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd lastfm-presto-display
   ```

2. Copy the required files to your Presto:
   - `lastfm_playing.py` - Main application
   - `secrets.py` - Configuration file (see [Configuration](#configuration))
   - `Roboto-Medium.af` - the [Roboto font in Alright Font format](https://github.com/pimoroni/picovector-fonts/releases/).

3. Ensure your Presto has the required dependencies (these should be included with Pimoroni's MicroPython build):
   - `picovector`
   - `presto`
   - `urequests`
   - `jpegdec`, `pngdec`

## Configuration

### Last.fm API Setup

1. Visit the [Last.fm API page](https://www.last.fm/api/account/create) to create an API account
2. Create a new API application to get your API key
3. Note down your API key and Last.fm username

### WiFi and API Configuration

Edit the `secrets.py` file with your credentials:

```python
WIFI_SSID = "your_wifi_network_name"
WIFI_PASSWORD = "your_wifi_password"
LASTFM_API_KEY = "your_lastfm_api_key"
LASTFM_USERNAME = "your_lastfm_username"
TIMEZONE_OFFSET = +1  # Adjust for your timezone (+1 for GMT+1, -5 for EST, etc.)
```

**Important**: Never commit your `secrets.py` file with real credentials to version control.

## Usage

1. Upload both `lastfm_playing.py` and your configured `secrets.py` to your Presto device
2. Run the application
   ```python
   import lastfm_playing
   ```
3. The device will connect to WiFi and start displaying your Last.fm data
4. **Touch the screen** to cycle between display modes:
   - Album Art → Recent Tracks → Clock → Album Art...

### Display Modes

**Album Art Mode**
- Shows full-screen album artwork for the currently playing track
- Displays artist name and track title at the bottom
- Updates automatically when you start playing new music

**Recent Tracks Mode**
- Lists your 4 most recent Last.fm scrobbles
- Shows track numbers, artist names, and song titles
- Indicates currently playing tracks

**Clock Mode**
- Large digital time display
- Shows current date with day of week
- May be useful as a bedside clock when not actively listening to music?

## Features

- **Automatic Updates**: Polls Last.fm API every ~30 seconds for new tracks
- **Album Art Display**: High-quality album artwork with rounded corners
- **Touch Navigation**: Simple tap-to-cycle interface between modes
- **WiFi Auto-Recovery**: Automatically reconnects if connection is lost
- **Timezone Support**: Configurable timezone offset for accurate time display

## API

This application uses the [Last.fm API](https://www.last.fm/api) with the following endpoints:

- `user.getrecenttracks` - Fetches recent listening history
- Image proxy via [wsrv.nl](https://wsrv.nl) for album art resizing and optimization

### Rate Limiting

The application makes API calls approximately every 30 seconds to respect Last.fm's rate limits and conserve battery life.

## Resources

- [Pimoroni Presto Product Page](https://shop.pimoroni.com/products/presto)
- [Pimoroni Presto GitHub Repository](https://github.com/pimoroni/presto)
- [Last.fm API Documentation](https://www.last.fm/api)
- [Last.fm API Key Registration](https://www.last.fm/api/account/create)

## Maintainers

[@andypiper](https://github.com/andypiper)

## Contributing

PRs accepted! Feel free to contribute improvements, bug fixes, or new features.

## License

[MIT](LICENSE) © 2025 Andy Piper
