"""Select the numerically newest complete release, independent of API ordering."""
def apply(target, replace):
    path = target/'common/src/main/java/com/shilapi/xcertplay/update/UpdateCatalog.kt'
    replace(path, '/** Returns the first published release that carries an APK and its checksums, or null. */',
        '/** Returns the newest complete published version, regardless of API list order. */')
    replace(path, '        val releases = JSONArray(json)',
        '        val releases = JSONArray(json)\n        var newest: UpdateRelease? = null')
    replace(path, '            val assets = release.optJSONArray("assets") ?: return null',
        '            if (UpdateVersion.parse(tag) == null) continue\n            val assets = release.optJSONArray("assets") ?: continue')
    replace(path, '''            if (apkUrl.isEmpty() || checksumsUrl.isEmpty()) return null
            return UpdateRelease(release.optString("tag_name"), apkName, apkUrl, checksumsUrl)
        }
        return null''', '''            if (apkUrl.isEmpty() || checksumsUrl.isEmpty()) continue
            val candidate = UpdateRelease(tag, apkName, apkUrl, checksumsUrl)
            if (newest == null || UpdateVersion.isNewer(candidate.tagName, newest.tagName)) newest = candidate
        }
        return newest''')
