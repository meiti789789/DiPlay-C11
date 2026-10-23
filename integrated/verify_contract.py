"""Fail closed when an upstream update drops a protected C11 adaptation or setting."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
REQUIRED = {
    'common/src/main/java/com/shilapi/xcertplay/CarPlayHostActivity.kt': [
        'C11WheelKeys.attach(this, next)', 'C11WheelKeys.detach(oldController)',
        'C11MusicGuard.stop(session)', 'C11ClusterRoute.normalizeLegacyCenter(this)',
        'return C11ClusterRoute.streamConfig(', 'markerXPercent = AirPlayPersistence.loadClusterMarkerXPercent(this)',
        'markerYPercent = AirPlayPersistence.loadClusterMarkerYPercent(this)',
        'clusterVideoWidth = airPlayConfig.cluster?.widthPixels'],
    'common/src/main/java/com/shilapi/xcertplay/ClusterMapPresentation.kt': [
        'TextureView(context).apply { isOpaque = false }', 'C11ClusterBlendLayout(context)',
        'override fun onSurfaceTextureUpdated(texture: SurfaceTexture) = onC11FrameUpdated()'],
    'common/src/main/java/com/shilapi/xcertplay/DiPlayActivity.kt': [
        'AirPlayPersistence.clusterTurnCardSizePercents()', 'C11AudioDiagnostics.report(appContext)'],
    'shared/src/main/java/com/shilapi/xcertplay/airplay/ClusterTurnCardOverlay.kt': [
        'val extendedSizePercents = (30..190 step 5).toList()', 'val legacySize = size.coerceAtMost(sizePercents.last())'],
    'common/src/main/java/com/shilapi/xcertplay/update/UpdateClient.kt': [
        'https://api.github.com/repos/meiti789789/DiPlay-C11/releases?per_page=30'],
    'common/src/main/java/com/shilapi/xcertplay/update/UpdateCatalog.kt': ['var newest: UpdateRelease? = null'],
    'shared/src/main/java/com/shilapi/xcertplay/airplay/CarPlayClusterDisplay.kt': [
        'INSTRUMENTS("maps:/car/instrumentcluster")'],
}


def verify(target):
    checked = 0
    for overlay in (ROOT / 'overlay').rglob('*'):
        if not overlay.is_file():
            continue
        dest = target / overlay.relative_to(ROOT / 'overlay')
        if not dest.is_file() or dest.read_bytes() != overlay.read_bytes():
            raise ValueError(f'C11 protected overlay changed/missing: {dest.relative_to(target)}')
        checked += 1
    for relative, snippets in REQUIRED.items():
        source = (target / relative).read_text()
        for snippet in snippets:
            if snippet not in source:
                raise ValueError(f'C11 behavior contract missing in {relative}: {snippet}')
    persistence = (target / 'common/src/main/java/com/shilapi/xcertplay/AirPlayPersistence.kt').read_text()
    keys = dict(re.findall(r'const val (\w+)\s*=\s*"([^"\n]*)"', persistence))
    expected = json.loads((ROOT / 'protected_settings.json').read_text())
    for name, value in expected.items():
        if keys.get(name) != value:
            raise ValueError(f'Existing preference key changed/missing: {name}')
    gradle = (target / 'mobile/build.gradle.kts').read_text()
    if 'applicationId = "com.c11.diplay"' not in gradle:
        raise ValueError('C11 package name changed')
    return {'protected_overlay_files': checked, 'preserved_settings_keys': len(expected),
            'note': 'Source contracts plus required regression tests; not actual vehicle validation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.target), indent=2))
