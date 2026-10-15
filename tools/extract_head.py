#!/usr/bin/env python3
"""extract_head.py PACK_MAIN_DIR OUT.iwi [NAME] : pull images/NAME.iwi (default c_ger_zombie_head1_c) out of the map pack's main/iw_*.iwd archives (plain zip files)."""
import sys, os, glob, zipfile
if len(sys.argv) < 3: sys.exit(__doc__)
main, out = sys.argv[1], sys.argv[2]; name = (sys.argv[3] if len(sys.argv) > 3 else 'c_ger_zombie_head1_c') + '.iwi'
for p in sorted(glob.glob(os.path.join(main, '*.iwd'))):
    try:
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.replace('\\', '/').lower() == 'images/' + name.lower():
                    open(out, 'wb').write(z.read(n)); print('extracted', n, 'from', os.path.basename(p)); sys.exit(0)
    except zipfile.BadZipFile: continue
sys.exit('images/%s not found in %s/*.iwd (is the map pack complete and unmodified?)' % (name, main))
