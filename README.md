# 🌊 EAFM-Enhanced: Environment Agency Flood Monitoring (Enhanced)

**EAFME** is a feature-rich, fork of the official Home Assistant Environment Agency integration.

While the original integration provides essential raw data, it could not support monitoring stations if they shared a name with other ones, which account for 8% of the total list.  **EAFME** is designed to provide actionable intelligence—telling you not just *how high* the river is, but what that level actually means for your local area.

---

## 🚀 Key Improvements in this Fork

### 1. 🆔 Fix: Duplicate Station Support

The original integration can struggle with "Station Shadowing." If two stations share the same name (e.g., "The Weir"), the original integration often only displays one, or fails to list the second.

* **The EAFM2 Solution:** We use unique RLOI IDs and Catchment names in the selection process. This ensures that every single gauge in the UK is selectable, even if there are 10 others with the same name.  Needless to say that this also makes it much easier to find the station which you are looking for. 

### 2. 🚦 Automated "River Status" Sensor

We've added a dedicated "Status" entity that categorizes the river's health in real-time:

* 🟢 **Normal**: Water levels are within the expected seasonal range.
* 🔴 **High**: Levels have exceeded the typical high threshold for this specific gauge.
* 🟡 **Low**: Levels are below the typical low threshold.

### 3. 🔍 Deep Metadata Fetching

EAFME doesn't just scrape the surface. It follows secondary API links to find "Stage Scale" data, providing you with:

* **Typical High/Low Thresholds** (now available as attributes).
* **Highest Recent Reading** (compare today's level to the last major flood).

---

## 🛠 Why Use This Over the Standard Version?

| Feature | Standard Integration | **EAFM2 (This Fork)** |
| --- | --- | --- |
| **Raw Water Levels** | ✅ | ✅ |
| **Handle Duplicate Names** | ❌ | ✅ |
| **River Status** (Normal/High/Low) | ❌ | ✅ |
| **Detailed Configuration** | Label Only | Label + Catchment + ID |
| **Typical Range Attributes** | ❌ | ✅ |

---

## ⚙️ Installation & Setup

1. **HACS:** Add this URL as a **Custom Repository** (Category: Integration).
2. **Install & Restart:** Download via HACS and restart Home Assistant.
3. **Configure:** Go to **Settings > Devices & Services > Add Integration** and search for **eafm enhanced**.

---

## 🙏 Credits & Acknowledgments

This project is a fork of the core [Environment Agency Flood Gauges](https://www.home-assistant.io/integrations/eafm/) integration.

* **Original Integration Author:** [Andrew Goddard (@Jc2k)](https://github.com/Jc2k).
* **Underlying Library:** Based on the `aioeafm` Python library.
* **Data Source:** This integration uses [Environment Agency flood and river level data](https://environment.data.gov.uk/flood-monitoring/doc/reference) from the real-time data API.

---

### 📝 Legal & Disclaimer

This integration is provided for informational purposes only. Data is sourced from the Environment Agency API (Open Government Licence v3.0). **Never rely solely on a smart home integration for life-safety decisions.** Always refer to the official [Check for Flooding](https://check-for-flooding.service.gov.uk/) service.

---

### Pro Dashboard Tip

You can now create a **Badge** on your Home Assistant dashboard that changes color based on the `sensor.[station]_river_status`. It makes it incredibly easy to see if you need to check the river at a single glance.

[Customizing Home Assistant Dashboards](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DkwLp99s_9Wc)

This video provides a great overview of how to customize your Home Assistant dashboard with custom sensors and states, perfect for making the most of your new River Status sensor.
