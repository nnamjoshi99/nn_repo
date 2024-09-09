dbsize = """SELECT
    DB_NAME() AS [Database_Name],
    sum(CAST( (size * 8.0/1024) AS DECIMAL(15,2) )) AS [Size]
    FROM sys.database_files"""
   
#Database object and counts
Objcount = """SELECT
  'ObjDescription' =
  CASE obj.type
    WHEN 'AF' THEN 'Aggregate function (CLR)'
    WHEN 'C' THEN 'CHECK Constraint'
    WHEN 'D' THEN 'DEFAULT (constraint or stand-alone)'
    WHEN 'EC' THEN 'Edge Constraint'
    WHEN 'ET' THEN 'External Table'
    WHEN 'F' THEN 'FOREIGN KEY Constraint'
    WHEN 'FN' THEN 'SQL Scalar functions'
    WHEN 'FS' THEN 'Assembly (CLR) scalar-function'
    WHEN 'FT' THEN 'Assembly (CLR) table-valued function'
    WHEN 'IF' THEN 'SQL Inline Table-valued Functions'
    WHEN 'IT' THEN 'Internal tables'
    WHEN 'P' THEN 'SQL Stored Procedures'
    WHEN 'PC' THEN 'Assembly (CLR) stored-procedure'
    WHEN 'PG' THEN 'Plan guide'
    WHEN 'PK' THEN 'Primary Key'
    WHEN 'R' THEN 'Rule (old-style, stand-alone)'
    WHEN 'RF' THEN 'Replication-filter procedure'
    WHEN 'S' THEN 'System base table'
    WHEN 'SN' THEN 'Synonym'
    WHEN 'SO' THEN 'Sequence Object'
    WHEN 'ST' THEN 'STATS_TREE'
    WHEN 'SQ' THEN 'Service Queue'
    WHEN 'TA' THEN 'Assembly (CLR) DML triggers'
    WHEN 'TF' THEN 'SQL table-valued-functions'
    WHEN 'TR' THEN 'SQL DML triggers'
    WHEN 'TT' THEN 'Table type'
    WHEN 'UQ' THEN 'UNIQUE Constraint'
    WHEN 'U' THEN 'User Tables'
    WHEN 'V' THEN 'Views'
    WHEN 'X' THEN 'Extended stored procedures'
    ELSE obj.type
  END
 ,COUNT(*) ObjCount
FROM sys.objects obj
WHERE obj.type IN ('X', 'V', 'U', 'TT', 'TR',  'TF', 'TA', 'SQ', 'SO', 'SN',  'RF', 'PC', 'P', 'IT', 'AF', 'ET', 'FN', 'FS', 'FT', 'IF')
GROUP BY obj.type
ORDER BY ObjCount DESC""" 

#types of indexes and counts
indexdf = """SELECT i.type_desc "Index Type", COUNT(*) AS Count
            FROM sys.indexes i, sys.objects o
            WHERE i.object_id = o.object_id 
            and o.type IN ('U', 'V') -- 'U' for user tables, 'V' for views
            group by i.type_desc"""

#Table Info Schema wise
tblSize = """select SchemaName, TableName, Table_Rows,TotalSpaceMB, UsedSpaceMB, UnusedSpaceMB 
from
(
 SELECT 
    s.name AS SchemaName,
    t.name AS TableName,
    p.rows AS Table_Rows,
    CAST(ROUND(((SUM(a.total_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS TotalSpaceMB,
    CAST(ROUND(((SUM(a.used_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS UsedSpaceMB, 
    CAST(ROUND(((SUM(a.total_pages) - SUM(a.used_pages)) * 8) / 1024.00, 2) AS NUMERIC(36, 2)) AS UnusedSpaceMB,
    CASE
                      WHEN  p.rows <= 500 THEN 'Simple'
                      WHEN  p.rows between 500 and 10000 THEN 'Medium'
                      ELSE 'Complex'
                      END AS complexity_level
    FROM 
    sys.tables t
INNER JOIN      
    sys.indexes i ON t.object_id = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN 
    sys.allocation_units a ON p.partition_id = a.container_id
LEFT OUTER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
WHERE 
    t.name NOT LIKE 'dt%' 
    AND t.is_ms_shipped = 0
    AND i.object_id > 255 
GROUP BY 
    t.name, s.name, p.rows
) A
ORDER BY 
    A.TotalSpaceMB DESC, A.TableName""" 


