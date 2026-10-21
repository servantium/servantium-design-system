"""Google Drive with no Google integration: Drive for Desktop plus Finder.

macOS privacy protection blocks this process from opening anything inside the Drive
mount, but Finder is allowed in. So the engine works in a plain local folder and asks
Finder (through AppleScript) to copy files across; Drive for Desktop syncs them.

    workspace --Finder copy--> Shared drives/Everything/Customers/<Client>/ --Drive--> cloud

THE RULE: never overwrite. Finder's "replace" deletes and recreates a file, so Drive
issues a new file ID and every share link and comment thread on it breaks. Every
publish is a new file with the next version number. Old versions can move to an
Archive folder through Claude's Drive connector, which keeps their IDs.

Native Google files (.gslides, .gdoc, .gsheet) are only links on disk. Read those
through Claude's Drive connector, not here.
"""
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

WORK = Path(os.environ.get('SV_WORK', Path.home() / 'Servantium-Work'))
SANDBOX = '_Sandbox'
NATIVE = ('.gslides', '.gdoc', '.gsheet', '.gform', '.gdraw', '.gsite')


class DriveError(Exception):
    pass


def drive_root():
    env = os.environ.get('SV_DRIVE_ROOT')
    if env:
        return Path(env)
    hits = sorted(glob.glob(str(Path.home() / 'Library/CloudStorage/GoogleDrive-*')))
    if not hits:
        raise DriveError('Google Drive for Desktop is not mounted. Open Google Drive and sign in.')
    return Path(hits[0])


def customers_dir():
    env = os.environ.get('SV_CUSTOMERS')
    return Path(env) if env else drive_root() / 'Shared drives' / 'Everything' / 'Customers'


# Fictional demo companies live beside Customers, never inside it, so a demo file can
# never be mistaken for (or published into) a real customer's folder.
DEMO_ROOT_NAME = 'Demo Companies'


def demo_dir():
    env = os.environ.get('SV_DEMO')
    return Path(env) if env else drive_root() / 'Shared drives' / 'Everything' / DEMO_ROOT_NAME


def root_dir(root='customers'):
    return demo_dir() if root == 'demo' else customers_dir()


def ensure_folder(base, parts):
    """Create base/parts[0]/parts[1]/... through Finder, one level at a time."""
    folder = Path(base)
    for part in [p for p in parts if p]:
        nxt = folder / part
        if not exists(nxt):
            _osa(_MKDIR, folder, part)
        folder = nxt
    return folder


def target_folder(client, root='customers', sub=None):
    """The folder a build publishes into. Customers: the client folder must already exist
       (a typo should fail, not invent a customer). Demo: created on demand."""
    if root == 'demo':
        base = demo_dir()
        if not exists(base):
            ensure_folder(base.parent, [base.name])
        return ensure_folder(base, [client, *(sub.split('/') if sub else [])])
    folder = client_folder(client)
    return ensure_folder(folder, sub.split('/')) if sub else folder


def _osa(script, *args, tries=4):
    import time
    for attempt in range(tries):
        r = subprocess.run(['osascript', '-', *map(str, args)], input=script, text=True, capture_output=True)
        if r.returncode == 0 or '-1712' not in r.stderr:      # -1712: Finder busy (AppleEvent timed out)
            break
        time.sleep(3 * (attempt + 1))
    if r.returncode != 0:
        msg = r.stderr.strip()
        if 'Not authorized' in msg or '-1743' in msg:
            raise DriveError('Claude is not allowed to control Finder. Allow it in System Settings > '
                             'Privacy & Security > Automation.')
        raise DriveError(msg or 'AppleScript failed')
    return r.stdout.strip()


_LIST = '''on run argv
  set AppleScript's text item delimiters to linefeed
  tell application "System Events"
    if not (exists folder (item 1 of argv)) then return "__MISSING__"
    if (item 2 of argv) is "folders" then
      return (name of every folder of folder (item 1 of argv)) as text
    else
      return (name of every file of folder (item 1 of argv)) as text
    end if
  end tell
end run'''

_EXISTS = '''on run argv
  tell application "System Events" to return (exists disk item (item 1 of argv)) as text
end run'''

_MKDIR = '''on run argv
  tell application "Finder" to make new folder at (POSIX file (item 1 of argv) as alias) with properties {name:(item 2 of argv)}
  return "ok"
end run'''

# No "with replacing": if the name exists, Finder refuses, which is what we want.
_COPY_IN = '''on run argv
  tell application "Finder" to duplicate (POSIX file (item 1 of argv) as alias) to (POSIX file (item 2 of argv) as alias)
  return "ok"
end run'''

# Copying OUT of Drive into the workspace may replace the local copy: no Drive ID involved.
_COPY_OUT = '''on run argv
  tell application "Finder" to duplicate (POSIX file (item 1 of argv) as alias) to (POSIX file (item 2 of argv) as alias) with replacing
  return "ok"
end run'''


# A move inside the Drive mount is a Drive move: the file keeps its ID, link and history.
_MOVE = '''on run argv
  tell application "Finder" to move (POSIX file (item 1 of argv) as alias) to (POSIX file (item 2 of argv) as alias)
  return "ok"
end run'''


def archive(folder, names):
    """Move superseded files into <folder>/_Archive. Never deletes, never overwrites: a name
       already in _Archive gets moved under a dated subfolder instead."""
    folder = Path(folder)
    arch = ensure_folder(folder, ['_Archive'])
    have = set(ls(arch))
    moved = []
    for n in names:
        src = folder / n
        if not exists(src):
            continue
        dest = arch
        if n in have:
            dest = ensure_folder(arch, [dt.datetime.now().strftime('%Y-%m-%d %H%M')])
        _osa(_MOVE, src, dest)
        moved.append(n)
    return moved


