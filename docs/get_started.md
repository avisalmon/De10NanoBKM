# Get started: from zero to a chat that guides you

You do this part once, by yourself. Its only goal is a **working editor with an AI chat inside it, opened on your own
copy of this project**. From the moment you type *"Tell me what to do"* in that chat, the assistant takes over: it
installs the rest (Python, the simulator), tells you exactly how to get Quartus, simulates and compiles the template,
puts it on your board, and then helps you build your own design. You never have to come back to this page.

Time: 20-40 minutes, mostly downloads and sign-ups. **You don't need the board yet**: leave it in its box until the
chat asks for it. Windows is described first; macOS and Linux notes are in each step.

```
 1. GitHub account  ->  2. VS Code  ->  3. an AI chat in VS Code (say hello)  ->  4. Git  ->  5. copy the project to your PC  ->  6. "Tell me what to do"
```

## 1. A GitHub account (free)

GitHub is where this project lives, and where your own designs can live later.

1. Go to https://github.com/signup and create an account.
2. Turn on **two-factor sign-in** (GitHub calls it "two-factor authentication", often written 2FA). Signing in then
   needs your password **and** a one-time code from your phone, so someone who steals your password still can't get in.
   * GitHub -> click your picture (top right) -> **Settings** -> **Password and authentication** -> **Enable
     two-factor authentication**.
   * Choose an **authenticator app** on your phone (for example Google Authenticator or Microsoft Authenticator): scan
     the square code GitHub shows, then type the 6-digit code the app shows. (A **passkey**, which uses your phone's or
     computer's fingerprint, face or PIN instead of a code, is fine too.)
   * GitHub then shows **recovery codes**. Save them somewhere safe: they are how you get back in if you lose your phone.

*You know it worked when* you can sign in at https://github.com.

## 2. VS Code (the editor)

Download it from https://code.visualstudio.com and install it. On Windows, keep the option **"Add to PATH"** ticked
(it is on by default). Other editors with an AI assistant can work, but this guide assumes VS Code.

*You know it worked when* VS Code opens.

## 3. An AI chat inside VS Code (pick one), and say hello

You need a chat that can **read your project and run commands for you**. Two options work with this project; its
playbooks are included for both.

### Option A: GitHub Copilot

1. In VS Code open Extensions, the add-ons store (**Ctrl+Shift+X**, or the icon of four squares on the left), search
   **GitHub Copilot**, and click **Install**.
2. Sign in with the GitHub account from step 1 when it asks.
3. Plan: Copilot has a free tier with limited monthly use; a long guided session usually needs a paid plan. Check
   yours at https://github.com/settings/copilot.
4. Open the chat (**Ctrl+Alt+I**) and set its mode to **Agent** (the dropdown in the chat box). Agent mode is what
   lets it run commands and edit files.

### Option B: Claude Code

1. You need a Claude account on a plan that includes Claude Code (see https://claude.com/product/claude-code), or
   API credits.
2. In VS Code open Extensions (**Ctrl+Shift+X**), search **Claude Code** (published by Anthropic), and click
   **Install**.
3. Open the Claude Code panel (the Claude icon at the top right of the editor, or **Ctrl+Shift+P** and type
   *Claude Code*) and sign in when it asks.

**Now type `hello` in the chat.**

*You know it worked when* it answers. You now have an editor with an AI in it: the hard part is done.

## 4. Git

Git is the tool that copies the project to your computer and keeps track of every change.

* **Windows:** download it from https://git-scm.com/downloads and accept the default choices (or, in a terminal:
  `winget install --id Git.Git -e`).
* **macOS:** open Terminal and run `xcode-select --install` (or `brew install git`).
* **Linux:** `sudo apt install git` (or your distribution's equivalent).

Then **close VS Code completely and open it again**, so it notices Git.

### First, what is a "terminal"?

A **terminal** is a window where you give the computer instructions by **typing** them instead of clicking. Each
instruction is one line of text, called a **command**. You need it for a few lines on this page; after that, the AI
chat runs the commands for you (and shows you what it runs).

* **How to open one:** in VS Code's top menu click **Terminal -> New Terminal** (or press **Ctrl+`**, the key under
  Esc). A panel opens at the bottom of the window.
* **What you will see:** a line ending in `>`, something like `PS C:\Users\dana>`. This is the **prompt**: "ready,
  type a command". (On macOS and Linux it ends in `$` or `%`.)
* **How to run a command:** click inside the terminal, type the command (or paste it: **Ctrl+V**, or right-click),
  and press **Enter**. Run one line at a time.
* **How to know it finished:** the prompt comes back. Some commands print nothing for a few seconds: just wait.
* **If you see red text,** read the first red line and check the table at the end of this page. The commands on this
  page cannot break your computer.

*You know it worked when* you type `git --version` in a VS Code terminal and see something like
`git version 2.53.0`.

## 5. Copy the project to your computer and open it

1. In VS Code, open a terminal: **Terminal -> New Terminal**.
2. Run these four commands **one at a time**: type or paste a line, press **Enter**, wait for the prompt, then the
   next. You may replace `my-fpga` with another short name (lowercase, no spaces) in the last two lines:

   ```powershell
   mkdir C:\fpga
   cd C:\fpga
   git clone https://github.com/avisalmon/De10NanoBKM.git my-fpga
   code my-fpga
   ```

   What each line does:
   * `mkdir C:\fpga` makes a new, empty folder called `fpga` on your C: drive ("make directory").
   * `cd C:\fpga` moves the terminal into it ("change directory"); the prompt now ends in `C:\fpga>`.
   * `git clone ... my-fpga` copies the whole project from GitHub into `C:\fpga\my-fpga`.
   * `code my-fpga` opens that folder in a new VS Code window.

   (macOS and Linux: `mkdir ~/fpga` and `cd ~/fpga` for the first two lines.)

3. The new window asks **"Do you trust the authors of the files in this folder?"** Click **Yes, I trust the
   authors**: the assistant needs to run commands here. If the last line said `code` is not recognised, use
   **File -> Open Folder** and choose `C:\fpga\my-fpga` instead.

Why `C:\fpga` and not your Documents folder: Documents is often synced by OneDrive, which locks files while it syncs
and breaks long paths, and Quartus writes many files in deep folders. A short, plain folder avoids both.

*You know it worked when* the Explorer on the left shows folders like `docs`, `scripts` and `templates`, and files
like `CLAUDE.md` and `README.md`.

**This is a copy on your computer only.** Nothing you do in it changes the project online. If you want your designs
on GitHub later, the assistant creates a repository of your own, and asks you first.

## 6. Say it

Open the chat in this new window (**Agent** mode for Copilot; the Claude Code panel for Claude Code) and type:

> **Tell me what to do**

(*"Help me build my FPGA project"* works too.) The assistant looks at your computer, tells you what it found,
installs what it can, and walks you through the rest: Quartus (a large download you start in a browser), the
template in simulation, the template compiled and running on your board, and then a design of your own. Whenever a
step needs *you* (a download, a cable, a switch, a look at the LEDs) it says exactly what to do. You never need to
paste a password or a key into the chat.

**Coming back later?** Open the project in VS Code (**File -> Open Recent**), open the chat, and say *"Tell me what to
do"* again. It first checks GitHub for improvements to this blueprint and pulls them in when that is safe (telling you
what changed), then reads [the checklist](journey_checklist.md) and continues where you stopped.

