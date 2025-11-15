DO $$
DECLARE
  r record;
BEGIN
  -- 1) Table-like objects first
  FOR r IN
    SELECT c.relkind,
           format('%I.%I', n.nspname, c.relname) AS obj
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r','p','m','v','f')  -- tables, partitions, matviews, views, foreign tables
  LOOP
    EXECUTE format('ALTER %s %s OWNER TO erp_user;',
                   CASE r.relkind
                     WHEN 'r' THEN 'TABLE'
                     WHEN 'p' THEN 'TABLE'
                     WHEN 'm' THEN 'MATERIALIZED VIEW'
                     WHEN 'v' THEN 'VIEW'
                     WHEN 'f' THEN 'FOREIGN TABLE'
                   END,
                   r.obj);
  END LOOP;

  -- 2) Sequences: detach OWNED BY, change owner, reattach
  FOR r IN
    SELECT n.nspname,
           s.relname       AS seqname,
           t.relname       AS tabname,
           a.attname       AS colname
    FROM pg_class s
    JOIN pg_namespace n ON n.oid = s.relnamespace
    LEFT JOIN pg_depend d ON d.objid = s.oid AND d.deptype = 'a'
    LEFT JOIN pg_class  t ON t.oid = d.refobjid
    LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
    WHERE n.nspname = 'public' AND s.relkind = 'S'
  LOOP
    -- If sequence is linked to a table column, drop the link temporarily
    IF r.tabname IS NOT NULL THEN
      EXECUTE format('ALTER SEQUENCE %I.%I OWNED BY NONE;', r.nspname, r.seqname);
    END IF;

    -- Change owner of the sequence
    EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO erp_user;', r.nspname, r.seqname);

    -- Re-establish OWNED BY if there was one
    IF r.tabname IS NOT NULL THEN
      EXECUTE format('ALTER SEQUENCE %I.%I OWNED BY %I.%I;', r.nspname, r.seqname, r.tabname, r.colname);
    END IF;
  END LOOP;
END $$;
