# Add to CartoVista Plugin

The Add to CartoVista QGIS plugin allows users to easily export layers and maps from their QGIS projects to the CartoVista platform. Currently, **polygon, polyline, and point layers are supported**, with support for **raster layers coming soon**. Layers of other types will be ignored when uploading a map and cannot be uploaded on their own. If the plugin skips an unsupported layer during map upload, it will notify you at the end of the process, as shown in the screenshot below.

<img width="592" height="356" alt="image" src="https://github.com/user-attachments/assets/feea379b-ce1a-4bf5-b27c-0d09d9ea62b9" />

**New to the plugin?** Watch the CartoVista tutorial video and browse the FAQ for a quick introduction and setup guide on our [home page](https://cartovista.com/cartovista-qgis-plugin/).


# Supported layer settings
**The following is a list of QGIS layer settings that are supported by
the plugin.** These settings will be transmitted along with your layers
when you export them to CartoVista, which allows the plugin to better
recreate your maps in CartoVista. If a layer setting is not supported by the plugin, do not worry, CartoVista will set sane defaults so your maps still look and feel good out of the box.
<details>
<summary>Symbology</summary>
  
## Symbology
  
*Only Single Symbol styles are supported*

 - **Opacity**
 - **Blend modes:**
   - Hard light
   - Lighten
   - Multiply
   - Normal
   - Overlay
   - Screen

> *Fallback if unsupported value is used: Multiply*

 - **Symbol layer Types**:
   - Simple marker (point layers)
   - Simple line (polyline layers)
   - Simple fill (polygon layers)
   - Gradient fill (polygon layers)

> *More information on what sub-settings for each symbol layer type are
> supported can be found below*

  <details>
    <summary>Simple marker</summary>
    
  ### Simple marker
  
   - **Color**
   - **Outline**
   - **Size** (With unit aware conversions)
   - **Shapes:**
     - square
     - diamond
     - pentagon
     - hexagon
     - equilateral triangle
     - star
     - arrow
     - circle
     - cross
     - cross 2
  
  > *Fallback if unsupported value is used: Circle*
  </details>

<details>
  <summary>Simple line</summary>
  
  ### Simple line

 - **Line color**
 - **Width** (With unit aware conversions)
 - **Patterns:**
   - solid
   - dash
   - dot
   - dash dot
   - dash dot dot

> *Fallback if unsupported value is used: Solid*
</details>

<details>
<summary>Simple fill</summary>

### Simple fill

 - **Stroke color**
 - **Stroke width** (With unit aware conversions)
 - **Stroke Patterns:**
   - solid
   - dash
   - dot
   - dash dot
   - dash dot dot

> *Fallback if unsupported value is used: Solid*

 - **Fill style:**
   - Solid
   - No Brush
   - horizontal
   - vertical
   - cross
   - b diagonal
   - f diagonal
   - diagonal x
   - dense 1
   - dense 2
   - dense 3
   - dense 4
   - dense 5
   - dense 6
   - dense 7

> **Fill color**
</details>

<details>
  <summary>Gradient fill</summary>
  
### Gradient fill

> *Only Two Color mode is supported, Color Ramp is not*

 - **Gradient types:**
   - Linear
   - Radial

> *Fallback if unsupported value is used: Linear*
</details>
</details>

<details>
  <summary>Label Settings</summary>
  
  ## Label Settings

*Only Single Labels mode is supported*

- **Value** (Column used for the labels)
- **Fonts:**
   - Poppins
   - Arimo
   - Lato
   - Open Sans
   - Roboto
   - Tinos
   - Vollkorn

> *Fallback if unsupported value is used: Poppins*

- **Text color**
- **Text buffer and buffer color** (Support for all platforms except
Linux)
- **Font-Size** (With unit aware conversions)
- **Label Priority**
- **Visibility ranges**
- **Overlapping Labels:**
   - Allow Overlap with no penalty
   - Never Overlap

> *Fallback if unsupported value is used: Never Overlap*

- **Placement Modes:**
   - Offset from centroid (including quadrant selection)
   - Around centroid

> *Fallback if unsupported value is used: Around centroid*
>
> ***Note:** Sub-settings from the supported placement modes such as
> distance, rotation ect are not supported in CartoVista.*

**Avoid Duplicate labels**
</details>

<details>
  <summary>Rendering</summary>
  
 ## Rendering

- **Visibility ranges** 
</details>
