# Architecting an offline-first HIPAA-compliant Patient CRM for Windows

A fully on-premises, offline-first architecture using **SQLite with SQLCipher** for local storage and **CouchDB/PouchDB** for synchronization provides the optimal balance of HIPAA compliance, data sovereignty, and long-term maintainability for the Patient Explorer App. This combination avoids cloud dependencies, uses mature open-source technologies with 15+ year track records, and enables team members to work offline for extended periods while maintaining complete control over protected health information.

Azure Cosmos DB is **not viable** for this use case—it lacks native offline-first capability and cannot be deployed on-premises. MongoDB Realm was deprecated in September 2024 with end-of-life in September 2025, eliminating another contender. The recommended architecture keeps all PHI on locally-owned hardware, requires no Business Associate Agreements with database vendors, and provides resilience against cloud infrastructure disruptions.

## Why Cosmos DB fails the core requirements

Azure Cosmos DB excels at cloud-to-cloud synchronization but fundamentally lacks client-side offline capabilities. Microsoft provides no built-in SDK for local storage that syncs with Cosmos DB—developers must build custom solutions using separate local databases, change tracking, conflict resolution, and queue management. The Azure Mobile Apps SDK's offline sync feature uses SQLite locally but only supports Azure SQL Database, not Cosmos DB.

The Azure Cosmos DB Emulator is explicitly **not supported for production workloads** by Microsoft. It has hard limitations: single instance only, maximum 10 containers, fixed authentication keys, and no ARM chip support. More critically, Microsoft has confirmed there are **no plans for Azure Stack support** for Cosmos DB. A Cosmos DB technical fellow described the Azure Stack effort as "in a defunct mode."

While Cosmos DB offers excellent HIPAA compliance when used as designed (automatic AES-256 encryption, BAA included in Microsoft licensing, HITRUST certification), these benefits become irrelevant without the ability to operate offline-first and on-premises. The Request Unit pricing model and proprietary NoSQL API also create significant vendor lock-in concerns.

## SQLite with SQLCipher emerges as the optimal local database

For local storage on each Windows device, SQLite with SQLCipher provides the strongest combination of encryption, stability, and .NET integration. SQLite is public domain software with a **20+ year track record**, and SQLCipher adds transparent **AES-256 full-database encryption** that covers all PHI including indexes and temporary data.

SQLCipher Enterprise offers **FIPS 140-2 validated cryptography**, which many healthcare organizations require for federal contracts or maximum compliance assurance. The community edition under BSD license satisfies most use cases. Unlike SQL Server Express's column-level Always Encrypted feature, SQLCipher encrypts the entire database file—this means backups are automatically encrypted without additional configuration.

SQL Server Express has a **10 GB hard limit** that becomes problematic as patient data grows, and it lacks Transparent Data Encryption (requiring third-party solutions like NetLib Encryptionizer at additional cost). SQL Server LocalDB is designed for development only and supports single-user access, making it unsuitable for production. LiteDB, while purely .NET and MIT-licensed, has documented encryption implementation weaknesses including use of the less-secure ECB cipher mode and insufficient key derivation iterations.

Performance testing shows SQLite handles databases with **80,000+ rows across 18 columns** as "small"—far exceeding typical patient CRM needs. Integration with .NET is first-class via Microsoft.Data.Sqlite, and proper indexing with Write-Ahead Logging mode provides excellent concurrent read performance.

## CouchDB and PouchDB deliver proven synchronization

For multi-device synchronization, the CouchDB/PouchDB ecosystem offers the most mature, fully open-source solution that can be entirely self-hosted. Apache CouchDB has been in development since 2005 with Apache Foundation stewardship, while PouchDB has **16,000+ GitHub stars** and active maintenance.

The CouchDB replication protocol operates over standard HTTP, using a changes feed with sequence numbers to track modifications and revision trees (similar to Git) for conflict management. When conflicts occur, CouchDB deterministically selects a winner while preserving losing revisions, allowing applications to surface conflicts for user resolution when needed for clinical data accuracy.

For WPF/.NET applications, two integration paths exist. The hybrid approach embeds an Electron process running PouchDB that handles local storage and sync, communicating with the .NET business logic via IPC. The pure .NET approach uses SQLite locally with custom change tracking, syncing to CouchDB via its REST API using HttpClient or the MyCouch third-party library. The hybrid approach provides battle-tested sync reliability; the pure .NET approach offers a smaller footprint but requires more custom development.

**CouchDB lacks built-in at-rest encryption**, requiring filesystem-level protection (BitLocker on Windows) or the crypto-pouch plugin for PouchDB, which provides xsalsa20-poly1305 encryption of document contents. All replication traffic should use HTTPS with TLS 1.2 or higher.

## Commercial alternative: Ditto for peer-to-peer scenarios

If budget permits and true peer-to-peer synchronization between devices (without requiring a central server) is important, Ditto offers the most advanced mesh networking technology. Ditto uses **CRDT-based conflict resolution** with automatic discovery over Bluetooth LE, WiFi Direct, LAN, and WebSockets.

Ditto provides a native .NET SDK and offers "Big Peer" for enterprise self-hosted deployments. However, it requires commercial licensing (contact for pricing), is backed by a startup rather than a foundation, and creates some vendor dependency. For small medical practices where devices typically sync over a local network, the CouchDB hub-and-spoke model provides equivalent functionality at zero licensing cost.

