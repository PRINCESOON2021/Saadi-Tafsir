from pathlib import Path
import re

root = Path('saadi-audio-tafsir')
res = root / 'app/src/main/res'
drawable = res / 'drawable'
drawable.mkdir(parents=True, exist_ok=True)
manifest = root / 'app/src/main/AndroidManifest.xml'
ui = root / 'app/src/main/java/com/distritech/saaditafsir/ui/SaadiApp.kt'

(drawable / 'ic_launcher_saadi.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
<path android:fillColor="#123C32" android:pathData="M0,0H108V108H0Z"/><path android:fillColor="#1B5A49" android:pathData="M54,8C31,8 12,27 12,50v44h84V50C96,27 77,8 54,8Z"/><path android:fillColor="#F4C86A" android:pathData="M54,17C43,25 36,35 36,47c0,12 7,22 18,30c11,-8 18,-18 18,-30c0,-12 -7,-22 -18,-30Z"/><path android:fillColor="#123C32" android:pathData="M54,28C48,34 45,40 45,47c0,7 3,13 9,18c6,-5 9,-11 9,-18c0,-7 -3,-13 -9,-19Z"/><path android:fillColor="#FFF7E6" android:pathData="M25,66C35,62 45,63 54,69V91C45,85 35,84 25,88Z"/><path android:fillColor="#FFF7E6" android:pathData="M83,66C73,62 63,63 54,69V91C63,85 73,84 83,88Z"/><path android:fillColor="#F4C86A" android:pathData="M52,68H56V93H52Z"/>
</vector>''',encoding='utf-8')
(drawable / 'ic_islamic_ornament.xml').write_text('''<?xml version="1.0" encoding="utf-8"?><vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="32dp" android:height="32dp" android:viewportWidth="32" android:viewportHeight="32"><path android:fillColor="#F4C86A" android:pathData="M16,1L20,8L28,8L23,14L26,22L18,20L16,31L14,20L6,22L9,14L4,8L12,8Z"/></vector>''',encoding='utf-8')

m=manifest.read_text(encoding='utf-8')
if 'android:icon=' not in m:
 m=m.replace('android:name=".SaadiApplication"','android:name=".SaadiApplication"\n        android:icon="@drawable/ic_launcher_saadi"\n        android:roundIcon="@drawable/ic_launcher_saadi"')
else:
 m=re.sub(r'android:icon="[^"]+"','android:icon="@drawable/ic_launcher_saadi"',m)
 if 'android:roundIcon=' not in m:m=m.replace('android:icon="@drawable/ic_launcher_saadi"','android:icon="@drawable/ic_launcher_saadi"\n        android:roundIcon="@drawable/ic_launcher_saadi"')
manifest.write_text(m,encoding='utf-8')

s=ui.read_text(encoding='utf-8')
# Required by the custom icon tint expressions below.
if 'import androidx.compose.ui.graphics.Color' not in s:
    lines=s.splitlines()
    insert_at=0
    for i,line in enumerate(lines):
        if line.startswith('import '): insert_at=i+1
    lines.insert(insert_at,'import androidx.compose.ui.graphics.Color')
    s='\n'.join(lines)+'\n'
s=s.replace('Icon(Icons.Default.Settings, "الإعدادات")','Icon(Icons.Default.Settings, "الإعدادات", tint = Color(0xFFF4C86A))')
s=s.replace('Icon(Icons.Default.Search, null)','Icon(Icons.Default.Search, "بحث", tint = Color(0xFF1B5A49))')
s=s.replace('Icon(Icons.Default.Download, "تحميل", tint = Color.White)','Icon(Icons.Default.Download, "تحميل", tint = Color(0xFFF4C86A))')
s=s.replace('Icon(Icons.Default.Favorite, null)','Icon(Icons.Default.Favorite, "مفضلة", tint = Color(0xFFC58A46))')
s=s.replace('Icon(if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, null)','Icon(if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder, "المفضلة", tint = if (isFavorite) Color(0xFFC58A46) else Color(0xFF1B5A49))')
ui.write_text(s,encoding='utf-8')
assert 'import androidx.compose.ui.graphics.Color' in ui.read_text(encoding='utf-8')
print('v0.3.3 Islamic icons + Compose Color import applied')
