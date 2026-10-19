// Writes the git commit history to data/git_history.json for the
// release notes page (content/release-notes.md, the git-history shortcode).
// Run automatically by `npm run build` and `npm run dev`.
//
// Each commit is assigned to the release it first shipped in: the nearest
// calendar-version tag (vYYYY.MM.DD or vYYYY.MM.DD.N) at or after it.
// Commits after the newest tag have `release: null` (not yet released).

import { VERSION_TAG, compareVersions } from './version-utils.mjs';
import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';

const FIELD = '\x1f';
const RECORD = '\x1e';


const git = (...args) => execFileSync('git', args, { encoding: 'utf8' });

let log = '';
try {
    log = git(
        'log', '--first-parent', '--decorate-refs=refs/tags/',
        `--format=%H${FIELD}%h${FIELD}%aI${FIELD}%D${FIELD}%s${FIELD}%b${RECORD}`
    );
} catch (error) {
    console.warn(`git-history: could not read git log (${error.message.split('\n')[0]}); writing an empty history`);
}

// Drop trailers such as "Co-Authored-By:" and "Signed-off-by:" from commit bodies.
const TRAILER = /^[A-Za-z-]+-By: .*$|^Signed-off-by: .*$/gim;

// Release date for each tag: when the tag was created (annotated) or its commit date.
const tagDates = {};
try {
    for (const line of git('for-each-ref', '--format=%(refname:short) %(creatordate:iso-strict)', 'refs/tags/').split('\n')) {
        const [tag, date] = line.split(' ');
        if (tag && VERSION_TAG.test(tag)) tagDates[tag] = date;
    }
} catch {
    // No tags yet.
}

let release = null;
const commits = log
    .split(RECORD)
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => {
        const [hash, short, date, refs, subject, body = ''] = entry.split(FIELD);
        const tags = refs
            .split(',')
            .map((ref) => ref.trim().replace(/^tag: /, ''))
            .filter((tag) => VERSION_TAG.test(tag))
            .sort(compareVersions);
        // Log is newest first, so a tag applies to its commit and everything older, until the next tag.
        if (tags.length) release = tags.at(-1);
        return {
            hash,
            short,
            date,
            subject,
            body: body.replace(TRAILER, '').trim(),
            release,
            releaseDate: release ? tagDates[release] ?? null : null
        };
    });

// Current site version: the release tag on HEAD, or the latest release plus
// "+dev" when building unreleased changes (npm run dev, preview deploys).
const latest = commits.find((c) => c.release)?.release ?? null;
const headReleased = commits.length > 0 && commits[0].release !== null &&
    git('tag', '--points-at', 'HEAD').split('\n').includes(commits[0].release);
const clean = git('status', '--porcelain').trim() === '';
const released = headReleased && clean;
const siteVersion = {
    version: latest ? (released ? latest : `${latest}+dev`) : 'unreleased',
    released
};

if (process.env.REQUIRE_RELEASE === 'true' && !released) {
    throw new Error('A deployment must build a clean commit with a calendar-version tag.');
}

mkdirSync('data', { recursive: true });
writeFileSync('data/git_history.json', JSON.stringify(commits, null, 2) + '\n');
writeFileSync('data/site_version.json', JSON.stringify(siteVersion, null, 2) + '\n');
const releases = new Set(commits.map((c) => c.release).filter(Boolean));
console.log(`git-history: wrote ${commits.length} commits in ${releases.size} releases; site version ${siteVersion.version}`);
