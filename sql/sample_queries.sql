-- =============================================================================
-- Oracle MCP Query Registry — Sample Queries
-- Views: VLS_DEAL, VLS_FACILITY, VLS_OUTSTANDING
-- =============================================================================

-- ---------------------------------------------------------------------------
-- VLS_DEAL Queries
-- ---------------------------------------------------------------------------

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_list_active',
    'Return all active deals with key identifying and status fields, ordered by deal name.',
    q'[SELECT DEA_PID_DEAL,
       DEA_NME_DEAL,
       DEA_NUM_DEAL_CNTL,
       DEA_CDE_DEAL_STAT,
       DEA_CDE_BANK,
       DEA_DTE_PROJ_CLOSE,
       DEA_DTE_DEAL_CLSD,
       DEA_UID_ORIGINATOR,
       DEA_UID_REL_MANAGR
FROM VLS_DEAL
WHERE DEA_IND_ACTIVE = 'Y'
ORDER BY DEA_NME_DEAL]',
    NULL,
    'deal,active'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_get_by_id',
    'Return all key fields for a single deal identified by its primary deal ID.',
    q'[SELECT DEA_PID_DEAL,
       DEA_NME_DEAL,
       DEA_NME_ALIAS_NAME,
       DEA_NUM_DEAL_CNTL,
       DEA_CDE_DEAL_STAT,
       DEA_CDE_DEAL_CLASS,
       DEA_CDE_BANK,
       DEA_CDE_ORIG_CCY,
       DEA_AMT_GLO_PRECLO,
       DEA_DTE_PROJ_CLOSE,
       DEA_DTE_DEAL_CLSD,
       DEA_DTE_APPROVED,
       DEA_IND_ACTIVE,
       DEA_UID_ORIGINATOR,
       DEA_UID_REL_MANAGR,
       DEA_CDE_SOURCE_SYS
FROM VLS_DEAL
WHERE DEA_PID_DEAL = :deal_id]',
    '[{"name":"deal_id","type":"VARCHAR2","required":true,"description":"Primary deal identifier"}]',
    'deal,lookup'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_search_by_name',
    'Search deals by partial deal name match (case-insensitive). Returns deal ID, name, alias, status, and bank.',
    q'[SELECT DEA_PID_DEAL,
       DEA_NME_DEAL,
       DEA_NME_ALIAS_NAME,
       DEA_NUM_DEAL_CNTL,
       DEA_CDE_DEAL_STAT,
       DEA_IND_ACTIVE,
       DEA_CDE_BANK
FROM VLS_DEAL
WHERE UPPER(DEA_NME_DEAL) LIKE UPPER('%' || :name_search || '%')
ORDER BY DEA_NME_DEAL]',
    '[{"name":"name_search","type":"VARCHAR2","required":true,"description":"Partial deal name to search for"}]',
    'deal,search'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_list_by_status',
    'Return deals filtered by a specific deal status code, ordered by approval date descending.',
    q'[SELECT DEA_PID_DEAL,
       DEA_NME_DEAL,
       DEA_NUM_DEAL_CNTL,
       DEA_CDE_DEAL_STAT,
       DEA_CDE_BANK,
       DEA_DTE_PROJ_CLOSE,
       DEA_DTE_APPROVED,
       DEA_IND_ACTIVE
FROM VLS_DEAL
WHERE DEA_CDE_DEAL_STAT = :deal_status
ORDER BY DEA_DTE_APPROVED DESC]',
    '[{"name":"deal_status","type":"VARCHAR2","required":true,"description":"Deal status code to filter by (e.g. ACTIVE, CLOSED, PENDING)"}]',
    'deal,status'
);

-- ---------------------------------------------------------------------------
-- VLS_FACILITY Queries
-- ---------------------------------------------------------------------------

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'facility_list_by_deal',
    'Return all facilities belonging to a given deal, including amounts, currency, type, and maturity dates.',
    q'[SELECT FAC_PID_FACILITY,
       FAC_NME_FACILITY,
       FAC_NUM_FAC_CNTL,
       FAC_CDE_FAC_TYPE,
       FAC_CDE_SUBTYPE,
       FAC_CDE_CURRENCY,
       FAC_AMT_GLOBL_ORIG,
       FAC_AMT_GLOBL_CURR,
       FAC_AMT_UNAVAIL,
       FAC_IND_COMMITTED,
       FAC_CDE_PERFORMING,
       FAC_DTE_EFFECTIVE,
       FAC_DTE_FINAL_MAT,
       FAC_DTE_EXPIRY
FROM VLS_FACILITY
WHERE FAC_PID_DEAL = :deal_id
ORDER BY FAC_NME_FACILITY]',
    '[{"name":"deal_id","type":"VARCHAR2","required":true,"description":"Deal ID whose facilities to retrieve"}]',
    'facility,deal'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'facility_list_maturing',
    'Return facilities with a final maturity date falling within the next N days, ordered by maturity date ascending.',
    q'[SELECT FAC_PID_FACILITY,
       FAC_PID_DEAL,
       FAC_NME_FACILITY,
       FAC_CDE_FAC_TYPE,
       FAC_CDE_CURRENCY,
       FAC_AMT_GLOBL_CURR,
       FAC_DTE_FINAL_MAT,
       FAC_DTE_EXPIRY,
       FAC_CDE_PERFORMING
FROM VLS_FACILITY
WHERE FAC_DTE_FINAL_MAT BETWEEN SYSDATE AND SYSDATE + :days_ahead
ORDER BY FAC_DTE_FINAL_MAT]',
    '[{"name":"days_ahead","type":"NUMBER","required":true,"description":"Number of days ahead to look for maturing facilities"}]',
    'facility,maturity,reporting'
);