tblComplexity = """select TBL.TABLE_CATALOG AS Catalog, A.SchemaName, complexity_level as Complexity, count(*) as "Table Count"
from
(
 SELECT 
    s.name AS SchemaName,
    t.name AS TableName,
    p.rows AS Table_Rows,
    CAST(ROUND(((SUM(a.total_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS TotalSpaceMB,
    CAST(ROUND(((SUM(a.used_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS UsedSpaceMB, 
    CAST(ROUND(((SUM(a.total_pages) - SUM(a.used_pages)) * 8) / 1024.00, 2) AS NUMERIC(36, 2)) AS UnusedSpaceMB,
    CASE
            WHEN  p.rows <= 500 THEN 'Simple'
            WHEN  p.rows between 500 and 10000 THEN 'Medium'
            ELSE 'Complex'
    END AS complexity_level
    FROM 
    sys.tables t
INNER JOIN      
    sys.indexes i ON t.object_id = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN 
    sys.allocation_units a ON p.partition_id = a.container_id
LEFT OUTER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
WHERE 
    t.name NOT LIKE 'dt%' 
    AND t.is_ms_shipped = 0
    AND i.object_id > 255 
GROUP BY 
    t.name, s.name, p.rows
) A , INFORMATION_SCHEMA.TABLES TBL
where A.TableName = TBL.Table_Name
and A.SchemaName = TBL.Table_Schema
GROUP BY
TBL.TABLE_CATALOG , A.SchemaName, A.complexity_level"""

viewComplexity = """select View_Name "View Name",  "Code Length", join_count "Num of Joins" , IIF(CL=3, 'Yes', 'No') "Complex DataType", Complexity_Level "Complexity Level"
FROM(
select View_Name, definition,v_len "Code Length", join_count , CL,COMP
,CASE 
    when CL = 1 and  COMP = 1 THEN 'Simple'
    when CL = 1 and  COMP = 3 and join_count < 7 THEN 'Medium'
    ELSE 'Complex'
END complexity_level
FROM (
select View_Name, definition,v_len, join_count, CL,
CASE 
    when v_len < 1100 and  join_count <= 3 THEN 1
    when v_len between 1101 and 2200 and  join_count between 4 and 6 THEN 2
    ELSE 3
END COMP
From (
select v.name View_Name, definition, len(definition) v_len, ((len(definition) - len(replace(definition, 'JOIN', '')))/len('JOIN')) as join_count,
CASE
    WHEN CHARINDEX('xml', definition) > 0 or CHARINDEX('varbinary', definition) > 0 or CHARINDEX('hierarchyid', definition) > 0 or CHARINDEX('geography', definition) > 0 or CHARINDEX('nvarchar', definition) > 0 THEN 3
    ELSE 1
END AS CL
from sys.sql_modules m, sys.views v
where m.object_id = v.object_id
--and definition like '%VIEW%'
) T) T1
)TT
order by complexity_level"""

