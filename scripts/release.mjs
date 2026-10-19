// Calendar-versioned GitHub Pages release. Published tags are never deleted or moved.
import { execFileSync } from 'node:child_process';
import { VERSION_TAG, compareVersions, nextVersion } from './version-utils.mjs';
const dryRun = process.argv.includes('--dry-run');
const run = (command, args, options = {}) => (execFileSync(command, args, { encoding: 'utf8', ...options }) ?? '').trim();
const git = (...args) => run('git', args);
const fail = (message) => { throw new Error(message); };
let created = false;
let published = false;
let version;
try {
    if (git('branch', '--show-current') !== 'main') fail('Release from main.');
    if (git('status', '--porcelain')) fail('Commit and push all changes before releasing.');
    if (!dryRun) git('fetch', '--quiet', '--tags', 'origin');
    const head = git('rev-parse', 'HEAD');
    if (head !== git('rev-parse', 'origin/main')) fail('main and origin/main differ. Push or pull before releasing.');
    const tags = git('tag', '--list').split('\n').filter(Boolean);
    const existing = git('tag', '--points-at', 'HEAD').split('\n').filter((tag) => VERSION_TAG.test(tag)).sort(compareVersions);
    version = existing.at(-1) ?? nextVersion(tags);
    if (dryRun) {
        console.log(`Would ${existing.length ? 'redeploy' : 'release'} ${version} from ${head.slice(0, 7)} to GitHub Pages. No tags, builds or deployments changed.`);
        process.exit(0);
    }
    run('gh', ['auth', 'status'], { stdio: 'ignore' });
    const repo = JSON.parse(run('gh', ['repo', 'view', '--json', 'nameWithOwner'])).nameWithOwner;
    const listRuns = () => JSON.parse(run('gh', ['run', 'list', '--repo', repo, '--workflow', 'hugo.yaml', '--commit', head, '--limit', '30', '--json', 'databaseId,headBranch,event']));
    const knownRuns = new Set(listRuns().map((item) => item.databaseId));
    if (!existing.length) {
        git('tag', '-a', version, '-m', `Release ${version}`);
        created = true;
    }
    console.log(`Building ${version}`);
    run('npm', ['run', 'build'], { stdio: 'inherit' });
    run('python3', ['scripts/verify_site.py'], { stdio: 'inherit' });
    const remoteTag = git('ls-remote', '--tags', 'origin', `refs/tags/${version}`);
    if (remoteTag) {
        published = true;
        run('gh', ['workflow', 'run', 'hugo.yaml', '--repo', repo, '--ref', version], { stdio: 'inherit' });
    } else {
        // Keep the local tag on ambiguous push failures so a retry never moves a published version.
        published = true;
        git('push', 'origin', `refs/tags/${version}`);
    }
    let deployment;
    for (let attempt = 0; attempt < 20 && !deployment; attempt++) {
        deployment = listRuns().find((item) => item.headBranch === version && !knownRuns.has(item.databaseId));
        if (!deployment) await new Promise((resolve) => setTimeout(resolve, 2000));
    }
    if (!deployment) fail(`Tag ${version} is published, but the workflow has not appeared. Check https://github.com/${repo}/actions before retrying.`);
    run('gh', ['run', 'watch', String(deployment.databaseId), '--repo', repo, '--exit-status', '--interval', '10'], { stdio: 'inherit' });
    console.log(`Released ${version} successfully.`);
} catch (error) {
    if (created && !published) git('tag', '-d', version);
    console.error(`Release failed: ${error.message.split('\n')[0]}`);
    if (published) console.error(`The published tag ${version} was preserved. Rerun npm run deploy to retry the same version.`);
    process.exitCode = 1;
}
