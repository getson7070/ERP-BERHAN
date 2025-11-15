DO $$
DECLARE r RECORD;
BEGIN
  -- tables, partitions, materialized views, regular views, sequences, foreign tables
  FOR r IN
    SELECT c.relkind, format('%I.%I', n.nspname, c.relname) AS obj
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r','p','m','v','S','f')
  LOOP
    EXECUTE format('ALTER %s %s OWNER TO erp_user;',
                   CASE r.relkind
                      WHEN 'r' THEN 'TABLE'
                      WHEN 'p' THEN 'TABLE'         -- partition
                      WHEN 'm' THEN 'MATERIALIZED VIEW'
                      WHEN 'v' THEN 'VIEW'
                      WHEN 'S' THEN 'SEQUENCE'
                      WHEN 'f' THEN 'FOREIGN TABLE'
                   END,
                   r.obj);
  END LOOP;

  -- functions/procedures
  FOR r IN
    SELECT format('%I.%I(%s)', n.nspname, p.proname,
                  pg_get_function_identity_arguments(p.oid)) AS fqn
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
  LOOP
    EXECUTE format('ALTER FUNCTION %s OWNER TO erp_user;', r.fqn);
  END LOOP;

  -- types
  FOR r IN
    SELECT format('%I.%I', n.nspname, t.typname) AS tname
    FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
      AND t.typtype IN ('b','c','d','e','m','p','r') -- base, composite, domain, enum, multirange, pseudo, range
  LOOP
    EXECUTE format('ALTER TYPE %s OWNER TO erp_user;', r.tname);
  END LOOP;
END $$;
