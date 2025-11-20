from typing import List

from .layer_upload_info import LayerUploadInfo, LayerUploadStatus

def interactive_layer_settings_template(layer_id: str, label_visible: bool, opacity):
    return f"""<LayerSettings layerId="{layer_id}" visible="true" labelVisible="{"true" if label_visible else "false"}" alpha="{opacity}">
    	<StyleSettings styleId="{layer_id}" visible="true" alpha="1" />
    </LayerSettings>"""

def generate_theme_set_group(layer_infos: List[LayerUploadInfo]):
    interactive_layer_settings = ""
    for layer_info in layer_infos:
        if layer_info.status == LayerUploadStatus.COMPLETE:
            interactive_layer_settings += interactive_layer_settings_template(layer_info.cv_identifier, layer_info.add_cv_labels, layer_info.opacity)
    return f"""
    	<ThemeSetGroup id="CVCustomAnalyses">
    		<Title><![CDATA[Custom Analyses]]></Title>
            <ThemeSet id="ThemeSet1" themeSetMode="pinable" selectedDataViewLayerId="USA_States11">
            	<Title><![CDATA[Name]]></Title>
            	<MapSettings>
                	<LayerSettings layerId="Fondstuiles" visible="true" labelVisible="true" activeTileProviderIndex="0" alpha="1" grayscale="0.85" labelSize="1" />
                		{interactive_layer_settings}
                </MapSettings>
            </ThemeSet>
        </ThemeSetGroup>"""
    