# SensMatch

**Set Borderlands 2 and The Pre-Sequel to your exact mouse sensitivity, even below the slider's minimum of 10.**

Borderlands 2 and Borderlands: The Pre-Sequel won't let the sensitivity slider go below 10. If you play other shooters at a low sensitivity, that's still far too fast, and there's no setting in the game to fix it. SensMatch sets Borderlands to exactly the sensitivity you already use elsewhere, so your aim feels the same. No hex editing, no save editing, and no typing console commands yourself.

SensMatch is also a sensitivity converter for the 10 most popular shooters.

**Example:** Valorant at 0.26 sensitivity and 800 DPI comes out as **11.0444** in Borderlands 2. That's 62.8 cm of mouse movement for a full 360° turn, the same as in Valorant.

### [⬇ Download SensMatch.exe](../../releases/latest)

---

## Contents

- [Before you start](#before-you-start)
- [Setting up Borderlands](#setting-up-borderlands)
- [Every time you play](#every-time-you-play)
- [Checking it's exact](#checking-its-exact)
- [Using the converter](#using-the-converter)
- [Troubleshooting](#troubleshooting)
- [Questions](#questions)
- [How it works](#how-it-works)
- [Building from source](#building-from-source)

---

## Before you start

You'll need:

- **Windows 10 or 11.**
- **Borderlands 2 and/or Borderlands: The Pre-Sequel**, from Steam or Epic. You need to have **launched the game at least once**, because that's when it creates the settings file SensMatch looks for.
- **Your sensitivity and DPI from the game you're coming from.** Your sensitivity is in that game's settings. Your DPI is in your mouse's software (Logitech G Hub, Razer Synapse and so on). If you've never changed it, 800 is a common default.

## Setting up Borderlands

You only do this once.

1. **Download `SensMatch.exe`** from the [releases page](../../releases/latest) and save it anywhere, such as your Desktop or Documents. There's nothing to install.

2. **Run it.** The first time, Windows may show a blue box saying **"Windows protected your PC"**. Click **More info**, then **Run anyway**. This appears for any program that hasn't paid for a code-signing certificate. It doesn't mean anything is wrong.

3. Click the **Borderlands** tab at the top.

4. Under **Your aim**, fill in:
   - **Game you're coming from**, such as Valorant
   - **Sensitivity**: your sensitivity in that game, such as 0.26
   - **Mouse DPI**, such as 800

   Your Borderlands sensitivity appears straight away in yellow, next to each game.

5. **Close Borderlands** if it's running, then click **Set up**. This switches on Borderlands' hidden console, which SensMatch uses to set your sensitivity. It does Borderlands 2 and The Pre-Sequel together, and backs up your settings file first.

That's it. The card at the bottom changes to **You're all set**.

## Every time you play

1. **Open SensMatch** before or after starting Borderlands. You can minimise it; it just needs to stay running.
2. **Load into your character.**
3. **Press Home.**

You'll see the console flash at the bottom of the screen for a split second. That's SensMatch typing your sensitivity in for you. Your aim is now set for the rest of the session.

If your aim ever feels fast again, for example after a loading screen, just press **Home** again.

Prefer a different key? Change it under **Options → Key to press in game**. You can choose Home, End, Insert, Page Up, Page Down or Pause.

## Checking it's exact

This step is optional, but it's satisfying.

1. In game, aim at something with a sharp edge, like a door frame or a pole.
2. In SensMatch, click **Start check**. The button counts down from 90 seconds.
3. Switch back to Borderlands and press **F11**.

SensMatch turns you by exactly the amount of mouse movement that equals one full circle in your other game. If you land back on the same edge, Borderlands now matches perfectly.

## Using the converter

The **Converter** tab works for any of these games:

> Valorant · Counter-Strike 2 · Apex Legends · Fortnite · Call of Duty (MW2019 onward and Warzone) · Overwatch 2 · Rainbow Six Siege · Marvel Rivals · Destiny 2 · Team Fortress 2

1. Pick **your current game** and enter your sensitivity and DPI.
2. Pick the game you want to **convert to**. If you use a different DPI there, change it.
3. The big yellow number is your new sensitivity. Click **Copy**, then paste it into that game's settings.

Underneath, **The same feel in every game** shows your sensitivity for every supported game at once. Click any of them to copy it. The **⇄** button swaps the two games around.

Some notes on specific games:

- **Fortnite:** use the X sensitivity percentage shown in game, such as 6.4.
- **Counter-Strike 2 and Team Fortress 2:** assume you haven't changed `m_yaw` from its default.
- **Rainbow Six Siege:** assumes the default sensitivity multiplier of 0.02.
- **Apex, Call of Duty and Destiny 2:** these are hipfire values. Aim-down-sights settings are separate in each game.

---

## Troubleshooting

### Setting up

**"Windows blocked the change" when I click Set up**

Windows Security has a feature called **Controlled folder access**. It protects your Documents folder, and it's blocking SensMatch from changing Borderlands' settings file there. You can either let SensMatch through, or make the change yourself.

- **Allow SensMatch:** open **Windows Security** and go to **Virus & threat protection → Protection history**. Click the **"Unauthorized changes blocked"** entry for SensMatch, then **Actions → Allow on device**. Go back to SensMatch and click **Set up** again.
- **Do it yourself:** in the window SensMatch shows, click **Open in Notepad**. Press **Ctrl+F**, search for `ConsoleKey`, and change that line to `ConsoleKey=Tilde`. If there's no ConsoleKey line, add it on the line under `[Engine.Console]`. Press **Ctrl+S** to save. Back in SensMatch, click **Check again**.

**"Bad file descriptor" or "The system cannot find the file specified"**

These are the same Controlled folder access block, with a different error message. Follow the steps above.

**It says "Not installed, or not launched yet"**

SensMatch can't find the game's settings file. Launch the game once, get to the main menu, then close it and switch tabs in SensMatch to refresh.

If you've definitely played the game, your Documents folder may be somewhere unusual. Click **Options → Find BL2 ini…** (or **Find TPS ini…**) and select the file yourself. It's usually here:

```
C:\Users\<you>\Documents\My Games\Borderlands 2\WillowGame\Config\WillowInput.ini
C:\Users\<you>\Documents\My Games\Borderlands The Pre-Sequel\WillowGame\Config\WillowInput.ini
```

If your Documents folder is in OneDrive, look under `C:\Users\<you>\OneDrive\Documents\` instead.

**I'm stuck on "One-time setup"**

Look at the small grey text on the card. It shows exactly which file SensMatch is reading and what it found:

- **"The file is marked read-only":** right-click `WillowInput.ini`, choose **Properties**, untick **Read-only**, then click **Set up** again.
- **"ConsoleKey line is empty":** the change didn't save. See "Windows blocked the change" above.
- **Wrong file path:** use **Find BL2 ini…** under Options.

If the console already opens in game, click **My console already works** and skip this step entirely.

**My console already works, for example because I use BLCMM**

Click **My console already works** on the setup card and pick the key that opens your console. SensMatch then leaves your settings file completely alone.

**The Pre-Sequel shows "Console off" but Borderlands 2 is "Ready"**

This won't stop you using Borderlands 2. To switch on The Pre-Sequel too, close the game and click **Set up** again.

### In game

**Pressing Home does nothing**

- Make sure **SensMatch is still running**. Check your taskbar; minimised is fine, closed isn't.
- Make sure **Borderlands is the active window**. Click inside the game first.
- If you changed the key under **Options**, press that key instead.
- If you set up the console while the game was running, the game may have undone the change when it closed. Close Borderlands, click **Set up** again, then restart the game.

**The console flashes, but my sensitivity doesn't change**

Open the console yourself to see what happened. On a UK keyboard that's usually the **@** key (next to Enter); on a US keyboard it's the key under **Esc**. If the text there looks garbled or incomplete, please [open an issue](../../issues) and include your keyboard layout.

**Letters appear in chat, or my character moves when I press Home**

The console didn't open in time, so the typed letters went to the game instead. Check the console is switched on: the Borderlands tab should say **Ready** next to your game. Then try again.

**My sensitivity went back to normal**

Borderlands reloads its own slider setting at certain points. Press **Home** again. If it keeps happening at a particular moment, such as after fast travel, please [open an issue](../../issues).

**The F11 check doesn't land exactly where I started**

- Make sure your **DPI** in SensMatch matches your mouse's actual DPI.
- If you use a different DPI in Borderlands, enter it under **Options → Different DPI in Borderlands?**
- Turn **Mouse Smoothing** off in Borderlands' options.
- Turn off **Enhance pointer precision** in Windows' mouse settings.

If it's still off, click **Options → Measure turn speed again**. This re-measures Borderlands on your PC in about two minutes, using a step-by-step guide.

**My hotkeys (F6 to F11) do strange things in other programs**

SensMatch only listens for F6 to F11 while you're measuring or during the 90-second check. The rest of the time, those keys are left alone.

### Windows and antivirus

**My antivirus flagged SensMatch.exe**

Programs made with PyInstaller, the tool used to package SensMatch, are sometimes flagged by mistake. That's especially common for programs that move the mouse or press keys, which SensMatch does for the F11 check and for typing into the console. The full source code is in this repository for anyone to read. You can also build the exe yourself (see [Building from source](#building-from-source)).

---

## Questions

**Is this safe to use? Can I get banned?**

Borderlands 2 and The Pre-Sequel have no anti-cheat, and SensMatch only sets your mouse sensitivity, using a command built into the game. **Don't** run SensMatch's F11 check while playing games that do have anti-cheat, like Valorant, CS2 or Apex. The check injects mouse movement, which their anti-cheat could flag. The converter tab is completely safe to use any time.

**Does it work with the Epic Games version?**

Yes. Both versions keep their settings in the same Documents folder.

**Does it work in co-op?**

Yes. Sensitivity is a local setting and only affects you.

**How do I undo everything?**

1. Open `WillowInput.ini` (see the file paths above).
2. Change `ConsoleKey=Tilde` back to `ConsoleKey=`.
3. Delete `SensMatch.exe`.

SensMatch keeps a backup of your original settings file at `%APPDATA%\SensMatch\backups`. Paste that address into File Explorer's address bar to open it.

**What does SensMatch save on my PC?**

Only your chosen key, your console key if you set one, and any turn speed you measured. These are kept in `%APPDATA%\SensMatch\config.json`, along with the backups. Nothing is sent anywhere.

---

## How it works

The Borderlands sensitivity slider stops at 10, but the game's console command `setsensitivity` accepts any value. Borderlands 2 ignores custom key binds in its settings files, because it reads them from your save profile instead. That means SensMatch can't simply bind the command to a key. So it:

1. switches on the game's console once, by changing one line in `WillowInput.ini`
2. waits for you to press your key while Borderlands is the active window
3. opens the console, types `setsensitivity <your value>` and presses Enter.

To work out your value, SensMatch keeps the distance of mouse movement per full turn the same as in your other game. Borderlands' turn speed was measured precisely in game and is built into the exe, so the result is exact rather than estimated. If you ever want to re-measure it on your own PC, use **Options → Measure turn speed again**.

---

## Building from source

1. Install [Python](https://www.python.org/downloads/) 3.8 or newer. On the first screen of the installer, tick **"Add python.exe to PATH"**.
2. Download this repository: click **Code → Download ZIP**, then extract it.
3. Double-click **`build.bat`**.

It installs PyInstaller, includes any Borderlands turn speed measured on that PC, and creates `SensMatch.exe` in the same folder. To run SensMatch without building it, double-click `sensmatch.py`.

---

## Support

SensMatch is free. If it fixed your aim, you can [buy me a coffee](https://www.paypal.com/ncp/payment/6PY8ZKAA2M9GS) ☕

Found a bug or want another game added? [Open an issue](../../issues).

## Licence

MIT
