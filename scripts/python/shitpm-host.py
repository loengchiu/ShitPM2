from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
USER_HOME = Path.home()
START_MARKER = '<!-- SHITPM GLOBAL RULES START -->'
END_MARKER = '<!-- SHITPM GLOBAL RULES END -->'
BUNDLE_NAME = 'shitpm'
HOSTS = ('codex', 'trae-cn', 'claude-code', 'workbuddy')
SKILL_NAMES = (
    'spm-start',
    'spm-align',
    'spm-design',
    'spm-prd',
    'spm-prototype',
    'spm-fix',
    'spm-design-review',
    'spm-prd-review',
    'spm-prototype-review',
    'spm-prototype-mark',
)


def host_base(host: str) -> Path:
    return {
        'codex': USER_HOME / '.codex',
        'claude-code': USER_HOME / '.claude',
        'trae-cn': USER_HOME / '.trae-cn',
        'workbuddy': USER_HOME / '.workbuddy',
    }[host]


def host_bundle(host: str) -> Path:
    return host_base(host) / BUNDLE_NAME


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _is_junction(path: Path) -> bool:
    """兼容 Python 3.12 以下版本的 is_junction 判断。"""
    return getattr(path, 'is_junction', lambda: False)()


def is_shitpm_junction(path: Path) -> bool:
    """判断路径是否为 ShitPM 管理的 junction。"""
    if not path.exists() and not path.is_symlink():
        return False
    if not (path.is_symlink() or _is_junction(path)):
        return False
    try:
        target = path.resolve()
        return str(REPO_ROOT) in str(target)
    except OSError:
        return False


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or _is_junction(path):
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def safe_remove_junction(path: Path, label: str) -> None:
    """安全移除 junction。如果不是 ShitPM 管理的，报错。"""
    if not path.exists() and not path.is_symlink():
        return
    is_junction = _is_junction(path)
    if path.is_symlink() or is_junction:
        if not is_shitpm_junction(path):
            raise RuntimeError(
                f'{label}: 路径已存在但不是 ShitPM 管理的 junction: {path}\n'
                f'请手动检查后重试。'
            )
        path.unlink()
        return
    raise RuntimeError(
        f'{label}: 路径已存在但不是 junction: {path}\n'
        f'请手动检查后重试。'
    )