#All Database object complexity counts (percentage)
complexityDF = """WITH CTE_COMPLX_DEFN as
(
SELECT
'ObjDescription' =
  CASE obj.type
    WHEN 'AF' THEN 'Aggregate function (CLR)'-- 
    WHEN 'C' THEN 'CHECK Constraint'--
    WHEN 'D' THEN 'DEFAULT (constraint or stand-alone)'--
    WHEN 'EC' THEN 'Edge Constraint'--
    WHEN 'ET' THEN 'External Table'
    WHEN 'F' THEN 'FOREIGN KEY Constraint'--
    WHEN 'FN' THEN 'SQL Scalar functions'
    WHEN 'FS' THEN 'Assembly (CLR) scalar-function'
    WHEN 'FT' THEN 'Assembly (CLR) table-valued function'
    WHEN 'IF' THEN 'SQL Inline Table-valued Function'
    WHEN 'IT' THEN 'Internal table'
    WHEN 'P' THEN 'SQL Stored Procedure'
    WHEN 'PC' THEN 'Assembly (CLR) stored-procedure'
    WHEN 'PG' THEN 'Plan guide'
    WHEN 'PK' THEN 'Primary Key'--
    WHEN 'R' THEN 'Rule (old-style, stand-alone)'
    WHEN 'RF' THEN 'Replication-filter procedure'
    WHEN 'S' THEN 'System base table'
    WHEN 'SN' THEN 'Synonym'
    WHEN 'SO' THEN 'Sequence Object'
    WHEN 'ST' THEN 'STATS_TREE'
    WHEN 'SQ' THEN 'Service Queue'
    WHEN 'TA' THEN 'Assembly (CLR) DML trigger'
    WHEN 'TF' THEN 'SQL table-valued-function'
    WHEN 'TR' THEN 'SQL DML trigger'
    WHEN 'TT' THEN 'Table type'
    WHEN 'UQ' THEN 'UNIQUE Constraint'
    WHEN 'U' THEN 'User Table'
    WHEN 'V' THEN 'View'
    WHEN 'X' THEN 'Extended stored procedure'
    ELSE obj.type
  END
 ,COUNT(*) ObjCount
FROM sys.objects obj
WHERE obj.type IN ('X', 'V', 'TT', 'TR',  'TF', 'TA', 'SQ', 'SO', 'SN',  'RF', 'PC', 'P', 'IT', 'AF', 'ET', 'FN', 'FS', 'FT', 'IF')
GROUP BY obj.type
)
select DB_NAME() AS TABLE_CATALOG, ObjDescription, 
CAST(CEILING((ObjCount * 0.5)) AS INT) as 'SIMPLE',
CAST(CEILING((ObjCount * 0.3)) AS INT) as 'MEDIUM',
CAST(CEILING((ObjCount * 0.2)) AS INT) as 'COMPLEX'
FROM CTE_COMPLX_DEFN
UNION
SELECT TABLE_CATALOG, OBJECT_TYPE, Simple, Medium, Complex
FROM
(select TBL.TABLE_CATALOG, 'Tables' as OBJECT_TYPE , complexity_level, 1 as count_v
from
(
 SELECT 'Tables' as Tables,
    s.name AS SchemaName,
    t.name AS TableName,
    p.rows AS Table_Rows,
    CAST(ROUND(((SUM(a.total_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS TotalSpaceMB,
    CAST(ROUND(((SUM(a.used_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS UsedSpaceMB, 
    CAST(ROUND(((SUM(a.total_pages) - SUM(a.used_pages)) * 8) / 1024.00, 2) AS NUMERIC(36, 2)) AS UnusedSpaceMB,
    CASE
            WHEN  p.rows <= 500 THEN 'Simple'
            WHEN  p.rows between 500 and 10000 THEN 'Medium'
            ELSE 'Complex'
    END AS complexity_level
    FROM 
    sys.tables t
INNER JOIN      
    sys.indexes i ON t.object_id = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN 
    sys.allocation_units a ON p.partition_id = a.container_id
LEFT OUTER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
WHERE 
    t.name NOT LIKE 'dt%' 
    AND t.is_ms_shipped = 0
    AND i.object_id > 255 
GROUP BY 
    t.name, s.name, p.rows
) A , INFORMATION_SCHEMA.TABLES TBL
where A.TableName = TBL.Table_Name
and A.SchemaName = TBL.Table_Schema
) SRC 
PIVOT
(
sum(count_v) 
FOR complexity_level IN (Simple, Medium, Complex)
--FOR OBJECT_TYPE IN (Tables)
) AS PivotTable"""

#Only Table count and Complexity
tblComplexitydf = """select  complexity_level "Complexity Level", count(*) as "Count"
    FROM (
    select DISTINCT SchemaName, TableName, Table_Rows,TotalSpaceMB, UsedSpaceMB, UnusedSpaceMB,
        CASE
                WHEN  Table_Rows <= 500  and c.data_type not in ('xml','varbinary','hierarchyid','geography','nvarchar') THEN 'Simple'
                WHEN  Table_Rows between 500 and 10000   and c.data_type not in ('xml','varbinary','hierarchyid','geography','nvarchar') THEN 'Medium'
                ELSE 'Complex'
        END AS complexity_level
    from
    (
    SELECT 
        s.name AS SchemaName,
        t.name AS TableName,
        p.rows AS Table_Rows,
        CAST(ROUND(((SUM(a.total_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS TotalSpaceMB,
        CAST(ROUND(((SUM(a.used_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS UsedSpaceMB, 
        CAST(ROUND(((SUM(a.total_pages) - SUM(a.used_pages)) * 8) / 1024.00, 2) AS NUMERIC(36, 2)) AS UnusedSpaceMB
        FROM 
        sys.tables t
    INNER JOIN      
        sys.indexes i ON t.object_id = i.object_id
    INNER JOIN 
        sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
    INNER JOIN 
        sys.allocation_units a ON p.partition_id = a.container_id
    LEFT OUTER JOIN 
        sys.schemas s ON t.schema_id = s.schema_id
    WHERE 
        t.name NOT LIKE 'dt%' 
        AND t.is_ms_shipped = 0
        AND i.object_id > 255 
    GROUP BY 
        t.name, s.name, p.rows
    ) A
    INNER JOIN 
        INFORMATION_SCHEMA.COLUMNS c on A.TableName = c.table_name
    --ORDER BY 
    --   A.TotalSpaceMB DESC, A.TableName
    ) T GROUP BY complexity_level"""

