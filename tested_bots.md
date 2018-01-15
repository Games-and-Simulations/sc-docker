# Testing results

We tested bots from SSCAIT tournament. All of these should work:

    game_time  bot_name
    -------------------
    46.66      igjbot
    49.41      Arrakhammer
    49.48      UPStarCraftAI 2016
    49.49      UC3ManoloBot
    49.58      OpprimoBot
    49.60      Guillermo Agitaperas
    49.82      Laura Martin Gallardo
    49.85      Gaoyuan Chen
    52.75      Kruecke
    52.81      KillAlll
    53.01      Lluvatar
    53.67      auxanic
    55.63      TyrProtoss
    62.03      Korean
    63.28      Matej Istenik
    65.16      ICELab
    65.52      HOLD Z
    68.07      Goliat
    69.69      Dave Churchill
    71.17      MorglozBot
    71.24      FTTankTER
    71.50      Sijia Xu
    74.09      Neo Edmund Zerg
    75.09      Microwave
    86.85      Lukas Moravec
    87.04      Flash
    89.45      Bryan Weber
    95.34      Black Crow
    99.08      MegaBot2017
    92.31      100382319
    104.95     Marine Hell
    107.40     Blonws31
    111.07     Roman Danielis
    113.91     NUS Bot
    126.60     Zia bot
    129.69     Andrey Kurdiumov
    141.52     Andrew Smith
    144.75     Dawid Loranc
    144.86     Marian Devecka
    145.20     PurpleCheese
    169.04     WuliBot
    175.51     Hannes Bredberg
    179.65     ZurZurZur
    185.17     Florian Richoux
    194.28     NiteKatT
    203.46     MadMixP
    227.52     Carsten Nielsen
    246.95     Niels Justesen
    261.69     Iron bot
    289.17     Tomas Vajda
    289.31     CherryPi
    360.64     McRave
    390.86     Jakub Trancik
    394.52     Martin Rooijackers
    403.29     Ecgberht
    619.33     Yuanheng Zhu


## Bots with errors

These bots are known to not work.

-----

- Tomas Cere
- Oleg Ostroumov
- Soeren Klett
- Marek Kadek

Error:

    Bridge: BWAPI Client launched!!!
    Bridge: Connecting...

-----

- JEMMET

Error:

    Unzipping Bot.zip to Z:\app\write\Bot
    unzipping SWI prolog libraries (win32.zip) to Z:\app\write\swi
    Loaded client bridge library.
    Exception in thread "BWAPI thread" java.lang.UnsatisfiedLinkError: jnibwapi.JNIBWAPI.startClient(Ljnibwapi/JNIBWAPI;)V
        at jnibwapi.JNIBWAPI.startClient(Native Method)
        at jnibwapi.JNIBWAPI.start(JNIBWAPI.java:130)
        at eisbw.BwapiListener$1.run(BwapiListener.java:68)

-----

- AyyyLmao

Error:

    Unzipping Bot.zip to Z:\app\write\Bot
    unzipping SWI prolog libraries (win32.zip) to Z:\app\write\swi
    Loaded client bridge library.
    Exception in thread "BWAPI thread" java.lang.UnsatisfiedLinkError: jnibwapi.JNIBWAPI.startClient(Ljnibwapi/JNIBWAPI;)V
        at jnibwapi.JNIBWAPI.startClient(Native Method)
        at jnibwapi.JNIBWAPI.start(JNIBWAPI.java:130)
        at eisbw.BwapiListener$1.run(BwapiListener.java:82)


-----

- NLPRbot
- Hao Pan
- Pineapple Cactus
- AILien
- PeregrineBot
- CasiaBot
- Steamhammer
- DAIDOES
- Travis Shelton

Error:

    wine: Unhandled page fault on read access to 0x00000000 at address 0x4c34f26 (thread 0035), starting debugger...

-----

- tscmoor
- WillBot
- KaonBot

Does not connect to the game:

    Game table mapping not found.
    Game table mapping not found.
    ...

-----

- Bereaver

bot.log:

    Failed to open bwapi-data/read/config.json
    Connecting...
    Game table mapping not found.
    Game table mapping not found.
    Game table mapping not found.
    0 | 53 | 0 | 18322591
    1 | 0 | 0 | 0
    2 | 0 | 0 | 0
    3 | 0 | 0 | 0
    4 | 0 | 0 | 0
    5 | 0 | 0 | 0
    6 | 0 | 0 | 0
    7 | 0 | 0 | 0
    fixme:ntdll:server_ioctl_file Unsupported ioctl 1b001c (device=1b access=0 func=7 method=0)
    Connected
    Connection successful
    waiting to enter match
    11 patches.
    Failed to open bwapi-data/read/strategies.json
    Disconnected

-----

- Bjorn P Mattsson
- Aurelien Lermant

bot.log:

    Attempting to init BWAPI...
    BWAPI ready.
    Connecting to Broodwar...

-----

- ForceBot

Hard to tell, nothing suspicious.

## Problematic

### Black crow

Has page fault after the game finishes:

    Connecting to Starcraft...
    Game table mapping not found.
    Game table mapping not found.
    0 | 53 | 0 | 18332753
    1 | 0 | 0 | 0
    2 | 0 | 0 | 0
    3 | 0 | 0 | 0
    4 | 0 | 0 | 0
    5 | 0 | 0 | 0
    6 | 0 | 0 | 0
    7 | 0 | 0 | 0
    fixme:ntdll:server_ioctl_file Unsupported ioctl 1b001c (device=1b access=0 func=7 method=0)
    Connected
    Connection successful
    Game ended
    failed, disconnecting
    Disconnected
    Exiting...
    wine: Unhandled page fault on read access to 0x00000000 at address 0x459dc4 (thread 0009), starting debugger...

### Yuanheng Zhu

Has page fault when the player leaves the game:

    # Cherry PI

    I23507 [zvpoverpool.cpp:210] Our Drones:                   1
    I23507 [zvpoverpool.cpp:211] Our Zerglings:                0
    I23507 [zvpoverpool.cpp:212] Our Hydralisks:               0
    I23507 [zvpoverpool.cpp:213] Our Lurkers:                  0
    I23507 [zvpoverpool.cpp:214] Our Mutalisks:                0
    I23507 [zvpoverpool.cpp:215] Our Scourge:                  0
    I23507 [zvpoverpool.cpp:216] Our Sunkens:                  0
    I23507 [zvpoverpool.cpp:217]
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    waiting for players...
    :: Yuanheng Zhu was dropped from the game.
    :: CherryPi: Goodbye Yuanheng Zhu!
    I23624 [bandit.cpp:128] Got |Yuanheng Zhu| saving bandit to bwapi-data/write/openings_yuanheng zhu.json
    I23624 [bandit.h:61] serializing OpeningBandit
    W23624 [main.cpp:141] Oh noes we lost :( -- with 1 buildings left

    # Yuanheng Zhu

    :: Yuanheng Zhu: BWAPI 4.1.2.4708 RELEASE is now live using "Juno.dll".
    :: Yuanheng Zhu: Enabled Flag UserInput
    :: CherryPi: BWAPI 4.2.0.4842 RELEASE is now live using "BWEnv.dll".
    :: CherryPi: Enabled Flag UserInput
    wine: Unhandled page fault on read access to 0x00000000 at address 0x5ba6e07 (thread 0034), starting debugger...