def ensure_junction(link_path: Path, target_path: Path) -> None:
    if link_path.exists() or link_path.is_symlink():
        remove_path(link_path)
    ensure_dir(link_path.parent)
    result = subprocess.run(
        ['cmd', '/c', 'mklink', '/J', str(link_path), str(target_path)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f'failed to create junction: {link_path} -> {target_path}: '
            f'{result.stderr or result.stdout}'
        )


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8-sig')


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    normalized = content.replace('\r\n', '\n').replace('\r', '\n')
    path.write_text(normalized, encoding='utf-8-sig')


def upsert_block(path: Path, block: str) -> None:
    existing = read_text(path) if path.exists() else ''
    pattern = re.compile(
        re.escape(START_MARKER) + r'.*?' + re.escape(END_MARKER), re.S
    )
    if pattern.search(existing):
        updated = pattern.sub(lambda _m: block, existing)
    elif existing.strip():
        updated = existing.rstrip() + '\r\n\r\n' + block
    else:
        updated = block
    write_text(path, updated)


def remove_block(path: Path) -> None:
    if not path.exists():
        return
    existing = read_text(path)
    pattern = re.compile(
        r'\r?\n?' + re.escape(START_MARKER) + r'.*?'
        + re.escape(END_MARKER) + r'\r?\n?',
        re.S,
    )
    updated = pattern.sub('', existing).strip()
    if updated:
        write_text(path, updated + '\r\n')
    else:
        write_text(path, '')


# ── bundle 映射 ──────────────────────────────────────────────

def write_bundle_mapping(host: str) -> None:
    safe_remove_junction(host_bundle(host), 'bundle')
    ensure_junction(host_bundle(host), REPO_ROOT)


def verify_bundle_mapping(host: str) -> None:
    path = host_bundle(host)
    if not path.exists():
        raise RuntimeError(f'bundle mapping missing: {path}')
    if not (path / 'AGENTS.md').exists() or not (path / 'skills').exists():
        raise RuntimeError(f'bundle mapping target wrong: {path}')


def remove_bundle_mapping(host: str) -> None:
    path = host_bundle(host)
    if path.exists() or path.is_symlink():
        if is_shitpm_junction(path):
            path.unlink()


# ── skill 映射 ───────────────────────────────────────────────

def write_skill_mappings(host: str) -> None:
    bundle_skills = host_bundle(host) / 'skills'
    skills_root = host_base(host) / 'skills'
    ensure_dir(skills_root)
    for skill_name in SKILL_NAMES:
        target_dir = skills_root / skill_name
        safe_remove_junction(target_dir, f'skill:{skill_name}')
        ensure_junction(target_dir, bundle_skills / skill_name)


def verify_skill_mappings(host: str) -> None:
    skills_root = host_base(host) / 'skills'
    for skill_name in SKILL_NAMES:
        path = skills_root / skill_name / 'SKILL.md'
        if not path.exists():
            raise RuntimeError(f'skill mapping missing: {path}')


def remove_skill_mappings(host: str) -> None:
    skills_root = host_base(host) / 'skills'
    for name in SKILL_NAMES:
        target_dir = skills_root / name
        if target_dir.exists() or target_dir.is_symlink():
            if is_shitpm_junction(target_dir):
                target_dir.unlink()


# ── 全局规则 ─────────────────────────────────────────────────

def write_global_rules(host: str) -> None:
    bundle_root = host_bundle(host).as_posix()
    block = '\n'.join([
        START_MARKER,
        f'ShitPM bundle root: {bundle_root}',
        f'If `.workflow/status.json` exists, read {bundle_root}/AGENTS.md.',
        f'If `.workflow/status.json` doesn\'t exist but user runs `spm-start`, read it too.',
        END_MARKER,
    ])
    if host == 'claude-code':
        upsert_block(host_base(host) / 'CLAUDE.md', block)
        return
    if host == 'codex':
        upsert_block(host_base(host) / 'AGENTS.md', block)
        return
    if host == 'trae-cn':
        content = '---\nalwaysApply: true\n---\n' + '\n'.join([
            f'ShitPM bundle root: {bundle_root}',
            f'If `.workflow/status.json` exists, read {bundle_root}/AGENTS.md.',
            f'If `.workflow/status.json` doesn\'t exist but user runs `spm-start`, read it too.',
        ])
        write_text(host_base(host) / 'rules' / 'shitpm-global.md', content)
        return
    if host == 'workbuddy':
        content = block + '\n'.join([
            '',
            '- 禁止使用 PS1/PowerShell 脚本，可用 js/sh/py 代替',
        ])
        upsert_block(host_base(host) / 'MEMORY.md', content)
        return
    raise ValueError(host)


def verify_global_rules(host: str) -> None:
    target = {
        'codex': host_base(host) / 'AGENTS.md',
        'claude-code': host_base(host) / 'CLAUDE.md',
        'trae-cn': host_base(host) / 'rules' / 'shitpm-global.md',
        'workbuddy': host_base(host) / 'MEMORY.md',
    }[host]
    if not target.exists():
        raise RuntimeError(f'global rules missing: {target}')
    content = read_text(target)
    if 'ShitPM bundle root:' not in content and 'ShitPM 插件' not in content:
        raise RuntimeError(f'global rules missing ShitPM block: {target}')
    if str(host_bundle(host) / 'AGENTS.md') not in content:
        raise RuntimeError(f'global rules missing bundle ref: {target}')


def remove_global_rules(host: str) -> None:
    if host == 'codex':
        remove_block(host_base(host) / 'AGENTS.md')
        return
    if host == 'claude-code':
        remove_block(host_base(host) / 'CLAUDE.md')
        return
    if host == 'trae-cn':
        path = host_base(host) / 'rules' / 'shitpm-global.md'
        if path.exists():
            path.unlink()
        return
    if host == 'workbuddy':
        # WorkBuddy MEMORY.md 可能包含其他内容，仅移除 ShitPM 段落
        remove_block(host_base(host) / 'MEMORY.md')
        return
    raise ValueError(host)


# ── 命令 ─────────────────────────────────────────────────────

def cmd_install(host: str) -> None:
    write_bundle_mapping(host)
    write_skill_mappings(host)
    write_global_rules(host)
    verify_bundle_mapping(host)
    verify_skill_mappings(host)
    verify_global_rules(host)
    print('shitpm-install:ok')


def cmd_verify(host: str) -> None:
    verify_bundle_mapping(host)
    verify_skill_mappings(host)
    verify_global_rules(host)
    print('shitpm-verify:ok')


def cmd_remove(host: str) -> None:
    remove_global_rules(host)
    remove_skill_mappings(host)
    remove_bundle_mapping(host)
    print('shitpm-remove:ok')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='ShitPM host installer')
    sub = parser.add_subparsers(dest='command', required=True)
    for cmd in ('install', 'verify', 'remove'):
        p = sub.add_parser(cmd)
        p.add_argument('--host', required=True, choices=HOSTS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == 'install':
            cmd_install(args.host)
        elif args.command == 'verify':
            cmd_verify(args.host)
        elif args.command == 'remove':
            cmd_remove(args.host)
        else:
            raise ValueError(args.command)
        return 0
    except Exception as exc:
        sys.stderr.write(f'{exc}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
