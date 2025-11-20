"""
QGIS to CartoVista styles
"""
from qgis.core import Qgis
import platform

def get_rendering_settings(interactive_layer):
    qgis_blendmode = interactive_layer.blendMode()
    blend_modes = {
        20: "HARDLIGHT",
        17: "LIGHTEN",
        13: "MULTIPLY",
        0: "NORMAL",
        15: "OVERLAY",
        14: "SCREEN"
    }
    cv_blendmode = "MULTIPLY"
    if qgis_blendmode in blend_modes:
        cv_blendmode = blend_modes[qgis_blendmode]

    if cv_blendmode == "MULTIPLY":
        return None
    return {
        "blendMode" : cv_blendmode
    }

def get_visibility_ranges_settings(interactive_layer):
    is_layer_default = True
    is_labels_default = True

    range_activated_layer = interactive_layer.hasScaleBasedVisibility()
    if range_activated_layer:
        layer_min = int(round(interactive_layer.minimumScale()))
        layer_max = int(round(interactive_layer.maximumScale()))
        is_layer_max_infinity = False
        is_layer_default = False
    else:
        layer_min = 50000000 #cv and qgis have opposite definitions for what a min and max zoom mean
        layer_max = 0
        is_layer_max_infinity = True

    range_activated_labels = False
    labels_min = 50000000 #cv and qgis have opposite definitions for what a min and max zoom mean
    labels_max = 0
    is_labels_max_infinity = True
    labels_on = interactive_layer.labelsEnabled()
    if labels_on:
        if interactive_layer.labeling().settings().scaleVisibility:
            labels_max = int(round(interactive_layer.labeling().settings().maximumScale))
            labels_min = int(round(interactive_layer.labeling().settings().minimumScale))
            is_labels_default = False

    if is_labels_default and is_layer_default: return None
    return {
        "layer": {
            "isZoomLayered": range_activated_layer,
            "isMaxInfinity": is_layer_max_infinity,
            "max": layer_min, #cv and qgis have opposite definitions for what a min and max zoom mean
            "min": layer_max
        },
        "labels": {
           "isZoomLayered": range_activated_labels,
            "isMaxInfinity": is_labels_max_infinity,
            "max": labels_min, #cv and qgis have opposite definitions for what a min and max zoom mean
            "min": labels_max 
        },
        "clusters": {
            "isZoomLayered": False,
            "min": 2500
        }
    }

def get_label_settings(qgis_label_settings, label_column_cv_guid):
    cv_fonts = ["Poppins", "Arimo", "Lato", "Open Sans", "Roboto", "Tinos", "Vollkorn"]
    qgis_font = qgis_label_settings.format().font().family()
    cv_font = next((cv_font for cv_font in cv_fonts if cv_font.lower() in qgis_font.lower()), "Poppins")

    qgis_color = qgis_label_settings.format().color()
    color = f"rgba({qgis_color.red()}, {qgis_color.green()}, {qgis_color.blue()}, {alpha_255_to_decimal(qgis_color.alpha())})"
    
    if platform.system() == "Linux":
        #For some reason accessing any property on qgis_label_settings.format().buffer() crashes QGIS in linux
        has_halo = False
        halo_color = "rgba(255,255,255,1)"
    else:
        has_halo = qgis_label_settings.format().buffer().enabled()
        qgis_halo_color = qgis_label_settings.format().buffer().color()
        halo_color = f"rgba({qgis_halo_color.red()}, {qgis_halo_color.green()}, {qgis_halo_color.blue()}, {alpha_255_to_decimal(qgis_halo_color.alpha())})"

    bold = qgis_label_settings.format().font().bold()
    italic = qgis_label_settings.format().font().italic()

    qgis_size = qgis_label_settings.format().size()
    size_unit = qgis_label_settings.format().sizeUnit().name

    size_in_points = size_to_points(qgis_size, size_unit)

    priority = qgis_label_settings.priority

    allow_overlap = qgis_label_settings.placementSettings().overlapHandling().name == "AllowOverlapAtNoCost"

    positions = {
        "AboveLeft": "TOP-LEFT",
        "Above": "TOP-CENTER",
        "AboveRight": "TOP-RIGHT",
        "Left": "MIDDLE-LEFT",
        "Over": "MIDDLE-CENTER",
        "Right": "MIDDLE-RIGHT",
        "BelowLeft": "BOTTOM-LEFT",
        "Below": "BOTTOM-CENTER",
        "BelowRight": "BOTTOM-RIGHT"
    }

    position = "AUTO-PLACEMENT"
    if qgis_label_settings.placement.name == "OverPoint":
        position = "MIDDLE-CENTER"
        if Qgis.QGIS_VERSION_INT >= 33800:
            quadrant = qgis_label_settings.pointSettings().quadrant().name
            if quadrant in positions:
                position = positions[quadrant]

    allowDuplicates = True
    if Qgis.QGIS_VERSION_INT >= 34400:
        allowDuplicates = not qgis_label_settings.thinningSettings().allowDuplicateRemoval()

    return {
        "font": cv_font,
        "color": color,
        "halo": has_halo,
        "haloColor": halo_color,
        "bold": bold,
        "italic": italic,
        "size": size_in_points,
        "labelColumn": label_column_cv_guid,
        "priority": priority,
        "allowOverlap": allow_overlap,
        "position": position,
        "allowDuplicates": allowDuplicates
    }

