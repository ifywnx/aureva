-- Isolated classroom schema used by PIN-gated presentation mode on Production.
-- NEVER store demo financial records in the live aureva schema.
-- Apply once with a privileged database administrator (no table data copied).
BEGIN;
CREATE SCHEMA IF NOT EXISTS aureva_presentation;
REVOKE ALL ON SCHEMA aureva_presentation FROM PUBLIC;
GRANT USAGE ON SCHEMA aureva_presentation TO aureva_backend;

DO $$
DECLARE tab_name TEXT;
BEGIN
 FOREACH tab_name IN ARRAY ARRAY[
   'users','sessions','attempts','campaigns','campaign_covers','donations',
   'expenses','audit','documents','attestations','reports'
 ] LOOP
   EXECUTE format(
     'CREATE TABLE IF NOT EXISTS aureva_presentation.%I (LIKE aureva.%I INCLUDING ALL)',
     tab_name,tab_name
   );
   EXECUTE format('ALTER TABLE aureva_presentation.%I ENABLE ROW LEVEL SECURITY',tab_name);
   IF NOT EXISTS (
     SELECT 1 FROM pg_policies
     WHERE schemaname='aureva_presentation' AND tablename=tab_name AND policyname='presentation_backend'
   ) THEN
     EXECUTE format(
       'CREATE POLICY presentation_backend ON aureva_presentation.%I FOR ALL TO aureva_backend USING (true) WITH CHECK (true)',
       tab_name
     );
   END IF;
   EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON TABLE aureva_presentation.%I TO aureva_backend',tab_name);
 END LOOP;
END $$;

-- LIKE INCLUDING ALL copies SERIAL defaults verbatim; replace the audit sequence
-- so demo audit IDs do not allocate from Production.
CREATE SEQUENCE IF NOT EXISTS aureva_presentation.audit_id_seq;
ALTER TABLE aureva_presentation.audit
 ALTER COLUMN id SET DEFAULT nextval('aureva_presentation.audit_id_seq'::regclass);
ALTER SEQUENCE aureva_presentation.audit_id_seq OWNED BY aureva_presentation.audit.id;
GRANT USAGE, SELECT ON SEQUENCE aureva_presentation.audit_id_seq TO aureva_backend;

-- LIKE does NOT copy foreign keys. Restore them only within this demo schema.
DO $$
DECLARE item RECORD;
BEGIN
 FOR item IN SELECT * FROM (VALUES
   ('audit','actor_id','users','id',''),
   ('campaign_covers','campaign_id','campaigns','id',' ON DELETE CASCADE'),
   ('campaigns','owner_id','users','id',''),
   ('documents','expense_id','expenses','id',''),
   ('donations','campaign_id','campaigns','id',''),
   ('donations','donor_id','users','id',''),
   ('expenses','campaign_id','campaigns','id',''),
   ('expenses','creator_id','users','id',''),
   ('expenses','reviewer_id','users','id',''),
   ('reports','campaign_id','campaigns','id',''),
   ('sessions','user_id','users','id','')
 ) AS f(tab,col,target_tab,target_col,action)
 LOOP
   IF NOT EXISTS (
     SELECT 1 FROM pg_constraint c
     JOIN pg_class r ON r.oid=c.conrelid
     JOIN pg_namespace n ON n.oid=r.relnamespace
     WHERE n.nspname='aureva_presentation'
       AND r.relname=item.tab
       AND c.conname=item.tab || '_' || item.col || '_fkey'
   ) THEN
     EXECUTE format(
       'ALTER TABLE aureva_presentation.%I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES aureva_presentation.%I(%I)%s',
       item.tab,item.tab || '_' || item.col || '_fkey',
       item.col,item.target_tab,item.target_col,item.action
     );
   END IF;
 END LOOP;
END $$;
COMMIT;
