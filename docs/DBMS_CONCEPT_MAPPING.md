# AURORA — DBMS Syllabus Concept Mapping

This mapping is intentionally evidence-based: it distinguishes concepts demonstrated by the current schema and queries from concepts that are discussed rather than implemented.

| Silberschatz, Korth & Sudarshan (6th ed.) | AURORA evidence | What to demonstrate |
|---|---|---|
| Ch. 1 — Introduction | Centralized MySQL database, desktop client, separate controller/customer roles | Why a DBMS is preferable to disconnected spreadsheets/files; client-server architecture and database users |
| Ch. 2 — Relational Model | 18 operational relations plus four RBAC relations; primary/foreign keys, unique and check constraints | Relations, tuples, attributes, domains, candidate/primary keys, referential and entity integrity |
| Ch. 3 — SQL | DDL, seed DML, constraints, updates/deletes, indexes and triggers | CREATE/ALTER-style schema design, INSERT/UPDATE/DELETE, predicates and ordering |
| Ch. 4 — Intermediate SQL | Joins, outer joins/anti-joins, self-join, nested queries, aggregates, views, UNION | Compare an inner join with an anti-join; query the departure view; explain grouping and HAVING |
| Ch. 7 — Entity-Relationship Model | ER diagram and explicit entities/relationships | Explain cardinalities and participation, and how the ER model maps into foreign keys and junction relations |
| Ch. 8 — Relational Design | Relational schema documentation, decomposed entities and junction relations | State functional dependencies and candidate keys; justify decomposition and discuss lossless join/dependency preservation. Do not claim BCNF for every table without a dependency proof. |
| Ch. 10 — Storage and File Structure | InnoDB tables and indexes | Explain the storage engine, pages/records, clustered primary-key organization and secondary-index storage. These are MySQL/InnoDB implementation details, not custom storage code in AURORA. |
| Ch. 11 — Indexing and Hashing | Seven explicit secondary indexes and EXPLAIN examples | Explain B+ tree indexes, leftmost-prefix behavior for composite indexes, selectivity and plan inspection. Hashing is a theory topic here, not a custom hash index implementation. |

## SQL objects currently present

- **18 operational tables:** the airport, fleet, schedule, compatibility, restrictions, assignment, map, and audit relations.
- **4 RBAC tables:** `app_user`, `app_role`, `app_permission`, and `role_permission`.
- **4 views:** arrivals, departures, assignment summary, and infrastructure summary.
- **7 explicit secondary indexes** in addition to primary/unique indexes.
- **5 triggers:** three assignment audit triggers (insert, update, delete) and two flight endpoint integrity triggers (before insert and before update).

Views are query abstractions and do not count as base tables.

## Important design decisions to defend

1. A physical runway and its directional designations are separate relations. A runway such as 09/27 is one physical asset with two directional operating vectors.
2. A scheduled movement and its runway assignment are separate. An operation can exist before a controller assigns a runway; this supports the unassigned-operations anti-join.
3. Aircraft type/runway compatibility is a many-to-many relation with eligibility attributes.
4. `role_permission` resolves the many-to-many relationship between roles and permissions. The desktop app checks these permissions before exposing protected actions.
5. Assignment revalidation and the assignment write are performed within one transaction. The audit triggers execute as part of the same database transaction.

## Boundaries and viva honesty

- The application RBAC layer gates the desktop application's screens and operations. It is not a substitute for separate MySQL login accounts and server-side GRANT privileges if customers are ever given direct database access.
- InnoDB's internal page layout and B+ tree implementation are explained using MySQL's behavior; AURORA does not implement its own storage manager or index structure.
- The runway validation model is a simplified academic rule set, not a real-world certified runway performance calculation.
- Normalization claims must be supported with explicit functional dependencies and candidate keys. Avoid saying every relation is BCNF unless the proof in the report establishes it.