Realm Database was formally **deprecated by MongoDB in September 2024** with complete end-of-life on September 30, 2025. Realm Sync required MongoDB Atlas cloud—there was never a self-hosted option. New projects should not use Realm.

## Recommended architecture for the Patient Explorer App

The optimal architecture uses a hub-and-spoke pattern with each Windows device maintaining a complete local database that syncs to a central on-premises server when connected.

Each Surface Pro and desktop runs the Patient Explorer application with SQLite/SQLCipher storing the complete patient database locally. The application operates fully offline, recording all patient communications, medication reminders, mPOA contacts, and maintenance items. When the device connects to the clinic network, PouchDB (in a background Electron process) or custom sync code replicates changes bidirectionally with the central CouchDB server.

The central server runs CouchDB on a Windows Server or Linux machine with **16 GB RAM and SSD storage**, protected by BitLocker or LUKS encryption. This server handles conflict resolution for simultaneous edits and provides the authoritative data store for backup purposes. A Restic or Borg backup job runs daily to a local NAS, with weekly encrypted backups to an air-gapped external drive stored offsite.

For remote work scenarios, team members connect via WireGuard VPN before syncing. The system continues functioning if the central server is unavailable—users simply work from their local database until connectivity returns.

## HIPAA compliance through layered encryption and audit controls

The on-premises architecture eliminates Business Associate Agreements with database vendors since no third party accesses PHI. The covered entity (medical practice) assumes **100% responsibility** for all HIPAA safeguards.

Encryption requires two layers for robust protection. **BitLocker with AES-256** encrypts the entire device, protecting against physical theft. **SQLCipher AES-256** encrypts the database file, protecting against unauthorized access even when the device is unlocked. This combination qualifies for breach notification safe harbor under 45 CFR 164.402—if properly encrypted data is breached but keys remain secure, notification is not required.

Audit logging is legally required under §164.312(b) with **6-year retention**. The application must log all successful and failed logins, every patient record accessed or modified, the user and timestamp for each action, and device identifiers. Implement this through database triggers creating shadow tables or application-level logging to a separate audit database. Consider WORM storage for tamper-proof logs.

Access control requirements include unique user identification (no shared accounts), automatic session timeout after **10-15 minutes** of inactivity, and role-based permissions limiting PHI access to minimum necessary. Multi-factor authentication is currently "addressable" but the December 2024 proposed HIPAA Security Rule updates would make MFA **mandatory**—implement Windows Hello or FIDO2 tokens now.

## Integration with AI models and long-term maintenance

IBM Granite models and open-source AI systems integrate well with this architecture since all components use standard formats. Patient data stored in SQLite or CouchDB can be extracted as JSON for AI processing, with appropriate de-identification for any cloud-based inference. Local AI inference using quantized models (via ONNX Runtime or llama.cpp) keeps PHI entirely on-premises.

The .NET ecosystem compatibility is excellent. SQLite integrates via Microsoft.Data.Sqlite with Entity Framework Core support. CouchDB's HTTP API works with standard HttpClient. The entire stack runs on Windows 10/11 Pro or Enterprise with no exotic dependencies.

Long-term maintainability favors this architecture significantly. SQLite, CouchDB, and PostgreSQL (if used as an alternative server database) all have **15-25 year histories** with foundation or enterprise backing. There are no forced version updates, no subscription costs, and no risk of service discontinuation. The open-source licensing (Apache 2.0, public domain, BSD) ensures perpetual access to the technology regardless of vendor decisions.

## Implementation path and key decisions

Begin with a proof of concept implementing SQLite/SQLCipher local storage in a WPF application with basic CRUD operations for patient records. Verify encryption performance with representative data volumes—expect approximately **5-15% overhead** from SQLCipher.

Next, establish the sync infrastructure by deploying CouchDB on a test server and implementing bidirectional replication. The hybrid Electron approach (PouchDB in background process, IPC to .NET) provides proven reliability; the pure REST approach offers simplicity but requires careful conflict handling implementation.

Critical configuration decisions include: whether to use field-level encryption (encrypting individual PHI fields before storage) in addition to full-database encryption; conflict resolution strategy (last-write-wins for non-clinical data, user-prompted resolution for clinical records); and backup frequency based on acceptable data loss window (recommend **maximum 24-hour RPO** for healthcare data).

The Windows device requirement is **Windows 10/11 Pro or Enterprise** for BitLocker support—Home edition lacks this capability. Ensure all devices have TPM 1.2+ for secure key storage.

## Conclusion

The Patient Explorer App achieves its goals through a carefully selected open-source stack that prioritizes offline operation, data sovereignty, and HIPAA compliance without cloud dependencies. SQLite with SQLCipher provides **AES-256 encrypted local storage** with FIPS 140-2 certification available. CouchDB and PouchDB deliver battle-tested synchronization using a standard HTTP protocol. The hub-and-spoke architecture with an on-premises server maintains complete control over PHI while enabling multi-device collaboration.

This architecture costs nothing in database licensing, requires no BAAs with vendors, and uses technologies with multi-decade track records backed by the Apache Foundation and broad open-source communities. The primary development investment lies in building the sync integration layer—roughly equivalent effort whether choosing the Electron hybrid or pure .NET REST approach. By implementing this architecture, the Patient Explorer App will operate reliably offline for extended periods, sync securely when connectivity allows, and maintain HIPAA compliance entirely under the practice's control.