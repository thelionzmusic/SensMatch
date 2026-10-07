# SensMatch

Your aim, in Borderlands 2 and The Pre-Sequel. Even below the slider's minimum.

Borderlands 2 and Borderlands: The Pre-Sequel won't let the mouse sensitivity slider go below 10. For anyone used to a low sensitivity in other shooters, that's still far too fast. SensMatch sets the game to the exact sensitivity you use elsewhere, with no hex editing, no save editing and no typing console commands.

It's also a sensitivity converter for the 10 most popular shooters.

Get SensMatch.exe from the latest release. There's nothing to install: just run it.

"Windows protected your PC"? That warning appears for any new program that isn't code-signed. Click More info, then Run anyway.

How to use it

Open SensMatch and go to the Borderlands tab.
Enter the game you're coming from, your sensitivity in it, and your mouse DPI.
The first time only, close Borderlands and click Set up. This switches on the game's console.
Start Borderlands and load in, then press Home. SensMatch sets your sensitivity for you.

Keep SensMatch open while you play; minimised is fine. Press Home once each session after you load in, and again if your aim ever feels fast after a loading screen.

Example: Valorant at 0.26 sensitivity and 800 DPI comes out as 11.0444 in Borderlands 2, which is 62.8 cm of mouse movement for a full 360° turn.

Check it's exact (optional)

On the Borderlands tab, click Start check, go back to the game and press F11. SensMatch turns you by exactly one full circle. If you land where you started, your sensitivity matches.

Sensitivity converter

The Converter tab matches your sensitivity between games, keeping the same distance of mouse movement per full turn. It shows the result for every supported game at once, and you can click any of them to copy its value.

Supported games: Valorant, Counter-Strike 2, Apex Legends, Fortnite, Call of Duty (MW2019 onward and Warzone), Overwatch 2, Rainbow Six Siege, Marvel Rivals, Destiny 2 and Team Fortress 2.

How it works

The Borderlands menu slider stops at 10, but the game's console command setsensitivity accepts any value. Borderlands 2 ignores custom key binds in its settings files, so SensMatch can't simply bind the command to a key. Instead, it switches the console on once. Then, when you press Home with Borderlands in focus, it opens the console, types the command and presses Enter. You'll see the console flash for a split second.

Borderlands' turn speed was measured precisely in game and is built into the exe, so the conversion is exact rather than estimated.

Troubleshooting

"Windows blocked the change" when clicking Set up Windows Security's Controlled folder access is protecting your Documents folder. SensMatch shows you two fixes: allow SensMatch through Windows Security, or make the one-line change yourself in Notepad.

My console already works (for example, I use BLCMM) Click My console already works on the setup card and pick the key that opens your console. SensMatch then won't touch your settings file.

Pressing Home does nothing Make sure SensMatch is open and Borderlands is the active window. If you changed the key under Options, press that key instead.

The Pre-Sequel shows "Console off" Close the game and click Set up again. It switches on the console in both games.

Building from source

You need Python 3.8 or newer on Windows, with the "Add python.exe to PATH" option ticked during install. Double-click build.bat. It installs PyInstaller, includes any Borderlands turn speed measured on that PC, and produces SensMatch.exe.

To run without building, double-click sensmatch.py.

Support

SensMatch is free. If it fixed your aim, you can buy me a coffee.

Licence

MIT
