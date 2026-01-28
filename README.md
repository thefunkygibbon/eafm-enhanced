# Environment Agency Flood Gauges Fixed (eafm2)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This is a custom Home Assistant integration for the UK Environment Agency (EA) flood monitoring API. It is a "Fixed" version of the built-in `eafm` integration, designed to solve the common problem of ambiguous station names which in turn caused stations to be missing from the list.   

## 🚀 The Fix: Catchment Awareness
The official integration only shows the **Station Label** when you are setting it up. If you live near a "St Ives," "Bridge End," for example, you would only see one in the list and have no idea which one it is.

**This version adds the Catchment Name to the selection list.**

- **Before:** `St Ives`
- **After:** `St Ives (Great Ouse)` | `St Ives (Cornwall)`

Therefore it will actually now list out all of the versions of that named Station. 

## ✨ Key Features
- **Catchment Identity:** See exactly which river system a station belongs to during setup.
- **Self-Contained:** Uses a bundled version of the `aioeafm` library, ensuring stability and independence from upstream dependency changes.
- **Side-by-Side Install:** Uses the domain `eafm2`, so you can keep the official integration installed while you test this version.

## 🛠 Installation

### Option 1: HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this GitHub repository.
4. Select **Integration** as the category and click **Add**.
5. Find "Environment Agency Flood Gauges Fixed" in the HACS list and click **Download**.
6. **Restart Home Assistant.**

### Option 2: Manual
1. Download the `eafm2` folder from `custom_components/` in this repo.
2. Copy it into your Home Assistant `/config/custom_components/` directory.
3. **Restart Home Assistant.**

## ⚙️ Configuration
1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Environment Agency Flood Gauges Fixed**.
4. Select your station from the newly clarified list!

---
*Note: This integration is based on the original work by @Jc2k in the Home Assistant Core repository but has been modified to enhance user experience during setup.*
