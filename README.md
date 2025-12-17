# OpenEvidence Panel for Anki

A modern Anki addon that integrates OpenEvidence directly into your Anki interface as a side panel.

## Features

- 📚 **Clean Toolbar Icon**: Open book icon in the top toolbar next to Sync
- 🎨 **Integrated Side Panel**: OpenEvidence opens as a docked panel on the right side of Anki
- 🎯 **Modern UI**: Minimalistic design with smooth hover effects
- 🔄 **Flexible Layout**: Dock, undock, or resize the panel as needed
- ⚡ **Quick Access**: Toggle the panel on/off with a single click
- ⌨️ **Tab Key Shortcut**: Press Tab while reviewing to send card text directly to OpenEvidence search

## Installation

### Method 1: Install from .ankiaddon file

1. Download the `openevidence_panel.ankiaddon` file
2. Double-click the file, or open Anki and go to **Tools → Add-ons → Install from file...**
3. Select the downloaded `.ankiaddon` file
4. Restart Anki

### Method 2: Manual Installation

1. Download and extract the addon files
2. Copy the `openevidence_panel` folder to your Anki addons directory:
   - **Windows**: `%APPDATA%\Anki2\addons21\`
   - **Mac**: `~/Library/Application Support/Anki2/addons21/`
   - **Linux**: `~/.local/share/Anki2/addons21/`
3. Restart Anki

## Usage

1. After installation, you'll see a book icon (📖) in the top toolbar next to Sync
2. Click the book icon to open/close the OpenEvidence panel
3. The panel will appear docked on the right side of Anki
4. You can:
   - Resize the panel by dragging the separator
   - Undock the panel by clicking the pop-out button
   - Close the panel by clicking the X button or the toolbar icon

### Quick Search Feature ⚡

Press **Tab** to automatically send the current card's text to the OpenEvidence search box - works from anywhere!

**Works in two ways:**
1. **Press Tab while reviewing in Anki** → Sends the current card text to OpenEvidence
2. **Press Tab while focused on the OpenEvidence panel** → Fills the search box with the current card text

**How it works:**
- Press Tab on the **question side** → Sends the question text
- Press Tab on the **answer side** → Sends the answer text  
- The OpenEvidence panel will automatically open if it's hidden
- The text will be inserted into the search box, ready for you to search
- Works whether you're focused on the Anki card OR the OpenEvidence panel!

## Configuration

You can customize the panel width by editing the addon's config:

1. Go to **Tools → Add-ons**
2. Select **OpenEvidence Panel**
3. Click **Config**
4. Adjust the settings:
   - `width`: Panel width in pixels (default: 500)
   - `height_percentage`: Panel height as percentage of screen (default: 0.9)

## Requirements

- Anki 2.1.45 or later
- Internet connection (to access OpenEvidence.com)

## Credits

Created for medical students and professionals who want quick access to OpenEvidence while studying with Anki.

## License

Free to use and distribute.

## Support

For issues or questions, please contact the addon developer.
