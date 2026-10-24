"""Patch Buildozer's Android target to pass p4a's application-child XML option.

This CI-only compatibility patch enables the existing config key in buildozer.spec
when the installed Buildozer release does not yet pass it to python-for-android.
"""
from pathlib import Path
import buildozer.targets.android

target = Path(buildozer.targets.android.__file__)
text = target.read_text(encoding="utf-8")
marker = """        # support for gradle dependencies
"""
block = """        # support for extra XML children inside <application>
        extra_manifest_application_xml = self.buildozer.config.get(
            'app', 'android.extra_manifest_application_xml', fallback='')
        if extra_manifest_application_xml:
            cmd.append('--extra-manifest-application-xml')
            cmd.append(open(extra_manifest_application_xml, 'rt').read())

"""
if "android.extra_manifest_application_xml" in text:
    print("Buildozer already supports android.extra_manifest_application_xml")
elif marker in text:
    text = text.replace(marker, block + marker, 1)
    target.write_text(text, encoding="utf-8")
    print(f"Enabled application-child manifest XML in {target}")
else:
    raise SystemExit(f"Could not safely patch expected Buildozer section in {target}")
