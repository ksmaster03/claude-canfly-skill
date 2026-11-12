/**
 * Launch (or re-launch) the persistent, headed Fastwork browser.
 * Run in a BACKGROUND bash task — it never exits.
 *   NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node launch.js [url]
 * First run after the profile has been idle a while sometimes exits immediately with exitCode=21 —
 * just run it again, no fix needed.
 */
const fw = require('./fw-lib.js');
const url = process.argv[2] || 'https://seller.fastwork.co/my-services';
fw.launchPersistent({ url }).catch(e => { console.error('LAUNCH_ERROR', e); process.exit(1); });
