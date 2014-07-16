/*
 * Cria tabela de informacoes para os pools
 */
DROP TABLE IF EXISTS poolinfo;
CREATE TABLE poolinfo
(
  id BIGSERIAL NOT NULL,
  pool_name CHARACTER VARYING(64),
  description CHARACTER VARYING(64),
  mask INET NOT NULL,
  router_address INET NOT NULL,
  domain_name CHARACTER VARYING(254),
  rev_domain_name CHARACTER VARYING(254),
  dns_server INET NOT NULL,
  dns_server2 INET,
  netbios CHARACTER VARYING(254),
  netbios_name_server INET,
  netbios_name_server2 INET,
  netbios_node_type SMALLINT NOT NULL DEFAULT 1,
  mtu BIGINT,
  ntp_server CHARACTER VARYING(128),
  lease_time BIGINT NOT NULL,
  root_path CHARACTER VARYING(128),
  boot_filename CHARACTER VARYING(128),
  next_server INET,
  init_address INET,
  end_address INET,
  bind_gateways INET[],
  vlan_id SMALLINT,
  CONSTRAINT poolinfo_pkey PRIMARY KEY (id),
  CONSTRAINT poolinfo_pool_name_key UNIQUE (pool_name),
  CONSTRAINT poolinfo_netbios_node_type_check CHECK (netbios_node_type IN (1, 2, 4, 8))
);

CREATE INDEX poolinfo_pool_name ON poolinfo USING btree (pool_name);

/*
 * Cria tabela de informacoes sobre os usuarios
 */
