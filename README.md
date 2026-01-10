# Discord Username Checker

A Python script for checking Discord username availability with support for OG usernames (dictionary words) and regular combinations.

## Features

- Check Discord username availability (tokenless)
- Support for OG usernames from public database
- Regular username combinations (3-4 letters)
- Multi-threaded async checking
- Proxy support
- RPS monitoring
- Auto-restart on stall detection
- Progress saving

## Installation

1. Install Python 3.x
2. Install dependencies:
```bash
pip install aiohttp
```

## Usage

1. Run the script:
```bash
python main.py
```

2. Choose check mode:
   - Regular combinations (3-4L)
   - OG words (all lengths from usernames.txt)

3. Configure proxies (optional):
   - Add proxies to `data/proxies.txt` (one per line)
   - Format: `ip:port` or `ip:port:user:pass`

4. Results are saved to `results/hits.txt`

## Credits

This project is based on [Cloudzik1337/DiscordUsernameChecker](https://github.com/Cloudzik1337/DiscordUsernameChecker) and has been modified for improved functionality.

## License

MIT License