def current_files(client, deck, root='customers', sub=None):
    """Every published file (and its _source spec) for one document, so a revision can
       archive them before publishing the new copy under the same name."""
    folder = target_folder(client, root, sub)
    stem = f'{_label(client)} {deck} '
    files = [f for f in ls(folder) if f.startswith(stem)]
    src = folder / '_source'
    specs = [f for f in ls(src) if f.startswith(stem)] if exists(src) else []
    return folder, files, specs


def ls(folder, kind='files'):
    out = _osa(_LIST, folder, kind)
    if out == '__MISSING__':
        raise DriveError(f'No folder at {folder}')
    return [x for x in out.split('\n') if x and not x.startswith('.')]


def exists(path):
    return _osa(_EXISTS, path) == 'true'


def client_folder(client, create_sandbox=True):
    root = customers_dir()
    folder = root / client
    if not exists(folder):
        if client == SANDBOX and create_sandbox:
            _osa(_MKDIR, root, SANDBOX)
        else:
            known = ', '.join(sorted(ls(root, 'folders')))
            raise DriveError(f'No customer folder "{client}". Customers: {known}')
    return folder


def _label(client):
    return 'Sandbox' if client == SANDBOX else client


def next_version(client, deck, folder=None):
    folder = folder or client_folder(client)
    stem = f'{_label(client)} {deck} '
    versions = [int(m.group(1)) for f in ls(folder) if f.startswith(stem)
                for m in [re.search(r' v(\d+)\.[a-z]+$', f)] if m]
    return max(versions, default=0) + 1


def publish(client, deck, date, files, spec_path=None, root='customers', sub=None, kind='deck'):
    """Copy built files into the client's folder under the next version name.
       files: {'.pptx': path, '.pdf': path, ...}. Returns the published names."""
    folder = target_folder(client, root, sub)
    v = next_version(client, deck, folder)
    final = f'{_label(client)} {deck} {date} v{v}'
    stage = WORK / '.publish' / final
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    staged = []
    for ext, src in files.items():
        dst = stage / f'{final}{ext}'
        shutil.copy2(src, dst)
        staged.append(dst)

    present = set(ls(folder))
    clash = [p.name for p in staged if p.name in present]
    if clash:
        raise DriveError(f'Refusing to overwrite {clash}. Publishing never replaces a file.')

    for p in staged:
        _osa(_COPY_IN, p, folder)
    published = [p.name for p in staged]

    if spec_path:
        src_dir = folder / '_source'
        if not exists(src_dir):
            _osa(_MKDIR, folder, '_source')
        spec_copy = stage / f'{final}.{kind}.yaml'
        shutil.copy2(spec_path, spec_copy)
        _osa(_COPY_IN, spec_copy, src_dir)
        published.append(f'_source/{spec_copy.name}')

    missing = [n for n in published if not exists(folder / n)]
    if missing:
        raise DriveError(f'Copied but not visible in Drive yet: {missing}')
    _log({'at': dt.datetime.now().isoformat(timespec='seconds'), 'client': client, 'deck': deck,
          'version': v, 'folder': str(folder), 'files': published})
    return folder, published


_SIZE = '''on run argv
  tell application "System Events" to return (size of disk item (item 1 of argv)) as text
end run'''


def local_size(path):
    return int(_osa(_SIZE, path))


def pull(client, match=None, dest=None, expect_size=None):
    """Copy the latest matching Office file out of the client's folder.

    expect_size: the size Google reports for the file (Drive connector `fileSize`).
    Drive for Desktop uploads in seconds but can go a long time without downloading a
    remote edit, so the local copy may be STALE. Without this check a pull silently
    returns the old file and a diff reports that nothing changed. (Found in the first
    round-trip test: the local copy stayed at the original size for 10+ minutes.)"""
    folder = client_folder(client, create_sandbox=False)
    files = [f for f in ls(folder) if not f.endswith(NATIVE) and (not match or match.lower() in f.lower())]
    office = [f for f in files if f.lower().endswith(('.pptx', '.docx', '.xlsx'))]
    if not office:
        natives = [f for f in ls(folder) if f.endswith(NATIVE) and (not match or match.lower() in f.lower())]
        hint = f' Native Google files ({", ".join(natives[:3])}) must be read through the Drive connector.' if natives else ''
        raise DriveError(f'No PowerPoint, Word or Excel file matching "{match}" in {client}.{hint}')

    def key(f):
        m = re.search(r' v(\d+)\.[a-z]+$', f)
        return (int(m.group(1)) if m else 0, f)
    pick = sorted(office, key=key)[-1]
    if expect_size is not None:
        have = local_size(folder / pick)
        if have != int(expect_size):
            raise DriveError(
                f'The local copy of "{pick}" is stale: {have:,} bytes here, {int(expect_size):,} in Google. '
                'Drive for Desktop has not downloaded the latest edit yet. Wake or restart Google Drive, '
                'then pull again. To see what changed now, read the file through the Drive connector.')
    dest = Path(dest) if dest else WORK / client / 'pulled'
    dest.mkdir(parents=True, exist_ok=True)
    _osa(_COPY_OUT, folder / pick, dest)
    local = dest / pick
    if not local.exists():
        raise DriveError(f'Finder reported success but {local} is missing')
    return local


def _log(entry):
    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / 'publish-log.jsonl', 'a') as fh:
        fh.write(json.dumps(entry) + '\n')
