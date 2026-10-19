import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { calendarDay, compareVersions, nextVersion } from './version-utils.mjs';
const today = new Date('2026-10-19T12:00:00Z');
const history = fileURLToPath(new URL('./git-history.mjs', import.meta.url));
const release = fileURLToPath(new URL('./release.mjs', import.meta.url));
function fixture() {
    const cwd = mkdtempSync(join(tmpdir(), 'medtrica-version-test-'));
    const git = (...args) => execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
    git('init', '-b', 'main');
    git('config', 'user.name', 'Versioning test');
    git('config', 'user.email', 'test@example.invalid');
    writeFileSync(join(cwd, '.gitignore'), 'data/\n');
    git('add', '.');git('commit', '-m', 'Initial commit');
    return { cwd, git, dispose: () => rmSync(cwd, { recursive: true, force: true }) };
}
test('calendar versions increment numerically and restart on a new day', () => {
    assert.equal(nextVersion([], today), 'v2026.10.19');
    assert.equal(nextVersion(['v2026.10.19'], today), 'v2026.10.19.1');
    assert.equal(nextVersion(['v2026.10.19.9', 'v2026.10.19.10', 'v2026.10.19.draft'], today), 'v2026.10.19.11');
    assert.equal(nextVersion(['v2026.10.18.12'], today), 'v2026.10.19');
    assert.ok(compareVersions('v2026.10.19.10', 'v2026.10.19.9') > 0);
});
test('calendar days use the configured client timezone rather than UTC', () => {
    assert.equal(calendarDay(new Date('2026-10-19T02:00:00Z')), '2026.10.18');
    assert.equal(calendarDay(today), '2026.10.19');
});
test('history groups commits by release and identifies dirty or unreleased previews', () => {
    const f = fixture();
    try {
        f.git('tag', '-a', 'v2026.10.18', '-m', 'First release');
        writeFileSync(join(f.cwd, 'page.txt'), 'A page');f.git('add', '.');f.git('commit', '-m', 'Add a page');
        f.git('tag', '-a', 'v2026.10.19', '-m', 'Second release');
        const generate = () => execFileSync(process.execPath, [history], { cwd: f.cwd, stdio: 'pipe' });
        const version = () => JSON.parse(readFileSync(join(f.cwd, 'data/site_version.json')));
        generate();
        assert.deepEqual(version(), { version: 'v2026.10.19', released: true });
        const commits = JSON.parse(readFileSync(join(f.cwd, 'data/git_history.json')));
        assert.equal(commits[0].release, 'v2026.10.19');
        assert.equal(commits[1].release, 'v2026.10.18');
        writeFileSync(join(f.cwd, 'page.txt'), 'An edited page');generate();
        assert.deepEqual(version(), { version: 'v2026.10.19+dev', released: false });
        f.git('add', '.');f.git('commit', '-m', 'Edit a page');generate();
        assert.equal(version().version, 'v2026.10.19+dev');
        assert.equal(JSON.parse(readFileSync(join(f.cwd, 'data/git_history.json')))[0].release, null);
    } finally { f.dispose(); }
});
test('release dry run reuses a tagged HEAD without creating tags or deployments', () => {
    const f = fixture();
    try {
        f.git('update-ref', 'refs/remotes/origin/main', 'HEAD');
        f.git('tag', '-a', 'v2026.10.19', '-m', 'Release');
        const output = execFileSync(process.execPath, [release, '--dry-run'], { cwd: f.cwd, encoding: 'utf8' });
        assert.match(output, /redeploy v2026\.10\.19/);
        assert.equal(f.git('tag', '--list'), 'v2026.10.19');
        f.git('switch', '-c', 'feature');
        assert.throws(() => execFileSync(process.execPath, [release, '--dry-run'], { cwd: f.cwd, stdio: 'pipe' }));
        f.git('switch', 'main');writeFileSync(join(f.cwd, 'uncommitted.txt'), 'Dirty tree');
        assert.throws(() => execFileSync(process.execPath, [release, '--dry-run'], { cwd: f.cwd, stdio: 'pipe' }));
    } finally { f.dispose(); }
});