def size_to_points(qgis_size, size_unit):
    if "Points" == size_unit:
        size_in_points = qgis_size
    elif "Millimeters" == size_unit:
        size_in_points = qgis_size / 0.352
    elif "Inches" == size_unit:
        size_in_points = qgis_size / 0.014
    elif "Pixels" == size_unit:
        size_in_points = qgis_size * 0.75
    else:
         size_in_points = 11
    return min(max(6, int(round(size_in_points))), 42)


# Marker style
def get_marker_style(properties):
    # Color
    qgis_color = properties.get('color')
    color = None
    if qgis_color is not None:
        split_color = qgis_color.split(',')
        color = f"rgba({split_color[0]}, {split_color[1]}, {split_color[2]}, {alpha_255_to_decimal(split_color[3])})"

    # Halo info
    outline_style = properties.get('outline_style')
    if outline_style != 'no' and outline_style is not None:
        hasHalo = True
        haloColor = None
        qgis_outline_color = properties.get('outline_color')
        if qgis_outline_color is not None:
            outline_color_split = qgis_outline_color.split(',')
            haloColor = f"rgba({outline_color_split[0]}, {outline_color_split[1]}, {outline_color_split[2]}, {alpha_255_to_decimal(outline_color_split[3])})"
    else:
        hasHalo = False
        haloColor = 'rgba(0, 0, 0, 1)'

    # Size
    size_unit = properties.get('size_unit')
    size = properties.get("size")
    pointSize = 18
    if size:
        if size_unit == 'MM':
            pointSize = round(float(size)*3.7795275591)
        elif size_unit == 'Pixel':
            pointSize = size

    # Shape
    shapes = {
        "square": "D",
        "diamond": "E",
        "pentagon": "N",
        "hexagon": "H",
        "equilateral_triangle": "B",
        "star": "A",
        "arrow": "F",
        "circle": "K",
        "cross": "K",
        "cross2": "G",
    }
    shape = "K"
    fontName = "Basic-Shapes"
    if properties.get('name') in shapes:
        shape = shapes[properties['name']]
        if properties.get('name') == 'arrow':
            fontName = "CartoVistaArrows"

    marker_style = {
        "color": color,
        "size": pointSize,
        "shape": shape,
        "hasHalo": hasHalo,
        "haloColor": haloColor,
        "fontName": fontName,
    }

    return marker_style


# Line style
def get_line_style(properties):
    # Fill color -> for Outline Simple Line
    fill_color = "rgba(0, 0, 0, 0)" # all 0 to make button visible in UI

    # Color
    qgis_color = properties.get("line_color")
    if qgis_color:
        line_color_split = qgis_color.split(',')
        color = f"rgba({int(line_color_split[0])}, {int(line_color_split[1])}, {int(line_color_split[2])}, {alpha_255_to_decimal(line_color_split[3])})"

    # Width
    width_unit = properties.get('line_width_unit')
    line_width = properties.get("line_width")
    width = 2
    if line_width is not None:
        if width_unit == 'MM':
            width = round(float(line_width)*3.7795275591)
        elif width_unit == 'Pixel':
            width = line_width

    # Pattern
    patterns = {
        "solid": "NORMAL",
        "no": "NORMAL",
        "dash": "DASHSTROKE6",
        "dot": "DASHSTROKE4",
        "dash dot": "DASHSTROKE18",
        "dash dot dot": "DASHSTROKE25",
    }
    pattern = "NORMAL"

    line_style = properties.get("line_style")
    if line_style is not None and line_style in patterns:
        pattern = patterns[properties['line_style']]
        if properties['line_style'] == 'no':
            width = 0

    line_style = {
        "fillSolid": {
            "color": fill_color
        },
         "stroke": {
            "color": color,
            "width": width,
            "pattern": pattern,
        }
    }

    return line_style

def alpha_255_to_decimal(value):
    return (round(int(value) / 255  * 100)) / 100