DROP TABLE IF EXISTS macinfo;
CREATE TABLE macinfo
(
  id BIGSERIAL NOT NULL,
  mac CHARACTER VARYING(64) NOT NULL,
  description TEXT NOT NULL,
  pool BIGSERIAL NOT NULL,
  insert_date TIMESTAMP WITH TIME ZONE NOT NULL,
  expiry_time TIMESTAMP WITH TIME ZONE,
  static BOOLEAN NOT NULL,
  full_access BOOLEAN,
  static_ip INET,
  vlan_id SMALLINT,
  CONSTRAINT macinfo_pkey PRIMARY KEY (id),
  CONSTRAINT macinfo_pool_fkey FOREIGN KEY (pool)
      REFERENCES poolinfo (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT macinfo_mac_key UNIQUE (mac)
);

ALTER TABLE macinfo ADD COLUMN static_standalone BOOLEAN NOT NULL DEFAULT false;
UPDATE macinfo SET static_standalone = true WHERE static = true;

CREATE INDEX macinfo_mac ON macinfo USING btree (mac);

/*
 * Tabela para identificar o fabricante a partir do MAC
 */
DROP TABLE IF EXISTS macvendor;
CREATE TABLE macvendor
(
  mac_prefix CHARACTER VARYING(64) NOT NULL,
  vendor_name CHARACTER VARYING(200) NOT NULL,
  CONSTRAINT macvendor_pkey PRIMARY KEY (mac_prefix)
);

/* Cria usuário para o daemon do freeradius. */
CREATE USER radius WITH PASSWORD 'example-password';

GRANT SELECT ON radcheck TO radius;
GRANT SELECT ON radreply TO radius;
GRANT SELECT ON radgroupcheck TO radius;
GRANT SELECT ON radgroupreply TO radius;
GRANT SELECT ON radusergroup TO radius;
GRANT SELECT ON nas TO radius;
GRANT SELECT ON poolinfo TO radius;
GRANT SELECT, INSERT, UPDATE on radacct TO radius;
GRANT SELECT, INSERT, UPDATE on radpostauth TO radius;
GRANT SELECT, INSERT, UPDATE on radippool TO radius;
GRANT SELECT, INSERT, UPDATE, DELETE on ddns TO radius;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO radius;

/*
 * Cria usuário para o django
 */
CREATE USER django WITH PASSWORD 'example-password';

GRANT ALL PRIVILEGES ON nas TO django;
GRANT ALL PRIVILEGES ON poolinfo TO django;
GRANT ALL PRIVILEGES ON macinfo TO django;
GRANT ALL PRIVILEGES ON ddns TO django;
GRANT ALL PRIVILEGES ON radacct TO django;
GRANT ALL PRIVILEGES ON radcheck TO django;
GRANT ALL PRIVILEGES ON radgroupcheck TO django;
GRANT ALL PRIVILEGES ON radgroupreply TO django;
GRANT ALL PRIVILEGES ON radippool TO django;
GRANT ALL PRIVILEGES ON radpostauth TO django;
GRANT ALL PRIVILEGES ON radreply TO django;
GRANT ALL PRIVILEGES ON radusergroup TO django;
GRANT ALL PRIVILEGES ON macvendor TO django;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO django;

/*
 * Criar as functions necessárias
 */
CREATE OR REPLACE FUNCTION pool_mask(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT mask FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_router_address(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT router_address FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_dns_server(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT dns_server FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_dns_server2(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT dns_server2 FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_netbios_name_server(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT netbios_name_server FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_netbios_name_server2(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT netbios_name_server2 FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_netbios_node_type(VARCHAR(64)) 
RETURNS SMALLINT AS
$delimiter$
  SELECT netbios_node_type FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_domain_name(VARCHAR(64)) 
RETURNS VARCHAR(254) AS
$delimiter$
  SELECT domain_name FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_netbios(VARCHAR(64)) 
RETURNS VARCHAR(254) AS
$delimiter$
  SELECT netbios FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_mtu(VARCHAR(64)) 
RETURNS BIGINT AS
$delimiter$
  SELECT mtu FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_ntp_server(VARCHAR(64)) 
RETURNS VARCHAR(128) AS
$delimiter$
  SELECT ntp_server FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_lease_time(VARCHAR(64)) 
RETURNS BIGINT AS
$delimiter$
  SELECT lease_time FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_root_path(VARCHAR(64)) 
RETURNS VARCHAR(128) AS
$delimiter$
  SELECT root_path FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_boot_filename(VARCHAR(64)) 
RETURNS VARCHAR(128) AS
$delimiter$
  SELECT boot_filename FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_next_server(VARCHAR(64)) 
RETURNS INET AS
$delimiter$
  SELECT next_server FROM poolinfo WHERE pool_name = $1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_count(VARCHAR(254))
RETURNS BIGINT AS
$delimiter$
  SELECT COUNT(*) FROM radcheck WHERE username = $1 AND attribute = 'Pool-Name';
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_name(VARCHAR(254))
RETURNS VARCHAR(64) AS
$delimiter$
  SELECT value FROM radcheck WHERE username = $1 AND attribute = 'Pool-Name';
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_name_by_gw(INET)
RETURNS VARCHAR(64) AS
$delimiter$
  SELECT pool_name FROM poolinfo WHERE $1 = ANY(bind_gateways);
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_count_by_gw(INET)
RETURNS BIGINT AS
$delimiter$
  SELECT COUNT(*) FROM poolinfo WHERE $1 = ANY(bind_gateways);
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_count_by_ippool(INET, CHARACTER VARYING(64))
RETURNS BIGINT AS
$delimiter$
  SELECT COUNT(*) FROM radippool WHERE framedipaddress = $1 AND pool_key = $2;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_name_by_ippool(INET, CHARACTER VARYING(64))
RETURNS VARCHAR(64) AS
$delimiter$
  SELECT pool_name FROM radippool WHERE framedipaddress = $1 AND pool_key = $2 ORDER BY expiry_time DESC LIMIT 1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_count_by_router(INET)
RETURNS BIGINT AS
$delimiter$
  SELECT COUNT(*) FROM poolinfo WHERE router_address = $1 AND pool_name NOT LIKE 'static-%';
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION pool_name_by_router(INET)
RETURNS VARCHAR(64) AS
$delimiter$
  SELECT pool_name FROM poolinfo WHERE router_address = $1 AND pool_name NOT LIKE 'static-%' LIMIT 1;
$delimiter$
LANGUAGE SQL;

CREATE OR REPLACE FUNCTION inet_to_longip(v_t INET)
RETURNS BIGINT AS 
$inet_to_longip$
DECLARE
    t1 TEXT;
    t2 TEXT;
    t3 TEXT;
    t4 TEXT;
    i BIGINT;

BEGIN
    t1 := SPLIT_PART(HOST(v_t), '.',1);
    t2 := SPLIT_PART(HOST(v_t), '.',2);
    t3 := SPLIT_PART(HOST(v_t), '.',3);
    t4 := SPLIT_PART(HOST(v_t), '.',4);
    i := (t1::BIGINT << 24) + (t2::BIGINT << 16) +
            (t3::BIGINT << 8) + t4::BIGINT;
    RETURN i;
END;
$inet_to_longip$ LANGUAGE plpgsql STRICT IMMUTABLE;

CREATE OR REPLACE FUNCTION netmask_bits(v_i BIGINT)
RETURNS INTEGER AS
$netmask_msb$
DECLARE
    n INTEGER;

BEGIN
    n := (32-log(2, 4294967296 - v_i ))::integer;
    RETURN n;
END;
$netmask_msb$ LANGUAGE plpgsql STRICT IMMUTABLE;

CREATE OR REPLACE FUNCTION pool_count_by_ippool_rebind(INET, CHARACTER VARYING(64), INET)
RETURNS BIGINT AS $$
DECLARE mask INET;
DECLARE result BIGINT;
BEGIN  
  SELECT COUNT(*) INTO result FROM radippool WHERE framedipaddress = $1 AND pool_key = $2 AND framedipaddress::inet << (host($3) || '/' || netmask_bits(inet_to_longip((SELECT poolinfo.mask FROM poolinfo WHERE poolinfo.pool_name = radippool.pool_name))))::inet;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION pool_name_by_ippool_rebind(INET, CHARACTER VARYING(64), INET)
RETURNS VARCHAR(64) AS $$
DECLARE mask INET;
DECLARE result VARCHAR(64);
BEGIN  
  SELECT pool_name INTO result FROM radippool WHERE framedipaddress = $1 AND pool_key = $2 AND framedipaddress::inet << (host($3) || '/' || netmask_bits(inet_to_longip((SELECT poolinfo.mask FROM poolinfo WHERE poolinfo.pool_name = radippool.pool_name))))::inet LIMIT 1;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION pool_gateway_on_subnet(INET, CHARACTER VARYING(64))
RETURNS BIGINT AS $$
DECLARE result BIGINT;
BEGIN
  SELECT COUNT(*) INTO result FROM poolinfo WHERE pool_name = $2 AND $1 << (host(router_address) || '/' || netmask_bits(inet_to_longip(mask)))::inet;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

/*
 * Altera a tabela radpostauth para guardar algumas informacoes uteis em relatorios
 */
ALTER TABLE radpostauth ADD COLUMN nasportid CHARACTER VARYING(253);
ALTER TABLE radpostauth ADD COLUMN nasipaddress INET;