-- ---------------------------------------------------------------------------
-- VLS_OUTSTANDING Queries
-- ---------------------------------------------------------------------------

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'outstanding_list_by_deal',
    'Return all outstanding positions for a given deal, including amounts, accrual rate, and performance status.',
    q'[SELECT OST_RID_OUTSTANDNG,
       OST_NME_ALIAS,
       OST_CID_BORROWER,
       OST_CDE_OUTSTD_TYP,
       OST_CDE_OBJ_STATE,
       OST_CDE_PERF_STAT,
       OST_CDE_CURRENCY,
       OST_AMT_ORIGINAL,
       OST_AMT_CURRENT,
       OST_AMT_BANK_GROSS,
       OST_AMT_BANK_NET,
       OST_DTE_EFFECTIVE,
       OST_DTE_REPRICING,
       OST_IND_FLOAT_RATE,
       OST_RTE_ACR_RATE
FROM VLS_OUTSTANDING
WHERE OST_PID_DEAL = :deal_id
ORDER BY OST_NME_ALIAS]',
    '[{"name":"deal_id","type":"VARCHAR2","required":true,"description":"Deal ID whose outstanding positions to retrieve"}]',
    'outstanding,deal'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'outstanding_summary_by_currency',
    'Aggregate all non-terminated outstanding positions by currency, returning position count and summed current, gross, and net bank amounts.',
    q'[SELECT OST_CDE_CURRENCY,
       COUNT(*) AS POSITION_COUNT,
       SUM(OST_AMT_CURRENT) AS TOTAL_CURRENT,
       SUM(OST_AMT_BANK_GROSS) AS TOTAL_BANK_GROSS,
       SUM(OST_AMT_BANK_NET) AS TOTAL_BANK_NET
FROM VLS_OUTSTANDING
WHERE OST_CDE_OBJ_STATE NOT IN ('TERMINATED', 'CANCELLED')
GROUP BY OST_CDE_CURRENCY
ORDER BY TOTAL_CURRENT DESC]',
    NULL,
    'outstanding,currency,summary,reporting'
);

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_get_by_cusip',
    'Return deal identifying and status fields for a deal matching a given CUSIP number.',
    q'[SELECT DEA_PID_DEAL,
       DEA_NME_DEAL,
       DEA_NME_ALIAS_NAME,
       DEA_NUM_DEAL_CNTL,
       DEA_TXT_CUSIP_NUM,
       DEA_IND_CUSIP_LST,
       DEA_CDE_DEAL_STAT,
       DEA_CDE_BANK,
       DEA_IND_ACTIVE
FROM VLS_DEAL
WHERE DEA_TXT_CUSIP_NUM = :cusip_num]',
    '[{"name":"cusip_num","type":"VARCHAR2","required":true,"description":"9-character CUSIP number to look up"}]',
    'deal,cusip,lookup'
);

-- ---------------------------------------------------------------------------
-- VLS_FACILITY — CUSIP Query
-- ---------------------------------------------------------------------------

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'facility_get_by_cusip',
    'Return facility identifying and amount fields for a facility matching a given CUSIP number.',
    q'[SELECT FAC_PID_FACILITY,
       FAC_PID_DEAL,
       FAC_NME_FACILITY,
       FAC_NUM_FAC_CNTL,
       FAC_TXT_CUSIP_NUM,
       FAC_IND_CUSIP_LST,
       FAC_CDE_FAC_TYPE,
       FAC_CDE_CURRENCY,
       FAC_AMT_GLOBL_CURR,
       FAC_DTE_FINAL_MAT
FROM VLS_FACILITY
WHERE FAC_TXT_CUSIP_NUM = :cusip_num]',
    '[{"name":"cusip_num","type":"VARCHAR2","required":true,"description":"9-character CUSIP number to look up"}]',
    'facility,cusip,lookup'
);

-- ---------------------------------------------------------------------------
-- Cross-View Query
-- ---------------------------------------------------------------------------

INSERT INTO query_registry (name, description, sql_text, parameters, tags)
VALUES (
    'deal_facility_outstanding_summary',
    'For a given deal, return each facility with a rollup of its outstanding position count and total current outstanding amount.',
    q'[SELECT d.DEA_PID_DEAL,
       d.DEA_NME_DEAL,
       d.DEA_CDE_DEAL_STAT,
       f.FAC_PID_FACILITY,
       f.FAC_NME_FACILITY,
       f.FAC_CDE_FAC_TYPE,
       f.FAC_AMT_GLOBL_CURR,
       f.FAC_CDE_CURRENCY,
       COUNT(o.OST_RID_OUTSTANDNG) AS OUTSTANDING_COUNT,
       SUM(o.OST_AMT_CURRENT) AS TOTAL_OUTSTANDING
FROM VLS_DEAL d
JOIN VLS_FACILITY f ON f.FAC_PID_DEAL = d.DEA_PID_DEAL
LEFT JOIN VLS_OUTSTANDING o ON o.OST_PID_FACILITY = f.FAC_PID_FACILITY
WHERE d.DEA_PID_DEAL = :deal_id
GROUP BY d.DEA_PID_DEAL, d.DEA_NME_DEAL, d.DEA_CDE_DEAL_STAT,
         f.FAC_PID_FACILITY, f.FAC_NME_FACILITY, f.FAC_CDE_FAC_TYPE,
         f.FAC_AMT_GLOBL_CURR, f.FAC_CDE_CURRENCY
ORDER BY f.FAC_NME_FACILITY]',
    '[{"name":"deal_id","type":"VARCHAR2","required":true,"description":"Deal ID to summarize"}]',
    'deal,facility,outstanding,summary,reporting'
);

COMMIT;
