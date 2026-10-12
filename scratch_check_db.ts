import { Database } from "bun:sqlite";

const db = new Database("backend/leados.db");
console.log("COMPANIES:", JSON.stringify(db.query("SELECT id, name, domain, industry, country FROM companies WHERE domain LIKE '%mantech%'").all(), null, 2));
console.log("EVIDENCE:", JSON.stringify(db.query("SELECT id, claim_type, verification_status, claim_value, source_url FROM evidence WHERE company_id IN (SELECT id FROM companies WHERE domain LIKE '%mantech%')").all(), null, 2));
console.log("SIGNALS:", JSON.stringify(db.query("SELECT id, signal_type, summary FROM business_signals WHERE company_id IN (SELECT id FROM companies WHERE domain LIKE '%mantech%')").all(), null, 2));
console.log("SEARCH_RUNS:", JSON.stringify(db.query("SELECT * FROM search_runs ORDER BY created_at DESC LIMIT 3").all(), null, 2));
