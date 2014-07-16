/*
 * Cria tabela para controle das entradas DDNS.
 */
CREATE TABLE public.ddns
(
  id BIGSERIAL NOT NULL, 
  expiry TIMESTAMP with TIME ZONE NOT NULL, 
  mac CHARACTER VARYING(20) NOT NULL, 
  ip INET NOT NULL, 
  hostname CHARACTER VARYING(254) NOT NULL, 
  fwd_name CHARACTER VARYING(254) NOT NULL, 
  txt CHARACTER VARYING(254) NOT NULL, 
  rev_name CHARACTER VARYING(254), 
  rev_domain CHARACTER VARYING(254),
  hw_type INTEGER NOT NULL,
  CONSTRAINT ddns_fwd_name_key PRIMARY KEY (fwd_name)
) 
WITH (
  OIDS = FALSE
);

CREATE INDEX ddns_expiry ON ddns USING btree (expiry);
CREATE INDEX ddns_ip ON ddns USING btree (ip);
CREATE INDEX ddns_mac ON ddns USING btree (mac);
