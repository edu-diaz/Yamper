# Yamper  ![yamper](https://play.pokemonshowdown.com/sprites/xyani/yamper.gif)
A Pokémon battle-bot based on NLP that can play battles on [Pokemon Showdown](https://pokemonshowdown.com/).

![badge](https://github.com/gameduser/Yamper/actions/workflows/pythonapp.yml/badge.svg)

## Python version
Developed and tested using Python 3.6.3.

## Getting Started

### Configuration
Environment variables are used for configuration which are by default read from a file named `.env`

The configurations available are:
```
BATTLE_BOT: (string, default "yamper") The BattleBot module to use. More on this below
TIMER: (string, default OFF) Request initiating timer at the beginning of the battle or not
SAVE_REPLAY: (bool, default False) Specifies whether or not to save replays of the battles
LOG_LEVEL: (string, default "DEBUG") The Python logging level 
WEBSOCKET_URI: (string, default is the official PokemonShowdown websocket address: "sim.smogon.com:8000") The address to use to connect to the Pokemon Showdown websocket 
PS_USERNAME: (string, required) Pokemon Showdown username
PS_PASSWORD: (string) Pokemon Showdown password 
BOT_MODE: (string, required) The mode the the bot will operate in. Options are "CHALLENGE_USER", "SEARCH_LADDER", or "ACCEPT_CHALLENGE"
USER_TO_CHALLENGE: (string, required if BOT_MODE is "CHALLENGE_USER") The user to challenge
POKEMON_MODE: (string, required) The type of game this bot will play games in
TEAM_NAME: (string, required if POKEMON_MODE is one where a team is required) The name of the file that contains the team you want to use. More on this below in the Specifying Teams section.
RUN_COUNT: (integer, required) The amount of games this bot will play before quitting
ROOM_NAME: (string, optional) Optionally join a room by this name is BOT_MODE is "ACCEPT_CHALLENGE"
BANANA_API_KEY: (string, required if BATTLE_BOT is yamper) The API key to connect with the GPT-J model developped by Banana.
```

There is a sample `.env` file in this repository.

### Running without Docker

**1. Clone**

Clone the repository with `git clone https://github.com/gameduser/Yamper.git`

**2. Install Requirements**

Install the requirements with `pip install -r requirements.txt`.
Be sure to use a virtual environment to isolate your packages.

**3. Run**

Run with `python run.py` and the bot will start with configurations
specified by environment variables read from the file named `.env`

### Running with Docker
This requires Docker 17.06 or higher.

**1. Create the configuration file**

Create an .env file like this example:
```
BATTLE_BOT=yamper
TIMER=OFF
SAVE_REPLAY=False
LOG_LEVEL=INFO
WEBSOCKET_URI=sim.smogon.com:8000
PS_USERNAME=<Your Pokemon Showdown user>
PS_PASSWORD=<Your Pokemon Showdown password>
BOT_MODE=SEARCH_LADDER
POKEMON_MODE=gen8randombattle
RUN_COUNT=1
BANANA_API_KEY=<Your Banana GPT-J API key>
```

**2. Run the docker image**

`docker run --env-file .env gameduser/yamper`

## Battle Bots

### Safest
use `BATTLE_BOT=safest`

The bot searches through the game-tree for two turns and selects the move that minimizes the possible loss for a turn.

For decisions with random outcomes a weighted average is taken for all possible end states.
For example: If using draco meteor versus some arbitrary other move results in a score of 1000 if it hits (90%) and a score of 900 if it misses (10%), the overall score for using
draco meteor is (0.9 * 1000) + (0.1 * 900) = 990.

This is equivalent to the [Expectiminimax](https://en.wikipedia.org/wiki/Expectiminimax) strategy.

This decision type is deterministic - the bot will always make the same move given the same situation again.

### Yamper
use `BATTLE_BOT=yamper` (default unless otherwise specified)

Using the [Banana GPT-J public model](https://www.banana.dev/pretrained-models/python3/gptj), it will decide each next movement by asking the model with an API call. Options are usually attacking or switching Pokemon, so first it asks what does it prefer. If decides to attack, we request which attack does prefer. Finally the answer is parsed for the showdown API and sent.

This follows a multiple-shot strategy. Usually it doesn't provide a good answer first time, so we ask Yamper until we get a valid response. This has the inconvenienve that making a decision may take a few seconds, so we recommend disabling timer to avoid running out of time.

## The Battle Engine
The bots in the project all use a Pokemon battle engine to determine all possible transpositions that may occur from a pair of moves.

For more information, see [ENGINE.md](https://github.com/gameduser/yamper/blob/master/ENGINE.md) 

## Specifying Teams
You can specify teams by setting the `TEAM_NAME` environment variable.
Examples can be found in `teams/teams/`.

Passing in a directory will cause a random team to be selected from that directory.

The path specified should be relative to `teams/teams/`.

#### Examples

Specify a file:
```
TEAM_NAME=gen8/ou/clef_sand
```

Specify a directory:
```
TEAM_NAME=gen8/ou
```
