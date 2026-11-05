#!/usr/bin/env python3
"""Werkzeug für die verschlüsselten Daten der Projektübersicht.

Das Passwort kommt aus der Umgebungsvariable PASSWORT und steht nie im Repo.

  PASSWORT=... python3 werkzeuge/daten.py init          einmalig: Salt anlegen
  PASSWORT=... python3 werkzeuge/daten.py entschluesseln  daten/*.enc -> klartext/*.json
  PASSWORT=... python3 werkzeuge/daten.py verschluesseln  klartext/*.json -> daten/*.enc (nur Geänderte)
  PASSWORT=... python3 werkzeuge/daten.py foto <projekt-id> <bild> [<bild> ...]
        verkleinert, verschlüsselt und legt fotos/<projekt-id>/<foto-id>.enc (1600 px)
        und <foto-id>_t.enc (480 px) an. Gibt die Foto-IDs aus.
  PASSWORT=... python3 werkzeuge/daten.py pruefen         prüft, ob das Passwort passt

Format jeder .enc-Datei: 12 Byte IV, dann AES-256-GCM-Chiffrat inklusive 16 Byte Tag.
Schlüssel: PBKDF2-HMAC-SHA256 mit Salt und Iterationen aus daten/meta.json.
"""
import base64, glob, hashlib, io, json, os, secrets, sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(ROOT, "daten")
KLAR = os.path.join(ROOT, "klartext")
FOTOS = os.path.join(ROOT, "fotos")
META = os.path.join(DATEN, "meta.json")
ITER = 600_000


def passwort():
    pw = os.environ.get("PASSWORT")
    if not pw:
        sys.exit("Umgebungsvariable PASSWORT fehlt.")
    return pw


def schluessel():
    with open(META, encoding="utf-8") as f:
        meta = json.load(f)
    salt = base64.b64decode(meta["salt"])
    return hashlib.pbkdf2_hmac("sha256", passwort().encode("utf-8"), salt, meta["iter"], 32)


def enc(key, data: bytes) -> bytes:
    iv = secrets.token_bytes(12)
    return iv + AESGCM(key).encrypt(iv, data, None)


def dec(key, blob: bytes) -> bytes:
    return AESGCM(key).decrypt(blob[:12], blob[12:], None)


def cmd_init():
    if os.path.exists(META):
        sys.exit("daten/meta.json existiert schon. Für ein neues Passwort: passwort_aendern.")
    os.makedirs(DATEN, exist_ok=True)
    meta = {"version": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "salt": base64.b64encode(secrets.token_bytes(16)).decode()}
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("Salt angelegt.")


def cmd_entschluesseln():
    key = schluessel()
    os.makedirs(KLAR, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(DATEN, "*.enc"))):
        name = os.path.basename(path)[:-4]
        with open(path, "rb") as f:
            data = dec(key, f.read())
        with open(os.path.join(KLAR, name + ".json"), "wb") as f:
            f.write(data)
        print("entschlüsselt:", name)


def _kompakt(path):
    with open(path, "rb") as f:
        obj = json.loads(f.read())  # bricht bei ungültigem JSON ab
    return obj, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _geaendert(key, name, data):
    target = os.path.join(DATEN, name + ".enc")
    if not os.path.exists(target):
        return True
    with open(target, "rb") as f:
        try:
            return dec(key, f.read()) != data
        except Exception:
            sys.exit(f"{name}.enc lässt sich mit diesem Passwort nicht öffnen. Abbruch.")


def cmd_verschluesseln():
    import datetime
    key = schluessel()
    pfade = sorted(glob.glob(os.path.join(KLAR, "*.json")))
    geaendert = []
    for path in pfade:
        name = os.path.basename(path)[:-5]
        _, data = _kompakt(path)
        if name != "index" and _geaendert(key, name, data):
            geaendert.append(name)
    idx_path = os.path.join(KLAR, "index.json")
    if geaendert and os.path.exists(idx_path):
        idx, _ = _kompakt(idx_path)
        from zoneinfo import ZoneInfo
        idx["aktualisiert"] = datetime.datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%dT%H:%M")
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
    for path in pfade:
        name = os.path.basename(path)[:-5]
        _, data = _kompakt(path)
        if not _geaendert(key, name, data):
            print("unverändert:", name)
            continue
        with open(os.path.join(DATEN, name + ".enc"), "wb") as f:
            f.write(enc(key, data))
        print("verschlüsselt:", name)


def cmd_foto(pid, bilder):
    from PIL import Image, ImageOps
    key = schluessel()
    ziel = os.path.join(FOTOS, pid)
    os.makedirs(ziel, exist_ok=True)
    for bild in bilder:
        im = ImageOps.exif_transpose(Image.open(bild)).convert("RGB")
        fid = "f" + secrets.token_hex(5)
        for suffix, kante, q in (("", 1600, 80), ("_t", 480, 72)):
            kopie = im.copy()
            kopie.thumbnail((kante, kante))
            buf = io.BytesIO()
            kopie.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
            with open(os.path.join(ziel, fid + suffix + ".enc"), "wb") as f:
                f.write(enc(key, buf.getvalue()))
        print(fid, os.path.basename(bild))


def cmd_pruefen():
    key = schluessel()
    with open(os.path.join(DATEN, "index.enc"), "rb") as f:
        dec(key, f.read())
    print("Passwort passt.")


def cmd_passwort_aendern():
    """PASSWORT=alt NEUES_PASSWORT=neu: alle Daten und Fotos neu verschlüsseln."""
    neu = os.environ.get("NEUES_PASSWORT")
    if not neu:
        sys.exit("Umgebungsvariable NEUES_PASSWORT fehlt.")
    alt_key = schluessel()
    salt = secrets.token_bytes(16)
    neu_key = hashlib.pbkdf2_hmac("sha256", neu.encode("utf-8"), salt, ITER, 32)
    dateien = glob.glob(os.path.join(DATEN, "*.enc")) + glob.glob(os.path.join(FOTOS, "*", "*.enc"))
    inhalte = {}
    for p in dateien:
        with open(p, "rb") as f:
            inhalte[p] = dec(alt_key, f.read())
    for p, data in inhalte.items():
        with open(p, "wb") as f:
            f.write(enc(neu_key, data))
    with open(META, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "salt": base64.b64encode(salt).decode()}, f, indent=2)
    print(f"{len(dateien)} Dateien neu verschlüsselt.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    c = sys.argv[1]
    if c == "init": cmd_init()
    elif c == "entschluesseln": cmd_entschluesseln()
    elif c == "verschluesseln": cmd_verschluesseln()
    elif c == "foto" and len(sys.argv) >= 4: cmd_foto(sys.argv[2], sys.argv[3:])
    elif c == "pruefen": cmd_pruefen()
    elif c == "passwort_aendern": cmd_passwort_aendern()
    else: sys.exit(__doc__)