#Top 7 big tables
bigTblDF = """select Top(7) TableName, Table_Rows,TotalSpaceMB, UsedSpaceMB, UnusedSpaceMB 
from
(
 SELECT 
    s.name AS SchemaName,
    t.name AS TableName,
    p.rows AS Table_Rows,
    CAST(ROUND(((SUM(a.total_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS TotalSpaceMB,
    CAST(ROUND(((SUM(a.used_pages) * 8) / 1024.00), 2) AS NUMERIC(36, 2)) AS UsedSpaceMB, 
    CAST(ROUND(((SUM(a.total_pages) - SUM(a.used_pages)) * 8) / 1024.00, 2) AS NUMERIC(36, 2)) AS UnusedSpaceMB,
    --need to add space condition here
    CASE
            WHEN  p.rows <= 500 THEN 'Simple' 
            WHEN  p.rows between 500 and 10000 THEN 'Medium'
            ELSE 'Complex'
    END AS complexity_level
    FROM 
    sys.tables t
INNER JOIN      
    sys.indexes i ON t.object_id = i.object_id
INNER JOIN 
    sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN 
    sys.allocation_units a ON p.partition_id = a.container_id
LEFT OUTER JOIN 
    sys.schemas s ON t.schema_id = s.schema_id
WHERE 
    t.name NOT LIKE 'dt%' 
    AND t.is_ms_shipped = 0
    AND i.object_id > 255 
GROUP BY 
    t.name, s.name, p.rows
) A
ORDER BY 
    A.TotalSpaceMB desc, Table_Rows DESC, A.TableName"""
    
#Normal 50, 30, 20 rule wise calculation
objCountdf = """
    WITH CTE_OBJECT_COUNT AS
    (
    select count(*) as Object_Count from sys.objects obj
    WHERE obj.type IN ('X', 'V', 'TT', 'TR',  'TF', 'TA', 'SQ', 'SO', 'SN',  'RF', 'PC', 'P', 'IT', 'AF', 'ET', 'FN', 'FS', 'FT', 'IF')
    )
    select 'Simple' as Category, CAST(CEILING((Object_Count * 0.5)) AS INT)  Count from CTE_OBJECT_COUNT
    union
    select 'Medium' as Category, CAST(CEILING((Object_Count * 0.3)) AS INT)  Count from CTE_OBJECT_COUNT
    union
    select 'Complex' as Category, CAST(CEILING((Object_Count * 0.2)) AS INT)  Count from CTE_OBJECT_COUNT"""

#Column Data Type Information
colDTdf = """
    SELECT 
    t.NAME AS TableName,
    c.NAME AS ColumnName,
    ty.NAME AS DataType,
    c.max_length AS MaxLength,
    c.precision AS Precision,
    c.scale AS Scale,
    CASE 
        WHEN c.is_nullable = 1 THEN 'YES'
        ELSE 'NO'
    END AS IsNullable
    FROM 
    sys.columns c
    INNER JOIN 
    sys.tables t ON c.object_id = t.object_id
    INNER JOIN 
    sys.types ty ON c.user_type_id = ty.user_type_id
    ORDER BY 
    t.NAME, c.column_id"""
        
#Index Information in Detail 
indInfodf = """SELECT 
    t.NAME AS TableName,
    i.name AS IndexName,
    i.is_disabled AS IsDisabled,
    i.type_desc AS IndexType,
    s.[name] AS SchemaName,
    i.is_unique AS IsUnique,
    i.is_primary_key AS IsPrimaryKey,
    i.is_unique_constraint AS IsUniqueConstraint,
    i.has_filter AS HasFilter,
    i.fill_factor AS "FillFactor"
    FROM 
        sys.indexes i
    INNER JOIN 
        sys.tables t ON i.object_id = t.object_id
    INNER JOIN 
        sys.schemas s ON t.schema_id = s.schema_id
    ORDER BY 
        t.NAME, i.name"""