# Fill style
def get_fill_style(properties):
    # Stroke Color
    stroke_color = "rgba(0, 0, 0, 0)"
    outline_color_qgis = properties.get('outline_color')
    if outline_color_qgis is not None:
        stroke_color_split = outline_color_qgis.split(',')
        stroke_color = f"rgba({int(stroke_color_split[0])}, {int(stroke_color_split[1])}, {int(stroke_color_split[2])}, {alpha_255_to_decimal(stroke_color_split[3])})"

    # Stroke Width
    stroke_width = 2
    outline_width_unit = properties.get('outline_width_unit')
    outline_width = properties.get('outline_width')
    if outline_width is not None:
        if outline_width_unit == 'MM':
            stroke_width = round(float(outline_width)*3.7795275591)
        elif outline_width_unit == 'Pixel':
            stroke_width = outline_width
    
    # Stroke Pattern
    stroke_patterns = {
            "solid": "NORMAL",
            "no": "NORMAL",
            "dash": "DASHSTROKE6",
            "dot": "DASHSTROKE4",
            "dash dot": "DASHSTROKE18",
            "dash dot dot": "DASHSTROKE25",
        }
    
    stroke_pattern = "NORMAL"
    outline_style = properties.get('outline_style')
    if outline_style is not None and outline_style in stroke_patterns:
        stroke_pattern = stroke_patterns[outline_style]

    # Fill Mode
    fill_mode = "SOLID"
    style = properties.get('style')
    if style == 'solid':
        fill_mode = "SOLID"
    elif style == 'no':
        fill_mode = "NONE"
    else:
        fill_mode = "PATTERN"
    
    is_linear = True
    if properties.get('rampType') == 'gradient':
        if properties.get('type') == '1':
            fill_mode = "GRADIENT_RADIAL"
            is_linear = False
        else:
            fill_mode = "GRADIENT_LINEAR"
            is_linear = True

    # Fill Color
    fill_color_qgis = properties.get("color")
    fill_color_split = fill_color_qgis.split(',')
    fill_color = f"rgba({int(fill_color_split[0])}, {int(fill_color_split[1])}, {int(fill_color_split[2])}, {alpha_255_to_decimal(fill_color_split[3])})"

    # Fill Pattern   
    fill_patterns = {
        "horizontal": "HORIZONTALLINES",
        "vertical": "VERTICALLINES",
        "cross": "CROSSHATCH90",
        "b_diagonal": "FRONTSLASHLINES",
        "f_diagonal": "BACKSLASHLINES",
        "diagonal_x": "CROSSHATCH45",
        "dense1": "CROSSDASHEDLINESSIZE5",
        "dense2": "CROSSDASHEDLINESSIZE4",
        "dense3": "CROSSDASHEDLINESSIZE3",
        "dense4": "FRONTDASHEDLINESSPACING5",
        "dense5": "DOTGRID",
        "dense6": "BIGDOTS",
        "dense7": "DOTDIAGLINES",
    }    

    # Fill Style
    fill_style = {
        "stroke": {
            "color": stroke_color,
            "width": stroke_width,
            "pattern": stroke_pattern
        },
        "fillMode": fill_mode,
    }

    # Solid
    if fill_mode == "SOLID":
        fill_solid_style = {
            "fillSolid": {
                "color": fill_color
            }   
        }
        fill_style.update(fill_solid_style)

    # Pattern
    if fill_mode == "PATTERN":
        fill_pattern = "VERTICALLINES"
        if style in fill_patterns:
            fill_pattern = fill_patterns[style]
        fill_pattern_style = {
            "fillPattern": {
                "color": "rgba(0, 0, 0, 0)",
                "patternStyle": fill_pattern,
                "patternColor": fill_color
            }
        }
        fill_style.update(fill_pattern_style)
    
    # Gradient
    if fill_mode in {"GRADIENT_LINEAR", "GRADIENT_RADIAL"}:
        color_qgis = properties.get("color")
        gradient_color_qgis = properties.get("gradient_color2")
        if color_qgis is not None and gradient_color_qgis is not None:
            colorG_split = color_qgis.split(',')
            colorG = f"rgba({int(colorG_split[0])}, {int(colorG_split[1])}, {int(colorG_split[2])}, {alpha_255_to_decimal(colorG_split[3])})"

            gradient_colorG_split = gradient_color_qgis.split(',')
            gradient_colorG = f"rgba({int(gradient_colorG_split[0])}, {int(gradient_colorG_split[1])}, {int(gradient_colorG_split[2])}, {alpha_255_to_decimal(gradient_colorG_split[3])})"

            fill_gradient_style = {
                "fillGradient": {
                    "color": colorG,
                    "gradientColor": gradient_colorG,
                    "isLinear": is_linear
                }
            }
            fill_style.update(fill_gradient_style)

    return fill_style