## Things you will be asked to approve

* The assistant asks before running commands. Read what it wants to run, and approve if it matches what it just said.
  If a command looks unrelated, say no and ask why.
* **A Windows "Do you want to allow this app to make changes?" window** appears when something installs (Quartus, the
  USB driver). It may open *behind* VS Code: if an install seems stuck, look for it in the taskbar.
* It will ask you to download Quartus in your browser (Intel's site may ask you to sign in with a free account), to
  click through its installer, and later to plug in the board and say what the LEDs do. That part nobody can do for
  you.

## If something goes wrong in this part

| Symptom | Fix |
|---|---|
| The chat can't run commands or edit files | Copilot: switch the mode to **Agent**. Claude Code: make sure the project folder is open and trusted |
| `git` is not recognised | Close VS Code completely and open it again after installing Git |
| `code` is not recognised (step 5) | Use **File -> Open Folder** -> `C:\fpga\my-fpga` instead |
| `mkdir` says the folder already exists | That's fine: carry on with `cd C:\fpga` |
| `git clone` says the destination already exists | Pick another name instead of `my-fpga`, or delete the old folder first |
| A download fails with `403 Forbidden` at work | Often the company's web filter, not the site: open the address in a browser and read the page. The assistant knows other routes ([gotchas.md](procedures/gotchas.md), row 17) |
| Copilot or Claude says you've run out of messages | Check your plan; the free tiers are limited |
| You use another editor, or only a terminal | The playbooks work in any assistant that reads `AGENTS.md`: open the folder there and say the same sentence |

**Already comfortable with GitHub?** You can click **Use this template** on the project's GitHub page, create your own
repository (private or public), and clone *that* instead. The assistant handles both starting points.

## Words you'll meet

Plain meanings, so nothing on the way sounds like a secret code. You can always ask the chat *"what does that mean?"*.

| Word | Meaning |
|---|---|
| **FPGA** | a chip full of logic blocks that you connect by *describing* a circuit. The description is compiled into a bitstream that sets the chip up as that circuit. |
| **DE10-Nano** | Terasic's board with a **Cyclone V SoC**: an FPGA and a dual-core ARM processor on one chip, with LEDs, buttons, switches and headers around it. |
| **HPS** | the "hard processor system": the ARM side of the chip, which can run Linux. This blueprint uses the FPGA side first. |
| **SystemVerilog, RTL** | the language the designs are written in. RTL ("register-transfer level") is the design's description in it. |
| **Clock** | a signal that ticks 50 million times a second on this board. Every register in the design updates on its tick, all at once. |
| **Simulation, simulator** | running the design on your computer instead of the board. This project uses **Icarus Verilog**, which is free. |
| **Testbench** | a second piece of code that plays the person at the board: it presses the buttons, watches the LEDs, and prints `PASS` or `FAIL`. |
| **Waveform** | a picture of every signal over time, from a simulation. **GTKWave** shows it. |
| **Quartus Prime Lite** | Intel's free tool that compiles a design for the FPGA. It needs the **Cyclone V device package** for this board. |
| **Compile, build** | turning the design into a bitstream. It takes minutes, which is why we simulate first. |
| **Timing, slack** | whether every signal arrives within one clock tick. Slack is the time to spare: positive is good. |
| **Bitstream (`.sof`)** | the compiled design. Loading it configures the FPGA until the power goes off. |
| **Pin, `.qsf`** | which leg of the chip each signal connects to (an LED, a button). They are listed in the project's `.qsf` file, copied from Terasic's. |
| **JTAG, USB-Blaster II** | the connection that loads a bitstream into the FPGA. The board has a USB-Blaster II built in, behind one of its USB ports. |
| **3.3 V** | the voltage of the FPGA's pins. A 5 V part needs a level shifter in between. |
| **GitHub, repository ("repo")** | a website that stores code; a repository is one project's folder there, with the history of every change. |
| **Git, clone** | the program that copies projects from GitHub and records your changes; a clone is your copy. |
| **VS Code, extension** | the editor where you see the files and talk to the AI; an extension is an add-on for it, like Copilot or Claude Code. |
| **Agent mode** | the Copilot setting that lets the chat *do* things (run commands, edit files), not just answer. |
| **Terminal, command** | a panel where you type instructions; each line is a command, run with Enter. |
| **Python** | the language this project's tools (`scripts/fpga.py`) are written in. The chat installs it for you. |
| **Private vs public** | who can see a repository: only you, or everyone. This blueprint is public so anyone can start from it; your own repository can be either. |
| **Playbooks ("skills")** | step-by-step instructions inside this project that the AI follows, so it works the same careful way every time. |

When the chat answers *"Tell me what to do"*, stop reading this page. The assistant has it from here.
