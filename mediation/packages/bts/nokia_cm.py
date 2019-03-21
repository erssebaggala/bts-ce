import psycopg2
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import os

class NokiaCM(object):

    def __init__(self):
        ''' Constructor for this class. '''

        #@TODO: Refactor
        sqlalchemy_db_uri = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            os.getenv("BTS_DB_USER", "bodastage"),
            os.getenv("BTS_DB_PASS", "password"),
            os.getenv("BTS_DB_HOST", "database"),
            os.getenv("BTS_DB_PORT", "5432"),
            os.getenv("BTS_DB_NAME", "bts"),
        )

        self.db_engine = create_engine(sqlalchemy_db_uri)

    def extract_live_network_bscs(self):
        Session = sessionmaker(bind=self.db_engine)
        session = Session()

        # BSC6900
        sql = """
            INSERT INTO live_network.nodes
            (pk,date_added, date_modified, type,"name", vendor_pk, tech_pk, added_by, modified_by)
            SELECT 
            NEXTVAL('live_network.seq_nodes_pk'),
            t1."DATETIME" AS date_added, 
            t1."DATETIME" AS date_modified, 
            'BSC' AS node_type,
            TRIM(t1."name") AS "name" , 
            4 AS vendor_pk, -- 1=Ericsson, 2=Huawei
            1 AS tech_pk , -- 1=gsm, 2-umts,3=lte
            0 AS added_by,
            0 AS modified_by
            FROM nokia_cm."BSC" t1
             INNER JOIN cm_loads t3 on t3.pk = t1."LOADID"
            LEFT OUTER  JOIN live_network.nodes t2 ON TRIM(t1."name") = t2."name"
            WHERE 
            t2."name" IS NULL
             ON CONFLICT ON CONSTRAINT unique_nodes
             DO NOTHING
         """

        self.db_engine.execute(text(sql).execution_options(autocommit=True))

    def extract_live_network_rncs(self):
        Session = sessionmaker(bind=self.db_engine)
        session = Session()

        sql = """
             INSERT INTO live_network.nodes
             (pk,date_added, date_modified, type,"name", vendor_pk, tech_pk, added_by, modified_by)
             SELECT 
             NEXTVAL('live_network.seq_nodes_pk'),
             t1."DATETIME" AS date_added, 
             t1."DATETIME" AS date_modified, 
             'RNC' AS node_type,
             TRIM(t1."name") AS "name" , 
             4 AS vendor_pk, -- 1=Ericsson, 2=Huawei, 3-ZTE
             2 AS tech_pk , -- 1=gsm, 2-umts,3=lte
             0 AS added_by,
             0 AS modified_by
             FROM nokia_cm."RNC" t1
             INNER JOIN cm_loads t3 on t3.pk = t1."LOADID"
             LEFT OUTER  JOIN live_network.nodes t2 ON TRIM(t1."name") = t2."name"
             WHERE 
             t2."name" IS NULL
             AND t3.is_current_load = true
             ON CONFLICT ON CONSTRAINT unique_nodes
             DO NOTHING
         """

        self.db_engine.execute(text(sql).execution_options(autocommit=True))

        session.close()

    def extract_live_network_enodebs(self):
        Session = sessionmaker(bind=self.db_engine)
        session = Session()

        sql = """
             INSERT INTO live_network.sites
             (pk, date_added,date_modified, tech_pk, vendor_pk, "name", added_by, modified_by)
             SELECT 
             NEXTVAL('live_network.seq_sites_pk'),
            "DATETIME" AS date_added, 
             "DATETIME" AS date_modified, 
             3 AS tech_pk , -- 1=gsm, 2-umts,3=lte,
             4 AS vendor_pk, -- 1=Ericsson, 2=Huawei
             TRIM(t1."name"),
             0 AS added_by,
             0 AS modified_by 
             FROM
             nokia_cm."LNBTS" t1
             INNER JOIN cm_loads t3 on t3.pk = t1."LOADID"
             LEFT OUTER  JOIN live_network.sites t2 ON TRIM(t1."name") = t2."name"
             WHERE 
             t2."name" IS NULL
              AND t3.is_current_load = true
         """

        self.db_engine.execute(text(sql).execution_options(autocommit=True))

        session.close()

    def extract_live_network_2g_sites(self):
        Session = sessionmaker(bind=self.db_engine)
        session = Session()

        sql = """
            INSERT INTO live_network.sites
            (pk, date_added,date_modified,added_by, modified_by, tech_pk, vendor_pk, name, node_pk)
            SELECT DISTINCT
            NEXTVAL('live_network.seq_sites_pk'),
            t1."DATETIME" AS date_added, 
            t1."DATETIME" AS date_modified, 
            0 AS added_by,
            0 AS modified_by,
            1 AS tech_pk, -- tech 3 -lte, 2 -umts, 1-gms
            4 AS vendor_pk, -- 1- Ericsson, 2 - Huawei, 3 - zte, 4-nokika, etc...
            CONCAT(TRIM(t1."name"),'(',TRIM(t1."lapdLinkName"),')') AS "name",
            t3.pk as node_pk -- node primary key
            from nokia_cm."BCF" t1
            INNER JOIN cm_loads t5 on t5.pk = t1."LOADID"
            INNER JOIN nokia_cm."BSC" t2 ON t2."FILENAME" = t1."FILENAME" 
                AND t2."LOADID" = t1."LOADID" 
                AND SUBSTRING(t1."DISTNAME",'(BSC-\d+)') =   SUBSTRING(t2."DISTNAME",'(BSC-\d+)')
            INNER join live_network.nodes t3 on TRIM( t3."name") = TRIM(t2."name")
                AND t3.vendor_pk = 4 and t3.tech_pk = 1
            LEFT JOIN live_network.sites t4 on t4."name" = CONCAT(TRIM(t1."name"),'(',TRIM(t1."lapdLinkName"),')')
                AND t4.vendor_pk = 4 and t4.tech_pk = 1
            WHERE 
            t4."name" IS NULL
            AND t5.is_current_load = true
            ON CONFLICT ON CONSTRAINT uq_site
            DO NOTHING
        """

        self.db_engine.execute(text(sql).execution_options(autocommit=True))
        session.close()

    def extract_live_network_2g_cells(self):
        Session = sessionmaker(bind=self.db_engine)
        session = Session()

        sql = """
            INSERT INTO live_network.cells
            (pk, date_added,date_modified,added_by, modified_by, tech_pk, vendor_pk, name, site_pk)
            SELECT DISTINCT
            nextval('live_network.seq_cells_pk'),
            t1."DATETIME" AS date_added, 
            t1."DATETIME" AS date_modified, 
            0 AS added_by,
            0 AS modified_by,
            1 AS tech_pk, -- tech 3 -lte, 2 -umts, 1-gms
            4 AS vendor_pk, -- 1- Ericsson, 2 - Huawei, 3 - ZTE, 4-Nokia
            CONCAT(TRIM(t1."name"),'(',TRIM(t1."cellId"),')') AS name,
            t4.pk as site_pk-- site primary key
            FROM nokia_cm."BTS" t1
            -- LOAD
            INNER JOIN cm_loads t8 on t8.pk = t1."LOADID"
            INNER JOIN nokia_cm."BCF" t9 ON 
                t9."FILENAME" = t1."FILENAME" 
                AND t9."LOADID" = t1."LOADID" 
                AND CONCAT(TRIM(t9."DISTNAME"), '/BTS-',TRIM(t1."segmentId")) = TRIM(t1."DISTNAME")
            INNER JOIN live_network.sites t4 ON 
            t4."name" = CONCAT(TRIM(t9."name"),'(',TRIM(t9."lapdLinkName"),')')
                AND t4.vendor_pk = 4
                AND t4.tech_pk = 1
            LEFT JOIN live_network.cells t5 on  t5."name" = CONCAT(TRIM(t1."name"),'(',TRIM(t1."cellId",')'))
                AND t5.tech_pk = 1
                AND t5.vendor_pk = 4
            WHERE
            t5."name" IS NULL
            AND t8.is_current_load = true
            ON CONFLICT ON CONSTRAINT uq_live_cells
            DO NOTHING
        """

        self.db_engine.execute(text(sql).execution_options(autocommit=True))

        session.close()

    def extract_live_network_2g_cells_params(self):
        pass

    def extract_live_network_3g_sites(self):
        pass

    def extract_live_network_3g_cells(self):
        pass

    def extract_live_network_3g_cells_params(self):
        pass

    def extract_live_network_4g_cells(self):
        pass

    def extract_live_network_2g_externals_on_2g(self):
        pass

    def extract_live_network_2g_externals_on_3g(self):
        pass

    def extract_live_network_2g_externals_on_4g(self):
        pass

    def extract_live_network_3g_externals_on_2g(self):
        pass

    def extract_live_network_3g_externals_on_3g(self):
        pass

    def extract_live_network_3g_externals_on_4g(self):
        pass

    def extract_live_network_4g_externals_on_2g(self):
        pass

    def extract_live_network_4g_externals_on_3g(self):
        pass

    def extract_live_network_4g_externals_on_4g(self):
        pass

    def extract_live_network_externals_on_2g(self):
        self.extract_live_network_2g_externals_on_2g()
        self.extract_live_network_3g_externals_on_2g()
        self.extract_live_network_4g_externals_on_2g()

    def extract_live_network_externals_on_3g(self):
        self.extract_live_network_2g_externals_on_3g()
        self.extract_live_network_3g_externals_on_3g()
        self.extract_live_network_4g_externals_on_3g()

    def extract_live_network_externals_on_4g(self):
        self.extract_live_network_2g_externals_on_4g()
        self.extract_live_network_3g_externals_on_4g()
        self.extract_live_network_4g_externals_on_4g()

    def extract_live_network_4g_cells_params(self):
        pass

    def extract_live_network_2g2g_nbrs(self):
        pass

    def extract_live_network_2g3g_nbrs(self):
        pass

    def extract_live_network_2g4g_nbrs(self):
        pass

    def extract_live_network_3g2g_nbrs(self):
        pass

    def extract_live_network_3g3g_nbrs(self):
        pass

    def extract_live_network_3g4g_nbrs(self):
        pass

    def extract_live_network_4g2g_nbrs(self):
        pass

    def extract_live_network_4g3g_nbrs(self):
        pass

    def extract_live_network_4g4g_nbrs(self):
        pass