# Schemas in the database
schemadf = """
    SELECT DB_NAME() AS Database_Name,
        s.name AS schema_name,
        u.name AS schema_owner
    FROM 
        sys.schemas s
    INNER JOIN 
        sys.sysusers u ON u.uid = s.principal_id
        where u.name not in ('INFORMATION_SCHEMA','guest','db_accessadmin',
    'db_backupoperator','db_datareader','db_datawriter','db_ddladmin',
    'db_denydatareader','db_denydatawriter','db_owner','db_securityadmin')
    ORDER BY s.name"""

##User Info
    
# userDF = """select name, sid, type_desc, is_disabled, create_date, default_database_name, default_language_name 
# from sys.server_principals where type in ('U', 'S', 'G', 'C', 'K' ,'E', 'X')
# order by type desc"""

users = """WITH CTE_USERS as
(select T1.[Total Users], T2.[Disabled Users], T1.[Total Users] - T2.[Disabled Users] [Current Active Users] from 
(select count(*) as "Total Users"
from sys.server_principals where type in ('A','U', 'S', 'G', 'C', 'K' ,'E', 'X') 
) T1,
(select count(*) as "Disabled Users"
from sys.server_principals where type in ('A','U', 'S', 'G', 'C', 'K' ,'E', 'X') 
and is_disabled = 1
) T2
)
select 'Total Users' "Users", [Total Users] from CTE_USERS
union all
select 'Current Active Users', [Current Active Users] from CTE_USERS
union all
select 'Disabled Users', [Disabled Users] from CTE_USERS"""

userRoledf = """SELECT 
    dp.name AS UserName,
    dp.type_desc AS UserType,
    r.name AS RoleName
    FROM sys.database_role_members drm
        INNER JOIN sys.database_principals dp ON drm.member_principal_id = dp.principal_id
        INNER JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id"""

userDtlDF = """select name as "User Name", type_desc as "User Type", is_disabled as "Is Disabled", 
create_date as "Creation Date", default_database_name as "Default Database Name", default_language_name as "Default Language Name"
from sys.server_principals where type in ('A','U', 'S', 'G', 'C', 'K' ,'E', 'X')
order by type desc"""

usergraphdf = """select IIF(is_disabled = 0, 'Active', 'Disabled') "User Type", Count
    from (
select is_disabled,
count(*) as Count
from sys.server_principals where type in ('A','U', 'S', 'G', 'C', 'K' ,'E', 'X')
group by is_disabled) t"""


userLoginDF = """select distinct login_name [Login], CAST(login_time AS DATE) as login_date, MAX(login_time) AS [Last Login Time] from sys.dm_exec_sessions
    GROUP BY login_name, CAST(login_time AS DATE)
    order by MAX(login_time) desc, CAST(login_time AS DATE) desc"""

foreignkeydf = """SELECT sch.name AS schema_name,
    tab1.name AS table_name,
    col1.name AS column_name,
    tab2.name AS referenced_table,
    col2.name AS referenced_column,
    obj.name AS FK_NAME
FROM sys.foreign_key_columns fkc
INNER JOIN sys.objects obj
    ON obj.object_id = fkc.constraint_object_id
INNER JOIN sys.tables tab1
    ON tab1.object_id = fkc.parent_object_id
INNER JOIN sys.schemas sch
    ON tab1.schema_id = sch.schema_id
INNER JOIN sys.columns col1
    ON col1.column_id = parent_column_id AND col1.object_id = tab1.object_id
INNER JOIN sys.tables tab2
    ON tab2.object_id = fkc.referenced_object_id
INNER JOIN sys.columns col2
    ON col2.column_id = referenced_column_id AND col2.object_id = tab2.object_id
order by tab1.name"""


lineageDF = """    SELECT
    FK.TABLE_NAME AS table_name,
    FK.COLUMN_NAME AS column_name,
    RC.CONSTRAINT_NAME foreign_key_name,
    PK.TABLE_NAME AS referenced_table_name,
    PK.COLUMN_NAME AS referenced_column_name
FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC
INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS FK
    ON RC.CONSTRAINT_NAME = FK.CONSTRAINT_NAME
INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS PK
    ON RC.UNIQUE_CONSTRAINT_NAME = PK.CONSTRAINT_NAME"""